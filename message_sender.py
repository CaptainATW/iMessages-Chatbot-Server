import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class MessageSender:
    def __init__(self):
        self.typing_tasks = {}
    
    @staticmethod
    def _escape_applescript_string(text: str) -> str:
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        return text
    
    async def mark_as_read(self, recipient: str) -> bool:
        escaped_recipient = self._escape_applescript_string(recipient)
        
        applescript = f'''
        tell application "Messages"
            try
                set targetChat to first chat whose participants contains participant "{escaped_recipient}"
                set unread of targetChat to false
            end try
        end tell
        '''
        
        try:
            logger.debug(f"Marking conversation as read for {recipient}")
            
            process = await asyncio.create_subprocess_exec(
                'osascript',
                '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Marked conversation as read for {recipient}")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.warning(f"Could not mark as read for {recipient}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking as read: {e}", exc_info=True)
            return False
    
    async def show_typing_indicator(self, recipient: str) -> bool:
        escaped_recipient = self._escape_applescript_string(recipient)
        
        applescript = f'''
        tell application "Messages"
            activate
        end tell
        
        tell application "System Events"
            tell process "Messages"
                try
                    set frontmost to true
                    delay 0.2
                    
                    set targetWindow to window 1
                    
                    click button 1 of targetWindow
                    delay 0.1
                    
                    keystroke "{escaped_recipient}"
                    delay 0.3
                    keystroke return
                    delay 0.2
                    
                    set value of text area 1 of splitter group 1 of targetWindow to "..."
                    
                on error errMsg
                    return errMsg
                end try
            end tell
        end tell
        '''
        
        try:
            logger.debug(f"Showing typing indicator for {recipient}")
            
            process = await asyncio.create_subprocess_exec(
                'osascript',
                '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Typing indicator shown for {recipient}")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.warning(f"Could not show typing indicator for {recipient}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error showing typing indicator: {e}", exc_info=True)
            return False
    
    async def clear_typing_indicator(self, recipient: str) -> bool:
        escaped_recipient = self._escape_applescript_string(recipient)
        
        applescript = f'''
        tell application "System Events"
            tell process "Messages"
                try
                    set targetWindow to window 1
                    set value of text area 1 of splitter group 1 of targetWindow to ""
                on error errMsg
                    return errMsg
                end try
            end tell
        end tell
        '''
        
        try:
            logger.debug(f"Clearing typing indicator for {recipient}")
            
            process = await asyncio.create_subprocess_exec(
                'osascript',
                '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return True
                
        except Exception as e:
            logger.error(f"Error clearing typing indicator: {e}", exc_info=True)
            return False
    
    async def send_message(self, recipient: str, message_text: str) -> bool:
        escaped_message = self._escape_applescript_string(message_text)
        escaped_recipient = self._escape_applescript_string(recipient)
        
        applescript = f'''
        tell application "Messages"
            set targetService to 1st account whose service type = iMessage
            set targetBuddy to participant "{escaped_recipient}" of targetService
            send "{escaped_message}" to targetBuddy
        end tell
        '''
        
        max_retries = Config.APPLESCRIPT_RETRY_COUNT
        base_delay = Config.APPLESCRIPT_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending message via AppleScript (attempt {attempt + 1}/{max_retries})")
                
                process = await asyncio.create_subprocess_exec(
                    'osascript',
                    '-e', applescript,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Successfully sent message to {recipient}")
                    return True
                else:
                    error_msg = stderr.decode().strip()
                    logger.error(f"AppleScript failed with code {process.returncode}: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"Retrying after {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    return False
                    
            except Exception as e:
                logger.error(f"Error executing AppleScript: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                return False
        
        return False

