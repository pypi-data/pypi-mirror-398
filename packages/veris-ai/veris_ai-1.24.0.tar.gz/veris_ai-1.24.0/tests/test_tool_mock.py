import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from veris_ai import veris
from veris_ai.api_client import get_api_client
from veris_ai.tool_mock import _session_id_context

# Generate a test RSA key pair for JWT signing
_test_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def create_test_token(
    session_id: str = "test-session", thread_id: str | None = "test-thread"
) -> str:
    """Create a JWT test token."""
    token_data = {"session_id": session_id}
    if thread_id is not None:
        token_data["thread_id"] = thread_id
    return jwt.encode(token_data, _test_private_key, algorithm="RS256")


@pytest.fixture
def tool_mock():
    return veris


# Test mock decorator
@pytest.mark.asyncio
async def test_mock_decorator_simulation_mode(simulation_env):
    @veris.mock(mode="function")
    async def test_func(param1: str, param2: int) -> dict[str, Any]:
        return {"result": "real"}

    mock_response = {"result": {"mocked": True}}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func("test", 42)
        assert result == {"result": {"mocked": True}}


@pytest.mark.asyncio
async def test_mock_decorator_production_mode(production_env):
    @veris.mock(mode="function")
    async def test_func(param1: str, param2: int) -> dict:
        return {"result": "real"}

    result = await test_func("test", 42)
    assert result == {"result": "real"}


@pytest.mark.asyncio
async def test_mock_with_context(simulation_env):
    @veris.mock(mode="function")
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"result": {"mocked": True}}

    with patch.object(get_api_client(), "post_async") as mock_request:
        mock_request.return_value = mock_response
        token = create_test_token("test-session-id", "test-thread-id")
        veris.parse_token(token, verify_signature=False)
        result = await test_func()
        # Check that the mock was called with thread_id as session_id value
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert (
            call_args[0][1]["session_id"] == "test-thread-id"
        )  # thread_id used as session_id value
        assert result == {"result": {"mocked": True}}


@pytest.mark.asyncio
async def test_mock_without_context():
    """Test that without session_id, the function runs in production mode."""

    @veris.mock(mode="function")
    async def test_func() -> dict:
        return {"result": "real"}

    # Clear session_id to ensure production mode
    veris.clear_context()

    # In production mode, the original function should be called
    result = await test_func()
    assert result == {"result": "real"}


# Test error handling
@pytest.mark.asyncio
async def test_mock_http_error(simulation_env):
    @veris.mock(mode="function")
    async def test_func(param1: str) -> dict:
        return {"result": "real"}

    with (
        patch.object(
            get_api_client(), "post_async", side_effect=httpx.HTTPError("Mock HTTP Error")
        ),
        pytest.raises(httpx.HTTPError),
    ):
        await test_func("test")


@pytest.mark.asyncio
async def test_mock_missing_endpoint():
    """Test that missing endpoint raises ConnectError when invalid URL is used."""
    # Use invalid URL that will trigger ConnectError
    with patch.dict(os.environ, {"VERIS_API_URL": "http://invalid-nonexistent-domain-12345.local"}):

        @veris.mock()
        async def test_func():
            return {"result": "real"}

        # Set session_id to enable simulation mode
        token = create_test_token("test-session")
        veris.parse_token(token, verify_signature=False)

        # Invalid domain will cause ConnectError
        with pytest.raises(httpx.ConnectError):
            await test_func()


@pytest.mark.asyncio
async def test_mock_invalid_endpoint(simulation_env):
    """Test that invalid endpoint URL raises ConnectError."""
    # Use invalid URL that will trigger ConnectError
    with (
        patch.dict(os.environ, {"VERIS_API_URL": "http://invalid-nonexistent-domain-67890.local"}),
        pytest.raises(httpx.ConnectError),
    ):

        @veris.mock()
        async def test_func():
            return {"result": "real"}

        await test_func()


@pytest.mark.asyncio
async def test_mock_string_json_response(simulation_env):
    @veris.mock(mode="function")
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"result": '{"key": "value"}'}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func()
        assert result == {"result": '{"key": "value"}'}


# Test context vars behavior
@pytest.mark.asyncio
async def test_context_var_isolation():
    """Test that session_id context vars are isolated between concurrent calls."""

    async def set_and_check_session(session_id: str):
        token = create_test_token(session_id)
        veris.parse_token(token, verify_signature=False)
        # Verify the session_id is set correctly
        assert veris.session_id == session_id
        # Simulate some async work
        await asyncio.sleep(0.01)
        # Verify the session_id hasn't changed
        assert veris.session_id == session_id
        return session_id

    # Run multiple concurrent tasks with different session IDs
    tasks = [
        set_and_check_session("session-1"),
        set_and_check_session("session-2"),
        set_and_check_session("session-3"),
    ]

    results = await asyncio.gather(*tasks)
    assert results == ["session-1", "session-2", "session-3"]


