"""
Airtime and Messaging Service using Africa's Talking API

This script provides a Gradio-based web interface for sending airtime and messages
using the Africa's Talking API. It also tracks the carbon emissions of the operations
using the CodeCarbon library.

Usage:
    1. Set the environment variables `AT_USERNAME` and `AT_API_KEY` with your
    Africa's Talking credentials.
    2. Run the script: `python app.py`
    3. Access the Gradio web interface to send airtime or messages or search for
    news articles.

Examples (Use these exact prompts for best results):
    Send airtime to a phone number:
        - `Send airtime to +254712345678 with an amount of 10 in currency KES`
        - `Send 50 KES airtime to +254701234567`

    Send SMS messages:
        - `Send a message to +254712345678 with the message 'Hello there', using the username 'sandbox'`
        - `Send SMS 'Meeting at 3PM today' to +254701234567 using username testuser`

    Send USSD codes:
        - `Send USSD code *544# to +254712345678`
        - `Check balance with USSD *100# for +254701234567`

    Send mobile data bundles:
        - `Send 500MB data bundle to +254712345678 using provider Safaricom with plan daily`
        - `Send 1GB data to +254701234567 using Airtel provider with weekly plan`

    Make voice calls:
        - `Make a voice call from +254712345678 to +254798765432`
        - `Call +254701234567 from +254787654321`
        - `Make a voice call from +254700000001 to +254712345678 and say "Hello, this is a test message"`
        - `Call +254701234567 from +254787654321 and say "Your appointment is confirmed for tomorrow at 2 PM"`
        - `Make a voice call from +254700000001 to +254712345678 and play audio from https://example.com/audio.mp3`
        - `Call +254701234567 from +254787654321 and play https://github.com/runpod-workers/sample-inputs/raw/main/audio/gettysburg.wav`

    Check account balances:
        - `Check my wallet balance`
        - `Get my application balance`
        - `Show application balance from sandbox`

    Send WhatsApp messages:
        - `Send WhatsApp message from +254799999999 to +254700000000 with message "Hello via WhatsApp!"`
        - `Send WhatsApp image from +254799999999 to +254700000000 with media type Image and URL https://example.com/image.jpg`

    Search for news:
        - `Latest news on climate change`
        - `Search news about artificial intelligence developments`
        - `Find recent news on renewable energy`

    Translate text:
        - `Translate the text 'Hello' to the target language 'French'`
        - `Translate 'Good morning' to Spanish`
        - `Convert 'Thank you' to Swahili`

Note: All API calls and responses are logged to 'func_calling_app.log' in the application directory for debugging purposes.
"""

# ------------------------------------------------------------------------------------
# Import Statements
# ------------------------------------------------------------------------------------

# Standard Library Imports
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from importlib.metadata import version, PackageNotFoundError

# Third-Party Library Imports
import gradio as gr
from langtrace_python_sdk import langtrace, with_langtrace_root_span
import ollama
from utils.function_call import (
    send_airtime,
    send_message,
    search_news,
    translate_text,
    send_ussd,
    make_voice_call,
    make_voice_call_with_text,
    make_voice_call_and_play_audio,
    get_wallet_balance,
    get_application_balance,
    send_whatsapp_message,
)
from utils.constants import VISION_SYSTEM_PROMPT, API_SYSTEM_PROMPT
from utils.models import ReceiptData, LineItem
from utils.communication_apis import send_mobile_data_wrapper


# ------------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------------


def setup_logger():
    """Sets up the logger with file and stream handlers.

    Parameters
    ----------
    None

    Returns
    -------

    logger: logging.Logger
        The logger object with the configured handlers.

    """

    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Capture all levels DEBUG and above

    # Prevent logs from being propagated to the root logger to avoid duplication
    logger.propagate = False

    # Define logging format
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")

    # Set up the Rotating File Handler
    # the log file will be rotated when it reaches 5MB and will keep the last 5 logs
    file_handler = RotatingFileHandler(
        "func_calling_app.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)  # Capture INFO and above in the file
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Set up the Stream Handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)  # Capture DEBUG and above in the console
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# Initialize logger
logger = setup_logger()

# Initialize Langtrace
langtrace.init(api_key=os.getenv("LANGTRACE_API_KEY"))

