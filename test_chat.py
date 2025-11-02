import asyncio
import logging
import sys
from datetime import datetime
from typing import List
from ai_client import AIClient
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class TerminalChatTester:
    def __init__(self):
        self.ai_client = AIClient()
        self.conversation_history = []
        self.sender_id = "test_user"
        self.message_delay = 0.8
    
    async def init(self):
        try:
            Config.validate()
            await self.ai_client.init_session()
            logger.info("Chat tester initialized successfully")
            return True
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please set GEMINI_API_KEY in your .env file")
            return False
    
    def _split_into_messages(self, text: str) -> List[str]:
        messages = [msg.strip() for msg in text.split('\n\n') if msg.strip()]
        return messages if messages else [text]
    
    async def send_message(self, message: str) -> List[str]:
        logger.info(f"User: {message}")
        
        self.conversation_history.append({
            'message': message,
            'is_from_user': True,
            'timestamp': datetime.now().timestamp()
        })
        
        response = await self.ai_client.get_response(
            sender_id=self.sender_id,
            message_text=message,
            conversation_history=self.conversation_history
        )
        
        if response:
            messages = self._split_into_messages(response)
            
            for msg in messages:
                self.conversation_history.append({
                    'message': msg,
                    'is_from_user': False,
                    'timestamp': datetime.now().timestamp()
                })
            
            logger.info(f"AI sent {len(messages)} message(s)")
            return messages
        else:
            return ["Error: No response from AI"]
    
    async def run(self):
        print("\n" + "="*60)
        print("🤖 Gemini Chat Tester (Multi-Message Mode)")
        print("="*60)
        print("Type your messages and press Enter to send.")
        print("AI responses are split into separate messages (by paragraph).")
        print("")
        print("Commands:")
        print("  • 'exit', 'quit', or 'q' - Stop the chat")
        print("  • 'clear' - Clear conversation history")
        print("  • 'history' - View conversation history")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    print("\n🗑️  Conversation history cleared.\n")
                    continue
                
                if user_input.lower() == 'history':
                    self._print_history()
                    continue
                
                messages = await self.send_message(user_input)
                
                for i, msg in enumerate(messages):
                    if i > 0:
                        await asyncio.sleep(self.message_delay)
                    print(f"\n🤖 AI: {msg}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error during chat: {e}", exc_info=True)
                print(f"\n❌ Error: {e}\n")
    
    def _print_history(self):
        if not self.conversation_history:
            print("\n📭 No conversation history yet.\n")
            return
        
        print("\n" + "="*60)
        print("📜 Conversation History")
        print("="*60)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "You" if msg['is_from_user'] else "AI"
            timestamp = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
            print(f"[{timestamp}] {role}: {msg['message']}")
        print("="*60 + "\n")
    
    async def cleanup(self):
        await self.ai_client.close_session()
        logger.info("Chat tester closed")

async def main():
    tester = TerminalChatTester()
    
    if not await tester.init():
        return
    
    try:
        await tester.run()
    finally:
        await tester.cleanup()

if __name__ == '__main__':
    asyncio.run(main())

