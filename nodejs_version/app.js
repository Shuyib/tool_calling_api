/**
 * Airtime and Messaging Service using Africa's Talking API
 * 
 * This script provides a REST API for sending airtime and messages
 * using the Africa's Talking API.
 * 
 * Usage:
 *     1. Set the environment variables `AT_USERNAME` and `AT_API_KEY` with your
 *        Africa's Talking credentials.
 *     2. Run the script: `node app.js`
 *     3. Access the REST API endpoints to send airtime, messages, or search for news articles.
 * 
 * Examples:
 *     Send airtime to a phone number:
 *         POST /api/chat with body: {"message": "Send airtime to +254712345678 with an amount of 10 in currency KES"}
 * 
 *     Send SMS messages:
 *         POST /api/chat with body: {"message": "Send a message to +254712345678 with the message 'Hello there', using the username 'sandbox'"}
 * 
 *     Search for news:
 *         POST /api/chat with body: {"message": "Latest news on climate change"}
 * 
 *     Translate text:
 *         POST /api/chat with body: {"message": "Translate the text 'Hello' to the target language 'French'"}
 */

// ------------------------------------------------------------------------------------
// Import Statements
// ------------------------------------------------------------------------------------

import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import ollama from 'ollama';
import { createLogger } from './utils/logger.js';
import {
  sendAirtime,
  sendMessage,
  searchNews,
  translateText,
  sendUssd,
  sendMobileData,
  getApplicationBalance,
  maskPhoneNumber,
  maskApiKey,
} from './utils/function_call.js';
import { API_SYSTEM_PROMPT } from './utils/constants.js';

// ------------------------------------------------------------------------------------
// Logging Configuration
// ------------------------------------------------------------------------------------

const logger = createLogger('app');

// ------------------------------------------------------------------------------------
// Log the Start of the Script
// ------------------------------------------------------------------------------------

logger.info('Starting the function calling script to send airtime and messages using Africa\'s Talking API');
logger.info('Let\'s review the packages and their versions');

// Log package versions (Node.js version)
logger.info(`Node.js version: ${process.version}`);
logger.info(`Express version: ${express.VERSION || 'unknown'}`);

// ------------------------------------------------------------------------------------
// Define Tools Schema
// ------------------------------------------------------------------------------------