# ------------------------------------------------------------------------------------
# Log the Start of the Script
# ------------------------------------------------------------------------------------

logger.info(
    "Starting the function calling script to send airtime and messages using Africa's Talking API"
)
logger.info("Let's review the packages and their versions")

# ------------------------------------------------------------------------------------
# Log Versions of the Libraries
# ------------------------------------------------------------------------------------

pkgs = ["langtrace-python-sdk", "gradio", "ollama", "codecarbon"]

for pkg in pkgs:
    try:
        pkg_version = version(pkg)
        logger.info("%s version: %s", pkg, pkg_version)
    except PackageNotFoundError:
        logger.error("Package %s is not installed.", pkg)
    except Exception as e:
        logger.error("Failed to retrieve version for %s: %s", pkg, str(e))

# ------------------------------------------------------------------------------------
# Define Masking Functions
# ------------------------------------------------------------------------------------


def mask_phone_number(phone_number):
    """Hide the first digits of a phone number. Only the last 4 digits will be visible.

    Parameters
    ----------
    phone_number : str
        The phone number to mask.

    Returns
    -------
    str
        The masked phone number.
    """
    if len(phone_number) < 4:
        return "****"
    return "x" * (len(phone_number) - 4) + phone_number[-4:]


def mask_api_key(api_key):
    """Hide the first characters of an API key. Only the last 4 characters will be visible.

    Parameters
    ----------
    api_key : str
        The API key to mask.

    Returns
    -------
    str
        The masked API key.
    """
    if len(api_key) < 4:
        return "****"
    return "x" * (len(api_key) - 4) + api_key[-4:]


