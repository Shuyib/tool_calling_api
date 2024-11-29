"""
Airtime and Messaging Service using Africa's Talking API

This script provides a Gradio-based web interface for sending airtime and messages
using the Africa's Talking API. It also tracks the carbon emissions of the operations
using the CodeCarbon library.

Usage:
    1. Set the environment variables `AT_USERNAME` and `AT_API_KEY` with your Africa's Talking credentials.
    2. Run the script: `python app.py`
    3. Access the Gradio web interface to send airtime or messages or search for news articles.

Example:
    Send airtime to a phone number:
        - `Send airtime to +254712345678 with an amount of 10 in currency KES`
    Send a message to a phone number:
        - `Send a message to +254712345678 with the message 'Hello there', using the username 'username'`
    Search for news about a topic:
        - `Latest news on climate change`
"""

import os
import json
import logging
import asyncio
import gradio as gr
from utils.function_call import send_airtime, send_message, search_news
import ollama

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

# Define tools schema
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
]


async def process_user_message(message: str, history: list) -> str:
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
        model="qwen2.5:0.5b",
        messages=messages,
        tools=tools,
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
            elif tool_name == "search_news":
                logger.info("Calling search_news with arguments: %s", arguments)
                function_response = search_news(arguments["query"])
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
    response = asyncio.run(process_user_message(message, history))
    return response


# Create Gradio interface
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
    ],
)

# Launch the Gradio interface
iface.launch(inbrowser=True, server_name="0.0.0.0", server_port=7860)

# Log the end of the script
logger.info("Script execution completed")
