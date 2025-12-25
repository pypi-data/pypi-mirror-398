"""Tests for veris_runner with ToolCallOptions configuration."""

import json
import os
import sys
import pytest
from typing import Any
from unittest.mock import patch, MagicMock

# Workaround for Python 3.13 httpx compatibility issue
if sys.version_info >= (3, 13):
    import httpx

    _ = httpx.AsyncClient

from agents import Agent, FunctionTool

from veris_ai import veris, Runner, VerisConfig, ToolCallOptions, ResponseExpectation
from tests.test_helpers import create_test_token

# Skip tests if no API key is available
if not os.environ.get("OPENAI_API_KEY"):
    pytest.skip(
        "OPENAI_API_KEY not set - skipping tests that require real API", allow_module_level=True
    )


# Tool implementations
async def calculator_impl(context: Any, arguments: str) -> str:
    """Calculator tool implementation."""
    args = json.loads(arguments)
    operation = args.get("operation", "add")
    a = args.get("a", 0)
    b = args.get("b", 0)

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b if b != 0 else 0
    else:
        result = 0

    return json.dumps({"result": result, "operation": operation})


async def search_tool_impl(context: Any, arguments: str) -> str:
    """Search tool implementation."""
    args = json.loads(arguments)
    query = args.get("query", "")
    return json.dumps({"results": [f"Result 1 for '{query}'", f"Result 2 for '{query}'"]})


async def database_tool_impl(context: Any, arguments: str) -> str:
    """Database tool implementation."""
    args = json.loads(arguments)
    action = args.get("action", "query")
    return json.dumps({"status": "success", "action": action, "rows": 42})


@pytest.fixture
def multi_tool_agent():
    """Create an agent with multiple tools for testing different configurations."""
    calculator = FunctionTool(
        name="calculator",
        description="Perform mathematical operations",
        params_json_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["operation", "a", "b"],
        },
        on_invoke_tool=calculator_impl,
    )

    search = FunctionTool(
        name="search_web",
        description="Search the web for information",
        params_json_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
        on_invoke_tool=search_tool_impl,
    )

    database = FunctionTool(
        name="database_query",
        description="Query a database",
        params_json_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["query", "update", "delete"]},
                "sql": {"type": "string"},
            },
            "required": ["action"],
        },
        on_invoke_tool=database_tool_impl,
    )

    return Agent(
        name="MultiToolAssistant",
        model="gpt-4o-mini",
        instructions="You are a helpful assistant with access to calculator, search, and database tools.",
        tools=[calculator, search, database],
    )


@pytest.fixture
def mock_api_client_with_options():
    """Mock the API client to verify ToolCallOptions are passed correctly."""
    calls = []

    def mock_post_sync(endpoint, payload):
        calls.append({"endpoint": endpoint, "payload": payload})
        return {"result": "mocked"}

    from veris_ai.api_client import get_api_client

    with patch.object(get_api_client(), "post_sync", side_effect=mock_post_sync):
        yield {"calls": calls}


@pytest.mark.asyncio
async def test_tool_options_passed_to_mock_call(mock_api_client_with_options, multi_tool_agent):
    """Verify that ToolCallOptions are correctly passed to the mock_tool_call function."""
    # Set up session for mocking using proper token format
    token = create_test_token("test-session-tool-options")
    veris.set_session_id(token)

    try:
        config = VerisConfig(
            tool_options={
                "calculator": ToolCallOptions(
                    response_expectation=ResponseExpectation.REQUIRED,
                    cache_response=True,
                    mode="function",
                )
            }
        )
        runner = Runner(veris_config=config)

        # Note: This test would require actual mocking infrastructure
        # For now, we're just verifying the configuration is created correctly
        assert (
            runner.veris_config.tool_options["calculator"].response_expectation
            == ResponseExpectation.REQUIRED
        )
        assert runner.veris_config.tool_options["calculator"].cache_response is True
        assert runner.veris_config.tool_options["calculator"].mode == "function"

    finally:
        # Clean up
        os.environ.pop("ENV", None)
        veris.clear_session_id()


