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
    
    async def navigate_to_chat_and_type_dot(self, recipient: str) -> bool:
        escaped_recipient = self._escape_applescript_string(recipient)
        
        applescript = f'''
        tell application "Messages"
            activate
            delay 0.3
            
            set targetService to 1st account whose service type = iMessage
            set targetBuddy to participant "{escaped_recipient}" of targetService
            set targetChat to missing value
            
            repeat with aChat in chats
                if targetBuddy is in participants of aChat then
                    set targetChat to aChat
                    exit repeat
                end if
            end repeat
            
            if targetChat is not missing value then
                set id of targetChat to id of targetChat
            end if
        end tell
        
        tell application "System Events"
            tell process "Messages"
                try
                    set frontmost to true
                    delay 0.3
                    
                    keystroke "f" using command down
                    delay 0.3
                    keystroke "{escaped_recipient}"
                    delay 0.5
                    keystroke return
                    delay 0.4
                    
                    keystroke "a" using command down
                    delay 0.1
                    
                    click text area 1 of splitter group 1 of window 1
                    delay 0.2
                    
                    keystroke "."
                    
                on error errMsg
                    log errMsg
                end try
            end tell
        end tell
        '''
        
        try:
            logger.debug(f"Navigating to chat and showing typing indicator for {recipient}")
            
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
    
    
    async def clear_dot_from_message_field(self) -> bool:
        applescript = '''
        tell application "System Events"
            tell process "Messages"
                try
                    click text area 1 of splitter group 1 of window 1
                    delay 0.05
                    keystroke "a" using command down
                    delay 0.05
                    key code 51
                on error errMsg
                    log errMsg
                end try
            end tell
        end tell
        '''
        
        try:
            logger.debug("Clearing dot from message field")
            
            process = await asyncio.create_subprocess_exec(
                'osascript',
                '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return True
                
        except Exception as e:
            logger.error(f"Error clearing message field: {e}", exc_info=True)
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

