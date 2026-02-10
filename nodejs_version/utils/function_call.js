/**
 * Function calling example using ollama to send airtime to a phone number
 * using the Africa's Talking API.
 * 
 * The user provides a query like
 * "Send airtime to +254712345678 with an amount of 10 in currency KES",
 * and the model decides to use the `sendAirtime` function to send
 * airtime to the provided phone number.
 * 
 * The user can also provide a query like
 * "Send a message to +254712345678 with the message
 * 'Hello there', using the username 'username'",
 * and the model decides to use the `sendMessage`
 * function to send a message to the provided phone number.
 * 
 * Credentials for the Africa's Talking API are loaded from
 * environment variables `AT_USERNAME` and `AT_API_KEY`.
 * 
 * Credit: https://www.youtube.com/watch?v=i0tsVzRbsNU
 */

import 'dotenv/config';
import ollama from 'ollama';
import axios from 'axios';
import { z } from 'zod';
import { createLogger } from './logger.js';
import {
  sendAirtime as commSendAirtime,
  sendMessage as commSendMessage,
  sendMobileDataWrapper,
  sendUssd,
  getWalletBalance,
  maskPhoneNumber,
  maskApiKey,
} from './communication_apis.js';

const logger = createLogger('function_call');

// Log the start of the script
logger.info('Starting the function calling script to send airtime and messages using the Africa\'s Talking API');
logger.info('Let\'s review the packages and their versions');

/**
 * Validation schemas using Zod
 */
const SendSMSRequestSchema = z.object({
  phone_number: z.string().startsWith('+', 'phone_number must be in international format, e.g. +254712345678'),
  message: z.string().min(1, 'message cannot be empty'),
  username: z.string().min(1, 'username cannot be empty'),
});

const SendMobileDataRequestSchema = z.object({
  phone_number: z.string().startsWith('+', 'phone_number must be in international format, e.g. +254712345678'),
  bundle: z.string().regex(/^\d+(?:MB|GB)?$/i, 'bundle must be a number or a string with unit, e.g. 50, 500MB, 1GB'),
  provider: z.string().min(1, 'provider must not be empty'),
  plan: z.string().refine(val => ['daily', 'weekly', 'monthly', 'day', 'week', 'month'].includes(val.toLowerCase()),
    { message: 'plan must be one of: daily, weekly, monthly, day, week, month' }),
});

const SendUSSDRequestSchema = z.object({
  phone_number: z.string().startsWith('+', 'Phone number must start with +'),
  code: z.string(),
});

const MakeVoiceCallRequestSchema = z.object({
  from_number: z.string().startsWith('+', 'Phone number must start with +'),
  to_number: z.string().startsWith('+', 'Phone number must start with +'),
});

const MakeVoiceCallWithTextRequestSchema = z.object({
  from_number: z.string().startsWith('+', 'Phone number must start with +'),
  to_number: z.string().startsWith('+', 'Phone number must start with +'),
  message: z.string(),
  voice: z.enum(['man', 'woman']).default('woman'),
});

const MakeVoiceCallAndPlayAudioRequestSchema = z.object({
  from_number: z.string().startsWith('+', 'Phone number must start with +'),
  to_number: z.string().startsWith('+', 'Phone number must start with +'),
  audio_url: z.string().url('audio_url must be a valid HTTP/HTTPS URL'),
});

const GetApplicationBalanceRequestSchema = z.object({
  sandbox: z.boolean().optional().default(false),
});

const SendWhatsAppMessageRequestSchema = z.object({
  wa_number: z.string().startsWith('+', 'Phone number must start with +'),
  phone_number: z.string().startsWith('+', 'Phone number must start with +'),
  message: z.string().optional(),
  media_type: z.enum(['Image', 'Video', 'Audio', 'Voice']).optional(),
  url: z.string().optional(),
  caption: z.string().optional(),
  sandbox: z.boolean().optional().default(false),
});

const SendAirtimeRequestSchema = z.object({
  phone_number: z.string().refine(
    val => val && val.startsWith('+') && val.slice(1).match(/^\d+$/),
    { message: 'phone_number must be in international format, e.g. +254712345678' }
  ),
  currency_code: z.string().refine(
    val => val && val.length === 3 && /^[A-Za-z]+$/.test(val),
    { message: 'currency_code must be a 3-letter ISO code, e.g. KES' }
  ),
  amount: z.string().regex(/^\d+(\.\d{1,2})?$/, 'amount must be a valid decimal number, e.g. 10 or 10.50'),
});

/**
 * Function to send airtime using Africa's Talking API
 * 
 * @param {string} phoneNumber - The phone number to send airtime to in international format.
 *   e.g. +254712345678 (Kenya) - +254 is the country code. 712345678 is the phone number.
 * @param {string} currencyCode - The 3-letter ISO currency code. e.g. KES for Kenya Shillings.
 * @param {string} amount - The amount of airtime to send. e.g. "10"
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendAirtime("+254712345678", "KES", "10")
 */
