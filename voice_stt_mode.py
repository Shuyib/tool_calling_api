"""
Airtime and Messaging Servicea using Africa's Talking API

This script provides a Gradio-based web interface for sending airtime and messages
using the Africa's Talking API. It also tracks the carbon emissions of the operations
using the CodeCarbon library.

The voice command interface allows users to send airtime, send messages, and search for
news articles using voice commands. However, the audio transcription and processing
is required since the model only accepts text inputs & has limited capabilities.

Usage:
    1. Set the environment variables `AT_USERNAME`, `GROQ_API_KEY`, and `AT_API_KEY` with
    your Africa's Talking credentials.
    2. Run the script: `python app.py`
    3. Access the Gradio web interface to send airtime or messages or search for news articles.

Example:
    Send airtime to a phone number:
        - `Send airtime to +254712345678 with an amount of 10 in currency KES`
    Send a message to a phone number:
        - `Send a message to +254712345678 with the message 'Hello there',
        using the username 'username'`
    Search for news about a topic:
        - `Latest news on climate change`
"""

# ------------------------------------------------------------------------------------
# Import Statements
# ------------------------------------------------------------------------------------

# Standard Library Imports
import os
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from importlib.metadata import version, PackageNotFoundError
import warnings
from typing import Optional

# Third-Party Library Imports
import gradio as gr
from langtrace_python_sdk import langtrace, with_langtrace_root_span
import groq
import numpy as np
import soundfile as sf
import ollama
import edge_tts

# Local Module Imports
from utils.function_call import send_airtime, send_message, search_news, translate_text
from utils.constants import VISION_SYSTEM_PROMPT, API_SYSTEM_PROMPT

# ------------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------------

# Initialize Langtrace
langtrace.init(api_key=os.getenv("LANGTRACE_API_KEY"))
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# Suppress Pydantic UserWarning from autogen
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*Field.*in.*has conflict with protected namespace.*",
)

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the logger to handle all levels DEBUG and above

# Prevent logs from being propagated to the root logger
logger.propagate = False

# Define logging format
formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")

# Set up the file handler for logging to a file
file_handler = RotatingFileHandler(
    "voice_stt_mode.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
file_handler.setLevel(logging.INFO)  # Capture INFO and above in the file
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Set up the stream handler for console output
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)  # Capture DEBUG and above in the console
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# ------------------------------------------------------------------------------------
# Log the Start of the Script
# ------------------------------------------------------------------------------------

logger.info(
    "Starting the voice&text function calling script to send airtime and messages using the "
    "Africa's Talking API"
)
logger.info("Review GROQ Speech-to-Text if they log the audio data or not")
logger.info("Let's review the packages and their versions")

# ------------------------------------------------------------------------------------
# Log Versions of the Libraries
# ------------------------------------------------------------------------------------

pkgs = [
    "africastalking",
    "ollama",
    "duckduckgo_search",
    "langtrace-python-sdk",
    "gradio",
    "groq",
    "soundfile",
    "numpy",
    "edge-tts",  # Add edge-tts to version checking
]

for pkg in pkgs:
    try:
        pkg_version = version(pkg)
        logger.info("%s version: %s", pkg, pkg_version)
    except PackageNotFoundError:
        logger.error("Package %s is not installed.", pkg)
    except Exception as e:
        logger.error("Failed to retrieve version for %s: %s", pkg, str(e))

# ------------------------------------------------------------------------------------
# Add TTS Configuration after version checking
# ------------------------------------------------------------------------------------

VOICE = "sw-TZ-RehemaNeural"
OUTPUT_FILE = "tts_output.mp3"  # Saved in current working directory


async def text_to_speech(text: str) -> None:
    """
    Generate speech from text using edge-tts.

    Parameters
    ----------
    text : str
        The text to convert to speech.
    """
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(OUTPUT_FILE)
        logger.info("Generated speech output: %s", OUTPUT_FILE)
    except Exception as e:
        logger.error("TTS Error: %s", str(e))
        raise


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
            "description": "Translate text to a specified language using Ollama",
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
# Function Definitions
# ------------------------------------------------------------------------------------


