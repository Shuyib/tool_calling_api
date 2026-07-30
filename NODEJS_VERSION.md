# Node.js Version - Quick Start Guide

## What is This?

This is the **Node.js version** of the Tool Calling API project. It provides the same functionality as the Python version but uses Node.js, Express, and modern JavaScript practices.

## Location

The Node.js version is located in the `nodejs_version/` directory.

## Quick Start

```bash
# Navigate to the Node.js version
cd nodejs_version

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Africa's Talking credentials

# Start the server
npm start
```

The API will be available at http://localhost:3000

## Key Differences from Python Version

| Feature | Python | Node.js |
|---------|--------|---------|
| Interface | Gradio Web UI | REST API |
| Port | 7860 | 3000 |
| Usage | Web browser | HTTP requests |
| Framework | Gradio + Flask | Express |
| Validation | Pydantic | Zod |

## API Usage

### Python (Gradio)
1. Open http://localhost:7860
2. Type message in chat
3. Get response in UI

### Node.js (REST API)
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Send airtime to +254712345678 with 10 KES"}'
```

## Documentation

For complete documentation, see:
- `nodejs_version/README.md` - Full documentation
- `nodejs_version/IMPLEMENTATION_SUMMARY.md` - Implementation details
- `nodejs_version/PYTHON_VS_NODEJS.md` - Comparison guide

## Features

- ✅ Send airtime
- ✅ Send SMS
- ✅ Search news
- ✅ Translate text
- ✅ Send USSD
- ✅ Send mobile data
- ✅ Get balance

## Requirements

- Node.js 18+
- Ollama running locally
- Africa's Talking credentials

## Testing

```bash
cd nodejs_version
npm test
```

## Questions?

Check the comprehensive documentation in `nodejs_version/README.md`
