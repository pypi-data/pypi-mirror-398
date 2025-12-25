"""Tests for external (non-class) callback functions that receive self parameter."""

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


# External callback functions (defined outside any class)


def track_input_calls(self, x: int, y: int):
    """External callback that tracks input calls on the instance."""
    self.call_count += 1
    self.last_inputs = {"x": x, "y": y}


def process_output(self, result: dict):
    """External callback that processes output using instance state."""
    self.output_count += 1
    self.last_output = result


def combine_data(self, x: int, y: int, mock_output: dict = None):
    """External callback that combines input and output."""
    self.combined_calls += 1
    self.last_combined = {
        "inputs": {"x": x, "y": y},
        "output": mock_output,
    }


async def async_track_input(self, a: int, b: int):
    """Async external callback for input tracking."""
    await asyncio.sleep(0)  # Simulate async work
    self.async_call_count += 1
    self.last_async_inputs = {"a": a, "b": b}


async def async_process_output(self, result: dict):
    """Async external callback for output processing."""
    await asyncio.sleep(0)  # Simulate async work
    self.async_output_count += 1
    self.last_async_output = result


# Test with external callbacks


class ServiceWithExternalCallbacks:
    """Test class that uses external callbacks (not class methods)."""

    def __init__(self):
        self.call_count = 0
        self.output_count = 0
        self.combined_calls = 0
        self.async_call_count = 0
        self.async_output_count = 0
        self.last_inputs = None
        self.last_output = None
        self.last_combined = None
        self.last_async_inputs = None
        self.last_async_output = None

    @veris.mock(mode="function", input_callback=track_input_calls)
    async def process_with_external_input_callback(self, x: int, y: int) -> dict:
        """Method using external input callback."""
        return {"result": x + y}

    @veris.mock(mode="function", output_callback=process_output)
    async def process_with_external_output_callback(self, x: int) -> dict:
        """Method using external output callback."""
        return {"value": x}

    @veris.mock(mode="function", combined_callback=combine_data)
    async def process_with_external_combined_callback(self, x: int, y: int) -> dict:
        """Method using external combined callback."""
        return {"sum": x + y}

    @veris.mock(mode="function", input_callback=async_track_input)
    async def process_with_async_external_callback(self, a: int, b: int) -> dict:
        """Method using async external callback."""
        return {"result": a * b}

    @veris.mock(mode="function", output_callback=async_process_output)
    async def process_with_async_output_callback(self, x: int) -> dict:
        """Method using async external output callback."""
        return {"doubled": x * 2}


@pytest.mark.asyncio
async def test_external_input_callback_receives_self(simulation_env):
    """Test that external input callback receives self and can modify instance state."""
    service = ServiceWithExternalCallbacks()

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process_with_external_input_callback(10, 20)
        assert result == {"mocked": True}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # External callback should have been called and modified instance state
        assert service.call_count == 1
        assert service.last_inputs == {"x": 10, "y": 20}


@pytest.mark.asyncio
async def test_external_output_callback_receives_self(simulation_env):
    """Test that external output callback receives self and can modify instance state."""
    service = ServiceWithExternalCallbacks()

    mock_response = {"value": 42}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process_with_external_output_callback(10)
        assert result == {"value": 42}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # External callback should have been called and modified instance state
        assert service.output_count == 1
        assert service.last_output == {"value": 42}


@pytest.mark.asyncio
async def test_external_combined_callback_receives_self(simulation_env):
    """Test that external combined callback receives self and can access both input and output."""
    service = ServiceWithExternalCallbacks()

    mock_response = {"sum": 100}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process_with_external_combined_callback(30, 70)
        assert result == {"sum": 100}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # External callback should have combined input and output
        assert service.combined_calls == 1
        assert service.last_combined == {
            "inputs": {"x": 30, "y": 70},
            "output": {"sum": 100},
        }


@pytest.mark.asyncio
async def test_async_external_input_callback(simulation_env):
    """Test that async external input callback works correctly."""
    service = ServiceWithExternalCallbacks()

    mock_response = {"result": 50}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process_with_async_external_callback(5, 10)
        assert result == {"result": 50}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # Async external callback should have been called
        assert service.async_call_count == 1
        assert service.last_async_inputs == {"a": 5, "b": 10}


@pytest.mark.asyncio
async def test_async_external_output_callback(simulation_env):
    """Test that async external output callback works correctly."""
    service = ServiceWithExternalCallbacks()

    mock_response = {"doubled": 20}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process_with_async_output_callback(7)
        assert result == {"doubled": 20}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # Async external callback should have been called
        assert service.async_output_count == 1
        assert service.last_async_output == {"doubled": 20}


