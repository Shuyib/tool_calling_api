"""
Unit tests for the function calling utilities.

This module contains tests for sending airtime, sending messages, and searching news
using the Africa's Talking API and DuckDuckGo News API. The tests mock external
dependencies to ensure isolation and reliability.
"""

import os
import re
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from utils.function_call import send_airtime, send_message, search_news, translate_text

# Load environment variables with fallbacks for testing
PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER", "+1234567890")
AT_USERNAME = os.getenv("AT_USERNAME", "test_user")


@patch("utils.function_call.africastalking.Airtime.send")
def test_send_airtime_success(mock_send):
    """
    Test the send_airtime function to ensure it successfully sends airtime.

    This test mocks the Africa's Talking Airtime API and verifies that the
    send_airtime function returns a response containing the word 'Sent'.

    Parameters
    ----------
    mock_airtime : MagicMock
        Mocked Airtime API from Africa's Talking.
    """
    # Configure the mock Airtime response
    mock_send.return_value = {
        "numSent": 1,
        "responses": [{"status": "Sent"}],
    }

    # Call the send_airtime function
    result = send_airtime(PHONE_NUMBER, "KES", 5)

    # Define patterns to check in the response
    message_patterns = [
        r"Sent",
    ]

    # Assert each pattern is found in the response
    for pattern in message_patterns:
        assert re.search(
            pattern, str(result)
        ), f"Pattern '{pattern}' not found in response"


@patch("utils.function_call.africastalking.SMS.send")
def test_send_message_success(mock_send):
    """
    Test the send_message function to ensure it successfully sends a message.

    This test mocks the Africa's Talking SMS API and verifies that the
    send_message function returns a response containing 'Sent to 1/1'.

    Parameters
    ----------
    mock_sms : MagicMock
        Mocked SMS API from Africa's Talking.
    """
    # Configure the mock SMS response
    mock_send.return_value = {"SMSMessageData": {"Message": "Sent to 1/1"}}

    # Call the send_message function
    result = send_message(PHONE_NUMBER, "In Qwen, we trust", AT_USERNAME)

    # Define patterns to check in the response
    message_patterns = [r"Sent to 1/1"]

    # Assert each pattern is found in the response
    for pattern in message_patterns:
        assert re.search(
            pattern, str(result)
        ), f"Pattern '{pattern}' not found in response"


@patch("utils.function_call.DDGS")
def test_search_news_success(mock_ddgs):
    """
    Test the search_news function to ensure it retrieves news articles correctly.

    This test mocks the DuckDuckGo News API and verifies that the
    search_news function returns results matching the expected patterns.

    Parameters
    ----------
    mock_ddgs : MagicMock
        Mocked DuckDuckGo DDGS API.
    """
    # Configure the mock DDGS response with a realistic news article
    mock_ddgs.return_value.news.return_value = [
        {
            "date": "2024-12-20T02:07:00+00:00",
            "title": "Hedge fund leader loves this AI stock",
            "body": "Sample article body text",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "source": "MSN",
        }
    ]

    # Call the search_news function
    result = search_news("AI")

    # Define regex patterns to validate response format
    patterns = [
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",  # Date format
        r'"title":\s*"[^"]+?"',  # Title field
        r'"source":\s*"[^"]+?"',  # Source field
        r'https?://[^\s<>"]+?',  # URL format
    ]

    # Convert result to string for regex matching
    result_str = str(result)

    # Assert all patterns match in the result
    for pattern in patterns:
        assert re.search(
            pattern, result_str
        ), f"Pattern '{pattern}' not found in response"

    # Verify that the news method was called with expected arguments
    mock_ddgs.return_value.news.assert_called_once_with(
        keywords="AI", region="wt-wt", safesearch="off", timelimit="d", max_results=5
    )


@pytest.mark.parametrize(
    "text,target_language,expected_response,should_call",
    [
        ("Hello", "French", "Bonjour", True),
        ("Good morning", "Arabic", "صباح الخير", True),
        ("Thank you", "Portuguese", "Obrigado", True),
        ("", "French", "Error: Empty text", False),
        (
            "Hello",
            "German",
            "Target language must be French, Arabic, or Portuguese",
            False,
        ),
    ],
)
def test_translate_text_function(text, target_language, expected_response, should_call):
    """
    Test translation functionality with various inputs.
    Note: translate_text is a synchronous function, so do not await.
    """
    # Mock client return
    mock_chat_response = {"message": {"content": expected_response}}

    with patch("ollama.AsyncClient") as mock_client:
        instance = MagicMock()
        instance.chat = AsyncMock(return_value=mock_chat_response)
        mock_client.return_value = instance

        if not text:
            with pytest.raises(ValueError) as exc:
                translate_text(text, target_language)
            assert "Empty text" in str(exc.value)
            return

        if target_language not in ["French", "Arabic", "Portuguese"]:
            with pytest.raises(ValueError) as exc:
                translate_text(text, target_language)
            assert "Target language must be French, Arabic, or Portuguese" in str(
                exc.value
            )
            return

        result = translate_text(text, target_language)
        assert expected_response in result

        if should_call:
            instance.chat.assert_called_once()
        else:
            instance.chat.assert_not_called()


@pytest.mark.asyncio
async def test_translate_text_special_chars():
    """Test translation with special characters."""
    with pytest.raises(ValueError) as exc:
        await translate_text("@#$%^", "French")
    assert "Invalid input" in str(exc.value)
