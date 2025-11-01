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
        self.running = False
        self.tasks = set()
    
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
                
                conversation_history = await self.db.get_conversation_history(sender_id)
                
                ai_response = await self.ai_client.get_response(
                    sender_id=sender_id,
                    message_text=message_text,
                    conversation_history=conversation_history
                )
                
                if ai_response:
                    success = await self.message_sender.send_message(sender_id, ai_response)
                    
                    if success:
                        await self.db.save_message(sender_id, ai_response, is_from_user=False)
                        logger.info(f"Successfully handled conversation for {sender_id}")
                    else:
                        logger.error(f"Failed to send message to {sender_id}")
                else:
                    logger.warning(f"No AI response received for {sender_id}, sending fallback")
                    fallback_message = "I'm having trouble processing your message right now. Please try again in a moment."
                    await self.message_sender.send_message(sender_id, fallback_message)
                    
            except Exception as e:
                logger.error(f"Error handling conversation for {sender_id}: {e}", exc_info=True)
    
    async def poll_messages(self):
        last_row_id = await self.db.get_last_processed_row_id()
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