@with_langtrace_root_span()
async def process_user_message(
    message: str,
    history: list,  # pylint: disable=unused-argument
    use_vision: bool = False,
    image_path: Optional[str] = None,
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
        Whether to use vision model for processing (default is False).
    image_path : str, optional
        Path to the image file for vision model (default is None).

    Returns
    -------
    str
        The model's response or the function execution result.
    """
    logger.info("Processing user message: %s", message)
    client = ollama.AsyncClient()
    messages = []

    # Add system prompt
    system_prompt = VISION_SYSTEM_PROMPT if use_vision else API_SYSTEM_PROMPT
    messages.append({"role": "system", "content": system_prompt})

    # Add user message with image if present
    if use_vision and image_path:
        messages.append({"role": "user", "content": message, "images": [image_path]})
    else:
        messages.append({"role": "user", "content": message})

    try:
        # Use 'llava' as it's a common Ollama vision model.
        # Ensure you have pulled the model with `ollama pull llava`.
        # You can use llama3.2-vision as well
        model_name = "llava" if use_vision else "qwen2.5:0.5b"
        response = await client.chat(
            model=model_name,
            messages=messages,
            tools=None if use_vision else tools,
            format="json" if use_vision else None,
            options={"temperature": 0},
        )
    except Exception:
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
    logger.debug("Model response details: %s", response.get("message"))

    if model_message.get("tool_calls"):
        for tool in model_message["tool_calls"]:
            tool_name = tool["function"]["name"]
            arguments = tool["function"]["arguments"]
            logger.info("Tool call detected: %s", tool_name)

            try:
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
                elif tool_name == "translate_text":
                    logger.info("Calling translate_text with arguments: %s", arguments)
                    function_response = translate_text(
                        arguments["text"],
                        arguments["target_language"],
                    )
                else:
                    function_response = json.dumps({"error": "Unknown function"})
                    logger.warning("Unknown function called: %s", tool_name)

                logger.debug("Function response: %s", function_response)
                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                    }
                )

                return (
                    f"Function `{tool_name}` executed successfully. Response:\n"
                    f"{function_response}"
                )
            except Exception as e:
                logger.exception("Unexpected error in tool `%s`: %s", tool_name, e)
                return f"An unexpected error occurred while executing `{tool_name}`."
    else:
        return model_content


# Add error handling for audio processing
async def process_audio_and_llm(audio):
    """
    Process the audio recording and get the transcription using Groq.

    Parameters
    ----------
    audio : tuple
        The audio recording tuple with the sample rate and audio data.

    Returns
    -------
    str
        The transcription and LLM response.

    Raises
    ------
    Exception
        If there is an error in processing the audio.
    """
    if audio is None:
        return "Error: No audio recorded. Please try again."
    try:
        sr, y = audio
        if len(y) == 0:
            return "Error: Empty audio recording. Please speak and try again."
        # Convert to mono if stereo
        if y.ndim > 1:
            y = y.mean(axis=1)

        # Normalize audio
        y = y.astype(np.float32)
        y /= np.max(np.abs(y))

        # Write audio to buffer
        buffer = io.BytesIO()
        sf.write(buffer, y, sr, format="wav")
        buffer.seek(0)

        try:
            # Get transcription from Groq
            transcription = groq_client.audio.transcriptions.create(
                model="distil-whisper-large-v3-en",
                file=("audio.wav", buffer),
                response_format="text",
            )

            # Process transcription with LLM
            response = await process_user_message(transcription, [])
            return f"Transcription: {transcription}\nLLM Response: {response}"

        except Exception as exc:
            logger.exception("Error during transcription or LLM processing: %s", exc)
            return f"Error: {str(exc)}"
    except Exception as exc:
        logger.exception("Error in audio processing: %s", exc)
        return f"Error: {str(exc)}"


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
    except Exception as exc:
        logger.exception("Error in gradio_interface: %s", exc)
        return "An unexpected error occurred while processing your message."


# ------------------------------------------------------------------------------------
# Create Gradio Interface with Both Text and Audio Inputs
# ------------------------------------------------------------------------------------

with gr.Blocks(title="🎙️ Voice & Vision Communication Interface 🌍") as demo:
    gr.Markdown("# Voice Command & Text Communication Interface")

    # Add tabs for voice and text input
    with gr.Tab("Voice Input"):
        # How to use
        gr.Markdown(
            """
This interface allows you to send airtime, messages, and search
for news articles using voice commands.
You can also type your commands in the text input tab.
Here are some examples of commands you can use:
- Send airtime to +254712345678 with an amount of 10 in currency KES 📞
- Send a message to +254712345678 with the message 'Hello there' with
                the username 'add your username'💬
- Search news for 'latest technology trends' 📰
- Translate the text "Hi" to the target language "French"
* Please speak clearly and concisely for accurate transcription. In English only for now.
* You can also edit the transcription before processing. We all make mistakes! 🤗
"""
        )
        audio_input = gr.Audio(
            sources=["microphone", "upload"],
            type="numpy",
            label="Speak your command",
            streaming=False,
        )
        transcription_preview = gr.Textbox(
            label="Preview Transcription (Edit if needed)",
            interactive=True,
            placeholder="Transcription will appear here first...",
        )
        audio_output = gr.Textbox(
            label="Final Result", placeholder="LLM response will appear here..."
        )
        tts_button = gr.Button("Play TTS")
        tts_audio = gr.Audio(label="TTS Output")

        with gr.Row():
            transcribe_button = gr.Button("Transcribe")
            process_button = gr.Button("Process Edited Text", variant="primary")

        def show_transcription(audio):
            """
            Transcribe the audio recording and show the preview.

            Parameters
            ----------
            audio : tuple
                The audio recording tuple with the sample rate and audio data.

            Returns
            -------
            str
                The transcription of the audio recording.
            """
            try:
                if audio is None:
                    return "Error: No audio recorded. Please try again."
                sr, y = audio
                if len(y) == 0:
                    return "Error: Empty audio recording. Please speak and try again."

                # Convert to mono if stereo
                if y.ndim > 1:
                    y = y.mean(axis=1)

                # Normalize audio
                y = y.astype(np.float32)
                y /= np.max(np.abs(y))

                # Write audio to buffer
                buffer = io.BytesIO()
                sf.write(buffer, y, sr, format="wav")
                buffer.seek(0)

                # Get transcription from Groq
                transcription = groq_client.audio.transcriptions.create(
                    model="distil-whisper-large-v3-en",
                    file=("audio.wav", buffer),
                    response_format="text",
                )
                logger.info("Audio transcribed successfully: %s", transcription)
                return transcription
            except Exception as exc:
                logger.exception("Error during transcription: %s", exc)
                return f"Error: {str(exc)}"

        # Define TTS Function
        async def generate_tts(text: str) -> str:
            """
            Generate TTS audio and return the file path.
            """
            try:
                communicate = edge_tts.Communicate(text, VOICE)
                await communicate.save(OUTPUT_FILE)
                logger.info("TTS audio generated successfully: %s", OUTPUT_FILE)
                return OUTPUT_FILE
            except Exception as exc:
                logger.error("TTS Generation Error: %s", str(exc))
                return None

        # Wire up the components
        transcribe_button.click(  # pylint: disable=no-member
            fn=show_transcription, inputs=audio_input, outputs=transcription_preview
        )

        # Process the edited text
        process_button.click(  # pylint: disable=no-member
            fn=lambda x: asyncio.run(process_user_message(x, [])),
            inputs=transcription_preview,
            outputs=audio_output,
        )

        # Connect TTS Button to Function
        tts_button.click(  # pylint: disable=no-member
            fn=lambda txt: asyncio.run(generate_tts(txt)),
            inputs=audio_output,
            outputs=tts_audio,
        )

    # Text input tab
    with gr.Tab("Text Input"):
        chat_interface = gr.ChatInterface(
            fn=gradio_interface,
            description=(
                "Type your commands or use voice input above:\n"
                "- Send airtime to +254712345678 with an amount of 10 in currency KES 📞\n"
                "- Send a message to +254712345678 with the message 'Hello there' 💬\n"
                "- Search news for 'latest technology trends' 📰"
            ),
            type="messages",
        )

    with gr.Tab("Receipt Scanner"):
        image_input = gr.Image(type="filepath", label="Upload Receipt/Invoice")
        scan_button = gr.Button("Scan Receipt")
        result_text = gr.Textbox(label="Analysis Result")

        async def process_with_speech(image):
            """
            Process image with vision model and return analysis.
            """
            try:
                # Get text result first
                text_result = await process_user_message(
                    "Analyze this receipt", [], use_vision=True, image_path=image
                )
                return text_result
            except Exception as exc:
                logger.error("Processing error: %s", str(exc))
                return str(exc)

        scan_button.click(  # pylint: disable=no-member
            fn=lambda img: asyncio.run(process_with_speech(img)),
            inputs=image_input,
            outputs=result_text,
        )

# ------------------------------------------------------------------------------------
# Launch Gradio Interface
# ------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        logger.info("Launching Gradio interface...")
        demo.launch(inbrowser=True, server_name="0.0.0.0", server_port=7860)
        logger.info("Gradio interface launched successfully.")
    except Exception as exc:
        logger.exception("Failed to launch Gradio interface: %s", exc)
    logger.info("Script execution completed")
