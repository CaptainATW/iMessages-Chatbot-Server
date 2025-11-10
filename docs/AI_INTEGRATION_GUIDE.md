# AI Integration Guide - Gemini API

Quick guide for integrating the Gemini API with the iMessage server.

## Your Task

Modify `ai_client.py` to send requests to Google's Gemini API and return responses. The server is already handling message detection, conversation management, and sending replies - you just need to connect it to Gemini.

## Current Structure

The file `ai_client.py` currently has a generic implementation that expects:
- **Input:** `sender_id`, `message_text`, `conversation_history`
- **Output:** A string response from the AI

You need to adapt this to work with Gemini's API format.

## Gemini API Integration

### 1. Update Requirements

Add the Gemini SDK to `requirements.txt`:

```
google-generativeai>=0.3.0
```

Then install: `pip3 install -r requirements.txt`

### 2. Update Configuration

In your `.env` file, replace:
```env
AI_API_ENDPOINT=https://api.example.com/chat
AI_API_KEY=your_api_key_here
```

With:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Modify ai_client.py

Replace the HTTP-based implementation with Gemini SDK calls. Here's the basic structure:

```python
import google.generativeai as genai
from config import Config

class AIClient:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def get_response(self, sender_id: str, message_text: str, conversation_history: List[dict]) -> Optional[str]:
        # Build your prompt using conversation_history
        # Call Gemini API
        # Return the response text
```

## Accessing Conversation Memory

The `conversation_history` parameter passed to `get_response()` contains recent messages from this sender.

### Conversation History Format

```python
[
    {
        'message': 'Hello, how are you?',
        'is_from_user': True,
        'timestamp': 1698765432.123
    },
    {
        'message': 'I am doing well, thanks!',
        'is_from_user': False,
        'timestamp': 1698765433.456
    }
]
```

- **`message`**: The actual text content
- **`is_from_user`**: `True` if from the user, `False` if from AI
- **`timestamp`**: Unix timestamp (float)
- Ordered chronologically (oldest first)

### Building Context for Gemini

Convert the conversation history into Gemini's format:

```python
def build_gemini_context(conversation_history):
    messages = []
    for item in conversation_history:
        role = "user" if item['is_from_user'] else "model"
        messages.append({
            "role": role,
            "parts": [item['message']]
        })
    return messages
```

## Database Access (Advanced)

If you need to access the conversation database directly (for custom memory features), here's the schema:

### Local Database: `conversation_state.db`

**Table: `messages`**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,           -- Phone number/iMessage ID
    message_text TEXT NOT NULL,        -- Message content
    is_from_user INTEGER NOT NULL,     -- 1 = from user, 0 = from AI
    timestamp REAL NOT NULL            -- Unix timestamp
)
```

**Accessing from ai_client.py:**

```python
import aiosqlite

async def get_custom_memory(sender_id: str):
    async with aiosqlite.connect('conversation_state.db') as db:
        cursor = await db.execute('''
            SELECT message_text, is_from_user, timestamp 
            FROM messages 
            WHERE sender_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''', (sender_id,))
        rows = await cursor.fetchall()
        return rows
```

**Note:** The server already provides conversation history automatically. You only need direct database access if you're building custom memory features beyond the standard history.

## Configuration Updates

The following environment variables are available in `.env`:

```env
GEMINI_API_KEY=your_api_key_here
POLL_INTERVAL=0.5
MESSAGE_HISTORY_LIMIT=20
ENABLE_READ_RECEIPTS=true
ENABLE_TYPING_INDICATOR=true
```

**New Features:**
- `ENABLE_READ_RECEIPTS`: Automatically marks conversations as read when processing (default: true)
- `ENABLE_TYPING_INDICATOR`: Shows "..." typing indicator while AI processes the message (default: true)

**Note:** Typing indicators require Accessibility permissions for Terminal in System Preferences → Security & Privacy → Privacy → Accessibility

## Testing Your Integration

1. **Start the server:**
   ```bash
   python3 server.py
   ```

2. **Send a test message** to your iPhone number from another device

3. **Check logs** in console and `server.log`:
   - Look for "Received AI response for [sender]"
   - Check for any Gemini API errors

4. **Verify response** appears in Messages app

## Common Patterns

### Adding System Prompts

```python
system_prompt = "You are a helpful therapy assistant. Be empathetic and supportive."