# ------------------------------------------------------------------------------------
# Define Tools Schema
# ------------------------------------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "send_airtime",
            "description": "Send airtime to a phone number using the Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The phone number in international format",
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "The 3-letter ISO currency code",
                    },
                    "amount": {
                        "type": "string",
                        "description": "The amount of airtime to send",
                    },
                },
                "required": ["phone_number", "currency_code", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message to a phone number using the Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The phone number in international format",
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send",
                    },
                    "username": {
                        "type": "string",
                        "description": "The username for the Africa's Talking account",
                    },
                },
                "required": ["phone_number", "message", "username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "Search for news articles using DuckDuckGo News API",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for news articles",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "The maximum number of news articles to retrieve",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": "Translate text to a specified language using Ollama & ",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate",
                    },
                    "target_language": {
                        "type": "string",
                        "description": "The target language for translation",
                    },
                },
                "required": ["text", "target_language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_ussd",
            "description": "Send a USSD code to a phone number using the Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The phone number in international format",
                    },
                    "code": {
                        "type": "string",
                        "description": "The USSD code to dial",
                    },
                },
                "required": ["phone_number", "code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_mobile_data",
            "description": "Send a mobile data bundle using the Africa's Talking API. The bundle can be specified as a string (e.g., '50', '500MB', or '1GB'). If a number is provided, it is interpreted as MB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The phone number in international format (e.g., '+254728303524')",
                    },
                    "bundle": {
                        "type": "string",
                        "description": "The bundle amount as a string. Examples: '50' (for 50MB), '500MB', '1GB'. If a number is provided, it is interpreted as MB.",
                    },
                    "provider": {
                        "type": "string",
                        "description": "The mobile network provider (e.g., 'Safaricom', 'Airtel')",
                    },
                    "plan": {
                        "type": "string",
                        "description": "The plan duration. Must be one of: 'daily', 'weekly', 'monthly' (case insensitive). Do not use bundle sizes here.",
                        "enum": ["daily", "weekly", "monthly", "day", "week", "month"],
                    },
                },
                "required": ["phone_number", "bundle", "provider", "plan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_voice_call",
            "description": "Initiate a voice call between two numbers using Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_number": {
                        "type": "string",
                        "description": "The caller ID",
                    },
                    "to_number": {
                        "type": "string",
                        "description": "The recipient phone number",
                    },
                },
                "required": ["from_number", "to_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wallet_balance",
            "description": "Fetch the current wallet balance from Africa's Talking account",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_voice_call_with_text",
            "description": "Make a voice call and say a message using text-to-speech with Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_number": {
                        "type": "string",
                        "description": "The caller ID",
                    },
                    "to_number": {
                        "type": "string",
                        "description": "The recipient phone number",
                    },
                    "message": {
                        "type": "string",
                        "description": "The text message to be spoken during the call",
                    },
                    "voice_type": {
                        "type": "string",
                        "description": "The voice type to use ('man' or 'woman')",
                        "default": "woman",
                    },
                },
                "required": ["from_number", "to_number", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_voice_call_and_play_audio",
            "description": "Make a voice call and play an audio file from a URL using Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_number": {
                        "type": "string",
                        "description": "The caller ID",
                    },
                    "to_number": {
                        "type": "string",
                        "description": "The recipient phone number",
                    },
                    "audio_url": {
                        "type": "string",
                        "description": "The public URL of the audio file to play (must be a direct HTTP/HTTPS URL to MP3, WAV, etc.)",
                    },
                },
                "required": ["from_number", "to_number", "audio_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_application_balance",
            "description": "Get application balance from Africa's Talking account using the Application Data endpoint",
            "parameters": {
                "type": "object",
                "properties": {
                    "sandbox": {
                        "type": "boolean",
                        "description": "Whether to use sandbox endpoint",
                        "default": False,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Send a WhatsApp message using Africa's Talking API",
            "parameters": {
                "type": "object",
                "properties": {
                    "wa_number": {
                        "type": "string",
                        "description": "The WhatsApp phone number associated with your AT account (sender)",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "The recipient's phone number",
                    },
                    "message": {
                        "type": "string",
                        "description": "The text message to send",
                    },
                    "media_type": {
                        "type": "string",
                        "description": "The type of media (Image, Video, Audio, Voice)",
                    },
                    "url": {
                        "type": "string",
                        "description": "The hosted URL of the media",
                    },
                    "caption": {
                        "type": "string",
                        "description": "The caption for the media",
                    },
                    "sandbox": {
                        "type": "boolean",
                        "description": "Use sandbox endpoint if True",
                        "default": False,
                    },
                },
                "required": ["wa_number", "phone_number"],
            },
        },
    },
]

# ------------------------------------------------------------------------------------
# Define Function to Process User Queries
# ------------------------------------------------------------------------------------


@with_langtrace_root_span()
async def process_user_message(
    message: str, history: list, use_vision: bool = False, image_path: str = None
) -> str:
    """
    Handle the conversation with the model asynchronously.

    Parameters
    ----------
    message : str
        The user's input message.
    history : list of list of str
        The conversation history up to that point.
    use_vision : bool, optional
        Flag to enable vision capabilities, by default False
    image_path : str, optional
        Path to the image file if using vision model, by default None

    Returns
    -------
    str
        The model's response or the function execution result.
    """
    masked_message = mask_phone_number(
        message
    )  # Assuming the message contains a phone number
    logger.info("Processing user message: %s", masked_message)
    client = ollama.AsyncClient()

    messages = []

    # Set the system prompt based on the vision flag
    system_prompt = VISION_SYSTEM_PROMPT if use_vision else API_SYSTEM_PROMPT

    # Construct message based on vision flag
    if use_vision:
        messages.append(
            {
                "role": "user",
                "content": message,
                "images": [image_path] if image_path else None,
            }
        )
    else:
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

    try:
        # Select model based on vision flag
        model_name = "llama3.2-vision" if use_vision else "qwen3:0.6b"

        response = await client.chat(
            model=model_name,
            messages=messages,
            tools=None if use_vision else tools,  # Vision models don't use tools
            options={
                "temperature": 0
            },  # Set temperature to 0 for deterministic responses
        )
    except Exception as e:
        logger.exception("Failed to get response from Ollama client.")
        return "An unexpected error occurred while communicating with the assistant."

    model_message = response.get("message", {})
    model_content = model_message.get("content", "")
    model_role = model_message.get("role", "assistant")
    logger.info("Model response: %s", model_content)

    messages.append(
        {
            "role": model_role,
            "content": model_content,
        }
    )

    if model_message.get("tool_calls"):
        for tool in model_message["tool_calls"]:
            tool_name = tool["function"]["name"]
            arguments = tool["function"]["arguments"]

            # Mask sensitive arguments before logging
            masked_args = {}
            for key, value in arguments.items():
                if "phone_number" in key:
                    masked_args[key] = mask_phone_number(value)
                elif "api_key" in key:
                    masked_args[key] = mask_api_key(value)
                else:
                    masked_args[key] = value

            # Fix string concatenation error by using proper string formatting
            logger.info(
                "Tool call detected: %s with arguments: %s", tool_name, str(masked_args)
            )

            try:
                if tool_name == "send_airtime":
                    logger.info("Calling send_airtime with arguments: %s", masked_args)
                    function_response = send_airtime(
                        arguments["phone_number"],
                        arguments["currency_code"],
                        arguments["amount"],
                    )
                elif tool_name == "send_message":
                    logger.info("Calling send_message with arguments: %s", masked_args)
                    function_response = send_message(
                        arguments["phone_number"],
                        arguments["message"],
                        arguments["username"],
                    )
                elif tool_name == "search_news":
                    logger.info("Calling search_news with arguments: %s", masked_args)
                    function_response = search_news(arguments["query"])
                elif tool_name == "translate_text":
                    logger.info(
                        "Calling translate_text with arguments: %s", masked_args
                    )
                    function_response = translate_text(
                        arguments["text"],
                        arguments["target_language"],
                    )
                elif tool_name == "send_ussd":
                    logger.info("Calling send_ussd with arguments: %s", masked_args)
                    function_response = send_ussd(
                        arguments["phone_number"],
                        arguments["code"],
                    )
                elif tool_name == "send_mobile_data":
                    logger.info(
                        "Calling send_mobile_data with arguments: %s",
                        masked_args,
                    )
                    # Check if credentials are available
                    if not os.getenv("AT_USERNAME") or not os.getenv("AT_API_KEY"):
                        return json.dumps(
                            {
                                "error": "Missing AT_USERNAME or AT_API_KEY environment variables"
                            }
                        )
                    function_response = send_mobile_data_wrapper(
                        phone_number=arguments["phone_number"],
                        bundle=arguments["bundle"],
                        provider=arguments["provider"],
                        plan=arguments["plan"],
                    )
                elif tool_name == "make_voice_call":
                    logger.info(
                        "Calling make_voice_call with arguments: %s", masked_args
                    )
                    function_response = make_voice_call(
                        arguments["from_number"],
                        arguments["to_number"],
                    )
                elif tool_name == "get_wallet_balance":
                    logger.info("Calling get_wallet_balance")
                    function_response = get_wallet_balance()
                elif tool_name == "make_voice_call_with_text":
                    logger.info(
                        "Calling make_voice_call_with_text with arguments: %s",
                        masked_args,
                    )
                    function_response = make_voice_call_with_text(
                        arguments["from_number"],
                        arguments["to_number"],
                        arguments["message"],
                        arguments.get("voice_type", "woman"),
                    )
                elif tool_name == "make_voice_call_and_play_audio":
                    logger.info(
                        "Calling make_voice_call_and_play_audio with arguments: %s",
                        masked_args,
                    )
                    function_response = make_voice_call_and_play_audio(
                        arguments["from_number"],
                        arguments["to_number"],
                        arguments["audio_url"],
                    )
                elif tool_name == "get_application_balance":
                    logger.info(
                        "Calling get_application_balance with arguments: %s",
                        masked_args,
                    )
                    function_response = get_application_balance(
                        arguments.get("sandbox", False),
                    )
                elif tool_name == "send_whatsapp_message":
                    logger.info(
                        "Calling send_whatsapp_message with arguments: %s",
                        masked_args,
                    )
                    function_response = send_whatsapp_message(
                        arguments["wa_number"],
                        arguments["phone_number"],
                        arguments.get("message"),
                        arguments.get("media_type"),
                        arguments.get("url"),
                        arguments.get("caption"),
                        arguments.get("sandbox", False),
                    )
                else:
                    function_response = json.dumps({"error": "Unknown function"})
                    logger.warning("Unknown function: %s", tool_name)

                logger.debug("Function response: %s", function_response)
                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                    }
                )

                return f"Function `{tool_name}` executed successfully.Response:\n{function_response}"  # noqa C0301
            except Exception as e:
                logger.exception("Error calling function %s: %s", tool_name, e)
                return "An unexpected error occurred while processing your message."
    else:
        logger.debug("No tool calls detected. Returning model content.")
        return model_content


