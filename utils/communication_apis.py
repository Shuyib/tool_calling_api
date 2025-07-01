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

Mobile data response
'{"entries": [{"phoneNumber": "+254728303524", "provider": "Safaricom", "status":
 "Queued", "transactionId": "ATPid_xxxx", "value": "KES 15.0000"}]}'

Make a voice call
'{"entries": [{"phoneNumber": "+254728303524", "sessionId": "ATVId_xxxx", "status":
 "Queued"}], "errorMessage": "None"}'

Make a voice call with text
{'entries': [{'phoneNumber': '+254728303524', 'sessionId': 'ATVId_xxxx', 
'status': 'Queued'}], 'errorMessage': 'None', 
'xml_response': '<?xml version="1.0"?>\n<Response>\n    
<Say voice="woman">Hello, this is a test message</Say>\n</Response>', 
'session_id': '1dbd2e4e-20be-4971-9455-dfed5fe5552c', 'callback_url': 
'https://80c4-165-73-248-94.ngrok-free.app/voice/callback'}
"""

import os
import json
import requests
import logging
from importlib.metadata import version
import africastalking
from pydantic import BaseModel, field_validator
from typing import Union, List, Dict, Any, Optional


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


class SendMobileDataRequest(BaseModel):
    phone_number: str
    bundle: str
    provider: Optional[str] = None
    plan: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v

    @field_validator("bundle")
    @classmethod
    def validate_bundle(cls, v):
        if not v:
            raise ValueError("Bundle amount is required")
        return v


class SendUSSDRequest(BaseModel):
    phone_number: str
    code: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v


class MakeVoiceCallRequest(BaseModel):
    from_number: str
    to_number: str

    @field_validator("from_number", "to_number")
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v


class MakeVoiceCallWithTextRequest(BaseModel):
    from_number: str
    to_number: str
    message: str
    voice: Optional[str] = "woman"

    @field_validator("from_number", "to_number")
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v

    @field_validator("voice")
    @classmethod
    def validate_voice(cls, v):
        if v not in ["man", "woman"]:
            raise ValueError("Voice must be either 'man' or 'woman'")
        return v


class MakeVoiceCallAndPlayAudioRequest(BaseModel):
    from_number: str
    to_number: str
    audio_url: str

    @field_validator("from_number", "to_number")
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v

    @field_validator("audio_url")
    @classmethod
    def validate_audio_url(cls, v):
        # Basic URL validation, can be expanded
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("audio_url must be a valid HTTP/HTTPS URL")
        return v


# log the start of the script
logger.info("Starting the communication api script")

# log versions of the libraries
pkgs = ["africastalking", "requests", "pydantic", "importlib-metadata"]

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


def send_airtime(phone_number: str, currency_code: str, amount: str) -> str:
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
    str
        JSON response from the API

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
        return json.dumps(responses)
    except Exception as e:
        logger.error("Encountered an error while sending airtime: %s", str(e))
        return json.dumps({"error": str(e)})


def send_message(phone_number: str, message: str, username: str) -> str:
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
    str
        JSON response from the API

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

    try:
        # Send message
        response = SMS.send(message, [phone_number])
        logger.info("The response is %s", response)
        return json.dumps(response)
    except Exception as e:
        logger.error("Encountered an error while sending message: %s", str(e))
        return json.dumps({"error": str(e)})


def send_ussd(phone_number: str, code: str) -> str:
    """Send a USSD code to a phone number.

    Note: USSD typically works for interactive sessions rather than sending codes.
    This function may not work as expected with the Africa\'s Talking API
    for initiating outgoing USSD pushes.
    Consider using USSD for handling incoming USSD sessions instead.

    Parameters
    ----------
    phone_number : str
        The phone number to dial the USSD code on.
    code : str
        The USSD code to send, e.g. ``*123#``.

    Returns
    -------
    str
        JSON response from the API.

    Examples
    --------
    send_ussd("+254712345678", "*123#")
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    africastalking.initialize(username, api_key)

    try:
        ussd_service = africastalking.USSD
    except AttributeError:
        ussd_service = None

    if ussd_service is None or not hasattr(ussd_service, "send"):
        logger.error(
            "Africa's Talking USSD service (africastalking.USSD) is None, does not exist, or lacks a 'send' method after initialization."
        )
        logger.error(
            "This strongly suggests the SDK may not support sending outgoing USSD codes this way, "
            "or the USSD product might not be enabled/configured for your account "
            "for this type of operation (e.g., Push USSD)."
        )
        logger.error(
            "Please verify your Africa's Talking account settings and consult their "
            "official Python SDK documentation for 'Push USSD' or application-initiated USSD features."
        )
        return json.dumps(
            {
                "error": "USSD service not available, not supported for sending outgoing codes via this SDK method, or not correctly accessed."
            }
        )

    masked_number = mask_phone_number(phone_number)
    logger.info("Attempting to send USSD %s to %s", code, masked_number)
    logger.warning(
        "USSD typically handles incoming interactive sessions. "
        "Initiating outgoing USSD codes via API might have limitations or require specific AT products."
    )

    try:
        response = ussd_service.send(phone_number=phone_number, text=code)
        logger.info("USSD response: %s", response)
        return json.dumps(response)
    except AttributeError as e:
        logger.error(
            "AttributeError encountered while sending USSD: %s. "
            "This often means the 'ussd_service' object is None or lacks the 'send' method, "
            "or the arguments are incorrect.",
            str(e),
        )
        logger.error(
            "Ensure 'africastalking.USSD' is the correct way to access the USSD push service "
            "and that it's initialized. Check the official AT Python SDK documentation."
        )
        return json.dumps(
            {"error": f"AttributeError: {str(e)} - USSD send operation failed."}
        )
    except Exception as e:
        logger.error("Encountered an unexpected error while sending USSD: %s", str(e))
        logger.error(
            "This could be due to network issues, invalid parameters, or API errors."
        )
        return json.dumps({"error": f"API Error: {str(e)}"})