export async function sendAirtime(phoneNumber, currencyCode, amount) {
  try {
    const validated = SendAirtimeRequestSchema.parse({
      phone_number: phoneNumber,
      currency_code: currencyCode,
      amount,
    });
  } catch (error) {
    logger.error(`Airtime parameter validation failed: ${error.message}`);
    return error.message;
  }

  try {
    const maskedNumber = maskPhoneNumber(phoneNumber);
    logger.info(`Delegating airtime sending to ${maskedNumber}`);
    logger.info(`Amount: ${amount} ${currencyCode}`);

    const response = await commSendAirtime(phoneNumber, currencyCode, amount);
    logger.debug(`Airtime delegation response: ${response}`);
    return response;
  } catch (error) {
    logger.error(`Encountered an error while sending airtime: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

/**
 * Function to send a message using Africa's Talking API
 * 
 * @param {string} phoneNumber - The phone number to send the message to in international format.
 * @param {string} message - The message to send.
 * @param {string} username - The username to use for sending the message.
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendMessage("+254712345678", "Hello there", "jak2")
 */
export async function sendMessage(phoneNumber, message, username) {
  try {
    const validated = SendSMSRequestSchema.parse({
      phone_number: phoneNumber,
      message,
      username,
    });
  } catch (error) {
    logger.error(`SMS parameter validation failed: ${error.message}`);
    return error.message;
  }

  try {
    const maskedNumber = maskPhoneNumber(phoneNumber);
    logger.info(`Delegating message sending to ${maskedNumber}`);
    logger.info(`Message: ${message}`);
    
    const response = await commSendMessage(phoneNumber, message, username);
    logger.debug(`Message delegation response: ${response}`);
    return response;
  } catch (error) {
    logger.error(`Encountered an error while sending message: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

/**
 * Search for news using DuckDuckGo search engine based on the query provided.
 * 
 * @param {string} query - The query to search for.
 * @param {number} maxResults - The maximum number of news articles to retrieve.
 * @returns {Promise<string>} The search results, formatted for readability.
 * 
 * @example
 * await searchNews("Python programming")
 */
export async function searchNews(query, maxResults = 5) {
  logger.info(`Searching for news based on the query: ${query}`);
  
  try {
    // Use DuckDuckGo's HTML API
    const url = 'https://html.duckduckgo.com/html/';
    const params = new URLSearchParams({
      q: query + ' news',
      kl: 'wt-wt',
    });

    const response = await axios.get(`${url}?${params}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      timeout: 10000,
    });

    // Note: For a production implementation, you would want to use a proper news API
    // DuckDuckGo doesn't have an official API for news search
    // This is a simplified implementation
    
    // As a fallback, return a message about using a proper news API
    return `News search functionality requires a proper news API integration. Consider using:
- NewsAPI (https://newsapi.org)
- Bing News Search API
- Google News API

Query: ${query}
Max Results: ${maxResults}`;
  } catch (error) {
    logger.error(`Error searching for news: ${error.message}`);
    return `Error searching for news: ${error.message}`;
  }
}

/**
 * Translate text to a specified language using Ollama.
 * 
 * @param {string} text - The text to translate.
 * @param {string} targetLanguage - The language of interest (limited to French, Arabic, Portuguese)
 * @returns {Promise<string>} Translated text
 * 
 * @example
 * await translateText("Hello, how are you?", "French")
 */
export async function translateText(text, targetLanguage) {
  const languageMap = {
    french: 'French',
    fr: 'French',
    arabic: 'Arabic',
    ar: 'Arabic',
    portuguese: 'Portuguese',
    pt: 'Portuguese',
  };

  const normalizedLanguage = languageMap[targetLanguage.toLowerCase()];

  if (!normalizedLanguage) {
    throw new Error('Target language must be French, Arabic, or Portuguese.');
  }

  try {
    // Use Ollama for translation
    const translationPrompt = `Translate the following English text to ${normalizedLanguage}. Provide only the translation without explanations:\n\n"${text}"`;
    
    const response = await ollama.chat({
      model: 'qwen3:0.6b',
      messages: [
        {
          role: 'system',
          content: 'You are a translation expert. Translate English text to the specified language with high accuracy. Provide only the translation without explanations.',
        },
        {
          role: 'user',
          content: translationPrompt,
        },
      ],
      options: {
        temperature: 0.5,
      },
    });

    const translation = response.message.content.trim();

    // Validation step
    const validationPrompt = `Review this ${normalizedLanguage} translation of "${text}": "${translation}". Rate accuracy (0-100%) and provide brief feedback.`;
    
    const validationResponse = await ollama.chat({
      model: 'qwen3:0.6b',
      messages: [
        {
          role: 'system',
          content: 'You are a bilingual translation validator. Review translations for: 1. Accuracy of meaning 2. Grammar correctness 3. Natural expression. Provide a confidence score (0-100%) and brief feedback.',
        },
        {
          role: 'user',
          content: validationPrompt,
        },
      ],
      options: {
        temperature: 0.5,
      },
    });

    logger.info(`Translation: ${translation}`);
    logger.info(`Validation: ${validationResponse.message.content}`);

    return `${translation}\n\nValidation: ${validationResponse.message.content}`;
  } catch (error) {
    logger.error(`Error translating text: ${error.message}`);
    return `Error: ${error.message}`;
  }
}

/**
 * Get wallet balance from Africa's Talking account
 * 
 * @returns {Promise<string>} JSON response from the API
 */
export async function getApplicationBalance() {
  try {
    return await getWalletBalance();
  } catch (error) {
    logger.error(`Error getting application balance: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

// Export additional functions for compatibility
export {
  sendMobileDataWrapper as sendMobileData,
  sendUssd,
  maskPhoneNumber,
  maskApiKey,
};