@pytest.mark.asyncio
async def test_context_var_persistence_in_call(simulation_env):
    """Test that session_id persists throughout a mock function call."""
    captured_session_ids = []

    @veris.mock(mode="function")
    async def test_func() -> dict:
        # Capture session_id inside the function
        captured_session_ids.append(veris.session_id)
        return {"result": "real"}

    mock_response = {"result": {"mocked": True}}

    async def mock_request_func(endpoint, payload):
        # Capture session_id during HTTP call
        captured_session_ids.append(veris.session_id)
        return mock_response

    with patch.object(
        get_api_client(), "post_async", side_effect=mock_request_func
    ) as mock_request:
        # Set session_id and call function
        token = create_test_token("test-session-123", "test-thread-123")
        veris.parse_token(token, verify_signature=False)
        await test_func()

        # Verify session_id was captured
        # In simulation mode, we should have captures from the HTTP call
        assert len(captured_session_ids) >= 1
        assert captured_session_ids[0] == "test-session-123"

        # Verify the HTTP client was called with correct session_id (should use thread_id)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["session_id"] == "test-thread-123"


@pytest.mark.asyncio
async def test_context_var_cleanup():
    """Test that clearing session_id works correctly."""
    # Set a session_id
    token = create_test_token("test-session")
    veris.parse_token(token, verify_signature=False)
    assert veris.session_id == "test-session"

    # Clear it
    veris.clear_context()
    assert veris.session_id is None

    # Verify it stays None
    await asyncio.sleep(0.01)
    assert veris.session_id is None


@pytest.mark.asyncio
async def test_context_var_no_interference():
    """Test that context vars don't interfere between different async contexts."""
    results = []

    async def task1():
        token = create_test_token("task1-session")
        veris.parse_token(token, verify_signature=False)
        await asyncio.sleep(0.02)
        results.append(("task1", veris.session_id))

    async def task2():
        await asyncio.sleep(0.01)
        # Should be None since we didn't set it in this context
        results.append(("task2", veris.session_id))
        token = create_test_token("task2-session")
        veris.parse_token(token, verify_signature=False)
        results.append(("task2-after", veris.session_id))

    await asyncio.gather(task1(), task2())

    # Verify results
    assert ("task1", "task1-session") in results
    assert ("task2", None) in results
    assert ("task2-after", "task2-session") in results


# Test spy decorator
@pytest.mark.asyncio
async def test_spy_decorator_with_session(simulation_env):
    """Test that spy decorator logs function calls and returns real results."""

    @veris.spy()
    async def test_func(x: int, y: str) -> dict:
        """A test function that returns a dict."""
        return {"value": x, "message": y}

    # Mock the async logging functions
    with (
        patch("veris_ai.tool_mock.log_tool_call_async") as mock_log_call,
        patch("veris_ai.tool_mock.log_tool_response_async") as mock_log_response,
    ):
        token = create_test_token("spy-session-123")
        veris.parse_token(token, verify_signature=False)
        result = await test_func(42, "hello")

        # Verify the original function was executed
        assert result == {"value": 42, "message": "hello"}

        # Verify logging was called
        mock_log_call.assert_called_once_with(
            session_id="spy-session-123",
            function_name="test_func",
            parameters={
                "x": {"value": "42", "type": "<class 'int'>"},
                "y": {"value": "hello", "type": "<class 'str'>"},
            },
            docstring="A test function that returns a dict.",
        )
        mock_log_response.assert_called_once_with(
            session_id="spy-session-123", response={"value": 42, "message": "hello"}
        )


@pytest.mark.asyncio
async def test_spy_decorator_without_session():
    """Test that spy decorator executes original function when no session_id."""

    @veris.spy()
    async def test_func(x: int) -> int:
        return x * 2

    # Clear session to ensure no spying
    veris.clear_context()

    with (
        patch("veris_ai.tool_mock.log_tool_call_async") as mock_log_call,
        patch("veris_ai.tool_mock.log_tool_response_async") as mock_log_response,
    ):
        result = await test_func(21)

        # Verify the original function was executed
        assert result == 42

        # Verify logging was NOT called
        mock_log_call.assert_not_called()
        mock_log_response.assert_not_called()


