import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class MessageSender:
    @staticmethod
    def _escape_applescript_string(text: str) -> str:
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        return text
    
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

