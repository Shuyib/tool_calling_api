"""
Unit tests for the function calling utilities.

This module contains tests for sending airtime, sending messages, and searching news
using the Africa's Talking API and DuckDuckGo News API. The tests mock external
dependencies to ensure isolation and reliability.

More test you can try can be found here: https://huggingface.co/datasets/DAMO-NLP-SG/MultiJail
"""

import os
import re
from unittest.mock import patch
from utils.function_call import send_airtime, send_message, search_news

# Load environment variables: TEST_PHONE_NUMBER
PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER")


@patch("utils.function_call.africastalking.Airtime")
def test_send_airtime_success(mock_airtime):
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
    mock_airtime.return_value.send.return_value = {
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


@patch("utils.function_call.africastalking.SMS")
def test_send_message_success(mock_sms):
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
    mock_sms.return_value.send.return_value = {
        "SMSMessageData": {"Message": "Sent to 1/1"}
    }

    # Call the send_message function
    result = send_message(PHONE_NUMBER, "In Qwen, we trust", os.getenv("AT_USERNAME"))

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