def send_mobile_data_wrapper(
    phone_number: str, bundle: Union[str, int], provider: str, plan: str
) -> str:
    """
    Wrapper function for send_mobile_data that handles parameter conversion.

    Parameters
    ----------
    phone_number : str
        The recipient phone number in international format (e.g., "+254728303524")
    bundle : Union[str, int]
        The data bundle amount as integer MB or string with unit (e.g., 50, "100MB", "1GB")
        If no unit is specified, MB is assumed
    provider : str
        The telecom provider (e.g., "Safaricom", "Airtel")
    plan : str
        The plan duration (e.g., "daily", "weekly", "monthly")

    Returns
    -------
    str
        JSON response from the API

    Examples
    --------
    >>> send_mobile_data_wrapper("+254728303524", 50, "Safaricom", "daily")
    >>> send_mobile_data_wrapper("+254712345678", "100MB", "Airtel", "weekly")
    >>> send_mobile_data_wrapper("+254798765432", "1GB", "Safaricom", "monthly")
    """
    try:
        # Handle integer input (assumed MB)
        if isinstance(bundle, (int, float)):
            quantity = int(bundle)
            unit = "MB"
        else:
            # Parse string bundle format
            bundle_lower = str(bundle).lower().strip()
            if "gb" in bundle_lower:
                unit = "GB"
                quantity = int("".join(filter(str.isdigit, bundle_lower)))
            else:
                # Default to MB if no unit or if MB specified
                unit = "MB"
                quantity = int("".join(filter(str.isdigit, bundle_lower)))
        if quantity <= 0:
            raise ValueError(f"Bundle quantity must be positive: {quantity}")

        # Map plan to validity period
        plan_mapping = {
            "daily": "Day",
            "weekly": "Week",
            "monthly": "Month",
            "day": "Day",
            "week": "Week",
            "month": "Month",
        }
        plan_lower = plan.lower().strip()
        if plan_lower not in plan_mapping:
            raise ValueError(
                f"Invalid plan duration: {plan}. Must be daily, weekly, or monthly."
            )
        validity = plan_mapping[plan_lower]

        # Use a consistent product name format
        product_name = f"{provider.strip()}_mobile_data"

        # Log the parsed parameters
        logger.info(
            "Parsed mobile data parameters: quantity=%s, unit=%s, validity=%s, product=%s",
            quantity,
            unit,
            validity,
            product_name,
        )

        return send_mobile_data_original(
            phone_number=phone_number,
            quantity=quantity,  # Now passing as int
            unit=unit,
            validity=validity,
            product_name=product_name,
        )

    except Exception as e:
        error_msg = f"Error in send_mobile_data_wrapper: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def get_wallet_balance() -> str:
    """
    Fetch the current wallet balance from Africa's Talking account using the documented API endpoint.
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))
    url = f"https://bundles.africastalking.com/query/wallet/balance?username={username}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apiKey": api_key,
    }
    logger.info("Fetching wallet balance from documented endpoint")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Wallet balance response: %s", data)
        return json.dumps(data)
    except Exception as e:
        logger.error("Encountered an error while fetching wallet balance: %s", str(e))
        return json.dumps({"error": str(e)})


def send_mobile_data_original(
    phone_number: str,
    quantity: Optional[Union[int, str]],
    unit: str,
    validity: str,
    product_name: str,
) -> str:
    """
    Send mobile data to a phone number using Africa's Talking API.

    Parameters
    ----------
    phone_number : str
        The recipient phone number in international format (e.g., "+254728303524")
    quantity : Union[int, str]
        The amount of data as an integer or string (e.g., 50, "100")
        Will be converted to int internally
    unit : str
        The data unit ("MB" or "GB")
    validity : str
        The validity period ("Day", "Week", "Month")
    product_name : str
        Your Africa's Talking app product name (e.g., "mobiledata")

    Returns
    -------
    str
        JSON response from the API

    Examples
    --------
    >>> send_mobile_data_original("+254728303524", 50, "MB", "Month", "mobiledata")
    >>> send_mobile_data_original("+254712345678", "100", "MB", "Week", "myapp")
    >>> send_mobile_data_original("+254798765432", 1, "GB", "Month", "data_service")

    Notes
    -------
    The Day plan has been phased out by Africa's Talking.
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")

    if not username or not api_key:
        error_msg = "Missing AT_USERNAME or AT_API_KEY environment variables"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    # Check wallet balance before proceeding
    try:
        balance_response = get_wallet_balance()
        balance_data = json.loads(balance_response)
        if balance_data.get("status") == "Success" and "balance" in balance_data:
            balance_str = balance_data["balance"].split(" ")[1]
            balance = float(balance_str)
            if balance <= 0:
                error_msg = f"Insufficient wallet balance: {balance}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
        else:
            error_msg = "Could not fetch wallet balance"
            logger.error(f"{error_msg}. Response: {balance_data}")
            return json.dumps({"error": error_msg})
    except Exception as e:
        error_msg = f"Error checking wallet balance: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    # Validate input parameters
    if not all([phone_number, quantity, unit, validity, product_name]):
        error_msg = "Missing required parameters"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    if not phone_number.startswith("+"):
        error_msg = f"Invalid phone number format: {mask_phone_number(phone_number)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    if unit not in ["MB", "GB"]:
        error_msg = f"Invalid unit: {unit}. Must be 'MB' or 'GB'"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    if validity not in ["Day", "Week", "Month"]:
        error_msg = f"Invalid validity: {validity}. Must be 'Day', 'Week', or 'Month'"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    # Convert quantity to integer as per API requirements
    try:
        quantity_int = int(quantity)
        if quantity_int <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError as e:
        error_msg = f"Invalid quantity value: {quantity}. Error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    # Always use the live endpoint
    url = "https://bundles.africastalking.com/mobile/data/request"

    # Prepare recipients with required metadata
    recipients = [
        {
            "phoneNumber": phone_number,
            "quantity": quantity_int,
            "unit": unit,
            "validity": validity,
            "metadata": {  # Always include metadata
                "phoneNumber": phone_number,
                "product": product_name,
                "quantity": str(quantity_int),
                "unit": unit,
                "validity": validity,
            },
        }
    ]

    # Prepare the request payload
    request_payload = {
        "username": username,
        "productName": product_name,
        "recipients": recipients,
    }

    # Set proper headers
    headers = {
        "apiKey": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    masked_number = mask_phone_number(phone_number)
    logger.info(
        f"Sending {quantity}{unit} data to {masked_number} (validity: {validity})"
    )
    logger.debug(f"Request payload: {json.dumps(request_payload, indent=2)}")
    logger.debug(f"Headers: {json.dumps(dict(headers), indent=2)}")

    try:
        response = requests.post(
            url,
            json=request_payload,  # Use json parameter for proper serialization
            headers=headers,
            timeout=10,
        )

        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        try:
            response_json = response.json()
            logger.info(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except ValueError:
            logger.error(f"Non-JSON response: {response.text}")
            return json.dumps({"error": f"Invalid JSON response: {response.text}"})

        if not response.ok:
            error_msg = f"API error: {response.status_code} - {response_json.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

        return json.dumps(response_json)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        if hasattr(e, "response") and e.response is not None:
            error_msg += f"\nResponse: {e.response.text}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def make_voice_call(from_number: str, to_number: str) -> str:
    """Initiate a voice call between two numbers.

    Parameters
    ----------
    from_number : str
        The caller ID for the voice call.
    to_number : str
        The recipient of the call.

    Returns
    -------
    str
        JSON response from the API.

    Examples
    --------
    make_voice_call("+254700000001", "+254712345678")
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))

    # Validate phone numbers
    try:
        request = MakeVoiceCallRequest(from_number=from_number, to_number=to_number)
    except ValueError as e:
        error_msg = f"Phone number validation failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    africastalking.initialize(username, api_key)
    voice = africastalking.Voice
    masked_number = mask_phone_number(to_number)
    logger.info("Calling %s from %s", masked_number, from_number)

    try:
        # Pass to_number as a list and use consistent parameter names
        response = voice.call(
            callFrom=from_number,
            callTo=[to_number],  # Pass as list as required by AT API
        )
        logger.info("Voice call response: %s", response)
        return json.dumps(response)
    except Exception as e:
        error_msg = f"Encountered an error while making voice call: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def make_voice_call_with_text(
    from_number: str, to_number: str, message: str, voice_type: str = "woman"
) -> str:
    """Make a voice call and say a message using text-to-speech.

    This function initiates a voice call and uses Africa\'s Talking text-to-speech
    engine to read the provided message to the recipient. It relies on the
    voice_callback_server.py to store the message and serve the XML.
    The callback URL must be configured in the Africa\'s Talking dashboard.

    Parameters
    ----------
    from_number : str
        The caller ID for the voice call (must start with +)
    to_number : str
        The recipient phone number (must start with +)
    message : str
        The text message to be spoken during the call
    voice_type : str, optional
        The voice type to use ("man" or "woman"), defaults to "woman"

    Returns
    -------
    str
        JSON response from the API containing call details

    Examples
    --------
    make_voice_call_with_text("+254700000001", "+254712345678", "Hello, this is a test message", "woman")
    """
    import requests
    import uuid

    try:
        # Validate inputs
        request = MakeVoiceCallWithTextRequest(
            from_number=from_number,
            to_number=to_number,
            message=message,
            voice=voice_type,
        )

        username = os.getenv("AT_USERNAME")
        api_key = os.getenv("AT_API_KEY")
        # Ensure this matches the port your voice_callback_server.py is running on
        callback_server_url = os.getenv("VOICE_CALLBACK_URL", "http://localhost:5001")

        logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))
        logger.info("Callback server URL for storing message: %s", callback_server_url)

        # Generate a unique session ID for this call
        session_id = str(uuid.uuid4())

        # Store the message in the callback server
        try:
            store_response = requests.post(
                f"{callback_server_url}/voice/store",
                json={
                    "session_id": session_id,
                    "to_number": to_number,
                    "message": message,
                    "voice_type": voice_type,
                },
                timeout=5,
            )
            if store_response.status_code != 200:
                logger.warning(
                    "Failed to store message in callback server: %s",
                    store_response.text,
                )
                # Optionally, you might want to return an error here if storing the message is critical
                # return json.dumps({"error": f"Failed to store message in callback server: {store_response.text}"})
        except requests.exceptions.RequestException as e:
            logger.warning(
                "Could not connect to callback server to store message: %s", str(e)
            )
            # Optionally, return an error if connection to callback server is critical
            # return json.dumps({"error": f"Could not connect to callback server: {str(e)}"})
            # Continue with the call anyway, but it won't have custom message if store failed

        africastalking.initialize(username, api_key)
        voice = africastalking.Voice
        masked_number = mask_phone_number(to_number)
        logger.info(
            "Making voice call with text to %s from %s", masked_number, from_number
        )
        logger.info(
            "Message: %s", message[:50] + "..." if len(message) > 50 else message
        )
        logger.info("Session ID: %s", session_id)

        # Make the voice call - callback URL is configured in AT dashboard
        response = voice.call(
            callFrom=from_number,
            callTo=[to_number],  # Pass as list, as required by africastalking API
        )

        # Create XML response for reference
        xml_response = f"""<?xml version="1.0"?>
<Response>
    <Say voice="{voice_type}">{message}</Say>
</Response>"""

        # Add additional info to the response
        if isinstance(response, dict):
            response["xml_response"] = xml_response
            response["session_id"] = session_id

        logger.info("Voice call with text response: %s", response)
        return json.dumps(response)

    except Exception as e:
        logger.error(
            "Encountered an error while making voice call with text: %s", str(e)
        )
        return json.dumps({"error": str(e)})


def make_voice_call_and_play_audio(
    from_number: str, to_number: str, audio_url: str
) -> str:
    """Make a voice call and play an audio file from a URL.

    This function initiates a voice call. The actual playback of the audio
    is handled by your voice_callback_server.py, which should serve an XML
    with the <Play> action when Africa's Talking requests call instructions.

    Parameters
    ----------
    from_number : str
        The caller ID for the voice call (must start with +)
    to_number : str
        The recipient phone number (must start with +)
    audio_url : str
        The public URL of the audio file to play (e.g., MP3, WAV).

    Returns
    -------
    str
        JSON response from the API containing call details.

    Examples
    --------
    make_voice_call_and_play_audio("+254700000001", "+254712345678", "http://example.com/audio.mp3")
    """
    import requests
    import uuid

    try:
        # Validate inputs
        request_data = MakeVoiceCallAndPlayAudioRequest(
            from_number=from_number, to_number=to_number, audio_url=audio_url
        )

        username = os.getenv("AT_USERNAME")
        api_key = os.getenv("AT_API_KEY")
        callback_server_url = os.getenv(
            "VOICE_CALLBACK_URL", "http://localhost:5001"
        )  # Ensure this is your callback server

        logger.info(
            "Loaded the credentials: %s %s",
            username,
            mask_api_key(api_key if api_key else ""),
        )
        logger.info(
            "Callback server URL for storing play info: %s", callback_server_url
        )

        if not username or not api_key:
            logger.error("AT_USERNAME or AT_API_KEY missing.")
            return json.dumps({"error": "Authentication credentials missing."})

        session_id = str(uuid.uuid4())

        # Store the audio URL and session ID in the callback server
        # This endpoint /voice/store_play_info needs to be implemented in voice_callback_server.py
        store_play_info_endpoint = f"{callback_server_url}/voice/store_play_info"
        try:
            store_response = requests.post(
                store_play_info_endpoint,
                json={"session_id": session_id, "audio_url": request_data.audio_url},
                timeout=5,
            )
            if store_response.status_code != 200:
                logger.warning(
                    "Failed to store play info in callback server (%s): %s",
                    store_play_info_endpoint,
                    store_response.text,
                )
                # Decide if you want to proceed if storing fails
        except requests.exceptions.RequestException as e:
            logger.warning(
                "Could not connect to callback server to store play info (%s): %s",
                store_play_info_endpoint,
                str(e),
            )

        africastalking.initialize(username, api_key)
        voice = africastalking.Voice
        masked_to_number = mask_phone_number(request_data.to_number)
        logger.info(
            "Making voice call to %s from %s to play audio: %s",
            masked_to_number,
            request_data.from_number,
            request_data.audio_url,
        )
        logger.info("Session ID for play audio call: %s", session_id)

        # Make the voice call. The callback URL configured in your AT dashboard
        # will be called by AT to get instructions (e.g., the <Play> XML).
        response = voice.call(
            callFrom=request_data.from_number, callTo=[request_data.to_number]
        )

        # Add session_id and audio_url to the response for reference
        if isinstance(response, dict):
            response["session_id"] = session_id
            response["audio_url_to_play"] = request_data.audio_url
            response["notes"] = (
                "Call initiated. Playback is controlled by the XML from your callback server "
                "which should use the stored audio_url for this session_id."
            )

        logger.info("Voice call (for play audio) response: %s", response)
        return json.dumps(response)

    except Exception as e:
        logger.error(
            "Encountered an error while making voice call to play audio: %s", str(e)
        )
        return json.dumps({"error": str(e)})


def get_application_balance(sandbox: bool = False) -> str:
    """
    Fetch the general application balance from Africa's Talking using the Application Data endpoint.

    Parameters
    ----------
    username : str
        Your Africa's Talking application username.
    api_key : str
        Your Africa's Talking API key.
    sandbox : bool
        Whether to use the sandbox endpoint (default: False).

    Returns
    -------
    str
        JSON response containing application balance information.

    Examples
    --------
    get_application_balance("my_username", "my_api_key")
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")

    logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))
    if sandbox:
        url = (
            f"https://api.sandbox.africastalking.com/version1/user?username={username}"
        )
    else:
        url = f"https://api.africastalking.com/version1/user?username={username}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apiKey": api_key,
    }
    logger.info("Fetching application balance from Application Data endpoint: %s", url)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Application balance response: %s", data)
        return json.dumps(data)
    except Exception as e:
        logger.error(
            "Encountered an error while fetching application balance: %s", str(e)
        )
        return json.dumps({"error": str(e)})


