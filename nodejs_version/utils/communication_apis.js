/**
 * Using the Africa's Talking API, send airtime to a phone number.
 * 
 * You'll need to have an Africa's Talking account, request for airtime API access in their dashboard,
 * and get your API key and username.
 * 
 * This is the error you get
 * {'errorMessage': 'Airtime is not enabled for this account', 'numSent': 0,
 * 'responses': [], 'totalAmount': '0', 'totalDiscount': '0'}
 * 
 * successful responses
 * {'errorMessage': 'None', 'numSent': 1, 'responses': [{'amount': 'KES 10.0000',
 * 'discount': 'KES 0.4000', 'errorMessage': 'None', 'phoneNumber': 'xxxxxxxx2046',
 * 'requestId': 'ATQid_xxxx', 'status': 'Sent'}], 'totalAmount': 'KES 10.0000',
 * 'totalDiscount': 'KES 0.4000'}
 */

import 'dotenv/config';
import AfricasTalking from 'africastalking';
import axios from 'axios';
import { z } from 'zod';
import { createLogger } from './logger.js';

const logger = createLogger('communication_apis');

/**
 * Validation schemas using Zod
 */
const SendMobileDataRequestSchema = z.object({
  phone_number: z.string().startsWith('+', 'Phone number must start with +'),
  bundle: z.string().min(1, 'Bundle amount is required'),
  provider: z.string().optional(),
  plan: z.string().optional(),
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
  audio_url: z.string().url('audio_url must be a valid URL'),
});

// Log the start of the script
logger.info('Starting the communication api script');

/**
 * Hide the first digits of a phone number.
 * Only the last 4 digits will be visible.
 * 
 * Why do we need to mask the phone number?
 * - This is information that can be used to identify a person.
 * PIIs (Personally Identifiable Information) should be protected.
 * 
 * @param {string} phoneNumber - The phone number to mask.
 * @returns {string} The masked phone number.
 * 
 * @example
 * maskPhoneNumber("+254712345678")
 */
export function maskPhoneNumber(phoneNumber) {
  return 'x'.repeat(phoneNumber.length - 4) + phoneNumber.slice(-4);
}

/**
 * Hide the first digits of an API key. Only the last 4 digits will be visible.
 * 
 * Why do we need to mask the API key?
 * - To prevent unauthorized access to your account.
 * 
 * @param {string} apiKey - The API key to mask.
 * @returns {string} The masked API key.
 * 
 * @example
 * maskApiKey("123456")
 */
export function maskApiKey(apiKey) {
  return 'x'.repeat(apiKey.length - 4) + apiKey.slice(-4);
}

/**
 * Allows you to send airtime to a phone number.
 * 
 * @param {string} phoneNumber - The phone number to send airtime to in international format.
 *   e.g. +254712345678 (Kenya) - +254 is the country code. 712345678 is the phone number.
 * @param {string} currencyCode - The 3-letter ISO currency code. e.g. KES for Kenya Shillings.
 * @param {string} amount - The amount of airtime to send. It should be a string. e.g. "10"
 *   That means you'll send airtime worth 10 currency units.
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendAirtime("+254712345678", "KES", "10")
 */
