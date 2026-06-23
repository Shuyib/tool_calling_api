/**
 * Simple example demonstrating how to use the function calling API
 */

import 'dotenv/config';
import { sendAirtime, sendMessage, searchNews, translateText } from '../utils/function_call.js';

async function main() {
  console.log('=== Function Calling API Examples ===\n');

  try {
    // Example 1: Send Airtime
    console.log('1. Sending airtime...');
    const airtimeResult = await sendAirtime('+254712345678', 'KES', '10');
    console.log('Result:', airtimeResult);
    console.log();

    // Example 2: Send Message
    console.log('2. Sending SMS...');
    const messageResult = await sendMessage(
      '+254712345678',
      'Hello from Node.js!',
      process.env.AT_USERNAME || 'sandbox'
    );
    console.log('Result:', messageResult);
    console.log();

    // Example 3: Search News
    console.log('3. Searching for news...');
    const newsResult = await searchNews('artificial intelligence', 5);
    console.log('Result:', newsResult);
    console.log();

    // Example 4: Translate Text
    console.log('4. Translating text...');
    const translationResult = await translateText('Hello, how are you?', 'French');
    console.log('Result:', translationResult);
    console.log();

  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
