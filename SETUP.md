# Echo Server - Complete Setup Guide

This guide will walk you through setting up the iMessage AI conversation server on your Mac Mini.

## Prerequisites

### Hardware Requirements
- Mac Mini (or any Mac) running macOS 10.15+
- iPhone with active SIM card and phone number
- Both devices signed into the same Apple ID

### Software Requirements
- Python 3.8 or later
- Terminal with Full Disk Access
- Messages app configured with iMessage

## Step 1: System Configuration

### 1.1 Enable Text Message Forwarding

On your iPhone:
1. Go to **Settings** → **Messages**
2. Tap **Text Message Forwarding**
3. Enable forwarding to your Mac Mini
4. Enter the code shown on your Mac

### 1.2 Grant Terminal Full Disk Access

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access** from the sidebar
3. Click the lock icon and authenticate
4. Click **+** and add your Terminal app
   - Terminal.app: `/Applications/Utilities/Terminal.app`
   - iTerm2: `/Applications/iTerm.app`
5. **Restart Terminal**

### 1.3 Grant Terminal Accessibility Permissions

For typing indicators to work:
1. **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Accessibility** from the sidebar
3. Click **+** and add your Terminal app
4. Check the box next to Terminal
5. **Restart Terminal**

## Step 2: Install Dependencies

### 2.1 Clone the Repository

```bash
cd ~/Documents
git clone <repository-url> hack-coms-therapy
cd hack-coms-therapy
```

### 2.2 Install Python Packages

```bash
pip3 install -r requirements.txt
```

This will install:
- `aiohttp` - Async HTTP client
- `aiosqlite` - Async SQLite
- `python-dotenv` - Environment variables
- `google-generativeai` - Gemini API SDK

## Step 3: Configure Environment

### 3.1 Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key

### 3.2 Create Environment File

```bash
cp .env.example .env
nano .env
```

Edit the file:
```env
GEMINI_API_KEY=your_actual_api_key_here
POLL_INTERVAL=0.5
MESSAGE_HISTORY_LIMIT=20
ENABLE_TYPING_INDICATOR=true
```

Save and exit (Ctrl+X, Y, Enter in nano)

## Step 4: Test the Setup

### 4.1 Verify Messages Database Access

```bash
python3 -c "import sqlite3; conn = sqlite3.connect('/Users/$USER/Library/Messages/chat.db'); print('✅ Database accessible')"
```

Should print: `✅ Database accessible`

If you get an error, revisit Step 1.2 (Full Disk Access)

### 4.2 Test Configuration

```bash
python3 -c "from src.config import Config; Config.validate(); print('✅ Configuration valid')"
```

Should print: `✅ Configuration valid`

## Step 5: Run the Server

### 5.1 Start the Server

```bash
python3 run.py
```

You should see:
```
2025-11-01 12:00:00,000 - __main__ - INFO - Initializing Echo Server...
2025-11-01 12:00:00,100 - __main__ - INFO - Database initialized at conversation_state.db
2025-11-01 12:00:00,200 - __main__ - INFO - Gemini AI client initialized
2025-11-01 12:00:00,300 - __main__ - INFO - Echo Server initialized successfully
2025-11-01 12:00:00,400 - __main__ - INFO - Starting message polling from row ID 12345
2025-11-01 12:00:00,500 - __main__ - INFO - Echo Server is now running. Press Ctrl+C to stop.
```

### 5.2 Send Test Message

From another device, send a text to your iPhone number:
```
Hey, are you there?
```

You should see in the logs:
```
2025-11-01 12:00:05,000 - message_monitor - INFO - New message from +1234567890: Hey, are you there?...
2025-11-01 12:00:05,100 - __main__ - INFO - Handling conversation for +1234567890
2025-11-01 12:00:05,600 - message_sender - INFO - Typing indicator shown for +1234567890
2025-11-01 12:00:07,200 - ai_client - INFO - Received Gemini response for +1234567890
2025-11-01 12:00:07,800 - message_sender - INFO - Successfully sent message to +1234567890
```

And receive a response!

## Step 6: Database Management

### View Statistics

```bash
python3 scripts/clear_database.py stats
```

### Clear All Data

```bash
python3 scripts/clear_database.py clear-all
```

## Step 7: Running as a Service (Optional)

### Create Launch Agent

Create `~/Library/LaunchAgents/com.echo.server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.echo.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/YOUR_USERNAME/Documents/hack-coms-therapy/run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/Documents/hack-coms-therapy</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Documents/hack-coms-therapy/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Documents/hack-coms-therapy/stderr.log</string>
</dict>
</plist>
```

Replace `YOUR_USERNAME` with your actual username.

### Load the Service

```bash
launchctl load ~/Library/LaunchAgents/com.echo.server.plist
launchctl start com.echo.server
```

### Check Status

```bash
launchctl list | grep echo
```

## Troubleshooting

### Issue: "GEMINI_API_KEY environment variable is required"
**Solution:** Ensure `.env` file exists and has valid `GEMINI_API_KEY` set

### Issue: "Error polling messages: unable to open database file"
**Solution:** Grant Full Disk Access to Terminal (Step 1.2)

### Issue: Typing indicators not working
**Solution:** Grant Accessibility permissions to Terminal (Step 1.3)

### Issue: Messages app keeps coming to foreground
**Solution:** This is normal behavior for GUI automation. Consider running on a dedicated Mac Mini.

### Issue: High CPU usage
**Solution:** 
- Increase `POLL_INTERVAL` in `.env` (e.g., `POLL_INTERVAL=1.0`)
- Check for runaway processes in Activity Monitor

## Project Structure Reference

```
hack-coms-therapy/
├── run.py                      # Main entry point
├── src/                        # Source code
│   └── server.py              # Core server logic
├── scripts/                    # Utility scripts
│   └── clear_database.py
├── docs/                       # Documentation
│   └── AI_INTEGRATION_GUIDE.md
└── data/                       # Data files
```

## Next Steps

- Read [AI_INTEGRATION_GUIDE.md](docs/AI_INTEGRATION_GUIDE.md) for customization
- Monitor `server.log` for issues
- Set up as a Launch Agent for automatic startup

## Support

- Check logs: `tail -f server.log`
- View stats: `python3 scripts/clear_database.py stats`
- Issues: Create an issue on GitHub