def test_spy_decorator_sync_function(simulation_env):
    """Test spy decorator with synchronous functions."""

    @veris.spy()
    def sync_func(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b

    with (
        patch("veris_ai.tool_mock.log_tool_call") as mock_log_call,
        patch("veris_ai.tool_mock.log_tool_response") as mock_log_response,
    ):
        token = create_test_token("sync-spy-session")
        veris.parse_token(token, verify_signature=False)
        result = sync_func(10, 20)

        # Verify the original function was executed
        assert result == 30

        # Verify logging was called
        mock_log_call.assert_called_once_with(
            session_id="sync-spy-session",
            function_name="sync_func",
            parameters={
                "a": {"value": "10", "type": "<class 'int'>"},
                "b": {"value": "20", "type": "<class 'int'>"},
            },
            docstring="Adds two numbers.",
        )
        mock_log_response.assert_called_once_with(session_id="sync-spy-session", response=30)


def test_spy_decorator_sync_without_session():
    """Test sync spy decorator without session executes normally."""

    @veris.spy()
    def sync_func(x: str) -> str:
        return x.upper()

    veris.clear_context()

    with (
        patch("veris_ai.tool_mock.log_tool_call") as mock_log_call,
        patch("veris_ai.tool_mock.log_tool_response") as mock_log_response,
    ):
        result = sync_func("hello")

        # Verify the original function was executed
        assert result == "HELLO"

        # Verify logging was NOT called
        mock_log_call.assert_not_called()
        mock_log_response.assert_not_called()


@pytest.mark.asyncio
async def test_spy_decorator_preserves_metadata():
    """Test that spy decorator preserves function metadata."""

    @veris.spy()
    async def documented_spy_function(x: int, y: str = "default") -> str:
        """This is a documented spy function."""
        return f"{x}: {y}"

    # Check function metadata is preserved
    assert documented_spy_function.__name__ == "documented_spy_function"
    assert documented_spy_function.__doc__ == "This is a documented spy function."

    # Test that it works correctly
    token = create_test_token("test-spy")
    veris.parse_token(token, verify_signature=False)
    result = await documented_spy_function(100)
    assert result == "100: default"


@pytest.mark.asyncio
async def test_spy_decorator_with_exception():
    """Test that spy decorator logs and re-raises exceptions."""

    @veris.spy()
    async def failing_func(x: int) -> int:
        """A function that raises an exception."""
        if x < 0:
            raise ValueError("Negative value not allowed")
        return x * 2

    with (
        patch("veris_ai.tool_mock.log_tool_call_async") as mock_log_call,
        patch("veris_ai.tool_mock.log_tool_response_async") as mock_log_response,
    ):
        token = create_test_token("exception-spy-session")
        veris.parse_token(token, verify_signature=False)

        # Test normal execution
        result = await failing_func(5)
        assert result == 10
        mock_log_call.assert_called()
        mock_log_response.assert_called()

        # Reset mocks
        mock_log_call.reset_mock()
        mock_log_response.reset_mock()

        # Test exception case
        with pytest.raises(ValueError, match="Negative value not allowed"):
            await failing_func(-1)

        # Verify logging was still called for the call
        mock_log_call.assert_called_once()
        # Response logging might not be called on exception, that's okay


# Test stub decorator
@pytest.mark.asyncio
async def test_stub_decorator_simulation_mode(simulation_env):
    """Test that stub decorator returns stubbed value in simulation mode."""
    stub_value = {"stubbed": True, "data": "test_data"}

    @veris.stub(return_value=stub_value)
    async def my_function(x: int) -> dict:
        return {"real": True, "value": x}

    result = await my_function(42)
    assert result == stub_value
    assert result["stubbed"] is True
    assert result["data"] == "test_data"


@pytest.mark.asyncio
async def test_stub_decorator_production_mode(production_env):
    """Test that stub decorator executes original function in production mode."""
    stub_value = {"stubbed": True, "data": "test_data"}

    @veris.stub(return_value=stub_value)
    async def my_function(x: int) -> dict:
        return {"real": True, "value": x}

    result = await my_function(42)
    assert result == {"real": True, "value": 42}
    assert result.get("stubbed") is None


@pytest.mark.asyncio
async def test_stub_decorator_with_complex_return_value(simulation_env):
    """Test stub decorator with complex return values."""

    class CustomObject:
        def __init__(self, name: str, values: list[int]):
            self.name = name
            self.values = values

    stub_obj = CustomObject("test", [1, 2, 3])

    @veris.stub(return_value=stub_obj)
    async def get_custom_object() -> CustomObject:
        return CustomObject("real", [4, 5, 6])

    result = await get_custom_object()
    assert isinstance(result, CustomObject)
    assert result.name == "test"
    assert result.values == [1, 2, 3]


@pytest.mark.asyncio
async def test_stub_decorator_preserves_function_metadata(simulation_env):
    """Test that stub decorator preserves function metadata."""
    stub_value = "stubbed"

    @veris.stub(return_value=stub_value)
    async def documented_function(x: int, y: str = "default") -> str:
        """This is a documented function."""
        return f"{x}: {y}"

    # Check function metadata is preserved
    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This is a documented function."

    # Function still works
    result = await documented_function(10)
    assert result == stub_value


@pytest.mark.asyncio
async def test_stub_decorator_with_none_value(simulation_env):
    """Test stub decorator with None as return value."""

    @veris.stub(return_value=None)
    async def returns_none() -> Any:
        return {"should": "not_return_this"}

    result = await returns_none()
    assert result is None


# Test mock decorator with mode parameter
@pytest.mark.asyncio
async def test_mock_decorator_tool_mode(simulation_env):
    """Test mock decorator with mode='tool'."""

    @veris.mock(mode="tool")
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"result": "mocked"}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func()
        assert result == {"result": "mocked"}