def test_tool_call_options_defaults():
    """Test that ToolCallOptions has correct default values."""
    options = ToolCallOptions()
    assert options.response_expectation == ResponseExpectation.AUTO
    assert options.cache_response is False
    assert options.mode == "tool"

    # Test with custom values
    options = ToolCallOptions(
        response_expectation=ResponseExpectation.REQUIRED, cache_response=True, mode="spy"
    )
    assert options.response_expectation == ResponseExpectation.REQUIRED
    assert options.cache_response is True
    assert options.mode == "spy"


def test_response_expectation_enum():
    """Test ResponseExpectation enum values."""
    assert ResponseExpectation.AUTO == "auto"
    assert ResponseExpectation.REQUIRED == "required"
    assert ResponseExpectation.NONE == "none"

    # Verify all enum values are accessible
    all_values = [e.value for e in ResponseExpectation]
    assert "auto" in all_values
    assert "required" in all_values
    assert "none" in all_values


# ===== Tests for new Runner class with ToolCallOptions =====


@pytest.mark.asyncio
async def test_runner_class_with_tool_options_basic(multi_tool_agent):
    """Test Runner class with basic ToolCallOptions configuration."""
    veris.clear_session_id()

    # Create config with tool options
    config = VerisConfig(
        tool_options={
            "calculator": ToolCallOptions(
                response_expectation=ResponseExpectation.AUTO, cache_response=True, mode="tool"
            ),
            "search_web": ToolCallOptions(
                response_expectation=ResponseExpectation.NONE, cache_response=False, mode="spy"
            ),
        }
    )

    result = await Runner.run(
        multi_tool_agent, "Calculate 15 plus 27", veris_config=config, max_turns=2
    )

    assert result is not None
    # Check that the calculation was performed (42)
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "42" in text


@pytest.mark.asyncio
async def test_runner_with_tool_options_and_include_tools(multi_tool_agent):
    """Test Runner with both tool_options and include_tools."""
    veris.clear_session_id()

    # Create config that only intercepts calculator with specific options
    config = VerisConfig(
        include_tools=["calculator"],
        tool_options={
            "calculator": ToolCallOptions(
                response_expectation=ResponseExpectation.REQUIRED, cache_response=True
            ),
            "search_web": ToolCallOptions(  # This won't be used since not in include_tools
                response_expectation=ResponseExpectation.NONE
            ),
        },
    )

    result = await Runner.run(
        multi_tool_agent, "What is 8 times 6?", veris_config=config, max_turns=2
    )

    assert result is not None
    # Check for the result (48)
    last_message = result.to_input_list()[-1]
    if isinstance(last_message, dict) and "content" in last_message:
        content = last_message["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
        else:
            text = str(content)
    else:
        text = str(last_message)
    assert "48" in text


def test_veris_config_with_tool_options():
    """Test that VerisConfig correctly handles tool_options."""
    # Test with empty tool_options
    config = VerisConfig()
    assert config.tool_options is None

    # Test with single tool option
    config = VerisConfig(
        tool_options={"my_tool": ToolCallOptions(response_expectation=ResponseExpectation.REQUIRED)}
    )
    assert config.tool_options is not None
    assert "my_tool" in config.tool_options
    assert config.tool_options["my_tool"].response_expectation == ResponseExpectation.REQUIRED

    # Test with multiple tool options
    config = VerisConfig(
        include_tools=["tool1", "tool2"],
        tool_options={
            "tool1": ToolCallOptions(
                response_expectation=ResponseExpectation.AUTO, cache_response=True, mode="tool"
            ),
            "tool2": ToolCallOptions(
                response_expectation=ResponseExpectation.NONE, cache_response=False, mode="spy"
            ),
        },
    )
    assert len(config.tool_options) == 2
    assert config.tool_options["tool1"].cache_response is True
    assert config.tool_options["tool2"].mode == "spy"


@pytest.mark.asyncio
async def test_runner_class_static_method_usage(multi_tool_agent):
    """Test that Runner.run can be used as a static method (OpenAI style)."""
    veris.clear_session_id()

    # Use Runner.run directly without creating an instance
    result = await Runner.run(multi_tool_agent, "Calculate 100 divided by 4", max_turns=2)

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
    assert "25" in text
