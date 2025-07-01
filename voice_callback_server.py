"""
Voice Callback Server for Africa's Talking Voice API

This Flask server handles voice callback requests from Africa's Talking
and serves the appropriate XML responses for text-to-speech functionality.

Usage:
    1. Start this server: python voice_callback_server.py
    2. Expose it via ngrok: ngrok http 5000
    3. Configure the ngrok URL in your Africa's Talking dashboard
    4. Use the make_voice_call_with_text function with callback URL

The server stores voice messages temporarily and serves them via XML responses.
"""

import os
import logging
from flask import Flask, request, Response
from flask_cors import CORS
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory storage for voice messages (in production, use Redis or database)
voice_messages: Dict[str, dict] = {}
# In-memory storage for audio play info (session_id -> audio_url)
audio_play_info: Dict[str, dict] = {}

# Cleanup old messages every hour
CLEANUP_INTERVAL = timedelta(hours=1)


def cleanup_old_messages():
    """Remove voice messages older than 1 hour."""
    current_time = datetime.now()
    expired_keys = [
        key
        for key, data in voice_messages.items()
        if current_time - data["created_at"] > CLEANUP_INTERVAL
    ]
    for key in expired_keys:
        del voice_messages[key]
    # Also cleanup old audio play info
    expired_audio = [
        key
        for key, data in audio_play_info.items()
        if current_time - data.get("created_at", current_time) > CLEANUP_INTERVAL
    ]
    for key in expired_audio:
        del audio_play_info[key]
    logger.info(f"Cleaned up {len(expired_keys)} expired voice messages")
    logger.info(f"Cleaned up {len(expired_audio)} expired audio play info entries")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.route("/voice/callback", methods=["POST"])
def voice_callback():
    """
    Handle voice callback from Africa's Talking.

    This endpoint receives the voice call event and returns the appropriate
    XML response for text-to-speech.
    """
    try:
        # Log the incoming request
        logger.info("Received voice callback")
        logger.info("Headers: %s", dict(request.headers))
        logger.info("Form data: %s", dict(request.form))

        # Get call details from Africa's Talking
        caller_number = request.form.get("callerNumber", "")
        session_id = request.form.get("sessionId", "")
        is_active = request.form.get("isActive", "0")
        # If we have audio to play for this session, serve <Play>
        if session_id and session_id in audio_play_info:
            audio_data = audio_play_info.pop(session_id)
            audio_url = audio_data.get("audio_url")
            logger.info(f"Serving audio for session {session_id}: {audio_url}")
            xml_response = f"""<?xml version="1.0"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""
            return Response(xml_response, mimetype="application/xml")

        logger.info(
            f"Voice callback - Caller: {caller_number}, Session: {session_id}, Active: {is_active}"
        )

        # Look for a stored message for this session or caller
        message_data = None

        # First try to find by session ID
        if session_id and session_id in voice_messages:
            message_data = voice_messages[session_id]
        # Then try to find by caller number (fallback)
        elif caller_number:
            for key, data in voice_messages.items():
                if data.get("to_number") == caller_number:
                    message_data = data
                    break

        if message_data:
            message = message_data["message"]
            voice_type = message_data.get("voice_type", "woman")
            logger.info(f"Found message for session {session_id}: {message[:50]}...")

            # Create XML response
            xml_response = f"""<?xml version="1.0"?>
<Response>
    <Say voice="{voice_type}">{message}</Say>
</Response>"""

            # Clean up the message after use
            if session_id in voice_messages:
                del voice_messages[session_id]

            return Response(xml_response, mimetype="application/xml")
        else:
            # Default response if no message found
            logger.warning(
                f"No message found for session {session_id} or caller {caller_number}"
            )
            xml_response = """<?xml version="1.0"?>
<Response>
    <Say voice="woman">Hello, this is a test message from Africa's Talking</Say>
</Response>"""
            return Response(xml_response, mimetype="application/xml")

    except Exception as e:
        logger.error(f"Error in voice callback: {str(e)}")
        # Return a safe default response
        xml_response = """<?xml version="1.0"?>
<Response>
    <Say voice="woman">Sorry, there was an error processing your call</Say>
</Response>"""
        return Response(xml_response, mimetype="application/xml")


@app.route("/voice/store", methods=["POST"])
def store_voice_message():
    """
    Store a voice message for later retrieval during callback.

    Expected JSON payload:
    {
        "session_id": "unique_session_id",
        "to_number": "+254712345678",
        "message": "Hello, this is a test message",
        "voice_type": "woman"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return {"error": "No JSON data provided"}, 400

        session_id = data.get("session_id")
        to_number = data.get("to_number")
        message = data.get("message")
        voice_type = data.get("voice_type", "woman")

        if not all([session_id, to_number, message]):
            return {"error": "session_id, to_number, and message are required"}, 400

        # Store the message
        voice_messages[session_id] = {
            "to_number": to_number,
            "message": message,
            "voice_type": voice_type,
            "created_at": datetime.now(),
        }

        logger.info(f"Stored voice message for session {session_id}: {message[:50]}...")

        # Cleanup old messages
        cleanup_old_messages()

        return {"success": True, "session_id": session_id}

    except Exception as e:
        logger.error(f"Error storing voice message: {str(e)}")
        return {"error": str(e)}, 500


@app.route("/voice/store_play_info", methods=["POST"])
def store_play_info():
    """
    Store audio URL for playback during callback.
    Expected JSON: {"session_id": str, "audio_url": str}
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        audio_url = data.get("audio_url")
        if not session_id or not audio_url:
            return {"error": "session_id and audio_url are required"}, 400
        # Store the audio info
        audio_play_info[session_id] = {
            "audio_url": audio_url,
            "created_at": datetime.now(),
        }
        logger.info(f"Stored audio play info for session {session_id}: {audio_url}")
        cleanup_old_messages()
        return {"success": True, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error storing play info: {str(e)}")
        return {"error": str(e)}, 500


@app.route("/voice/messages", methods=["GET"])
def list_voice_messages():
    """List all stored voice messages (for debugging)."""
    return {
        "count": len(voice_messages),
        "messages": {
            k: {
                "to_number": v["to_number"],
                "message": (
                    v["message"][:50] + "..."
                    if len(v["message"]) > 50
                    else v["message"]
                ),
                "voice_type": v["voice_type"],
                "created_at": v["created_at"].isoformat(),
            }
            for k, v in voice_messages.items()
        },
    }


@app.route("/", methods=["GET"])
def index():
    return {
        "status": "ok",
        "message": "Africa's Talking Voice Callback Server is running.",
        "endpoints": ["/health", "/voice/callback", "/voice/store", "/voice/messages"],
    }


if __name__ == "__main__":
    logger.info("Starting Voice Callback Server...")
    logger.info("Make sure to:")
    logger.info("1. Expose this server via ngrok: ngrok http 5000")
    logger.info("2. Configure the ngrok URL in Africa's Talking dashboard")
    logger.info("3. Set the callback URL in your voice calls")

    # Run Flask server
    app.run(host="0.0.0.0", port=5001, debug=False)  # Set to True for development
