<img align="right" alt="logo" width="300px" src="docs/images/demo.gif" />

# iMessages Chatbot Server

iMessage has no public API. This project provides a high-performance solution by turning any macOS device into a headless iMessage gateway for large language models/automated messaging. It uses an asynchronous Python server that programmatically controls the native Messages app, achieving what Apple doesn't natively support: read receipts, typing indicators, and concurrent AI conversations over the iMessage network.

## Key Features

*   Manages up to 20 concurrent conversations at the same time using asynchronous API calls.
*   Injects a realistic perceived typing latency by automatically chunking multi-paragraph AI responses and sending them sequentially with a dynamically calculated delay.
*   Implements an asynchronous debounce timer (0.3s) to batch rapid incoming messages from a user, preventing premature API calls and providing the AI with a more complete conversational context.
*   Achieves stateful conversation by maintaining a persistent SQLite-backed message history for each unique user, which is re-injected as context in subsequent API calls.
*   Simulates native iMessage interactivity through targeted AppleScript automation, triggering the "..." typing indicator during AI processing and marking messages as "Read" as soon as they are ingested.

---

## How It Works

The whole system is one simple loop. Our asyncio Python server constantly watches the local Messages database for new messages. When one comes in, it grabs the content, bundles it with the conversation history, and sends it off to the Gemini API. Once Gemini replies, the server uses AppleScript to type and send the response right back through the Messages app.

![Architecture Diagram](docs/images/diagrammessages.png)

## Technical Stack

*   **Runtime**: Python 3.8+ using <code>asyncio</code> for a non-blocking event loop.
*   **AI Backend**: Google's Gemini Pro model, accessed via its official API.
*   **Message I/O**: Reads directly from the <code>chat.db</code> SQLite file on macOS and writes responses using AppleScript automation.
*   **Concurrency**: Manages simultaneous API calls with a semaphore, while a lock ensures messages are sent one-by-one to the GUI.

## Performance

Here's what you can expect in terms of performance on a standard Mac Mini:

| Metric | Value |
| :--- | :--- |
| **Optimal Capacity** | 15-20 concurrent users |
| **Internal Latency** | Under 2 seconds (excluding AI processing time) |
| **AI Response Time** | ~1.5s average, 0.8s standard deviation |
| **Message Throughput** | ~10-15 messages per minute, sustained |

---

## Installation Guide

### 1. Clone or Download the Repository

```bash
cd ~/Documents
git clone <repository-url> hack-coms-therapy
cd hack-coms-therapy
```

### 2. Install Python Dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project directory:

```bash
touch .env
```

Edit `.env` and add your configuration:

```env
GEMINI_API_KEY=your_gemini_api_key_here
POLL_INTERVAL=0.5
MESSAGE_HISTORY_LIMIT=20
ENABLE_TYPING_INDICATOR=true
```

**Required Variables:**
- `GEMINI_API_KEY`: Your Google Gemini API key

**Optional Variables:**
- `POLL_INTERVAL`: How often to check for new messages in seconds (default: 0.5)
- `MESSAGE_HISTORY_LIMIT`: Number of recent messages to send to AI for context (default: 20)
- `ENABLE_TYPING_INDICATOR`: Show typing indicators (default: true)

### 4. Grant Full Disk Access to Terminal

For the server to read the Messages database, you must grant Full Disk Access:

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access** from the left sidebar
3. Click the lock icon and authenticate
4. Click the **+** button and add your Terminal application
   - For Terminal.app: `/Applications/Utilities/Terminal.app`
   - For iTerm2: `/Applications/iTerm.app`
5. Restart your Terminal application

### 5. Grant Accessibility Permissions (for Typing Indicators)

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Accessibility** from the left sidebar
3. Click **+** and add your Terminal application
4. Check the box next to Terminal
5. Restart your Terminal application

---

## Usage

### Starting the Server

```bash
python3 run.py
```

The server will:
- Initialize the local conversation database
- Connect to the Gemini API
- Begin monitoring for new messages
- Log all activity to both console and `server.log`

### Stopping the Server

Press `Ctrl+C` or send a SIGTERM signal. The server will gracefully:
- Complete all in-flight conversations
- Close database connections
- Clean up resources

### Testing

Send a test message to your iPhone's phone number from another device. You should see:
1. Console log showing message detection
2. AI API request/response logs
3. Message sent confirmation
4. Reply appearing in Messages app
