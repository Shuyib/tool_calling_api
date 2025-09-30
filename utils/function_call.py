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
from logging.handlers import RotatingFileHandler
from importlib.metadata import version
import asyncio
import re
import warnings
from typing import Optional, Union

import ollama
import requests

# Suppress Pydantic UserWarning from autogen
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*Field.*in.*has conflict with protected namespace.*",
)


# Monkey-patch for pydantic issue with autogen
# See: https://github.com/microsoft/autogen/issues/1996
try:
    from pydantic._internal import _typing_extra
except ImportError:
    pass  # not a pydantic v2.7.0+ installation, no issue
else:
    try:
        # pydantic v2.7.0+
        from pydantic._internal._typing_extra import try_eval_type
    except ImportError:
        # autogen is not yet compatible with pydantic v2.7.0+
        # see: https://github.com/microsoft/autogen/issues/1996
        # monkey-patch pydantic
        from typing import Any, Dict, Type

        def try_eval_type(t: Type[Any]) -> Type[Any]:
            try:
                return _typing_extra._eval_type(
                    t, globalns=None, localns=None, type_aliases=None
                )
            except (NameError, TypeError):
                return t

        _typing_extra.try_eval_type = try_eval_type


from autogen.agentchat.conversable_agent import ConversableAgent
from pydantic import BaseModel, field_validator, ValidationError

from .communication_apis import send_mobile_data_wrapper

# from codecarbon import EmissionsTracker  # Import the EmissionsTracker
from duckduckgo_search import DDGS
from .inspect_safety import create_safety_evaluator


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
        "func_calling.log", maxBytes=5 * 1024 * 1024, backupCount=5
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


class SendSMSRequest(BaseModel):
    phone_number: str
    message: str
    username: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v or not v.startswith("+"):
            raise ValueError(
                "phone_number must be in international format, e.g. +254712345678"
            )
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("message cannot be empty")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("username cannot be empty")
        return v


class SendMobileDataRequest(BaseModel):
    phone_number: str
    bundle: str
    provider: str
    plan: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v or not v.startswith("+"):
            raise ValueError(
                "phone_number must be in international format, e.g. +254712345678"
            )
        return v

    @field_validator("bundle")
    @classmethod
    def validate_bundle(cls, v):
        # Allow numeric values or strings with MB/GB
        if not re.match(r"^\d+(?:MB|GB)?$", str(v), re.IGNORECASE):
            raise ValueError(
                "bundle must be a number or a string with unit, e.g. 50, 500MB, 1GB"
            )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        if not v:
            raise ValueError("provider must not be empty")
        return v

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v):
        valid_plans = ["daily", "weekly", "monthly", "day", "week", "month"]
        if v.lower() not in valid_plans:
            raise ValueError(f"plan must be one of: {', '.join(valid_plans)}")
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


class GetApplicationBalanceRequest(BaseModel):
    """Request model for getting application balance"""

    sandbox: Optional[bool] = False

    @field_validator("sandbox")
    @classmethod
    def validate_sandbox(cls, v):
        return bool(v)


class SendWhatsAppMessageRequest(BaseModel):
    """Request model for sending WhatsApp messages"""

    wa_number: str
    phone_number: str
    message: Optional[str] = None
    media_type: Optional[str] = None
    url: Optional[str] = None
    caption: Optional[str] = None
    sandbox: Optional[bool] = False

    @field_validator("wa_number", "phone_number")
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone number must start with +")
        return v

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v):
        if v and v not in ["Image", "Video", "Audio", "Voice"]:
            raise ValueError("media_type must be one of: Image, Video, Audio, Voice")
        return v