@pytest.mark.asyncio
async def test_mock_decorator_function_mode(simulation_env):
    """Test mock decorator with mode='function'."""

    @veris.mock(mode="function")
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"mocked": True, "data": [1, 2, 3]}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func()
        assert result == mock_response


@pytest.mark.asyncio
async def test_mock_decorator_with_expects_response(simulation_env):
    """Test mock decorator with expects_response parameter."""

    @veris.mock(mode="function", expects_response=True)
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"result": {"mocked": True}}

    with patch.object(get_api_client(), "post_async", return_value=mock_response) as mock_request:
        result = await test_func()
        # Verify the request payload included expects_response
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["response_expectation"] == "required"
        assert result == {"result": {"mocked": True}}


@pytest.mark.asyncio
async def test_mock_decorator_with_cache_response(simulation_env):
    """Test mock decorator with cache_response parameter."""

    @veris.mock(mode="function", cache_response=True)
    async def test_func(x: int) -> dict:
        return {"result": x}

    mock_response = {"result": {"cached": True}}

    with patch.object(get_api_client(), "post_async", return_value=mock_response) as mock_request:
        result = await test_func(42)
        # Verify the request payload included cache_response
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["cache_response"] is True
        assert result == {"result": {"cached": True}}


@pytest.mark.asyncio
async def test_mock_decorator_all_parameters(simulation_env):
    """Test mock decorator with all parameters."""

    @veris.mock(mode="function", expects_response=False, cache_response=True)
    async def test_func(name: str, count: int) -> dict:
        return {"name": name, "count": count}

    mock_response = {"status": "mocked", "values": [1, 2, 3]}

    with patch.object(get_api_client(), "post_async", return_value=mock_response) as mock_request:
        result = await test_func("test", 3)
        # Verify the request payload
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        payload = call_args[0][1]
        assert payload["response_expectation"] == "none"
        assert payload["cache_response"] is True
        assert result == mock_response


@pytest.mark.asyncio
async def test_mock_decorator_function_mode_defaults_expects_response(simulation_env):
    """Test that function mode defaults expects_response to False."""

    @veris.mock(mode="function")
    async def test_func() -> dict:
        return {"result": "real"}

    mock_response = {"result": {"mocked": True}}

    with patch.object(get_api_client(), "post_async", return_value=mock_response) as mock_request:
        await test_func()
        # Verify expects_response is False for function mode by default
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][1]["response_expectation"] == "none"


@pytest.mark.asyncio
async def test_mock_decorator_json_schema_in_payload(simulation_env):
    """Test that mock decorator includes JSON schema of return type in payload."""
    from typing import List

    @veris.mock()
    async def test_func() -> List[dict]:
        return [{"result": "real"}]

    mock_response = [{"mocked": True}]

    with patch.object(get_api_client(), "post_async", return_value=mock_response) as mock_request:
        await test_func()
        # Verify the JSON schema was included in the payload
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        payload = call_args[0][1]
        return_type_schema = payload["tool_call"]["return_type"]
        # Should be a JSON string containing schema for List[dict]
        assert isinstance(return_type_schema, str)
        import json

        schema = json.loads(return_type_schema)
        assert schema["type"] == "array"
        assert "items" in schema