# Test with sync functions and external callbacks


class SyncServiceWithExternalCallbacks:
    """Test class using sync methods with external callbacks."""

    def __init__(self):
        self.counter = 0

    @veris.mock(mode="function", input_callback=track_input_calls)
    def sync_process(self, x: int, y: int) -> int:
        """Sync method using external input callback."""
        return x + y


def test_sync_method_with_external_callback(simulation_env):
    """Test that sync methods work with external callbacks."""
    # Redefine call_count tracking for sync test
    service = SyncServiceWithExternalCallbacks()
    service.call_count = 0
    service.last_inputs = None

    mock_response = 999

    with patch.object(get_api_client(), "post", return_value=mock_response):
        result = service.sync_process(15, 25)
        assert result == 999

        # External callback should have been called synchronously
        assert service.call_count == 1
        assert service.last_inputs == {"x": 15, "y": 25}


# Test external callback that doesn't use self (regular function)


def regular_callback_no_self(x: int, y: int):
    """Regular callback that doesn't need self."""
    print(f"Called with x={x}, y={y}")


regular_callback_calls = []


def regular_callback_with_tracking(x: int, y: int):
    """Regular callback that tracks calls globally."""
    regular_callback_calls.append({"x": x, "y": y})


class ServiceWithRegularCallback:
    """Test class using regular callbacks (no self parameter)."""

    @veris.mock(mode="function", input_callback=regular_callback_with_tracking)
    async def process(self, x: int, y: int) -> dict:
        """Method using regular callback without self."""
        return {"result": x + y}


@pytest.mark.asyncio
async def test_regular_callback_without_self_parameter(simulation_env):
    """Test that callbacks without self parameter still work (backward compatibility)."""
    regular_callback_calls.clear()
    service = ServiceWithRegularCallback()

    mock_response = {"result": 30}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.process(10, 20)
        assert result == {"result": 30}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # Regular callback should have been called without self
        assert len(regular_callback_calls) == 1
        assert regular_callback_calls[0] == {"x": 10, "y": 20}


# Example showing the pattern for decoupled callbacks


def audit_log_callback(self, **kwargs):
    """
    External callback for audit logging.

    This is decoupled from the service class but can access instance state.
    """
    if not hasattr(self, "audit_log"):
        self.audit_log = []
    self.audit_log.append(
        {
            "action": "api_call",
            "params": kwargs,
            "timestamp": "2024-01-01",  # In real code, use datetime.now()
        }
    )


def metrics_callback(self, mock_output: dict = None, **kwargs):
    """
    External callback for metrics collection.

    Demonstrates combining input and output for analytics.
    """
    if not hasattr(self, "metrics"):
        self.metrics = []
    self.metrics.append(
        {
            "input_count": len(kwargs),
            "output_type": type(mock_output).__name__,
            "success": mock_output is not None,
        }
    )


class ProductionService:
    """Example production service using external callbacks for separation of concerns."""

    def __init__(self):
        self.audit_log = []
        self.metrics = []

    @veris.mock(
        mode="function",
        input_callback=audit_log_callback,
        combined_callback=metrics_callback,
    )
    async def fetch_user_data(self, user_id: str, include_details: bool = False) -> dict:
        """
        Production method with audit logging and metrics collection.

        The callbacks are external, making them:
        - Easier to test independently
        - Reusable across multiple services
        - Easier to mock/disable in tests
        """
        return {"user_id": user_id, "details": {}}


@pytest.mark.asyncio
async def test_production_service_with_decoupled_callbacks(simulation_env):
    """Test production service with decoupled audit and metrics callbacks."""
    service = ProductionService()

    mock_response = {"user_id": "123", "name": "Alice"}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await service.fetch_user_data("123", include_details=True)
        assert result == {"user_id": "123", "name": "Alice"}

        # Wait for background tasks
        await asyncio.sleep(0.01)

        # Audit log should be populated
        assert len(service.audit_log) == 1
        assert service.audit_log[0]["action"] == "api_call"
        assert service.audit_log[0]["params"]["user_id"] == "123"
        assert service.audit_log[0]["params"]["include_details"] is True

        # Metrics should be collected
        assert len(service.metrics) == 1
        assert service.metrics[0]["input_count"] == 2  # user_id and include_details
        assert service.metrics[0]["output_type"] == "dict"
        assert service.metrics[0]["success"] is True
