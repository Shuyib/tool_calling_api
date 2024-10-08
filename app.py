"""
Airtime and Messaging Service using Africa's Talking API

This script provides a Gradio-based web interface for sending airtime and messages
using the Africa's Talking API. It also tracks the carbon emissions of the operations
using the CodeCarbon library.

Usage:
    1. Set the environment variables `AT_USERNAME` and `AT_API_KEY` with your Africa's Talking credentials.
    2. Run the script: `python app.py`
    3. Access the Gradio web interface to send airtime or messages.

Example:
    Send airtime to a phone number:
        - `Send airtime to +254712345678 with an amount of 10 in currency KES`
    Send a message to a phone number:
        - `Send a message to +254712345678 with the message 'Hello there', using the username 'username'`
"""

import os
import json
import logging
from importlib.metadata import version
import asyncio
import africastalking
import ollama
from codecarbon import EmissionsTracker
import gradio as gr

# Set up the logger
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Logging format
formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")

# Set up the file handler & stream handler
file_handler = logging.FileHandler("func_calling_app.log")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Log the start of the script
logger.info(
    "Starting the function calling script to send airtime and messages using the "
    "Africa's Talking API"
)
logger.info("Let's review the packages and their versions")

# Set the region explicitly to East Africa
os.environ["CODECARBON_REGION"] = "africa_east"

# Log versions of the libraries
pkgs = ["africastalking", "ollama"]

for pkg in pkgs:
    try:
        logger.debug("%s version: %s", pkg, version(pkg))
    except Exception as e:
        logger.error("Failed to import %s: %s", pkg, str(e))


def mask_phone_number(phone_number):
    """
    Hide the first digits of a phone number. Only the last 4 digits will be visible.

    Parameters
    ----------
    phone_number : str
        The phone number to mask.

    Returns
    -------
    str
        The masked phone number.
    """
    return "x" * (len(phone_number) - 4) + phone_number[-4:]


def mask_api_key(api_key):
    """
    Hide the first digits of an API key. Only the last 4 digits will be visible.

    Parameters
    ----------
    api_key : str
        The API key to mask.

    Returns
    -------
    str
        The masked API key.
    """
    return "x" * (len(api_key) - 4) + api_key[-4:]


def send_airtime(phone_number: str, currency_code: str, amount: str, **kwargs) -> str:
    """
    Send airtime using Africa's Talking API.

    Parameters
    ----------
    phone_number : str
        The phone number in international format.
    currency_code : str
        The 3-letter ISO currency code.
    amount : str
        The amount of airtime to send.

    Returns
    -------
    str
        The response from the API in JSON format.
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    africastalking.initialize(username, api_key)
    airtime = africastalking.Airtime

    masked_number = mask_phone_number(phone_number)
    logger.info("Sending airtime to %s", masked_number)

    try:
        responses = airtime.send(
            phone_number=phone_number, amount=amount, currency_code=currency_code
        )
        logger.debug("The response from sending airtime: %s", responses)
        response_data = responses["responses"][0]
        return json.dumps(response_data)
    except Exception as e:
        logger.error("Encountered an error while sending airtime: %s", str(e))
        return json.dumps({"error": str(e)})


def send_message(phone_number: str, message: str, username: str, **kwargs) -> str:
    """
    Send a message using Africa's Talking API.

    Parameters
    ----------
    phone_number : str
        The phone number in international format.
    message : str
        The message to send.
    username : str
        The username for the Africa's Talking account.

    Returns
    -------
    str
        The response from the API in JSON format.
    """
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the API key: %s", mask_api_key(api_key))

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS

    masked_number = mask_phone_number(phone_number)
    logger.info("Sending message to %s", masked_number)

    try:
        response = sms.send(message, [phone_number])
        logger.debug("Message sent to %s. Response: %s", masked_number, response)
        response_data = response["SMSMessageData"]["Recipients"][0]
        return json.dumps(response_data)
    except Exception as e:
        logger.error("Encountered an error while sending the message: %s", str(e))
        return json.dumps({"error": str(e)})


async def process_user_message(message, history):
    """
    Handle the conversation with the model asynchronously.

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
    logger.info("Processing user message: %s", message)
    client = ollama.AsyncClient()

    messages = [
        {
            "role": "user",
            "content": message,
        }
    ]

    response = await client.chat(
        model="llama3.2",
        messages=messages,
        tools=[
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
        ],
    )

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
    logger.debug("Model response: %s", response["message"])

    if model_message.get("tool_calls"):
        for tool in model_message["tool_calls"]:
            tool_name = tool["function"]["name"]
            arguments = tool["function"]["arguments"]
            logger.info("Tool call detected: %s", tool_name)

            if tool_name == "send_airtime":
                logger.info("Calling send_airtime with arguments: %s", arguments)
                function_response = send_airtime(
                    arguments["phone_number"],
                    arguments["currency_code"],
                    arguments["amount"],
                )
            elif tool_name == "send_message":
                logger.info("Calling send_message with arguments: %s", arguments)
                function_response = send_message(
                    arguments["phone_number"],
                    arguments["message"],
                    arguments["username"],
                )
            else:
                function_response = json.dumps({"error": "Unknown function"})

            logger.debug("Function response: %s", function_response)
            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )

            return f"Function `{tool_name}` executed successfully. Response:\n{function_response}"
    else:
        return model_content


def gradio_interface(message, history):
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
    with EmissionsTracker(
        measure_power_secs=15,
        tracking_mode="offline",
        project_name="function_call",
        experiment_name="send_airtime_and_messages",
    ) as tracker:
        response = asyncio.run(process_user_message(message, history))
        tracker.stop()
    return response


# Create Gradio interface
iface = gr.ChatInterface(
    fn=gradio_interface,
    title="📱 Airtime and Messaging Service 🌍",
    description=(
        "Welcome to the Airtime and Messaging Service using Africa's Talking API! 🎉\n\n"
        "You can send airtime or messages by typing commands such as:\n"
        "- `Send airtime to +254712345678 with an amount of 10 in currency KES` 📞\n"
        "- `Send a message to +254712345678 with the message 'Hello there', using the username 'username'` 💬\n\n"
        "Please enter your command below to get started. 🚀"
    ),
)

# Launch the Gradio interface
iface.launch(inbrowser=True, server_name="0.0.0.0", server_port=7860)