export async function sendAirtime(phoneNumber, currencyCode, amount) {
  // Load credentials
  const username = process.env.AT_USERNAME;
  const apiKey = process.env.AT_API_KEY;
  logger.info(`Loaded the credentials: ${username} ${maskApiKey(apiKey)}`);

  // Initialize the SDK
  const client = AfricasTalking({
    apiKey,
    username,
  });

  const airtime = client.AIRTIME;
  const maskedNumber = maskPhoneNumber(phoneNumber);
  logger.info(`Sending airtime to ${maskedNumber}`);
  logger.info(`Amount: ${amount} ${currencyCode}`);

  try {
    // Send airtime
    const response = await airtime.send({
      recipients: [
        {
          phoneNumber,
          amount: `${currencyCode} ${amount}`,
        },
      ],
    });
    logger.info(`The response is ${JSON.stringify(response)}`);
    return JSON.stringify(response);
  } catch (error) {
    logger.error(`Encountered an error while sending airtime: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

/**
 * Allows you to send a message to a phone number.
 * 
 * @param {string} phoneNumber - The phone number to send the message to in international format.
 *   e.g. +254712345678 (Kenya) - +254 is the country code. 712345678 is the phone number.
 * @param {string} message - The message to send. e.g. "Hello, this is a test message"
 * @param {string} username - The username to use for sending the message.
 *   This is the username you used to sign up for the Africa's Talking account.
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendMessage("+254712345678", "Hello there", "jak2")
 */
export async function sendMessage(phoneNumber, message, username) {
  // Load API key from environment variables
  const apiKey = process.env.AT_API_KEY;
  const atUsername = process.env.AT_USERNAME;
  
  if (!apiKey) {
    throw new Error('API key not found in the environment');
  }
  
  logger.info(`Loaded the credentials: ${atUsername} ${maskApiKey(apiKey)}`);

  // Initialize the SDK
  const client = AfricasTalking({
    apiKey,
    username: atUsername,
  });

  const sms = client.SMS;
  const maskedNumber = maskPhoneNumber(phoneNumber);
  logger.info(`Sending message to ${maskedNumber}`);
  logger.info(`Message: ${message}`);

  try {
    // Send message
    const response = await sms.send({
      to: [phoneNumber],
      message,
    });
    logger.info(`The response is ${JSON.stringify(response)}`);
    return JSON.stringify(response);
  } catch (error) {
    logger.error(`Encountered an error while sending message: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

/**
 * Send a USSD code to a phone number.
 * 
 * Note: USSD typically works for interactive sessions rather than sending codes.
 * This function may not work as expected with the Africa's Talking API
 * for initiating outgoing USSD pushes.
 * Consider using USSD for handling incoming USSD sessions instead.
 * 
 * @param {string} phoneNumber - The phone number to dial the USSD code on.
 * @param {string} code - The USSD code to send, e.g. `*123#`.
 * @returns {Promise<string>} JSON response from the API.
 * 
 * @example
 * await sendUssd("+254712345678", "*123#")
 */
export async function sendUssd(phoneNumber, code) {
  const username = process.env.AT_USERNAME;
  const apiKey = process.env.AT_API_KEY;
  logger.info(`Loaded the credentials: ${username} ${maskApiKey(apiKey)}`);

  const client = AfricasTalking({
    apiKey,
    username,
  });

  const maskedNumber = maskPhoneNumber(phoneNumber);
  logger.info(`Attempting to send USSD ${code} to ${maskedNumber}`);
  logger.warn(
    'USSD typically handles incoming interactive sessions. ' +
    'Initiating outgoing USSD codes via API might have limitations or require specific AT products.'
  );

  try {
    // Note: The africastalking Node.js SDK may not support USSD push
    // This is a placeholder implementation
    logger.error(
      "Africa's Talking USSD service may not support sending outgoing USSD codes this way, " +
      "or the USSD product might not be enabled/configured for your account."
    );
    return JSON.stringify({
      error: 'USSD service not available or not supported for sending outgoing codes via this SDK method.',
    });
  } catch (error) {
    logger.error(`Encountered an unexpected error while sending USSD: ${error.message}`);
    return JSON.stringify({ error: `API Error: ${error.message}` });
  }
}

/**
 * Wrapper function for sendMobileData that handles parameter conversion.
 * 
 * @param {string} phoneNumber - The recipient phone number in international format (e.g., "+254728303524")
 * @param {string|number} bundle - The data bundle amount as integer MB or string with unit (e.g., 50, "100MB", "1GB")
 *   If no unit is specified, MB is assumed
 * @param {string} provider - The telecom provider (e.g., "Safaricom", "Airtel")
 * @param {string} plan - The plan duration (e.g., "daily", "weekly", "monthly")
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendMobileDataWrapper("+254728303524", 50, "Safaricom", "daily")
 * await sendMobileDataWrapper("+254712345678", "100MB", "Airtel", "weekly")
 * await sendMobileDataWrapper("+254798765432", "1GB", "Safaricom", "monthly")
 */
export async function sendMobileDataWrapper(phoneNumber, bundle, provider, plan) {
  try {
    let quantity;
    let unit;

    // Handle integer input (assumed MB)
    if (typeof bundle === 'number') {
      quantity = Math.floor(bundle);
      unit = 'MB';
    } else {
      // Parse string bundle format
      const bundleLower = String(bundle).toLowerCase().trim();
      if (bundleLower.includes('gb')) {
        unit = 'GB';
        quantity = parseInt(bundleLower.replace(/\D/g, ''), 10);
      } else {
        // Default to MB if no unit or if MB specified
        unit = 'MB';
        quantity = parseInt(bundleLower.replace(/\D/g, ''), 10);
      }
    }

    if (quantity <= 0) {
      throw new Error(`Bundle quantity must be positive: ${quantity}`);
    }

    // Map plan to validity period
    const planMapping = {
      daily: 'Day',
      weekly: 'Week',
      monthly: 'Month',
      day: 'Day',
      week: 'Week',
      month: 'Month',
    };

    const planLower = plan.toLowerCase().trim();
    if (!planMapping[planLower]) {
      throw new Error(
        `Invalid plan duration: ${plan}. Must be daily, weekly, or monthly.`
      );
    }
    const validity = planMapping[planLower];

    // Use a consistent product name format
    const productName = `${provider.trim()}_mobile_data`;

    // Log the parsed parameters
    logger.info(
      `Parsed mobile data parameters: quantity=${quantity}, unit=${unit}, validity=${validity}, product=${productName}`
    );

    return await sendMobileDataOriginal(
      phoneNumber,
      quantity,
      unit,
      validity,
      productName
    );
  } catch (error) {
    const errorMsg = `Error in sendMobileDataWrapper: ${error.message}`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }
}

/**
 * Fetch the current wallet balance from Africa's Talking account.
 * 
 * @returns {Promise<string>} JSON response from the API
 */
export async function getWalletBalance() {
  const username = process.env.AT_USERNAME;
  const apiKey = process.env.AT_API_KEY;
  logger.info(`Loaded the credentials: ${username} ${maskApiKey(apiKey)}`);
  
  const url = `https://bundles.africastalking.com/query/wallet/balance?username=${username}`;
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    apiKey,
  };

  logger.info('Fetching wallet balance from documented endpoint');
  
  try {
    const response = await axios.get(url, { headers, timeout: 10000 });
    const data = response.data;
    logger.info(`Wallet balance response: ${JSON.stringify(data)}`);
    return JSON.stringify(data);
  } catch (error) {
    logger.error(`Encountered an error while fetching wallet balance: ${error.message}`);
    return JSON.stringify({ error: error.message });
  }
}

/**
 * Send mobile data to a phone number using Africa's Talking API.
 * 
 * @param {string} phoneNumber - The recipient phone number in international format (e.g., "+254728303524")
 * @param {number} quantity - The amount of data as an integer (e.g., 50, 100)
 * @param {string} unit - The data unit ("MB" or "GB")
 * @param {string} validity - The validity period ("Day", "Week", "Month")
 * @param {string} productName - Your Africa's Talking app product name (e.g., "mobiledata")
 * @returns {Promise<string>} JSON response from the API
 * 
 * @example
 * await sendMobileDataOriginal("+254728303524", 50, "MB", "Month", "mobiledata")
 * await sendMobileDataOriginal("+254712345678", 100, "MB", "Week", "myapp")
 * await sendMobileDataOriginal("+254798765432", 1, "GB", "Month", "data_service")
 * 
 * @note The Day plan has been phased out by Africa's Talking.
 */
export async function sendMobileDataOriginal(phoneNumber, quantity, unit, validity, productName) {
  const username = process.env.AT_USERNAME;
  const apiKey = process.env.AT_API_KEY;

  if (!username || !apiKey) {
    const errorMsg = 'Missing AT_USERNAME or AT_API_KEY environment variables';
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  logger.info(`Loaded the credentials: ${username} ${maskApiKey(apiKey)}`);

  // Check wallet balance before proceeding
  try {
    const balanceResponse = await getWalletBalance();
    const balanceData = JSON.parse(balanceResponse);
    
    if (balanceData.status === 'Success' && balanceData.balance) {
      const balanceStr = balanceData.balance.split(' ')[1];
      const balance = parseFloat(balanceStr);
      
      if (balance <= 0) {
        const errorMsg = `Insufficient wallet balance: ${balance}`;
        logger.error(errorMsg);
        return JSON.stringify({ error: errorMsg });
      }
    } else {
      const errorMsg = 'Could not fetch wallet balance';
      logger.error(`${errorMsg}. Response: ${JSON.stringify(balanceData)}`);
      return JSON.stringify({ error: errorMsg });
    }
  } catch (error) {
    const errorMsg = `Error checking wallet balance: ${error.message}`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  // Validate input parameters
  if (!phoneNumber || !quantity || !unit || !validity || !productName) {
    const errorMsg = 'Missing required parameters';
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  if (!phoneNumber.startsWith('+')) {
    const errorMsg = `Invalid phone number format: ${maskPhoneNumber(phoneNumber)}`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  if (!['MB', 'GB'].includes(unit)) {
    const errorMsg = `Invalid unit: ${unit}. Must be 'MB' or 'GB'`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  if (!['Day', 'Week', 'Month'].includes(validity)) {
    const errorMsg = `Invalid validity: ${validity}. Must be 'Day', 'Week', or 'Month'`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  // Convert quantity to integer
  try {
    const quantityInt = parseInt(quantity, 10);
    if (quantityInt <= 0 || isNaN(quantityInt)) {
      throw new Error('Quantity must be positive');
    }
    quantity = quantityInt;
  } catch (error) {
    const errorMsg = `Invalid quantity value: ${quantity}. Error: ${error.message}`;
    logger.error(errorMsg);
    return JSON.stringify({ error: errorMsg });
  }

  // Always use the live endpoint
  const url = 'https://bundles.africastalking.com/mobile/data/request';

  // Prepare recipients with required metadata
  const recipients = [
    {
      phoneNumber,
      quantity,
      unit,
      validity,
      metadata: {
        phoneNumber,
        product: productName,
        quantity: String(quantity),
        unit,
        validity,
      },
    },
  ];

  // Prepare the request payload
  const requestPayload = {
    username,
    productName,
    recipients,
  };

  // Set proper headers
  const headers = {
    apiKey,
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };

  const maskedNumber = maskPhoneNumber(phoneNumber);
  logger.info(`Sending ${quantity}${unit} data to ${maskedNumber} (validity: ${validity})`);
  logger.debug(`Request payload: ${JSON.stringify(requestPayload, null, 2)}`);
  logger.debug(`Headers: ${JSON.stringify(headers, null, 2)}`);

  try {
    const response = await axios.post(url, requestPayload, { headers, timeout: 30000 });
    logger.info(`Mobile data API response: ${JSON.stringify(response.data)}`);
    return JSON.stringify(response.data);
  } catch (error) {
    let errorMsg;
    if (error.response) {
      errorMsg = `API Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`;
    } else if (error.request) {
      errorMsg = 'No response received from the API';
    } else {
      errorMsg = `Request setup error: ${error.message}`;
    }
    logger.error(`Encountered an error while sending mobile data: ${errorMsg}`);
    return JSON.stringify({ error: errorMsg });
  }
}
