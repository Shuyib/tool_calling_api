# Voice Server Setup Guide

This guide explains how to set up the voice callback server for text-to-speech functionality with Africa's Talking.

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install ngrok (if not already installed):
```bash
# macOS with Homebrew
brew install ngrok

# Or download from https://ngrok.com/download
```

## Setup Steps

### 1. Start the Voice Callback Server

```bash
python voice_callback_server.py
```

The server will start on `http://localhost:5000`

### 2. Expose Server with ngrok

In a new terminal, run:
```bash
ngrok http 5000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 3. Configure Environment Variable

Set the callback URL environment variable:
```bash
export VOICE_CALLBACK_URL="https://abc123.ngrok.io"
```

Or add it to your `.env` file:
```
VOICE_CALLBACK_URL=https://abc123.ngrok.io
```

### 4. Configure Africa's Talking Dashboard (Optional)

1. Log in to your Africa's Talking dashboard
2. Go to Voice settings
3. Set the callback URL to: `https://abc123.ngrok.io/voice/callback`

### 5. Test the Setup

Now when you use `make_voice_call_with_text`, it should:
1. Store the message in the callback server
2. Make the voice call with the callback URL
3. When Africa's Talking calls back, serve the XML with your message

## Usage Example

```python
from utils.communication_apis import make_voice_call_with_text

# This will now speak your custom message instead of the default greeting
result = make_voice_call_with_text(
    from_number="+254700000001",
    to_number="+254712345678", 
    message="Hello, this is a test message",
    voice_type="woman"
)
```

## Debugging

### Check server status:
```bash
curl http://localhost:5000/health
```

### List stored messages:
```bash
curl http://localhost:5000/voice/messages
```

### Test storing a message:
```bash
curl -X POST http://localhost:5000/voice/store \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "to_number": "+254712345678",
    "message": "Test message",
    "voice_type": "woman"
  }'
```

## Production Deployment

For production, instead of ngrok:

1. Deploy the voice server to a cloud provider (AWS, GCP, etc.)
2. Use a proper domain with HTTPS
3. Set up proper logging and monitoring
4. Use Redis or a database instead of in-memory storage

## Troubleshooting

**Issue**: Still hearing default Africa's Talking message
- Ensure ngrok is running and accessible
- Check that `VOICE_CALLBACK_URL` is set correctly
- Verify the callback server is receiving requests (check logs)
- Make sure the callback URL is accessible from the internet

**Issue**: Voice server not starting
- Check that port 5000 is available
- Install missing dependencies: `pip install flask flask-cors`

**Issue**: Callback not received
- Verify ngrok tunnel is active
- Check Africa's Talking dashboard callback URL settings
- Ensure firewall allows incoming connections