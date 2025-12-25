"""Tests for class method callbacks that need access to self."""

import asyncio
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from veris_ai import veris
from veris_ai.api_client import get_api_client

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
def simulation_env():
    """Set up simulation environment with session_id."""
    token = create_test_token("test-session", "test-thread")
    veris.parse_token(token, verify_signature=False)
    yield
    veris.clear_context()


# Test class method callbacks that need self


class CounterClass:
    """Test class with instance state that callbacks need to access."""

    def __init__(self):
        self.counter = 0
        self.call_log = []

    def input_callback(self, x: int, y: int):
        """Callback that needs self to update instance state."""
        self.counter += x + y
        self.call_log.append(f"input: x={x}, y={y}")

    def output_callback(self, result: dict):
        """Callback that processes output using instance state."""
        self.counter += result.get("value", 0)
        self.call_log.append(f"output: {result}")

    def combined_callback(self, x: int, y: int, mock_output: dict = None):
        """Callback that uses both input and output."""
        total = x + y + (mock_output.get("value", 0) if mock_output else 0)
        self.counter = total
        self.call_log.append(f"combined: x={x}, y={y}, output={mock_output}")

    @veris.mock(
        mode="function", input_callback=lambda self, **kwargs: self.input_callback(**kwargs)
    )
    async def process_with_input_callback(self, x: int, y: int) -> dict:
        return {"result": x + y}

    @veris.mock(mode="function", output_callback=lambda self, result: self.output_callback(result))
    async def process_with_output_callback(self, x: int) -> dict:
        return {"value": x}

    @veris.mock(
        mode="function",
        combined_callback=lambda self, mock_output=None, **kwargs: self.combined_callback(
            mock_output=mock_output, **kwargs
        ),
    )
    async def process_with_combined_callback(self, x: int, y: int) -> dict:
        return {"value": x + y}


@pytest.mark.asyncio
async def test_class_method_input_callback_with_lambda(simulation_env):
    """Test that class method callbacks work when wrapped in lambda."""
    obj = CounterClass()

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await obj.process_with_input_callback(10, 20)
        assert result == {"mocked": True}

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Check that the callback was called and updated instance state
        assert obj.counter == 30  # 10 + 20
        assert len(obj.call_log) == 1
        assert "input: x=10, y=20" in obj.call_log[0]


@pytest.mark.asyncio
async def test_class_method_output_callback_with_lambda(simulation_env):
    """Test that class method output callbacks work when wrapped in lambda."""
    obj = CounterClass()

    mock_response = {"value": 42}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await obj.process_with_output_callback(10)
        assert result == {"value": 42}

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Check that the callback was called and updated instance state
        assert obj.counter == 42
        assert len(obj.call_log) == 1
        assert "output:" in obj.call_log[0]


@pytest.mark.asyncio
async def test_class_method_combined_callback_with_lambda(simulation_env):
    """Test that class method combined callbacks work when wrapped in lambda."""
    obj = CounterClass()

    mock_response = {"value": 100}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await obj.process_with_combined_callback(10, 20)
        assert result == {"value": 100}

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Check that the callback was called and updated instance state
        assert obj.counter == 130  # 10 + 20 + 100
        assert len(obj.call_log) == 1
        assert "combined:" in obj.call_log[0]


class AutoBindCallbackClass:
    """Test class that uses direct method references (should work after fix)."""

    def __init__(self):
        self.counter = 0

    def increment_counter(self, x: int):
        """Callback that increments instance counter."""
        self.counter += x

    def double_counter(self, result: dict):
        """Callback that doubles the counter based on result."""
        self.counter = result.get("value", 0) * 2


# These tests will pass after we implement the fix
@pytest.mark.skip(reason="Not implemented yet - will be fixed")
class TestAutoBindingCallbacks:
    """Tests for auto-binding of self to callbacks."""

    @pytest.mark.asyncio
    async def test_direct_method_reference_input_callback(self, simulation_env):
        """Test that direct method references work for input callbacks."""

        class TestClass:
            def __init__(self):
                self.value = 0

            def my_callback(self, x: int):
                self.value = x

            @veris.mock(mode="function", input_callback=my_callback)
            async def my_method(self, x: int) -> dict:
                return {"result": x}

        obj = TestClass()
        mock_response = {"mocked": True}

        with patch.object(get_api_client(), "post_async", return_value=mock_response):
            result = await obj.my_method(42)
            assert result == {"mocked": True}
            await asyncio.sleep(0.01)
            assert obj.value == 42
