"""Simplified tests for the OpenAI agents wrapper with live API calls only."""

import json
import os
import sys
import pytest
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock

# Workaround for Python 3.13 httpx compatibility issue
if sys.version_info >= (3, 13):
    import httpx

    # Pre-import httpx to ensure it's available for isinstance checks
    _ = httpx.AsyncClient

from agents import Agent, FunctionTool

from veris_ai import veris, Runner
from tests.test_helpers import create_test_token

# Skip tests if no API key is available
if not os.environ.get("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set - skipping tests that require real API", allow_module_level=True
    )


# Simple tool implementations
async def add_numbers_impl(context: Any, arguments: str) -> str:
    """Add two numbers together."""
    args = json.loads(arguments)
    result = args.get("a", 0) + args.get("b", 0)
    return json.dumps({"result": result})


async def multiply_numbers_impl(context: Any, arguments: str) -> str:
    """Multiply two numbers together."""
    args = json.loads(arguments)
    result = args.get("a", 0) * args.get("b", 0)
    return json.dumps({"result": result})


@pytest.fixture
def test_agent():
    """Fixture that creates a simple test agent with math tools."""
    add_tool = FunctionTool(
        name="add_numbers",
        description="Add two numbers together",
        params_json_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        on_invoke_tool=add_numbers_impl,
    )

    multiply_tool = FunctionTool(
        name="multiply_numbers",
        description="Multiply two numbers",
        params_json_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        on_invoke_tool=multiply_numbers_impl,
    )

    return Agent(
        name="MathAssistant",
        model="gpt-4o-mini",  # Using cheaper model for testing
        instructions="You are a helpful math assistant. Use the add_numbers or multiply_numbers tools to perform calculations when asked.",
        tools=[add_tool, multiply_tool],
    )


@pytest.fixture
def mock_veris_endpoint():
    """Fixture that mocks the veris SDK's HTTP request method."""
    calls = []

    async def mock_request_async(endpoint, payload):
        """Mock the post_async method."""
        # Record the call
        calls.append({"endpoint": endpoint, "payload": payload})

        # Return a distinctive mocked value
        return {"result": 999}

    def mock_request_sync(endpoint, payload):
        """Mock the post method."""
        # Record the call
        calls.append({"endpoint": endpoint, "payload": payload})

        # Return a distinctive mocked value
        return {"result": 999}

    # Patch both sync and async methods of the API client
    from veris_ai.api_client import get_api_client

    with (
        patch.object(get_api_client(), "post", side_effect=mock_request_sync),
        patch.object(get_api_client(), "post_async", side_effect=mock_request_async),
    ):
        yield {"calls": calls}


@pytest.fixture
def simulation_env_with_session():
    """Fixture that sets up simulation environment variables and session ID."""
    # Store original values
    original_endpoint = os.environ.get("VERIS_ENDPOINT_URL")

    # Set up simulation environment
    os.environ["VERIS_ENDPOINT_URL"] = "http://localhost:8000"

    # Set session ID using proper token format
    token = create_test_token("test-session-123")
    veris.set_session_id(token)

    yield

    # Clean up
    veris.clear_session_id()

    # Restore original environment variables
    if original_endpoint is None:
        os.environ.pop("VERIS_ENDPOINT_URL", None)
    else:
        os.environ["VERIS_ENDPOINT_URL"] = original_endpoint


# ===== Tests for Runner class =====


@pytest.mark.asyncio
async def test_runner_class_basic(test_agent):
    """Test basic Runner class functionality with real OpenAI API."""
    veris.clear_session_id()  # Ensure no session is set

    # Use the Runner class directly (like OpenAI's Runner)
    result = await Runner.run(test_agent, "What is 5 plus 3?", max_turns=2)

    # Verify we got a result
    assert result is not None
    # Check that the agent used the tool and got the correct answer (8)
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "8" in text


@pytest.mark.asyncio
async def test_runner_with_config(test_agent):
    """Test Runner class with configuration."""
    veris.clear_session_id()

    # Create configuration
    config = VerisConfig(include_tools=["add_numbers"])

    # Run with configuration
    result = await Runner.run(test_agent, "Calculate 2 plus 2", veris_config=config, max_turns=2)

    # Verify we got a result
    assert result is not None
    # Check that the calculation was performed
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "4" in text


@pytest.mark.asyncio
async def test_runner_with_exclude_tools(test_agent):
    """Test Runner class with exclude_tools configuration."""
    veris.clear_session_id()

    # Create configuration that excludes multiply_numbers
    config = VerisConfig(exclude_tools=["multiply_numbers"])

    # Run addition (should work)
    result = await Runner.run(test_agent, "What is 10 plus 5?", veris_config=config, max_turns=2)

    assert result is not None
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "15" in text


@pytest.mark.asyncio
async def test_runner_without_session_does_not_call_endpoint(mock_veris_endpoint, test_agent):
    """Test that Runner does NOT call the endpoint when no session is set."""
    # Ensure we're NOT in simulation mode and no session is set
    os.environ.pop("ENV", None)
    veris.clear_session_id()

    # Run without session - should use real tools
    result = await Runner.run(test_agent, "What is 3 plus 4?", max_turns=2)

    # Verify the endpoint was NOT called
    assert len(mock_veris_endpoint["calls"]) == 0, (
        "Veris endpoint should not be called without session"
    )

    # Verify real calculation was performed (7, not 999)
    assert result is not None
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "7" in text, "Should use real calculation"
    assert "999" not in text, "Should not use mocked result"


@pytest.mark.asyncio
async def test_runner_with_session_calls_endpoint(
    mock_veris_endpoint, simulation_env_with_session, test_agent
):
    """Test that Runner calls the veris endpoint when session is set."""
    # Use Runner.run directly
    result = await Runner.run(test_agent, "What is 10 plus 5?", max_turns=5)

    # Verify the endpoint was called
    assert len(mock_veris_endpoint["calls"]) > 0, "Veris endpoint should have been called"

    # Verify the call had correct structure
    first_call = mock_veris_endpoint["calls"][0]
    assert first_call["endpoint"] == "http://localhost:8000/v3/tool_mock"
    assert first_call["payload"]["session_id"] == "test-session-123"
    assert "add_numbers" in str(first_call["payload"]) or "veris_tool_function" in str(
        first_call["payload"]
    )

    assert result is not None


def test_runner_config_validation():
    """Test that Runner validates configuration correctly."""
    # Test that include_tools alone works
    config = VerisConfig(include_tools=["tool1", "tool2"])
    assert config.include_tools == ["tool1", "tool2"]

    # Test that exclude_tools alone works
    config = VerisConfig(exclude_tools=["tool3"])
    assert config.exclude_tools == ["tool3"]

    # Test that both cannot be set at runtime
    async def test_both_set():
        config = VerisConfig(include_tools=["tool1"], exclude_tools=["tool2"])
        with pytest.raises(ValueError, match="Cannot specify both include_tools and exclude_tools"):
            await Runner.run(None, "test", veris_config=config)

    # Run the async test
    import asyncio

    asyncio.run(test_both_set())

    # Test that empty config works
    config = VerisConfig()
    assert config.include_tools is None
    assert config.exclude_tools is None