class SendAirtimeRequest(BaseModel):
    phone_number: str
    currency_code: str
    amount: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if not v or not v.startswith("+") or not v[1:].isdigit():
            raise ValueError(
                "phone_number must be in international format, e.g. +254712345678"
            )
        return v

    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v):
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError("currency_code must be a 3-letter ISO code, e.g. KES")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if not v or not re.match(r"^\d+(\.\d{1,2})?$", v):
            raise ValueError("amount must be a valid decimal number, e.g. 10 or 10.50")
        return v


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
    str
        JSON response from the API

    Examples
    --------
    send_airtime("+254712345678", "KES", "10")

    """
    try:
        validated = SendAirtimeRequest(
            phone_number=phone_number, currency_code=currency_code, amount=amount
        )
    except ValidationError as ve:
        logger.error(f"Airtime parameter validation failed: {ve}")
        return str(ve)

    try:
        # Delegate to the standardized implementation in communication_apis
        from .communication_apis import send_airtime as comm_send_airtime

        masked_number = mask_phone_number(phone_number)
        logger.info("Delegating airtime sending to %s", masked_number)
        logger.info("Amount: %s %s", amount, currency_code)

        response = comm_send_airtime(phone_number, currency_code, amount)
        logger.debug("Airtime delegation response: %s", response)
        return response

    except Exception as e:
        logger.error("Encountered an error while sending airtime: %s", str(e))
        return json.dumps({"error": str(e)})


def send_message(phone_number: str, message: str, username: str, **kwargs) -> str:
    """Allows you to send a message to a phone number.

    Parameters
    ----------
    phone_number: str : The phone number to send the message to.
    It should be in the international format.
    eg. +254712345678 (Kenya) - +254 is the country code. 712345678 is the phone number.

    message: str : The message to send. It should be a string.
    eg. "Hello, this is a test message"

    username: str : The username to use for sending the message.
    this is the username you used to sign up for the Africa's Talking account.

    Returns
    -------
    str
        JSON response from the API

    Examples
    --------
    send_message("+254712345678", "Hello there", "jak2")

    """
    # Remove the fallback relative import, which causes issues when run as a script
    try:
        validated = SendSMSRequest(
            phone_number=phone_number, message=message, username=username
        )
    except ValidationError as ve:
        logger.error(f"SMS parameter validation failed: {ve}")
        return str(ve)

    try:
        # Use absolute import for communication_apis to avoid relative import errors
        from .communication_apis import send_message as comm_send_message

        masked_number = mask_phone_number(phone_number)
        logger.info("Delegating message sending to %s", masked_number)
        logger.info("Message: %s", message)
        response = comm_send_message(phone_number, message, username)
        logger.debug("Message delegation response: %s", response)
        return response
    except Exception as e:
        logger.error("Encountered an error while sending message: %s", str(e))
        return json.dumps({"error": str(e)})


def send_ussd(phone_number: str, code: str, **kwargs) -> str:
    """Send a USSD code to a phone number.

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
    logger.info("send_ussd received: phone_number=%r, code=%r", phone_number, code)
    if not phone_number or not code:
        error_msg = (
            f"Missing required arguments: phone_number={phone_number}, code={code}"
        )
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    try:
        # Delegate to the standardized implementation in communication_apis
        from .communication_apis import send_ussd as comm_send_ussd

        masked_number = mask_phone_number(phone_number)
        logger.info("Delegating USSD sending to %s", masked_number)

        response = comm_send_ussd(phone_number, code)
        logger.debug("USSD delegation response: %s", response)
        return response

    except Exception as e:
        error_msg = f"Encountered an error while sending USSD: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


def get_wallet_balance(**kwargs) -> str:
    """
    Fetch the current wallet balance from Africa's Talking account using the
    documented API endpoint.
    """
    try:
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
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Wallet balance response: %s", data)
        return json.dumps(data)
    except Exception as e:
        logger.error("Encountered an error while fetching wallet balance: %s", str(e))
        return json.dumps({"error": str(e)})


def make_voice_call(from_number: str, to_number: str, **kwargs) -> str:
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
    logger.info(
        "make_voice_call received: from_number=%r, to_number=%r", from_number, to_number
    )
    # Defensive check for argument validity
    if not from_number or not to_number or not to_number.startswith("+"):
        logger.error(
            "Invalid phone numbers: from_number=%r, to_number=%r",
            from_number,
            to_number,
        )
        return json.dumps(
            {
                "error": f"Invalid phone numbers: from_number={from_number}, to_number={to_number}"
            }
        )
    try:
        # Delegate to the standardized implementation in communication_apis
        from .communication_apis import make_voice_call as comm_make_voice_call

        masked_to_number = mask_phone_number(to_number)
        masked_from_number = mask_phone_number(from_number)
        logger.info(
            "Delegating voice call to %s from %s", masked_to_number, masked_from_number
        )

        response = comm_make_voice_call(from_number, to_number)
        logger.debug("Voice call delegation response: %s", response)
        return response

    except Exception as e:
        logger.error("Encountered an error while making voice call: %s", str(e))
        return json.dumps({"error": str(e)})


