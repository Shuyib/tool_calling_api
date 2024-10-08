"""
Function calling example using ollama to send airtime to a phone number 
using the Africa's Talking API.

The user provides a query like 
"Send airtime to +254712345678 with an amount of 10 in currency KES",
and the model decides to use the `send_airtime` function to send 
airtime to the provided phone number.

The user can also provide a query like 
"Send a message to +254712345678 with the message 
'Hello there', using the username 'username'",
and the model decides to use the `send_message` 
function to send a message to the provided phone number.

Credentials for the Africa's Talking API are loaded from 
environment variables `AT_USERNAME` and `AT_API_KEY`.

Credit: https://www.youtube.com/watch?v=i0tsVzRbsNU

You'll be prompted your computer password for codecarbon to track emissions.
"""

import os
import json
import logging
from importlib.metadata import version
import asyncio
import africastalking
import ollama
from codecarbon import EmissionsTracker  # Import the EmissionsTracker


# Set up the logger
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Logging format
formatter = logging.Formatter("%(asctime)s:%(name)s:%(message)s")

# Set up the file handler & stream handler
file_handler = logging.FileHandler("func_calling.log")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Flush logs
for handler in logger.handlers:
    handler.flush()

# Log the start of the script
logger.info(
    "Starting the function calling script to send airtime and messages using the "
    "Africa's Talking API"
)
logger.info("Let's review the packages and their versions")

# log versions of the libraries
pkgs = ["africastalking", "ollama"]

for pkg in pkgs:
    try:
        logger.debug("%s version: %s", pkg, version(pkg))
    except Exception as e:
        logger.error("Failed to import %s: %s", pkg, str(e))

# Flush logs again
# this is to ensure that the logs are written to the file
for handler in logger.handlers:
    handler.flush()

# Set the region explicitly to East Africa
os.environ["CODECARBON_REGION"] = "africa_east"


# Mask phone number and API key for the logs
def mask_phone_number(phone_number):
    """Hide the first digits of a phone number.
    Only the last 4 digits will be visible.

    Why do we need to mask the phone number?
    - This is information that can be used to
    identify a person. PIIs (Personally Identifiable Information)
    should be protected.

    Parameters
    ----------
    phone_number : str : The phone number to mask.

    Returns
    -------
    str : The masked phone number.

    Examples
    --------
    mask_phone_number("+254712345678")

    """
    return "x" * (len(phone_number) - 4) + phone_number[-4:]


def mask_api_key(api_key):
    """Hide the first digits of an API key. Only the last 4 digits will be visible.

    Why do we need to mask the API key?
    - To prevent unauthorized access to your account.

    Parameters
    ----------
    api_key : str : The API key to mask.

    Returns
    -------
    str : The masked API key.

    Examples
    --------
    mask_api_key("123456")
    """
    return "x" * (len(api_key) - 4) + api_key[-4:]


# Function to send airtime using Africa's Talking API
def send_airtime(phone_number: str, currency_code: str, amount: str, **kwargs) -> str:
    """Allows you to send airtime to a phone number.

    Parameters
    ----------
    phone_number: str : The phone number to send airtime to.
    It should be in the international format.
    eg. +254712345678 (Kenya) -
    +254 is the country code. 712345678 is the phone number.

    currency_code: str :
    The 3-letter ISO currency code. eg. KES for Kenya Shillings.

    amount: str :
    The amount of airtime to send. It should be a string. eg. "10"
    That means you'll send airtime worth 10 currency units.

    Returns
    -------
    None

    Examples
    --------
    send_airtime("+254712345678", "KES", "10")

    """
    # Load credentials from environment variables
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    # Initialize the SDK
    africastalking.initialize(username, api_key)

    # Get the airtime service
    airtime = africastalking.Airtime

    # Mask the phone number for logging
    masked_number = mask_phone_number(phone_number)
    logger.info("Sending airtime to %s", masked_number)

    try:
        # Send airtime
        responses = airtime.send(
            phone_number=phone_number, amount=amount, currency_code=currency_code
        )
        logger.debug("The response from sending airtime: %s", responses)
        return json.dumps(responses)
    except Exception as e:
        logger.error("Encountered an error while sending airtime: %s", str(e))
        return json.dumps({"error": str(e)})