response = self.model.generate_content([
    system_prompt,
    f"User ({sender_id}): {message_text}"
])
```

### Handling Long Conversations

The server limits history to 20 messages by default (configurable via `MESSAGE_HISTORY_LIMIT`). If you need more context:

1. Increase in `.env`: `MESSAGE_HISTORY_LIMIT=50`
2. Or implement conversation summarization in your AI logic

### Error Handling

If Gemini API fails, return `None`:

```python
try:
    response = self.model.generate_content(prompt)
    return response.text
except Exception as e:
    logger.error(f"Gemini API error: {e}")
    return None
```

The server will automatically send a fallback message to the user.

## Complete Example

Here's a minimal working implementation:

```python
import google.generativeai as genai
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def init_session(self):
        logger.info("Gemini AI client initialized")
    
    async def close_session(self):
        logger.info("Gemini AI client closed")
    
    async def get_response(self, sender_id: str, message_text: str, 
                          conversation_history: List[dict]) -> Optional[str]:
        try:
            context = self._build_context(conversation_history)
            
            prompt = f"{context}\n\nUser: {message_text}\nAssistant:"
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                logger.info(f"Received Gemini response for {sender_id}")
                return response.text
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return None
    
    def _build_context(self, history: List[dict]) -> str:
        if not history:
            return "You are a helpful AI assistant."
        
        context_lines = ["Previous conversation:"]
        for msg in history[-10:]:
            role = "User" if msg['is_from_user'] else "Assistant"
            context_lines.append(f"{role}: {msg['message']}")
        
        return "\n".join(context_lines)
```

## Multi-Message Responses

The server automatically splits your AI responses into multiple iMessage bubbles for a more natural conversation flow.

### How It Works

If your AI response contains double newlines (`\n\n`), it will be split into separate messages:

```python
response = """That's wonderful to hear! I'm really happy for you. 😊

What's making you feel so great today?"""

# This becomes 2 separate iMessage bubbles
```

### Rules

- Splits on `\n\n` (double newline)
- Maximum 5 bubbles per response
- If more than 5 parts, remaining parts are combined into the 5th bubble
- Typing indicators shown between each bubble
- Delay between bubbles: 1-3 seconds (calculated based on message length)

### Tips for AI Developers

**Good Response Structure:**
```python
"Short greeting.\n\nLonger explanation or question.\n\nFollow-up thought."
# → 3 bubbles
```

**What Happens:**
1. User sends message
2. Typing indicator appears ("...")
3. First bubble sent
4. Typing indicator appears immediately
5. User waits 1-3s (sees typing indicator the whole time)
6. Second bubble sent
7. Repeat for remaining bubbles

**Database Storage:**
Each message part is stored separately in the database, so conversation history will include all individual bubbles.

## Multi-Message User Input Handling

The server intelligently handles cases where users send multiple messages in quick succession (like how people naturally text).

### How It Works

**Example:**
```
User sends: "what do u think about the giannas travel"
User sends: "it was not a travel bro"
User sends: "it was gather + 2 steps tf people talking bout"
```

**Server behavior:**
1. First message arrives → Processing starts (0.3s debounce + AI call)
2. Second message arrives → First processing is cancelled
3. Third message arrives → Second processing is cancelled
4. After 0.3s with no new messages → Third message is processed
5. AI gets all three messages in `conversation_history`

### Why This Matters

- Users won't get interrupting responses mid-thought
- AI sees the complete context before responding
- More natural conversation flow
- Conversation history includes all messages, even ones that didn't trigger responses

### For AI Developers

You don't need to do anything special - the server handles this automatically. Just note:
- `conversation_history` may contain consecutive user messages
- This is normal and reflects how people actually text
- Your AI should handle multiple user messages in a row gracefully

## Key Points

✅ The server handles all message detection and sending  
✅ You only modify `ai_client.py` and `config.py`  
✅ `conversation_history` is automatically provided  
✅ Return `None` on errors - server sends fallback message  
✅ Keep `init_session()` and `close_session()` methods for compatibility  
✅ Use `\n\n` in responses to create natural multi-bubble conversations  

## Need Help?

- Check `server.log` for detailed error messages
- Verify `GEMINI_API_KEY` is set correctly
- Test Gemini API independently before integrating
- Ensure Messages app is running and accessible

That's it! The rest of the system is already built and working.

