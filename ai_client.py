import aiohttp
import asyncio
import logging
from typing import List, Optional
from config import Config

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.endpoint = Config.AI_API_ENDPOINT
        self.api_key = Config.AI_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=Config.AI_API_TIMEOUT)
        self.session = None
    
    async def init_session(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        logger.info("AI client session initialized")
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            logger.info("AI client session closed")
    
    async def get_response(self, sender_id: str, message_text: str, conversation_history: List[dict]) -> Optional[str]:
        if not self.session:
            await self.init_session()
        
        payload = {
            'sender_id': sender_id,
            'message_text': message_text,
            'conversation_history': conversation_history
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending request to AI API (attempt {attempt + 1}/{max_retries})")
                async with self.session.post(self.endpoint, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply_text = data.get('reply', data.get('response', data.get('text')))
                        
                        if reply_text:
                            logger.info(f"Received AI response for {sender_id}")
                            return reply_text
                        else:
                            logger.error(f"AI response missing reply field: {data}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"AI API returned status {response.status}: {error_text}")
                        
                        if response.status >= 500 and attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            logger.info(f"Retrying after {delay}s due to server error")
                            await asyncio.sleep(delay)
                            continue
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"AI API request timed out (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Error calling AI API: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                return None
        
        return None