def send_whatsapp_message(
    username: str,
    api_key: str,
    wa_number: str,
    phone_number: str,
    message: str = None,
    media_type: str = None,
    url: str = None,
    caption: str = None,
    body: list = None,
    action: list = None,
    buttons: list = None,
    sandbox: bool = False,
) -> str:
    """
    Send a WhatsApp message using Africa's Talking API.

    Parameters
    ----------
    username : str
        Your Africa's Talking application username.
    api_key : str
        Your Africa's Talking API key.
    wa_number : str
        The WhatsApp phone number associated with your Africa's Talking account (sender).
    phone_number : str
        The recipient's phone number.
    message : str, optional
        The text message to send.
    media_type : str, optional
        The type of media (Image, Video, Audio, Voice).
    url : str, optional
        The hosted URL of the media.
    caption : str, optional
        The caption for the media.
    body : list, optional
        List for interactive messages.
    action : list, optional
        List of actions for interactive messages.
    buttons : list, optional
        List of buttons for interactive messages.
    sandbox : bool, optional
        Use sandbox endpoint if True.

    Returns
    -------
    str
        JSON response from the API.

    Examples
    --------
    send_whatsapp_message("my_username", "my_api_key", "+254799999999", "+254700000000", message="Hello!")
    """
    if sandbox:
        url_endpoint = "https://chat.sandbox.africastalking.com/whatsapp/message/send"
    else:
        url_endpoint = "https://chat.africastalking.com/whatsapp/message/send"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apiKey": api_key,
    }

    body_dict = {}
    if message:
        body_dict["message"] = message
    if media_type:
        body_dict["mediaType"] = media_type
    if url:
        body_dict["url"] = url
    if caption:
        body_dict["caption"] = caption
    if body:
        body_dict["body"] = body
    if action:
        body_dict["action"] = action
    if buttons:
        body_dict["buttons"] = buttons

    payload = {
        "username": username,
        "waNumber": wa_number,
        "phoneNumber": phone_number,
        "body": body_dict,
    }

    logger.info(f"Sending WhatsApp message to {phone_number} via {wa_number}")
    logger.info(f"Payload: {payload}")

    try:
        response = requests.post(
            url_endpoint, headers=headers, json=payload, timeout=10
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"WhatsApp message response: {data}")
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # replace phone_number with the phone number you want to send airtime to
    send_airtime("phone_number", "KES", "10")
    # replace phone_number with the phone number you want to send a message to
    send_message("phone_number", "Hello, this is a test message", "my_username")
    print("Your wallet balance is: ", get_wallet_balance())