def make_voice_call_with_text(
    from_number: str, to_number: str, message: str, voice_type: str = "woman", **kwargs
) -> str:
    """Make a voice call and say a message using text-to-speech.

    This function initiates a voice call and uses Africa's Talking text-to-speech
    engine to read the provided message to the recipient.

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
    ------
    str
        JSON response from the API containing call details

    Examples
    --------
    make_voice_call_with_text("+254700000001", "+254712345678", "Hello, this is a test message", "woman")
    """
    try:
        # Validate inputs
        request = MakeVoiceCallWithTextRequest(
            from_number=from_number,
            to_number=to_number,
            message=message,
            voice=voice_type,
        )

        from .communication_apis import (
            make_voice_call_with_text as comm_make_voice_call_with_text,
        )

        masked_to_number = mask_phone_number(to_number)
        masked_from_number = mask_phone_number(from_number)
        logger.info(
            "Making voice call with text to %s from %s",
            masked_to_number,
            masked_from_number,
        )
        logger.info(
            "Message: %s", message[:50] + "..." if len(message) > 50 else message
        )

        # Call the communication_apis function
        response = comm_make_voice_call_with_text(
            from_number, to_number, message, voice_type
        )

        logger.debug("Voice call with text response: %s", response)
        return response

    except Exception as e:
        logger.error(
            "Encountered an error while making voice call with text: %s", str(e)
        )
        return json.dumps({"error": str(e)})


def make_voice_call_and_play_audio(
    from_number: str, to_number: str, audio_url: str, **kwargs
) -> str:
    """Make a voice call and play an audio file from a URL.

    This function initiates a voice call and plays an audio file from a publicly
    accessible URL. The actual playback is handled by the voice_callback_server.py
    which should serve an XML with the <Play> action when Africa's Talking requests
    call instructions.

    Parameters
    ----------
    from_number : str
        The caller ID for the voice call (must start with +)
    to_number : str
        The recipient phone number (must start with +)
    audio_url : str
        The public URL of the audio file to play (e.g., MP3, WAV).
        Must be a direct HTTP/HTTPS URL to the audio file.

    Returns
    -------
    str
        JSON response from the API containing call details.

    Examples
    --------
    make_voice_call_and_play_audio("+254700000001", "+254712345678", "https://example.com/audio.mp3")
    """
    try:
        # Validate inputs using pydantic
        request = MakeVoiceCallAndPlayAudioRequest(
            from_number=from_number, to_number=to_number, audio_url=audio_url
        )

        from .communication_apis import (
            make_voice_call_and_play_audio as comm_make_voice_call_and_play_audio,
        )

        masked_to_number = mask_phone_number(to_number)
        masked_from_number = mask_phone_number(from_number)
        logger.info(
            "Making voice call to %s from %s to play audio: %s",
            masked_to_number,
            masked_from_number,
            audio_url,
        )

        # Call the communication_apis function
        response = comm_make_voice_call_and_play_audio(
            from_number, to_number, audio_url
        )
        logger.debug("Voice call (for play audio) response: %s", response)
        return response

    except Exception as e:
        logger.error(
            "Encountered an error while making voice call to play audio: %s", str(e)
        )
        return json.dumps({"error": str(e)})


