import asyncio
import signal
import logging
import sys
from datetime import datetime
from config import Config
from database import ConversationDatabase
from message_monitor import MessageMonitor
from ai_client import AIClient
from message_sender import MessageSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)

logger = logging.getLogger(__name__)

class EchoServer:
    def __init__(self):
        self.db = ConversationDatabase()
        self.monitor = MessageMonitor()
        self.ai_client = AIClient()
        self.message_sender = MessageSender()
        self.semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
        self.gui_lock = asyncio.Lock()
        self.running = False
        self.tasks = set()
    
    @staticmethod
    def split_into_messages(text: str, max_messages: int = 5) -> list:
        if not text:
            return []
        
        parts = text.split('\n\n')
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) <= max_messages:
            return parts
        
        result = parts[:max_messages - 1]
        remaining = '\n\n'.join(parts[max_messages - 1:])
        result.append(remaining)
        
        return result
    
    @staticmethod
    def calculate_typing_delay(message: str) -> float:
        length = len(message)
        
        if length < 20:
            return 1.0
        elif length < 50:
            return 1.5
        elif length < 100:
            return 2.0
        elif length < 200:
            return 2.5
        else:
            return 3.0
    
    async def init(self):
        logger.info("Initializing Echo Server...")
        Config.validate()
        await self.db.init_db()
        await self.ai_client.init_session()
        logger.info("Echo Server initialized successfully")
    
    async def handle_conversation(self, sender_id: str, message_text: str):
        async with self.semaphore:
            try:
                logger.info(f"Handling conversation for {sender_id}")
                
                await self.db.save_message(sender_id, message_text, is_from_user=True)
                
                if Config.ENABLE_TYPING_INDICATOR:
                    async with self.gui_lock:
                        await self.message_sender.navigate_to_chat_and_type_dot(sender_id)
                
                conversation_history = await self.db.get_conversation_history(sender_id)
                
                ai_response = await self.ai_client.get_response(
                    sender_id=sender_id,
                    message_text=message_text,
                    conversation_history=conversation_history
                )
                
                if ai_response:
                    message_parts = self.split_into_messages(ai_response, max_messages=5)
                    logger.info(f"Split response into {len(message_parts)} message(s) for {sender_id}")
                    
                    async with self.gui_lock:
                        for i, message_part in enumerate(message_parts):
                            if i == 0:
                                if Config.ENABLE_TYPING_INDICATOR:
                                    await self.message_sender.clear_dot_from_message_field()
                            
                            success = await self.message_sender.send_message(sender_id, message_part)
                            
                            if success:
                                await self.db.save_message(sender_id, message_part, is_from_user=False)
                                logger.info(f"Sent message part {i+1}/{len(message_parts)} to {sender_id}")
                            else:
                                logger.error(f"Failed to send message part {i+1} to {sender_id}")
                                break
                            
                            if i < len(message_parts) - 1:
                                if Config.ENABLE_TYPING_INDICATOR:
                                    await self.message_sender.navigate_to_chat_and_type_dot(sender_id)
                                    
                                    typing_delay = self.calculate_typing_delay(message_parts[i + 1])
                                    logger.debug(f"Typing indicator shown, waiting {typing_delay}s before next message to {sender_id}")
                                    await asyncio.sleep(typing_delay)
                                    
                                    await self.message_sender.clear_dot_from_message_field()
                    
                    logger.info(f"Successfully handled conversation for {sender_id}")
                else:
                    logger.warning(f"No AI response received for {sender_id}, sending fallback")
                    fallback_message = "I'm having trouble processing your message right now. Please try again in a moment."
                    
                    async with self.gui_lock:
                        if Config.ENABLE_TYPING_INDICATOR:
                            await self.message_sender.clear_dot_from_message_field()
                        await self.message_sender.send_message(sender_id, fallback_message)
                    
            except Exception as e:
                logger.error(f"Error handling conversation for {sender_id}: {e}", exc_info=True)
    
    async def poll_messages(self):
        last_row_id = await self.db.get_last_processed_row_id()
        
        if last_row_id == 0:
            logger.info("First run detected, initializing to current max ROWID to skip historical messages")
            last_row_id = await self.monitor.get_current_max_row_id()
            await self.db.update_last_processed_row_id(last_row_id)
            logger.info(f"Initialized last_processed_row_id to {last_row_id}")
        
        logger.info(f"Starting message polling from row ID {last_row_id}")
        
        while self.running:
            try:
                messages, new_row_id = await self.monitor.poll_new_messages(last_row_id)
                
                if messages:
                    logger.info(f"Found {len(messages)} new message(s)")
                    
                    for sender_id, message_text, _ in messages:
                        task = asyncio.create_task(
                            self.handle_conversation(sender_id, message_text)
                        )
                        self.tasks.add(task)
                        task.add_done_callback(self.tasks.discard)
                    
                    await self.db.update_last_processed_row_id(new_row_id)
                    last_row_id = new_row_id
                
                await asyncio.sleep(Config.POLL_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(Config.POLL_INTERVAL)
    
    async def run(self):
        await self.init()
        self.running = True
        
        logger.info("Echo Server is now running. Press Ctrl+C to stop.")
        
        try:
            await self.poll_messages()
        except asyncio.CancelledError:
            logger.info("Server polling cancelled")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        logger.info("Shutting down Echo Server...")
        self.running = False
        
        if self.tasks:
            logger.info(f"Waiting for {len(self.tasks)} active tasks to complete...")
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        await self.ai_client.close_session()
        await self.db.close()
        
        logger.info("Echo Server shut down successfully")

async def main():
    server = EchoServer()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        server.running = False
    
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)

if __name__ == '__main__':
    asyncio.run(main())

