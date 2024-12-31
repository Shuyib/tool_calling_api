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

Example:
    Send airtime to a phone number:
        - `Send airtime to +254712345678 with an amount of 10 in currency KES`
    Send a message to a phone number:
        - `Send a message to +254712345678 with the message 'Hello there',
        using the username 'username'`
    Search for news about a topic:
        - `Latest news on climate change`
        - `Translate the text 'Hello' to the target language 'French'`
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
from utils.function_call import send_airtime, send_message, search_news, translate_text

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
        messages.append({"role": "user", "content": message})

    try:
        # Select model based on vision flag
        model_name = "llama3.2-vision" if use_vision else "qwen2.5:0.5b"

        response = await client.chat(
            model=model_name,
            messages=messages,
            tools=None if use_vision else tools,  # Vision models don't use tools
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
        "You can send airtime or messages by typing commands such as:\n"
        "- `Send airtime to +254712345678 with an amount of 10 in currency KES` 📞\n"
        "- `Send a message to +254712345678 with the message 'Hello there', using the username 'username'` 💬\n"
        "- `Search news for 'latest technology trends'` 📰\n\n"
        "Please enter your command below to get started. 🚀"
    ),
    examples=[
        ["Send airtime to +254712345678 with an amount of 10 in currency KES"],
        [
            "Send a message to +254712345678 with the message 'Hello there', using the username 'username'"
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