def get_application_balance(sandbox: bool = False, **kwargs) -> str:
    """Fetch the general application balance from Africa's Talking using the Application Data endpoint."""
    try:
        username = os.getenv("AT_USERNAME")
        api_key = os.getenv("AT_API_KEY")
        logger.info("Loaded the credentials: %s %s", username, mask_api_key(api_key))
        if sandbox:
            url = f"https://api.sandbox.africastalking.com/version1/user?username={username}"
        else:
            url = f"https://api.africastalking.com/version1/user?username={username}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": api_key,
        }
        logger.info(
            "Fetching application balance from Application Data endpoint: %s", url
        )
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
    wa_number: str,
    phone_number: str,
    message: str = None,
    media_type: str = None,
    url: str = None,
    caption: str = None,
    sandbox: bool = False,
    **kwargs,
) -> str:
    """Send a WhatsApp message using Africa's Talking API.

    Parameters
    ----------
    wa_number : str
        The WhatsApp phone number associated with your AT account (sender)
    phone_number : str
        The recipient's phone number
    message : str, optional
        The text message to send
    media_type : str, optional
        The type of media (Image, Video, Audio, Voice)
    url : str, optional
        The hosted URL of the media
    caption : str, optional
        The caption for the media
    sandbox : bool, optional
        Use sandbox endpoint if True

    Returns
    -------
    str
        JSON response from the API

    Examples
    --------
    send_whatsapp_message("+254799999999", "+254700000000", message="Hello!")
    send_whatsapp_message("+254799999999", "+254700000000", media_type="Image", url="https://example.com/image.jpg", caption="Check this out!")
    """
    try:
        from .communication_apis import send_whatsapp_message as send_whatsapp

        # Validate inputs
        request = SendWhatsAppMessageRequest(
            wa_number=wa_number,
            phone_number=phone_number,
            message=message,
            media_type=media_type,
            url=url,
            caption=caption,
            sandbox=sandbox,
        )

        username = os.getenv("AT_USERNAME")
        api_key = os.getenv("AT_API_KEY")

        if not username or not api_key:
            logger.error("AT_USERNAME or AT_API_KEY missing")
            return '{"error": "Authentication credentials missing"}'

        logger.info(
            "Sending WhatsApp message from %s to %s",
            mask_phone_number(request.wa_number),
            mask_phone_number(request.phone_number),
        )

        result = send_whatsapp(
            username=username,
            api_key=api_key,
            wa_number=request.wa_number,
            phone_number=request.phone_number,
            message=request.message,
            media_type=request.media_type,
            url=request.url,
            caption=request.caption,
            sandbox=request.sandbox,
        )

        logger.info("WhatsApp message sent successfully")
        return result

    except Exception as e:
        logger.error("Error sending WhatsApp message: %s", str(e))
        return json.dumps({"error": str(e)})


def search_news(query: str, max_results: int = 5, **kwargs) -> str:
    """Search for news using DuckDuckGo search engine based on the query provided.

    Parameters
    ----------
    query: str : The query to search for.
    max_results: int : The maximum number of news articles to retrieve.

    Returns
    -------
    str : The search results, formatted for readability.

    Examples
    --------
    search_news("Python programming")
    """
    logging.info("Searching for news based on the query: %s", query)
    ddgs = DDGS()
    # Remove max_results from kwargs if present to avoid duplicate argument
    kwargs.pop("max_results", None)
    results = ddgs.news(
        keywords=query,
        region="wt-wt",
        safesearch="off",
        timelimit="d",
        max_results=max_results,
        **kwargs,
    )
    logger.debug("The raw search results are: %s", results)

    if not results:
        return "No news found for your query."

    formatted_results = []
    for article in results:
        title = article.get("title", "No Title")
        source = article.get("source", "No Source")
        body = article.get("body", "No Summary")
        url = article.get("url", "No URL")

        formatted_article = (
            f"Title: {title}\n" f"Source: {source}\n" f"Summary: {body}\n" f"URL: {url}"
        )
        formatted_results.append(formatted_article)

    return "\n\n---\n\n".join(formatted_results)


