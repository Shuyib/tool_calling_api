# Docker Setup for Voice Functionality

## Overview

The Docker setup has been updated to support the new voice functionality with Africa's Talking. This includes a dedicated voice callback server that handles text-to-speech and audio playback features.

## Services

### 1. Ollama Service (`ollama`)
- **Container**: `ollama-server`
- **Port**: `11434`
- **Purpose**: Provides the LLM backend for function calling

### 2. Voice Callback Server (`voice-server`)
- **Container**: `voice-callback-server`
- **Port**: `5001`
- **Purpose**: Handles voice callback requests from Africa's Talking API
- **Features**:
  - Text-to-speech message storage and serving
  - Audio file playback coordination
  - Health check endpoint
  - CORS support for cross-origin requests

### 3. Gradio App (`app`)
- **Container**: `gradio-app`
- **Port**: `7860`
- **Purpose**: Main web interface for the application
- **Dependencies**: Requires both `ollama` and `voice-server` to be running

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Africa's Talking API credentials
AT_USERNAME=your_username
AT_API_KEY=your_api_key

# Langtrace API key (optional)
LANGTRACE_API_KEY=your_langtrace_key

# Groq API key (optional)
GROQ_API_KEY=your_groq_key

# Voice callback URL (automatically set for Docker)
VOICE_CALLBACK_URL=http://voice-server:5001
```

## Running the Services

### Development Mode
```bash
# Start all services
docker-compose up --build

# Start specific service
docker-compose up --build voice-server
docker-compose up --build app

# View logs
docker-compose logs -f voice-server
docker-compose logs -f app
```

### Production Mode
```bash
# Start in detached mode
docker-compose up -d --build

# Check service health
docker-compose ps

# Scale voice server if needed
docker-compose up -d --scale voice-server=2
```

## Networking

- **Internal Network**: All services communicate via Docker's internal network
- **External Access**:
  - Gradio App: `http://localhost:7860`
  - Voice Server: `http://localhost:5001`
  - Ollama: `http://localhost:11434`

## Voice Callback Setup

### For Development (with ngrok)
1. Start the services: `docker-compose up --build`
2. Install ngrok: `brew install ngrok`
3. Expose the voice server: `ngrok http 5001`
4. Update the environment variable with the ngrok URL:
   ```bash
   export VOICE_CALLBACK_URL="https://abc123.ngrok.io"
   ```
5. Restart the app service:
   ```bash
   docker-compose restart app
   ```

### For Production
1. Deploy to a cloud provider with a proper domain
2. Set up HTTPS with a valid SSL certificate
3. Configure the `VOICE_CALLBACK_URL` environment variable to your domain:
   ```env
   VOICE_CALLBACK_URL=https://your-domain.com
   ```

## Health Checks

The voice callback server includes health checks:
- **Endpoint**: `GET /health`
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts

## Troubleshooting

### Voice Server Not Starting
```bash
# Check logs
docker-compose logs voice-server

# Restart service
docker-compose restart voice-server

# Rebuild if needed
docker-compose up --build voice-server
```

### Callback Not Received
1. Verify the voice server is accessible:
   ```bash
   curl http://localhost:5001/health
   ```
2. Check if the callback URL is correctly set:
   ```bash
   docker-compose exec app env | grep VOICE_CALLBACK_URL
   ```
3. Ensure ngrok tunnel is active (for development)

### Port Conflicts
If ports are already in use, modify the `docker-compose.yml`:
```yaml
ports:
  - "5002:5001"  # Map to different external port
```

## File Structure

```
.
├── docker-compose.yml          # Main Docker Compose configuration
├── Dockerfile.app             # Dockerfile for Gradio app
├── Dockerfile.voice           # Dockerfile for voice callback server
├── Dockerfile.ollama          # Dockerfile for Ollama service
├── voice_callback_server.py   # Voice callback server implementation
├── app.py                     # Main Gradio application
└── utils/
    ├── communication_apis.py   # Africa's Talking API functions
    └── function_call.py       # Function calling logic
```

## Security Considerations

- API keys are passed as environment variables (never hardcoded)
- Voice server runs with restricted privileges
- Health checks ensure service availability
- CORS is properly configured for the voice server
- Phone numbers are masked in logs for privacy

## Scaling

To handle multiple concurrent voice calls:
```bash
# Scale the voice server
docker-compose up -d --scale voice-server=3

# Use a load balancer in production
# Configure Africa's Talking webhook to distribute load
```
