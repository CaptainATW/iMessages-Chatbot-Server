import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    POLL_INTERVAL = float(os.getenv('POLL_INTERVAL', '0.5'))
    MESSAGE_HISTORY_LIMIT = int(os.getenv('MESSAGE_HISTORY_LIMIT', '20'))
    CHAT_DB_PATH = os.path.expanduser('~/Library/Messages/chat.db')
    LOCAL_DB_PATH = 'conversation_state.db'
    MAX_CONCURRENT_REQUESTS = 20
    APPLESCRIPT_RETRY_COUNT = 3
    APPLESCRIPT_RETRY_DELAY = 1
    ENABLE_TYPING_INDICATOR = os.getenv('ENABLE_TYPING_INDICATOR', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        if cls.POLL_INTERVAL <= 0:
            raise ValueError("POLL_INTERVAL must be positive")
        if cls.MESSAGE_HISTORY_LIMIT < 0:
            raise ValueError("MESSAGE_HISTORY_LIMIT must be non-negative")
        
        return True

