# app.py

"""
Airtime, Messaging, Email, Push Notifications, and S3 Storage Service

This script provides a Gradio-based web interface for sending airtime, messages, emails, push notifications,
and uploading files to S3. It uses the Africa's Talking API, SendGrid API, Firebase Cloud Messaging, and AWS S3.

Usage:
    1. Set the required environment variables:
       - Africa's Talking: `AT_USERNAME`, `AT_API_KEY`
       - SendGrid: `SENDGRID_API_KEY`, `SENDGRID_SENDER_EMAIL`
       - Firebase: Provide the path to your service account JSON file
       - AWS: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
    2. Run the script: `python app.py`
    3. Access the Gradio web interface to use the services.

Example Commands:
    - Send airtime:
        `Send airtime to +254712345678 with an amount of 10 in currency KES`
    - Send a message:
        `Send a message to +254712345678 with the message 'Hello there', using the username 'username'`
    - Send an email:
        `Send an email to 'email@example.com' with the subject 'Greetings' and content 'Hello World'`
    - Send a push notification:
        `Send a push notification to token 'device_token' with title 'Alert' and body 'This is a test'`
    - Upload a file to S3:
        `Upload file 'path/to/file.txt' to bucket 'my-bucket' with object name 'file.txt'`

"""

import os
import re
import json
import logging
from importlib.metadata import version
import asyncio
import africastalking
import ollama
import gradio as gr

# New imports for SendGrid, Firebase Admin, and Boto3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import firebase_admin
from firebase_admin import credentials, messaging
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    firebase_cred_path = "path/to/serviceAccountKey.json"
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)

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
    "Starting the function calling script to send airtime, messages, emails, push notifications, and upload files to S3"
)
logger.info("Let's review the packages and their versions")

# Log versions of the libraries
pkgs = ["africastalking", "ollama", "sendgrid", "firebase_admin", "boto3"]

for pkg in pkgs:
    try:
        logger.debug("%s version: %s", pkg, version(pkg))
    except Exception as e:
        logger.error("Failed to get version for %s: %s", pkg, str(e))

def mask_sensitive_data(data):
    """
    Mask sensitive data, displaying only last 4 characters.

    Parameters
    ----------
    data : str
        The data to mask.

    Returns
    -------
    str
        The masked data.
    """
    if data:
        return "x" * (len(data) - 4) + data[-4:]
    else:
        return data

