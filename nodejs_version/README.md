# Node.js Version - Function Calling with Ollama 🦙 and Africa's Talking 📱

This is the Node.js implementation of the Tool Calling API project. It provides the same functionality as the Python version but uses Node.js and Express.

## Features

- ✅ Send airtime via Africa's Talking API
- ✅ Send SMS messages
- ✅ Search for news (DuckDuckGo)
- ✅ Translate text using Ollama
- ✅ Send USSD codes
- ✅ Send mobile data bundles
- ✅ Get wallet balance
- ✅ REST API with Express
- ✅ Winston logging with rotation
- ✅ Zod validation
- ✅ Rate limiting

## Tech Stack

- **Runtime**: Node.js 18+
- **Web Framework**: Express.js
- **LLM Integration**: Ollama
- **Validation**: Zod
- **Logging**: Winston
- **Testing**: Jest
- **Code Quality**: ESLint + Prettier

## Prerequisites

- Node.js 18+ and npm 9+
- Ollama installed and running (https://ollama.com)
- Africa's Talking account with API credentials
- Pull the recommended Ollama model: `ollama pull qwen3:0.6b`

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file with your credentials:
```bash
cp .env.example .env
```

Edit `.env` and add:
```
AT_USERNAME=your_africas_talking_username
AT_API_KEY=your_africas_talking_api_key
TEST_PHONE_NUMBER=+254712345678
PORT=3000
LOG_LEVEL=info
```

## Usage

### Development Mode

```bash
npm run dev
```

### Production Mode

```bash
npm start
```

### Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch
```

### Linting and Formatting

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Chat (Function Calling)
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Send airtime to +254712345678 with an amount of 10 in currency KES",
  "history": []
}
```

### Example Requests

#### Send Airtime
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send airtime to +254712345678 with an amount of 10 in currency KES"
  }'
```

#### Send SMS
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send a message to +254712345678 with the message '\''Hello there'\'', using the username '\''sandbox'\''"
  }'
```

#### Search News
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Latest news on climate change"
  }'
```

#### Translate Text
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Translate the text '\''Hello'\'' to the target language '\''French'\''"
  }'
```

## Project Structure

```
nodejs_version/
├── app.js                          # Main Express application
├── package.json                    # Project dependencies and scripts
├── .env.example                    # Example environment variables
├── utils/
│   ├── logger.js                   # Winston logging configuration
│   ├── constants.js                # System prompts and constants
│   ├── models.js                   # Zod validation schemas
│   ├── communication_apis.js       # Africa's Talking API functions
│   └── function_call.js            # Main function calling logic
├── tests/
│   └── test_cases.test.js          # Jest test cases
└── examples/
    └── (example scripts)
```

## Differences from Python Version

1. **Web Framework**: Uses Express.js instead of Gradio
2. **Validation**: Uses Zod instead of Pydantic
3. **Logging**: Uses Winston instead of Python's logging module
4. **Testing**: Uses Jest instead of pytest
5. **API**: Provides REST endpoints instead of a Gradio UI
6. **Async**: Native async/await support without autogen

## Coding Practices

This Node.js version follows the same coding practices as the Python version:

- **Modular structure**: Separate files for different concerns
- **Validation**: Input validation using schemas (Zod)
- **Logging**: Comprehensive logging with rotation
- **Error handling**: Try-catch blocks with proper error messages
- **Security**: Masking of sensitive information (phone numbers, API keys)
- **Documentation**: JSDoc comments for functions
- **Testing**: Unit tests with mocking

## Equivalent Packages

| Python Package | Node.js Equivalent | Purpose |
|----------------|-------------------|---------|
| africastalking | africastalking | Africa's Talking SDK |
| black/pylint | eslint/prettier | Code formatting/linting |
| logging | winston | Logging |
| pytest | jest | Testing |
| gradio | express | Web framework |
| pydantic | zod | Validation |
| ollama | ollama | LLM integration |
| dotenv | dotenv | Environment variables |
| requests | axios | HTTP client |

## Logging

Logs are written to rotating files in the current directory:
- `app-YYYY-MM-DD.log` - Application logs
- `function_call-YYYY-MM-DD.log` - Function calling logs
- `communication_apis-YYYY-MM-DD.log` - API communication logs

Log files are rotated daily and kept for 5 days.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| AT_USERNAME | Africa's Talking username | Yes |
| AT_API_KEY | Africa's Talking API key | Yes |
| TEST_PHONE_NUMBER | Phone number for testing | No |
| PORT | Server port (default: 3000) | No |
| LOG_LEVEL | Log level (debug/info/warn/error) | No |

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull the required model
ollama pull qwen3:0.6b
```

### Africa's Talking API Issues
- Verify your credentials in `.env`
- Check your Africa's Talking account balance
- Ensure the phone numbers are in international format (+254...)

### Port Already in Use
```bash
# Change the PORT in .env or use a different port
PORT=3001 npm start
```

## License

Apache-2.0 - Same as the original Python version

## Contributing

Contributions are welcome! Please follow the same conventions as the Python version:
- Use ESLint and Prettier for code formatting
- Write tests for new features
- Update documentation
- Follow the existing code structure

## Credits

This is a Node.js port of the original Python project by Shuyib.
Original project: https://github.com/Shuyib/tool_calling_api
