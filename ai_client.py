import logging
from typing import List, Optional
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = 'gemini-2.5-flash'
        try:
            with open('data/prompt.txt', 'r', encoding='utf-8') as f:
                self.system_instruction = f.read().strip()
        except FileNotFoundError:
            logger.warning("data/prompt.txt not found, using default system instruction.")
            self.system_instruction = 'You are a helpful, empathetic AI assistant.'
    async def init_session(self):
        logger.info("Gemini AI client initialized")
    
    async def close_session(self):
        logger.info("Gemini AI client closed")
    
    async def get_response(self, sender_id: str, message_text: str, conversation_history: List[dict]) -> Optional[str]:
        try:
            contents = self._build_conversation_contents(conversation_history, message_text)
            
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
            )
            
            logger.debug(f"Sending request to Gemini API for {sender_id}")
            
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            if response and response.text:
                logger.info(f"Received Gemini response for {sender_id}")
                return response.text
            else:
                logger.error(f"Gemini response missing text content")
                return None
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return None
    
    def _build_conversation_contents(self, history: List[dict], current_message: str) -> List[types.Content]:
        contents = []
        
        for msg in history:
            role = "user" if msg['is_from_user'] else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg['message'])]
                )
            )
        
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=current_message)]
            )
        )
        
        return contents
