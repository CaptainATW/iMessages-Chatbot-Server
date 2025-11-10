import aiosqlite
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from src.config import Config

logger = logging.getLogger(__name__)

class ConversationDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.LOCAL_DB_PATH
        self.db = None
    
    async def init_db(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                message_text TEXT NOT NULL,
                is_from_user INTEGER NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        await self.db.execute('''
            CREATE INDEX IF NOT EXISTS idx_sender_timestamp 
            ON messages (sender_id, timestamp)
        ''')
        
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS processing_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_processed_row_id INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        await self.db.execute('''
            INSERT OR IGNORE INTO processing_state (id, last_processed_row_id) 
            VALUES (1, 0)
        ''')
        
        await self.db.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def save_message(self, sender_id: str, message_text: str, is_from_user: bool):
        timestamp = datetime.now().timestamp()
        await self.db.execute(
            'INSERT INTO messages (sender_id, message_text, is_from_user, timestamp) VALUES (?, ?, ?, ?)',
            (sender_id, message_text, int(is_from_user), timestamp)
        )
        await self.db.commit()
        logger.debug(f"Saved message from {'user' if is_from_user else 'bot'}: {sender_id}")
    
    async def get_conversation_history(self, sender_id: str, limit: int = None) -> List[dict]:
        limit = limit or Config.MESSAGE_HISTORY_LIMIT
        cursor = await self.db.execute(
            '''
            SELECT message_text, is_from_user, timestamp 
            FROM messages 
            WHERE sender_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            ''',
            (sender_id, limit)
        )
        rows = await cursor.fetchall()
        
        history = [
            {
                'message': row[0],
                'is_from_user': bool(row[1]),
                'timestamp': row[2]
            }
            for row in reversed(rows)
        ]
        
        return history
    
    async def get_last_processed_row_id(self) -> int:
        cursor = await self.db.execute(
            'SELECT last_processed_row_id FROM processing_state WHERE id = 1'
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    
    async def update_last_processed_row_id(self, row_id: int):
        await self.db.execute(
            'UPDATE processing_state SET last_processed_row_id = ? WHERE id = 1',
            (row_id,)
        )
        await self.db.commit()
        logger.debug(f"Updated last processed row ID to {row_id}")
    
    async def close(self):
        if self.db:
            await self.db.close()
            logger.info("Database connection closed")

