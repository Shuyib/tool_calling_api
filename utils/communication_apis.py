"""
Using the Africa's Talking API, send airtime to a phone number.

You'll need to have an Africa's Talking account, request for airtime API access in their dashboard, 
and get your API key and username.

This is the error you get
{'errorMessage': 'Airtime is not enabled for this account', 'numSent': 0,
'responses': [], 'totalAmount': '0', 'totalDiscount': '0'}

successful responses
{'errorMessage': 'None', 'numSent': 1, 'responses': [{'amount': 'KES 10.0000', 
'discount': 'KES 0.4000', 'errorMessage': 'None', 'phoneNumber': 'xxxxxxxx2046', 
'requestId': 'ATQid_xxxx', 'status': 'Sent'}], 'totalAmount': 'KES 10.0000', 
'totalDiscount': 'KES 0.4000'}

{'errorMessage': 'None', 'numSent': 1, 'responses': [{'amount': 'KES 10.0000',
'discount': 'KES 0.4000', 'errorMessage': 'None', 'phoneNumber': 'xxxxxxxx2046', 
'requestId': 'ATQid_xxxx', 'status': 'Sent'}], 'totalAmount': 'KES 10.0000', 
'totalDiscount': 'KES 0.4000'}
"""

import os
import logging
from importlib.metadata import version
import africastalking


# set up the logger
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# logging format
formatter = logging.Formatter("%(asctime)s:%(name)s:%(message)s")

# set up the file handler & stream handler
file_handler = logging.FileHandler("communication_apis.log")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# add the file handler to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# log the start of the script
logger.info("Starting the airtime script")

# log versions of the libraries
pkgs = ["africastalking"]

# see the versions of the libraries
for pkg in pkgs:
    try:
        logger.info("%s version: %s", pkg, version(pkg))
    except ImportError as e:
        logger.error("Failed to import %s: %s", pkg, str(e))


def mask_phone_number(phone_number):
    """Hide the first digits of a phone number.
    Only the last 4 digits will be visible.

    Why do we need to mask the phone number?
    - This is information that can be used to identify a person.
    PIIs (Personally Identifiable Information) should be protected.


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


def send_airtime(phone_number: str, currency_code: str, amount: str) -> None:
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
    # Load credentials
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    # Initialize the SDK
    africastalking.initialize(username, api_key)

    # Get the airtime service
    airtime = africastalking.Airtime

    masked_number = mask_phone_number(phone_number)
    logger.info("Sending airtime to %s", masked_number)
    logger.info("Amount: %s %s", amount, currency_code)

    try:
        # Send airtime
        responses = airtime.send(
            phone_number=phone_number, amount=amount, currency_code=currency_code
        )
        logger.info("The response is %s", responses)
    except Exception as e:
        logger.error("Encountered an error while sending airtime: %s", str(e))


def send_message(phone_number: str, message: str, username: str) -> None:
    """Allows you to send a message to a phone number.

    Parameters
    ----------
    phone_number: str : The phone number to send the message to.
    It should be in the international format.
    eg. +254712345678 (Kenya) - +254 is the country code.
    712345678 is the phone number.

    message: str : The message to send.
    It should be a string.
    eg. "Hello, this is a test message"

    username: str :
    The username to use for sending the message.
    this is the username you used to sign up for
    the Africa's Talking account.


    Returns
    -------
    None

    Examples
    --------
    send_message("+254712345678", "Hello there", "jak2")

    """
    # Load API key from environment variables
    api_key = os.getenv("AT_API_KEY")
    username = os.getenv("AT_USERNAME")
    if api_key is None:
        raise ValueError("API key not found in the environment")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    # Initialize the SDK
    africastalking.initialize(username, api_key)

    # Get the SMS service
    SMS = africastalking.SMS

    # Mask the phone number and log the message
    masked_number = mask_phone_number(phone_number)
    logger.info("Sending message to %s", masked_number)
    logger.info("Message: %s", message)

    # try-except block to catch any errors
    try:
        # Send message
        response = SMS.send(message, [phone_number])
        logger.info("The response is %s", response)
    except Exception as e:
        logger.error("Encountered an error while sending message: %s", str(e))


if __name__ == "__main__":
    # replace phone_number with the phone number you want to send airtime to
    send_airtime("phone_number", "KES", "10")
    # replace phone_number with the phone number you want to send a message to
    send_message("phone_number", "Hello, this is a test message", "my_username")