def send_message(phone_number: str, message: str, username: str, **kwargs) -> None:
    """Allows you to send a message to a phone number.

    Parameters
    ----------
    phone_number: str :
    The phone number to send the message to.
    It should be in the international format.
    eg. +254712345678 (Kenya) -
    +254 is the country code. 712345678 is the phone number.

    message: str : The message to send. It should be a string.
    eg. "Hello, this is a test message"

    username: str : The username to use for sending the message.
    this is the username you used to sign up for the Africa's Talking account.

    Returns
    -------
    None

    Examples
    --------
    send_message("+254712345678", "Hello there", "jak2")

    """
    # Load API key from environment variables
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the API key: %s", mask_api_key(api_key))

    # Initialize the SDK
    africastalking.initialize(username, api_key)

    # Get the SMS service
    sms = africastalking.SMS

    # Mask the phone number for logging
    masked_number = mask_phone_number(phone_number)
    logger.info("Sending message to %s", masked_number)

    try:
        # Send the message
        response = sms.send(message, [phone_number])
        logger.debug("Message sent to %s. Response: %s", masked_number, response)
        return json.dumps(response)
    except Exception as e:
        logger.error("Encountered an error while sending the message: %s", str(e))
        return json.dumps({"error": str(e)})


# Asynchronous function to handle the conversation with the model
async def run(model: str, user_input: str):
    """Run the conversation with the model.

    Parameters
    ----------
    model : str : The model to use for the conversation.

    user_input : str : The user query to start the conversation.

    Returns
    -------
    None

    Examples
    --------
    asyncio.run(run("llama3.1",
    "Send airtime to +254712345678 with an amount of 10 in currency KES"))

    """
    client = ollama.AsyncClient()

    # Initialize conversation with a user query
    messages = [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
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
                    "description": "Send a message to a phone number using the Africa's Talking API",  # noqa
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

    # Add the model's response to the conversation history
    messages.append(response["message"])

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        logger.debug("The model didn't use the function. Its response was:")
        logger.debug(response["message"]["content"])
        return None

    if response["message"].get("tool_calls"):
        # Dictionary of available functions
        available_functions = {
            "send_airtime": send_airtime,
            "send_message": send_message,
        }
        for tool in response["message"]["tool_calls"]:
            # Get the function to call based on the tool name
            function_to_call = available_functions[tool["function"]["name"]]
            logger.debug("function to call: %s", function_to_call)

            # Call the function with the provided arguments
            if tool["function"]["name"] == "send_airtime":
                function_response = function_to_call(
                    tool["function"]["arguments"]["phone_number"],
                    tool["function"]["arguments"]["currency_code"],
                    tool["function"]["arguments"]["amount"],
                )
            elif tool["function"]["name"] == "send_message":
                function_response = function_to_call(
                    tool["function"]["arguments"]["phone_number"],
                    tool["function"]["arguments"]["message"],
                    tool["function"]["arguments"]["username"],
                )
                logger.debug("function response: %s", function_response)

            # Add the function response to the conversation history
            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )


# Main loop to get user input and run the conversation
if __name__ == "__main__":
    while True:
        user_prompt = input(
            "\n Hi, you can send airtime and messages using this interface for example \n\n"
            "Send airtime to +254712345678 with an amount of 10 in currency KES \n\n"
            "Send a message to +254712345678 with the message 'Hello there', using the username 'your_username'\n\n"
            "=> "
        )
        if not user_prompt:
            logger.info("No input provided. Exiting...")
            break
        elif user_prompt.lower() == "exit":
            break

        # Run the asynchronous function with tracker
        with EmissionsTracker(
            measure_power_secs=15,
            tracking_mode="offline",
            output_dir="carbon_output",
            project_name="function_call",
            experiment_name="send_airtime_and_messages",
        ) as tracker:
            asyncio.run(run("llama3.2", user_input=user_prompt))
            tracker.stop()