const tools = [
  {
    type: 'function',
    function: {
      name: 'send_airtime',
      description: 'Send airtime to a phone number using the Africa\'s Talking API',
      parameters: {
        type: 'object',
        properties: {
          phone_number: {
            type: 'string',
            description: 'The phone number in international format',
          },
          currency_code: {
            type: 'string',
            description: 'The 3-letter ISO currency code',
          },
          amount: {
            type: 'string',
            description: 'The amount of airtime to send',
          },
        },
        required: ['phone_number', 'currency_code', 'amount'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'send_message',
      description: 'Send a message to a phone number using the Africa\'s Talking API',
      parameters: {
        type: 'object',
        properties: {
          phone_number: {
            type: 'string',
            description: 'The phone number in international format',
          },
          message: {
            type: 'string',
            description: 'The message to send',
          },
          username: {
            type: 'string',
            description: 'The username for the Africa\'s Talking account',
          },
        },
        required: ['phone_number', 'message', 'username'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'search_news',
      description: 'Search for news articles using DuckDuckGo News API',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'The search query for news articles',
          },
          max_results: {
            type: 'integer',
            description: 'The maximum number of news articles to retrieve',
            default: 5,
          },
        },
        required: ['query'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'translate_text',
      description: 'Translate text to a specified language using Ollama',
      parameters: {
        type: 'object',
        properties: {
          text: {
            type: 'string',
            description: 'The text to translate',
          },
          target_language: {
            type: 'string',
            description: 'The target language (French, Arabic, or Portuguese)',
          },
        },
        required: ['text', 'target_language'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'send_ussd',
      description: 'Send a USSD code to a phone number',
      parameters: {
        type: 'object',
        properties: {
          phone_number: {
            type: 'string',
            description: 'The phone number in international format',
          },
          code: {
            type: 'string',
            description: 'The USSD code to send (e.g., *544#)',
          },
        },
        required: ['phone_number', 'code'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'send_mobile_data',
      description: 'Send mobile data bundle to a phone number',
      parameters: {
        type: 'object',
        properties: {
          phone_number: {
            type: 'string',
            description: 'The phone number in international format',
          },
          bundle: {
            type: 'string',
            description: 'The data bundle amount (e.g., 500MB, 1GB)',
          },
          provider: {
            type: 'string',
            description: 'The telecom provider (e.g., Safaricom, Airtel)',
          },
          plan: {
            type: 'string',
            description: 'The plan duration (daily, weekly, monthly)',
          },
        },
        required: ['phone_number', 'bundle', 'provider', 'plan'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_application_balance',
      description: 'Get the wallet balance from Africa\'s Talking account',
      parameters: {
        type: 'object',
        properties: {},
      },
    },
  },
];

// ------------------------------------------------------------------------------------
// Process User Message Function
// ------------------------------------------------------------------------------------

async function processUserMessage(userMessage, history = []) {
  /**
   * Process user message and handle tool calls
   * 
   * @param {string} userMessage - The user's input message
   * @param {Array} history - The conversation history
   * @returns {Promise<string>} The response from the model or function execution result
   */
  logger.info(`User message: ${userMessage}`);

  // Build messages array from history
  const messages = [
    {
      role: 'system',
      content: API_SYSTEM_PROMPT,
    },
  ];

  // Add history to messages
  for (const [user, assistant] of history) {
    messages.push({ role: 'user', content: user });
    messages.push({ role: 'assistant', content: assistant });
  }

  // Add current user message
  messages.push({
    role: 'user',
    content: userMessage,
  });

  try {
    // Select model
    const modelName = 'qwen3:0.6b';

    const response = await ollama.chat({
      model: modelName,
      messages,
      tools,
      options: {
        temperature: 0, // Set temperature to 0 for deterministic responses
      },
    });

    const modelMessage = response.message || {};
    const modelContent = modelMessage.content || '';
    const modelRole = modelMessage.role || 'assistant';
    
    logger.info(`Model response: ${modelContent}`);

    messages.push({
      role: modelRole,
      content: modelContent,
    });

    if (modelMessage.tool_calls && modelMessage.tool_calls.length > 0) {
      for (const tool of modelMessage.tool_calls) {
        const toolName = tool.function.name;
        const args = tool.function.arguments;

        // Mask sensitive arguments before logging
        const maskedArgs = {};
        for (const [key, value] of Object.entries(args)) {
          if (key.includes('phone_number')) {
            maskedArgs[key] = maskPhoneNumber(value);
          } else if (key.includes('api_key')) {
            maskedArgs[key] = maskApiKey(value);
          } else {
            maskedArgs[key] = value;
          }
        }

        logger.info(`Tool call detected: ${toolName} with arguments: ${JSON.stringify(maskedArgs)}`);

        try {
          let functionResponse;

          switch (toolName) {
            case 'send_airtime':
              logger.info(`Calling send_airtime with arguments: ${JSON.stringify(maskedArgs)}`);
              functionResponse = await sendAirtime(
                args.phone_number,
                args.currency_code,
                args.amount
              );
              break;

            case 'send_message':
              logger.info(`Calling send_message with arguments: ${JSON.stringify(maskedArgs)}`);
              functionResponse = await sendMessage(
                args.phone_number,
                args.message,
                args.username
              );
              break;

            case 'search_news':
              logger.info(`Calling search_news with arguments: ${JSON.stringify(maskedArgs)}`);
              functionResponse = await searchNews(args.query, args.max_results);
              break;

            case 'translate_text':
              logger.info(`Calling translate_text with arguments: ${JSON.stringify(maskedArgs)}`);
              functionResponse = await translateText(args.text, args.target_language);
              break;

            case 'send_ussd':
              logger.info(`Calling send_ussd with arguments: ${JSON.stringify(maskedArgs)}`);
              functionResponse = await sendUssd(args.phone_number, args.code);
              break;

            case 'send_mobile_data':
              logger.info(`Calling send_mobile_data with arguments: ${JSON.stringify(maskedArgs)}`);
              if (!process.env.AT_USERNAME || !process.env.AT_API_KEY) {
                functionResponse = JSON.stringify({
                  error: 'Missing AT_USERNAME or AT_API_KEY environment variables',
                });
              } else {
                functionResponse = await sendMobileData(
                  args.phone_number,
                  args.bundle,
                  args.provider,
                  args.plan
                );
              }
              break;

            case 'get_application_balance':
              logger.info('Calling get_application_balance');
              functionResponse = await getApplicationBalance();
              break;

            default:
              functionResponse = JSON.stringify({ error: 'Unknown function' });
              logger.warn(`Unknown function: ${toolName}`);
          }

          logger.debug(`Function response: ${functionResponse}`);
          messages.push({
            role: 'tool',
            content: functionResponse,
          });

          return `Function \`${toolName}\` executed successfully. Response:\n${functionResponse}`;
        } catch (error) {
          logger.error(`Error calling function ${toolName}: ${error.message}`);
          return 'An unexpected error occurred while processing your message.';
        }
      }
    } else {
      logger.debug('No tool calls detected. Returning model content.');
      return modelContent;
    }
  } catch (error) {
    logger.error(`Failed to get response from Ollama client: ${error.message}`);
    return 'An unexpected error occurred while communicating with the assistant.';
  }
}

// ------------------------------------------------------------------------------------
// Set Up Express Application
// ------------------------------------------------------------------------------------

const app = express();
const PORT = process.env.PORT || 3000;

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(limiter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Service is running' });
});

// Main chat endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { message, history = [] } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const response = await processUserMessage(message, history);
    res.json({ response });
  } catch (error) {
    logger.error(`Error in /api/chat endpoint: ${error.message}`);
    res.status(500).json({ error: 'An unexpected error occurred while processing your message.' });
  }
});

// Start server
app.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
  logger.info(`Health check: http://localhost:${PORT}/health`);
  logger.info(`Chat endpoint: http://localhost:${PORT}/api/chat`);
});

export default app;