# ------------------------------------------------------------------------------------
# Set Up Gradio Interface
# ------------------------------------------------------------------------------------


def gradio_interface(message: str, history: list) -> str:
    """
    Gradio interface function to process user messages and track emissions.

    Parameters
    ----------
    message : str
        The user's input message.
    history : list of list of str
        The conversation history up to that point.

    Returns
    -------
    str
        The model's response or the function execution result.
    """
    try:
        response = asyncio.run(process_user_message(message, history))
        return response
    except Exception as e:
        logger.exception("Error processing user message: %s", e)
        return "An unexpected error occurred while processing your message."


# ------------------------------------------------------------------------------------
# Create Gradio Interface
# ------------------------------------------------------------------------------------

iface = gr.ChatInterface(
    fn=gradio_interface,
    title="📱 Multi-Service Communication Interface 🌍",
    description=(
        "Welcome to the Airtime and Messaging Service using Africa's Talking API! 🎉\n\n"
        "You can send airtime, messages, USSD codes, mobile data, make voice calls, send WhatsApp messages, or check your account balance by typing commands such as:\n"
        "- `Send airtime to +254712345678 with an amount of 10 in currency KES` 📞\n"
        "- `Send a message to +254712345678 with the message 'Hello there', using the username 'username'` 💬\n"
        "- `Send USSD code *544# to +254712345678` 📱\n"
        "- `Send 500MB data bundle to +254712345678 using provider Safaricom with plan daily` 📶\n"
        "- `Make a voice call from +254712345678 to +254798765432` ☎️\n"
        "- `Make a voice call from +254700000001 to +254712345678 and say 'Hello, this is a test message'` 🗣️\n"
        "- `Make a voice call from +254700000001 to +254712345678 and play audio from https://github.com/runpod-workers/sample-inputs/raw/main/audio/gettysburg.wav` 🎵\n"
        "- `Check my wallet balance` 💰\n"
        "- `Get my application balance` 🏦\n"
        "- `Send WhatsApp message from +254799999999 to +254700000000 with message 'Hello via WhatsApp!'` 💻\n"
        "- `Search news for 'latest technology trends'` 📰\n\n"
        "You can also translate text to a target language by typing:\n"
        "- `Translate the text 'Hi' to the target language 'French'` 🌐\n\n"
        "Please enter your command below to get started. 🚀"
    ),
    examples=[
        ["Send airtime to +254712345678 with an amount of 10 in currency KES"],
        [
            "Send a message to +254712345678 with the message 'Hello there', using the username 'username'"
        ],
        ["Send USSD code *544# to +254712345678"],
        [
            "Send 500MB data bundle to +254712345678 using provider Safaricom with plan daily"
        ],
        ["Make a voice call from +254712345678 to +254798765432"],
        [
            "Make a voice call from +254700000001 to +254712345678 and say 'Hello, this is a test message'"
        ],
        [
            "Make a voice call from +254700000001 to +254712345678 and play audio from https://github.com/runpod-workers/sample-inputs/raw/main/audio/gettysburg.wav"
        ],
        ["Check my wallet balance"],
        ["Get my application balance. I am using a regular account"],
        [
            "Send WhatsApp message from +254799999999 to +254700000000 with message 'Hello via WhatsApp!'"
        ],
        ["Search news for 'latest technology trends'"],
        ["Translate the text 'Hi' to the target language 'French'"],
    ],
    type="messages",
)

# ------------------------------------------------------------------------------------
# Run the Gradio Interface
# ------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        logger.info("Launching Gradio interface...")
        iface.launch(inbrowser=True, server_name="0.0.0.0", server_port=7860)
        logger.info("Gradio interface launched successfully.")
    except Exception as e:
        logger.exception("Error launching Gradio interface: %s", e)

    # Log the end of the script
    logger.info("Script execution completed.")

    # Flush logs to ensure all logs are written out
    for handler in logger.handlers:
        handler.flush()
    # Flush logs to ensure all logs are written out
    for handler in logger.handlers:
        handler.flush()