def translate_text(text: str, target_language: str) -> str:
    """Translate text to a specified language using Ollama & Autogen.

    Parameters
    ----------
    text : str :
        The text to translate.

    target_language: str :
        The language of interest
        limited to french, arabic and portugese

    Returns
    -------
    str: translated language with autogen feedback

    Raises
    ------
    ValueError
        If the target language is not one of "French", "Arabic", or "Portuguese".


    Examples
    -------
    >>> translate_text("Hello, how are you?", "French")
    'Bonjour, comment ça va?'

    """
    language_map = {
        "french": "French",
        "fr": "French",
        "arabic": "Arabic",
        "ar": "Arabic",
        "portuguese": "Portuguese",
        "pt": "Portuguese",
    }
    normalized_language = language_map.get(target_language.lower())

    if not normalized_language:
        raise ValueError("Target language must be French, Arabic, or Portuguese.")

    config = [
        {
            "base_url": "http://localhost:11434/v1",
            "model": "qwen3:0.6b",
            "api_key": "ollama",
            "api_type": "ollama",
            "temperature": 0.5,
        }
    ]

    zoe = ConversableAgent(
        "Zoe",
        system_message="""You are a translation expert.
Translate English text to the specified language with high accuracy.
Provide only the translation without explanations.""",
        llm_config={"config_list": config},
        human_input_mode="NEVER",
    )

    joe = ConversableAgent(
        "joe",
        system_message="""You are a bilingual translation validator.
Review translations for:
1. Accuracy of meaning
2. Grammar correctness
3. Natural expression
Provide a confidence score (0-100%) and brief feedback.""",
        llm_config={"config_list": config},
        human_input_mode="NEVER",
    )

    message = f"Zoe, translate '{text}' to {normalized_language}"
    result = joe.initiate_chat(zoe, message=message, max_turns=2)
    # Extract the last message from the chat history, which is the translation
    return result.summary


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
    # ============================================================================
    # INSPECT AI SAFETY LAYER - Evaluate input safety
    # ============================================================================
    safety_evaluator = create_safety_evaluator(strict_mode=False)
    safety_result = safety_evaluator.evaluate_safety(user_input)
    
    logger.info("=" * 60)
    logger.info("INSPECT AI SAFETY CHECK")
    logger.info("=" * 60)
    logger.info("User input: %s", user_input)
    logger.info("Safety status: %s", "SAFE" if safety_result.is_safe else "UNSAFE")
    logger.info("Safety score: %.2f/1.00", safety_result.score)
    logger.info("Violations detected: %d", len(safety_result.flagged_patterns))
    logger.info("Message: %s", safety_result.message)
    
    if safety_result.flagged_patterns:
        logger.warning("Flagged patterns:")
        for pattern in safety_result.flagged_patterns:
            logger.warning("  - %s", pattern)
    
    logger.info("=" * 60)
    
    # If input is unsafe, log warning but continue (can be configured to block)
    if not safety_result.is_safe:
        logger.warning(
            "⚠️  INPUT FAILED SAFETY CHECKS - Proceeding with caution. "
            "Safety score: %.2f", safety_result.score
        )
        # Optionally, you can return here to block unsafe requests:
        # logger.error("Request blocked due to safety concerns.")
        # return None
    
    # ============================================================================
    # END SAFETY CHECK
    # ============================================================================
    
    client = ollama.AsyncClient()

    # Initialize conversation with a user query
    messages = [
        {
            "role": "user",
            "content": user_input,
        }
    ]
    # Log the initial user message
    logger.info("User message: %s", user_input)

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        # keep_alive=True,
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
                    "description": "Translate text to a specified language using Ollama & Autogen",
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
                    "name": "send_mobile_data",  # Change from "send_mobile_data_wrapper" to "send_mobile_data"
                    "description": "Send a mobile data bundle using the Africa's Talking API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {
                                "type": "string",
                                "description": "The phone number in international format",
                            },
                            "bundle": {
                                "type": "string",
                                "description": "The bundle amount, e.g. '100MB', '1GB', or just '50' for 50MB",
                            },
                            "provider": {
                                "type": "string",
                                "description": "The mobile network provider, e.g. 'Safaricom', 'Airtel'",
                            },
                            "plan": {
                                "type": "string",
                                "description": "The bundle plan duration, e.g. 'daily', 'weekly', 'monthly'",
                            },
                            "product_name": {
                                "type": "string",
                                "description": "The name of the product to be used for the bundle, eg. 'data_bundle'",
                            },
                        },
                        "required": [
                            "phone_number",
                            "bundle",
                            "provider",
                            "plan",
                            "product_name",
                        ],
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
                    "description": "Make a voice call and play a message using Africa's Talking API",
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
                                "description": "The URL of the audio file to play",
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
                    "description": "Get application balance from Africa's Talking account",
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
        ],
    )
    # Add the model's response to the conversation history
    messages.append(response["message"])

    # Log the model's response message
    logger.info("LLM response: %s", response["message"].get("content", ""))

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
            "search_news": search_news,
            "translate_text": translate_text,
            "send_ussd": send_ussd,
            "send_mobile_data": send_mobile_data_wrapper,  # Use the wrapper function here
            "make_voice_call": make_voice_call,
            "make_voice_call_with_text": make_voice_call_with_text,
            "make_voice_call_and_play_audio": make_voice_call_and_play_audio,
            "get_wallet_balance": get_wallet_balance,
            "get_application_balance": get_application_balance,
            "send_whatsapp_message": send_whatsapp_message,
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

            elif tool["function"]["name"] == "search_news":
                function_response = function_to_call(
                    tool["function"]["arguments"]["query"],
                    max_results=tool["function"]["arguments"].get("max_results", 5),
                )
                logger.debug("function response: %s", function_response)

            elif tool["function"]["name"] == "translate_text":
                function_response = function_to_call(
                    tool["function"]["arguments"]["text"],
                    tool["function"]["arguments"]["target_language"],
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "send_ussd":
                function_response = function_to_call(
                    tool["function"]["arguments"]["phone_number"],
                    tool["function"]["arguments"]["code"],
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "send_mobile_data":
                function_response = function_to_call(
                    tool["function"]["arguments"]["phone_number"],
                    tool["function"]["arguments"]["bundle"],
                    tool["function"]["arguments"]["provider"],
                    tool["function"]["arguments"]["plan"],
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "make_voice_call":
                function_response = function_to_call(
                    tool["function"]["arguments"]["from_number"],
                    tool["function"]["arguments"]["to_number"],
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "make_voice_call_with_text":
                function_response = function_to_call(
                    tool["function"]["arguments"]["from_number"],
                    tool["function"]["arguments"]["to_number"],
                    tool["function"]["arguments"]["message"],
                    voice_type=tool["function"]["arguments"].get("voice_type", "woman"),
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "get_wallet_balance":
                function_response = function_to_call()
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "make_voice_call_and_play_audio":
                function_response = function_to_call(
                    tool["function"]["arguments"]["from_number"],
                    tool["function"]["arguments"]["to_number"],
                    tool["function"]["arguments"]["audio_url"],
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "get_application_balance":
                function_response = function_to_call(
                    tool["function"]["arguments"].get("sandbox", False),
                )
                logger.debug("function response: %s", function_response)
            elif tool["function"]["name"] == "send_whatsapp_message":
                function_response = function_to_call(
                    tool["function"]["arguments"]["wa_number"],
                    tool["function"]["arguments"]["phone_number"],
                    tool["function"]["arguments"].get("message"),
                    tool["function"]["arguments"].get("media_type"),
                    tool["function"]["arguments"].get("url"),
                    tool["function"]["arguments"].get("caption"),
                    tool["function"]["arguments"].get("sandbox", False),
                )
                logger.debug("function response: %s", function_response)

            # Add the function response to the conversation history
            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )

        # Second API call: Get the final response from the model
        final_response = await client.chat(model=model, messages=messages)
        logger.info("Final LLM Response: %s", final_response["message"]["content"])
    else:
        logger.info("Model Response: %s", response["message"]["content"])


# Main loop to get user input and run the conversation
if __name__ == "__main__":
    while True:
        user_prompt = input(
            "\n Hi, this is a 📱 Multi-Service Communication Interface 🌍: you can send airtime and messages using this interface for example \n\n"
            "Send airtime to +254712345678 with an amount of 10 in currency KES \n\n"
            "Send a message to +254712345678 with the message 'Hello there', using the username 'your_username'\n\n"
            "You can also search for news by providing a query like 'Python programming'\n\n"
            "=> "
        )
        if not user_prompt:
            logger.info("No input provided. Exiting...")
            break
        if user_prompt.lower() == "exit":
            break

        # Run the asynchronous function with tracker
        # with EmissionsTracker(
        #     measure_power_secs=15,
        #     tracking_mode="offline",
        #     output_dir="carbon_output",
        #     project_name="function_call",
        #     experiment_name="send_airtime_and_messages",
        # ) as tracker:
        asyncio.run(run("qwen3:0.6b", user_input=user_prompt))
        # tracker.stop()

__all__ = [
    "send_airtime",
    "send_message",
    "send_ussd",
    "get_wallet_balance",
    "make_voice_call",
    "make_voice_call_with_text",
    "make_voice_call_and_play_audio",
    "get_application_balance",
    "send_whatsapp_message",
    "search_news",
    "translate_text",
    "SendSMSRequest",
    "SendMobileDataRequest",
    "SendUSSDRequest",
    "MakeVoiceCallRequest",
    "MakeVoiceCallWithTextRequest",
    "MakeVoiceCallAndPlayAudioRequest",
    "GetApplicationBalanceRequest",
    "SendWhatsAppMessageRequest",
]
