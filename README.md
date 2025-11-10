<img align="right" alt="logo" width="200px" src="https://raw.githubusercontent.com/CaptainATW/iMessages-Chatbot-Server/refs/heads/main/yesss.png" />

# iMessages Chatbot Server 

This project turns a Mac Mini into a smart, conversational AI that anyone can talk to using iMessage. It's a Python server that cleverly bridges the native macOS Messages app with the power of Google's Gemini AI.

The goal is to create a seamless, natural chat experience. Users send a text, and the AI responds thoughtfully, just like a real person would. It can handle multiple conversations at once and remembers what you've talked about before.

For a deep dive into the architecture and the challenges of taming iMessage, check out our full write-up on the blog! [<-- LINK YOUR BLOG POST HERE]

How It Works

The whole system is a simple, powerful loop. Our Python server constantly watches the local Messages database for new messages. When one comes in, it grabs the content, bundles it with the conversation history, and sends it off to the Gemini API. Once Gemini replies, the server uses AppleScript to type and send the response right back through the Messages app.

![alt text](https://raw.githubusercontent.com/CaptainATW/iMessages-Chatbot-Server/refs/heads/main/diagrammessages.png)

Key Features

Handles a Crowd: Comfortably manages up to 20 conversations at the same time without breaking a sweat.

Feels Human: Long AI responses are automatically split into separate paragraphs, with a realistic typing delay between each one to feel more natural.

Smart Replies: If someone sends a bunch of messages in a row, the bot waits a moment (a 0.3s debounce) to reply to the whole thought, not just the first part.

Remembers a Conversation: Never loses track. The bot remembers past messages using a simple SQLite database, so every chat has context.

Real-time Feedback: Shows the "..." typing indicator and marks messages as read, making the conversation feel alive and responsive.

Technical Stack

Runtime: Python 3.8+ using asyncio for a non-blocking event loop.

AI Backend: Google's Gemini Pro model, accessed via its official API.

Message I/O: Reads directly from the chat.db SQLite file on macOS and writes responses using AppleScript automation.

Concurrency: Manages simultaneous API calls with a semaphore, while a lock ensures messages are sent one-by-one to the GUI.

Performance

Here's what you can expect in terms of performance on a standard Mac Mini:

Metric	Value
Optimal Capacity	15-20 concurrent users
Internal Latency	Under 2 seconds (excluding AI processing time)
AI Response Time	~1.5s average, 0.8s standard deviation
Message Throughput	~10-15 messages per minute, sustained
Use Cases

Therapy Assistance: Offer 24/7 mental health support through a familiar and private interface.

Customer Service: Automate your support channels using a business iMessage number.

Personal AI Assistant: Create your own context-aware assistant that you can text anytime.

Educational Tutoring: Provide on-demand learning support and answer questions via SMS/iMessage.
