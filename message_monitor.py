import aiosqlite
import logging
from typing import List, Tuple
from config import Config

logger = logging.getLogger(__name__)

class MessageMonitor:
    def __init__(self, chat_db_path: str = None):
        self.chat_db_path = chat_db_path or Config.CHAT_DB_PATH
    
    async def poll_new_messages(self, last_row_id: int) -> Tuple[List[Tuple[str, str, int]], int]:
        try:
            async with aiosqlite.connect(f'file:{self.chat_db_path}?mode=ro', uri=True) as db:
                cursor = await db.execute('''
                    SELECT 
                        message.ROWID,
                        chat.chat_identifier,
                        message.text,
                        message.is_from_me
                    FROM message
                    JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
                    JOIN chat ON chat_message_join.chat_id = chat.ROWID
                    WHERE message.ROWID > ?
                        AND message.is_from_me = 0
                        AND message.text IS NOT NULL
                        AND message.text != ''
                    ORDER BY message.ROWID ASC
                ''', (last_row_id,))
                
                rows = await cursor.fetchall()
                
                if not rows:
                    return [], last_row_id
                
                messages = []
                max_row_id = last_row_id
                
                for row in rows:
                    row_id, sender_id, message_text, is_from_me = row
                    
                    if row_id > max_row_id:
                        max_row_id = row_id
                    
                    messages.append((sender_id, message_text, row_id))
                    logger.info(f"New message from {sender_id}: {message_text[:50]}...")
                
                return messages, max_row_id
                
        except Exception as e:
            logger.error(f"Error polling messages: {e}", exc_info=True)
            return [], last_row_id