def send_airtime(phone_number: str, currency_code: str, amount: str, **kwargs) -> str:
    """
    Send airtime using Africa's Talking API.
    """
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the credentials: %s %s", username, mask_sensitive_data(api_key))

    africastalking.initialize(username, api_key)
    airtime = africastalking.Airtime

    masked_number = mask_sensitive_data(phone_number)
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
    """
    api_key = os.getenv("AT_API_KEY")
    logger.info("Loaded the API key: %s", mask_sensitive_data(api_key))

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS

    masked_number = mask_sensitive_data(phone_number)
    logger.info("Sending message to %s", masked_number)

    try:
        response = sms.send(message, [phone_number])
        logger.debug("Message sent to %s. Response: %s", masked_number, response)
        response_data = response["SMSMessageData"]["Recipients"][0]
        return json.dumps(response_data)
    except Exception as e:
        logger.error("Encountered an error while sending the message: %s", str(e))
        return json.dumps({"error": str(e)})
    finally:
        logger.info("Message sent to %s", masked_number)

def send_email(to_email: str, subject: str, content: str, **kwargs) -> str:
    """
    Send an email using SendGrid API.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        logger.error("SendGrid API key not found in environment variables.")
        return json.dumps({"error": "SendGrid API key not found"})

    sender_email = os.getenv("SENDGRID_SENDER_EMAIL")
    if not sender_email:
        logger.error("SendGrid sender email not found in environment variables.")
        return json.dumps({"error": "SendGrid sender email not found"})

    message = Mail(
        from_email=sender_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.debug("Email sent to %s. Response: %s", to_email, response)
        return json.dumps({"status": "success", "response": response.status_code})
    except Exception as e:
        logger.error("Encountered an error while sending the email: %s", str(e))
        return json.dumps({"error": str(e)})

def send_push_notification(token: str, title: str, body: str, **kwargs) -> str:
    """
    Send a push notification using Firebase Cloud Messaging (FCM).
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )

    try:
        response = messaging.send(message)
        logger.debug("Push notification sent to %s. Response: %s", token, response)
        return json.dumps({"status": "success", "response": response})
    except Exception as e:
        logger.error("Error sending push notification: %s", str(e))
        return json.dumps({"error": str(e)})

def upload_file_to_s3(file_path: str, bucket_name: str, object_name: str = None, **kwargs) -> str:
    """
    Upload a file to an S3 bucket.
    """
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    s3_client = boto3.client('s3', region_name=aws_region)
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        logger.debug("File uploaded to %s/%s", bucket_name, object_name)
        return json.dumps({"status": "success", "bucket": bucket_name, "object": object_name})
    except FileNotFoundError:
        logger.error("The file was not found: %s", file_path)
        return json.dumps({"error": "File not found"})
    except NoCredentialsError:
        logger.error("AWS credentials not available")
        return json.dumps({"error": "AWS credentials not available"})
    except ClientError as e:
        logger.error("AWS ClientError: %s", e)
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error("Error uploading file to S3: %s", str(e))
        return json.dumps({"error": str(e)})

def is_valid_airtime_request(prompt: str) -> bool:
    """
    Validate if the prompt is a valid airtime request.
    """
    airtime_pattern = re.compile(
        r"Send airtime to \+\d{10,15} with an amount of \d+(\.\d+)? in currency [A-Z]{3}"
    )
    return bool(airtime_pattern.match(prompt))

def is_valid_message_request(prompt: str) -> bool:
    """
    Validate if the prompt is a valid message request.
    """
    message_pattern = re.compile(
        r"Send a message to \+\d{10,15} with the message '.*', using the username '.*'"
    )
    return bool(message_pattern.match(prompt))

def is_valid_email_request(prompt: str) -> bool:
    """
    Validate if the prompt is a valid email request.
    """
    email_pattern = re.compile(
        r"Send an email to '.*' with the subject '.*' and content '.*'"
    )
    return bool(email_pattern.match(prompt))

def is_valid_push_request(prompt: str) -> bool:
    """
    Validate if the prompt is a valid push notification request.
    """
    push_pattern = re.compile(
        r"Send a push notification to token '.*' with title '.*' and body '.*'"
    )
    return bool(push_pattern.match(prompt))

def is_valid_upload_request(prompt: str) -> bool:
    """
    Validate if the prompt is a valid file upload request.
    """
    upload_pattern = re.compile(
        r"Upload file '.*' to bucket '.*'( with object name '.*')?"
    )
    return bool(upload_pattern.match(prompt))

async def process_user_message(message: str, history: list) -> str:
    """
    Handle the conversation with the model asynchronously.
    """
    logger.info("Processing user message: %s", message)

    if not any([
        is_valid_airtime_request(message),
        is_valid_message_request(message),
        is_valid_email_request(message),
        is_valid_push_request(message),
        is_valid_upload_request(message)
    ]):
        return "Invalid command. Please enter a valid command."

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
                            "phone_number": {"type": "string"},
                            "currency_code": {"type": "string"},
                            "amount": {"type": "string"},
                        },
                        "required": ["phone_number", "currency_code", "amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_message",
                    "description": "Send a message using the Africa's Talking API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {"type": "string"},
                            "message": {"type": "string"},
                            "username": {"type": "string"},
                        },
                        "required": ["phone_number", "message", "username"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email using SendGrid API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to_email": {"type": "string"},
                            "subject": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["to_email", "subject", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_push_notification",
                    "description": "Send a push notification using Firebase Cloud Messaging",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "token": {"type": "string"},
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["token", "title", "body"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "upload_file_to_s3",
                    "description": "Upload a file to an S3 bucket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "bucket_name": {"type": "string"},
                            "object_name": {"type": "string"},
                        },
                        "required": ["file_path", "bucket_name"],
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
            elif tool_name == "send_email":
                logger.info("Calling send_email with arguments: %s", arguments)
                function_response = send_email(
                    arguments["to_email"],
                    arguments["subject"],
                    arguments["content"],
                )
            elif tool_name == "send_push_notification":
                logger.info("Calling send_push_notification with arguments: %s", arguments)
                function_response = send_push_notification(
                    arguments["token"],
                    arguments["title"],
                    arguments["body"],
                )
            elif tool_name == "upload_file_to_s3":
                logger.info("Calling upload_file_to_s3 with arguments: %s", arguments)
                function_response = upload_file_to_s3(
                    arguments["file_path"],
                    arguments["bucket_name"],
                    arguments.get("object_name"),
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

def gradio_interface(message: str, history: list) -> str:
    """
    Gradio interface function to process user messages.
    """
    response = asyncio.run(process_user_message(message, history))
    return response

# Create Gradio interface
iface = gr.ChatInterface(
    fn=gradio_interface,
    title="📱 Multi-Service Communication Interface 🌍",
    description=(
        "Welcome! This interface allows you to send airtime, messages, emails, push notifications, "
        "and upload files to S3. 🚀\n\n"
        "Available commands:\n"
        "- Send airtime:\n"
        "  `Send airtime to +254712345678 with an amount of 10 in currency KES`\n"
        "- Send a message:\n"
        "  `Send a message to +254712345678 with the message 'Hello there', using the username 'username'`\n"
        "- Send an email:\n"
        "  `Send an email to 'email@example.com' with the subject 'Greetings' and content 'Hello World'`\n"
        "- Send a push notification:\n"
        "  `Send a push notification to token 'device_token' with title 'Alert' and body 'This is a test'`\n"
        "- Upload a file to S3:\n"
        "  `Upload file 'path/to/file.txt' to bucket 'my-bucket' with object name 'file.txt'`\n"
    ),
    examples=[
        ["Send airtime to +254712345678 with an amount of 10 in currency KES"],
        ["Send a message to +254712345678 with the message 'Hello there', using the username 'my_username'"],
        ["Send an email to 'recipient@example.com' with the subject 'Test Email' and content 'This is a test email.'"],
        ["Send a push notification to token 'abc123' with title 'Notification' and body 'This is a push notification.'"],
        ["Upload file 'local/path/to/file.txt' to bucket 'my-bucket' with object name 'file.txt'"],
    ],
    cache_examples=False,
    allow_flagging="never"
)

# Launch the Gradio interface
iface.launch(inbrowser=True, server_name="0.0.0.0", server_port=7860)
