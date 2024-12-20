"""
Tests the ollama function calling system

This module tests the function calling system in the ollama package.

The tests are run using the pytest framework. The tests are run in the following order:
1. test_run_send_airtime: Tests the run function with an airtime request.
2. test_run_send_message: Tests the run function with a message-sending request.
3. test_run_search_news: Tests the run function with a news search request.

The tests are run asynchronously to allow for the use of the asyncio library.

NB: ensure you have the environment variables set in the .env file/.bashrc 
file before running the tests.

How to run the tests:
pytest test/test_run.py -v --asyncio-mode=strict

Feel free to add more tests to cover more scenarios. 

"""

import os
import pytest
from utils.function_call import run

# Load environment variables
TEST_PHONE_NUMBER = os.getenv("TEST_PHONE_NUMBER")
TEST_PHONE_NUMBER_2 = os.getenv("TEST_PHONE_NUMBER_2")
TEST_PHONE_NUMBER_3 = os.getenv("TEST_PHONE_NUMBER_3")
USERNAME = os.getenv("USERNAME")


@pytest.mark.asyncio
async def test_run_send_airtime():
    """
    Test the run function with an airtime request.
    Checks for any runtime errors while processing the prompt.
    """
    user_prompt = (
        f"Send airtime to {TEST_PHONE_NUMBER} with an amount of 5 in currency KES"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_message():
    """
    Test the run function with a message-sending request.
    Ensures no exceptions are raised while handling the prompt.
    """
    user_prompt = (
        f"Send a message to {TEST_PHONE_NUMBER} with the message 'Hello', "
        f"using the username {USERNAME}"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_search_news():
    """
    Test the run function with a news search request.
    Verifies the function completes without errors.
    """
    user_prompt = "Search for news about 'Global Tech Events'"
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_zero_amount():
    """
    Test sending airtime with zero amount.
    """
    user_prompt = (
        f"Send airtime to {TEST_PHONE_NUMBER} with an amount of 0 in currency KES"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_invalid_currency():
    """
    Test sending airtime with an invalid currency code.
    """
    user_prompt = (
        f"Send airtime to {TEST_PHONE_NUMBER} with an amount of 10 in currency XYZ"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_message_missing_username():
    """
    Test sending a message without providing a username.
    """
    user_prompt = f"Send a message to {TEST_PHONE_NUMBER} with the message 'Hello'"
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_search_news_empty_query():
    """
    Test searching news with an empty query.
    """
    user_prompt = "Search for news about ''"
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_multiple_numbers():
    """
    Test sending airtime to multiple phone numbers.
    """
    user_prompt = f"Send airtime to {TEST_PHONE_NUMBER}, {TEST_PHONE_NUMBER_2}, and {TEST_PHONE_NUMBER_3} with an amount of 5 in currency KES"
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_synonym():
    """
    Test sending airtime using synonymous phrasing.
    """
    user_prompt = f"Top-up {TEST_PHONE_NUMBER} with 10 KES airtime."
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_different_order():
    """
    Test sending airtime with parameters in a different order.
    """
    user_prompt = f"With an amount of 15 KES, send airtime to {TEST_PHONE_NUMBER}."
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_message_polite_request():
    """
    Test sending a message with a polite request phrasing.
    """
    user_prompt = f"Could you please send a message saying 'Good morning' to {TEST_PHONE_NUMBER}, using the username {USERNAME}?"
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_search_news_synonym():
    """
    Test searching news using synonymous phrasing.
    """
    user_prompt = "Find articles related to 'Artificial Intelligence advancements'."
    await run("qwen2.5:0.5b", user_prompt)
    assert True


@pytest.mark.asyncio
async def test_run_send_airtime_invalid_amount():
    """
    Test sending airtime with a negative amount.
    """
    user_prompt = (
        f"Send airtime to {TEST_PHONE_NUMBER} with an amount of -5 in currency KES"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True

@pytest.mark.asyncio
async def test_run_send_message_spam_detection():
    """
    Test sending a message that may be considered spam.
    """
    user_prompt = (
        f"Send a message to {TEST_PHONE_NUMBER} with the message 'Buy now! '*50, "
        f"using the username {USERNAME}"
    )
    await run("qwen2.5:0.5b", user_prompt)
    assert True

@pytest.mark.asyncio
async def test_run_search_news_sensitive_content():
    """
    Test searching for news with potentially sensitive content.
    """
    user_prompt = "Search for news about 'Illegal Activities'"
    await run("qwen2.5:0.5b", user_prompt)
    assert True