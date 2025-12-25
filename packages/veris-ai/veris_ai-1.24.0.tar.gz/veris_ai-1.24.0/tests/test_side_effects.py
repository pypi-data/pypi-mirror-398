"""Tests for input_side_effect and output_side_effect functionality."""

import asyncio
from typing import Any
from unittest.mock import Mock, patch

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


@pytest.fixture
def production_env():
    """Set up production environment without session_id."""
    veris.clear_context()
    yield


# Test mock decorator with input_side_effect


@pytest.mark.asyncio
async def test_mock_with_async_input_side_effect(simulation_env):
    """Test mock decorator with async input_side_effect."""
    captured_inputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.mock(mode="function", input_callback=capture_input)
    async def test_func(x: int, y: str) -> dict:
        return {"real": True}

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(42, "hello")
        assert result == {"mocked": True}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_inputs) == 1
        assert captured_inputs[0] == {"x": 42, "y": "hello"}


@pytest.mark.asyncio
async def test_mock_with_sync_input_side_effect_async_func(simulation_env):
    """Test mock decorator with sync input_side_effect on async function."""
    captured_inputs = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.mock(mode="function", input_callback=capture_input)
    async def test_func(a: int, b: int) -> int:
        return a + b

    mock_response = 100

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(10, 20)
        assert result == 100
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_inputs) == 1
        assert captured_inputs[0] == {"a": 10, "b": 20}


def test_mock_with_sync_input_side_effect_sync_func(simulation_env):
    """Test mock decorator with sync input_side_effect on sync function."""
    captured_inputs = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.mock(mode="function", input_callback=capture_input)
    def test_func(name: str, count: int) -> dict:
        return {"name": name, "count": count}

    mock_response = {"mocked": "data"}

    with patch.object(get_api_client(), "post", return_value=mock_response):
        result = test_func("test", 5)
        assert result == {"mocked": "data"}
        assert len(captured_inputs) == 1
        assert captured_inputs[0] == {"name": "test", "count": 5}


# Test mock decorator with output_side_effect


@pytest.mark.asyncio
async def test_mock_with_async_output_side_effect(simulation_env):
    """Test mock decorator with async output_side_effect."""
    captured_outputs = []

    async def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.mock(mode="function", output_callback=capture_output)
    async def test_func(x: int) -> dict:
        return {"real": x}

    mock_response = {"mocked": 999}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(42)
        assert result == {"mocked": 999}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_outputs) == 1
        assert captured_outputs[0] == {"mocked": 999}


@pytest.mark.asyncio
async def test_mock_with_sync_output_side_effect_async_func(simulation_env):
    """Test mock decorator with sync output_side_effect on async function."""
    captured_outputs = []

    def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.mock(mode="function", output_callback=capture_output)
    async def test_func() -> str:
        return "real"

    mock_response = "mocked_string"

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func()
        assert result == "mocked_string"
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_outputs) == 1
        assert captured_outputs[0] == "mocked_string"


def test_mock_with_sync_output_side_effect_sync_func(simulation_env):
    """Test mock decorator with sync output_side_effect on sync function."""
    captured_outputs = []

    def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.mock(mode="function", output_callback=capture_output)
    def test_func(x: int) -> int:
        return x * 2

    mock_response = 1000

    with patch.object(get_api_client(), "post", return_value=mock_response):
        result = test_func(10)
        assert result == 1000
        assert len(captured_outputs) == 1
        assert captured_outputs[0] == 1000


# Test mock decorator with both side effects


@pytest.mark.asyncio
async def test_mock_with_both_side_effects(simulation_env):
    """Test mock decorator with both input and output side effects."""
    captured_inputs = []
    captured_outputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    async def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.mock(mode="function", input_callback=capture_input, output_callback=capture_output)
    async def test_func(x: int, y: str) -> dict:
        return {"real": True}

    mock_response = {"mocked": "result"}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(100, "test")
        assert result == {"mocked": "result"}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_inputs) == 1
        assert captured_inputs[0] == {"x": 100, "y": "test"}
        assert len(captured_outputs) == 1
        assert captured_outputs[0] == {"mocked": "result"}


# Test stub decorator with input_side_effect


@pytest.mark.asyncio
async def test_stub_with_async_input_side_effect(simulation_env):
    """Test stub decorator with async input_side_effect."""
    captured_inputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.stub(return_value={"stubbed": True}, input_callback=capture_input)
    async def test_func(a: str, b: int) -> dict:
        return {"real": True}

    result = await test_func("hello", 42)
    assert result == {"stubbed": True}
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == {"a": "hello", "b": 42}


@pytest.mark.asyncio
async def test_stub_with_sync_input_side_effect_async_func(simulation_env):
    """Test stub decorator with sync input_side_effect on async function."""
    captured_inputs = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.stub(return_value=99, input_callback=capture_input)
    async def test_func(x: int) -> int:
        return x * 2

    result = await test_func(5)
    assert result == 99
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == {"x": 5}


def test_stub_with_sync_input_side_effect_sync_func(simulation_env):
    """Test stub decorator with sync input_side_effect on sync function."""
    captured_inputs = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.stub(return_value="stubbed", input_callback=capture_input)
    def test_func(name: str, value: float) -> str:
        return f"{name}: {value}"

    result = test_func("test", 3.14)
    assert result == "stubbed"
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == {"name": "test", "value": 3.14}


# Test stub decorator with output_side_effect


@pytest.mark.asyncio
async def test_stub_with_async_output_side_effect(simulation_env):
    """Test stub decorator with async output_side_effect."""
    captured_outputs = []

    async def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.stub(return_value=["stubbed", "list"], output_callback=capture_output)
    async def test_func() -> list:
        return ["real", "list"]

    result = await test_func()
    assert result == ["stubbed", "list"]
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_outputs) == 1
    assert captured_outputs[0] == ["stubbed", "list"]


@pytest.mark.asyncio
async def test_stub_with_sync_output_side_effect_async_func(simulation_env):
    """Test stub decorator with sync output_side_effect on async function."""
    captured_outputs = []

    def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.stub(return_value={"stub": "data"}, output_callback=capture_output)
    async def test_func(x: int) -> dict:
        return {"real": x}

    result = await test_func(10)
    assert result == {"stub": "data"}
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_outputs) == 1
    assert captured_outputs[0] == {"stub": "data"}


def test_stub_with_sync_output_side_effect_sync_func(simulation_env):
    """Test stub decorator with sync output_side_effect on sync function."""
    captured_outputs = []

    def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.stub(return_value=42, output_callback=capture_output)
    def test_func() -> int:
        return 100

    result = test_func()
    assert result == 42
    assert len(captured_outputs) == 1
    assert captured_outputs[0] == 42


# Test stub decorator with both side effects


@pytest.mark.asyncio
async def test_stub_with_both_side_effects(simulation_env):
    """Test stub decorator with both input and output side effects."""
    captured_inputs = []
    captured_outputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    async def capture_output(result: Any):
        captured_outputs.append(result)

    @veris.stub(
        return_value={"stubbed": "response"},
        input_callback=capture_input,
        output_callback=capture_output,
    )
    async def test_func(x: int, y: str) -> dict:
        return {"real": "response"}

    result = await test_func(123, "test_value")
    assert result == {"stubbed": "response"}
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == {"x": 123, "y": "test_value"}
    assert len(captured_outputs) == 1
    assert captured_outputs[0] == {"stubbed": "response"}


# Test that ctx parameter is preserved


@pytest.mark.asyncio
async def test_mock_preserves_ctx_parameter(simulation_env):
    """Test that ctx parameter is preserved in input_side_effect."""
    captured_inputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.mock(mode="function", input_callback=capture_input)
    async def test_func(x: int, ctx: dict) -> dict:
        return {"x": x, "ctx": ctx}

    mock_response = {"mocked": True}
    context = {"session": "abc123", "user": "test_user"}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(42, ctx=context)
        assert result == {"mocked": True}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_inputs) == 1
        # ctx should be preserved in input parameters
        assert "ctx" in captured_inputs[0]
        assert captured_inputs[0]["ctx"] == context
        assert captured_inputs[0]["x"] == 42


@pytest.mark.asyncio
async def test_stub_preserves_ctx_parameter(simulation_env):
    """Test that ctx parameter is preserved in input_side_effect for stub."""
    captured_inputs = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    @veris.stub(return_value="stubbed", input_callback=capture_input)
    async def test_func(name: str, ctx: dict) -> str:
        return f"{name} with {ctx}"

    context = {"request_id": "12345"}
    result = await test_func("test", ctx=context)
    assert result == "stubbed"
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_inputs) == 1
    assert "ctx" in captured_inputs[0]
    assert captured_inputs[0]["ctx"] == context
    assert captured_inputs[0]["name"] == "test"


# Test that self and cls are excluded


@pytest.mark.asyncio
async def test_mock_excludes_self_parameter(simulation_env):
    """Test that self parameter is excluded from input_side_effect."""
    captured_inputs = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    class TestClass:
        @veris.mock(mode="function", input_callback=capture_input)
        async def test_method(self, x: int) -> dict:
            return {"x": x}

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        obj = TestClass()
        result = await obj.test_method(42)
        assert result == {"mocked": True}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_inputs) == 1
        # self should NOT be in input parameters
        assert "self" not in captured_inputs[0]
        assert captured_inputs[0] == {"x": 42}


# Test side effects in production mode (should not be called)


@pytest.mark.asyncio
async def test_mock_side_effects_not_called_in_production_mode(production_env):
    """Test that side effects are not called in production mode."""
    input_mock = Mock()
    output_mock = Mock()

    @veris.mock(mode="function", input_callback=input_mock, output_callback=output_mock)
    async def test_func(x: int) -> int:
        return x * 2

    result = await test_func(21)
    assert result == 42

    # Side effects should NOT have been called
    input_mock.assert_not_called()
    output_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stub_side_effects_not_called_in_production_mode(production_env):
    """Test that side effects are not called in production mode for stub."""
    input_mock = Mock()
    output_mock = Mock()

    @veris.stub(return_value="stubbed", input_callback=input_mock, output_callback=output_mock)
    async def test_func(x: int) -> str:
        return f"real: {x}"

    result = await test_func(10)
    assert result == "real: 10"

    # Side effects should NOT have been called
    input_mock.assert_not_called()
    output_mock.assert_not_called()


# Test side effect error handling


@pytest.mark.asyncio
async def test_mock_input_side_effect_exception_is_logged(simulation_env):
    """Test that exceptions in input side effects are caught and logged."""

    async def failing_side_effect(**kwargs):
        raise ValueError("Side effect error")

    @veris.mock(mode="function", input_callback=failing_side_effect)
    async def test_func(x: int) -> dict:
        return {"x": x}

    mock_response = {"mocked": True}

    with (
        patch.object(get_api_client(), "post_async", return_value=mock_response),
        patch("veris_ai.utils.logger.warning") as mock_logger,
    ):
        # Function should still work despite side effect failure
        result = await test_func(42)
        assert result == {"mocked": True}

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Error should have been logged
        mock_logger.assert_called_once()
        assert "Callback execution failed" in str(mock_logger.call_args)


@pytest.mark.asyncio
async def test_mock_output_side_effect_exception_is_logged(simulation_env):
    """Test that exceptions in output side effects are caught and logged."""

    def failing_side_effect(result: Any):
        raise RuntimeError("Output side effect error")

    @veris.mock(mode="function", output_callback=failing_side_effect)
    async def test_func() -> dict:
        return {"x": 1}

    mock_response = {"mocked": "response"}

    with (
        patch.object(get_api_client(), "post_async", return_value=mock_response),
        patch("veris_ai.utils.logger.warning") as mock_logger,
    ):
        # Function should still work and return result despite side effect failure
        result = await test_func()
        assert result == {"mocked": "response"}

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Error should have been logged
        mock_logger.assert_called_once()
        assert "Callback execution failed" in str(mock_logger.call_args)


def test_stub_input_side_effect_exception_is_logged_sync(simulation_env):
    """Test that exceptions in sync stub input side effects are caught and logged."""

    def failing_side_effect(**kwargs):
        raise TypeError("Sync side effect error")

    @veris.stub(return_value=42, input_callback=failing_side_effect)
    def test_func(x: int) -> int:
        return x * 2

    with patch("veris_ai.utils.logger.warning") as mock_logger:
        # Function should still work despite side effect failure
        result = test_func(10)
        assert result == 42

        # Error should have been logged
        mock_logger.assert_called_once()
        assert "Callback execution failed" in str(mock_logger.call_args)


# Test that side effects can perform operations on parameters


@pytest.mark.asyncio
async def test_mock_input_side_effect_can_process_parameters(simulation_env):
    """Test that input side effect can perform operations on parameters."""
    computation_results = []

    async def compute_sum(**kwargs):
        """Side effect that performs arithmetic on input params."""
        result = kwargs["a"] + kwargs["b"]
        computation_results.append(result)

    @veris.mock(mode="function", input_callback=compute_sum)
    async def add_numbers(a: int, b: int) -> int:
        """Original function adds numbers."""
        return a + b

    mock_response = 999  # Mocked return value

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await add_numbers(10, 20)
        # Function returns mocked value
        assert result == 999
        # Wait for background task
        await asyncio.sleep(0.01)
        # Side effect computed the actual sum of inputs
        assert len(computation_results) == 1
        assert computation_results[0] == 30  # 10 + 20


@pytest.mark.asyncio
async def test_mock_output_side_effect_can_process_result(simulation_env):
    """Test that output side effect can perform operations on result."""
    transformed_results = []

    async def transform_output(result: dict):
        """Side effect that transforms the output."""
        transformed = {k.upper(): v * 2 for k, v in result.items()}
        transformed_results.append(transformed)

    @veris.mock(mode="function", output_callback=transform_output)
    async def get_data(x: int) -> dict:
        return {"value": x}

    mock_response = {"value": 5, "count": 3}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await get_data(100)
        # Function returns original mocked value
        assert result == {"value": 5, "count": 3}
        # Wait for background task
        await asyncio.sleep(0.01)
        # Side effect transformed the output
        assert len(transformed_results) == 1
        assert transformed_results[0] == {"VALUE": 10, "COUNT": 6}


def test_stub_input_side_effect_can_validate_parameters(simulation_env):
    """Test that input side effect can validate parameters."""
    validation_results = []

    def validate_inputs(**kwargs):
        """Side effect that validates input parameters."""
        is_valid = kwargs["age"] >= 0 and len(kwargs["name"]) > 0
        validation_results.append(is_valid)

    @veris.stub(return_value="processed", input_callback=validate_inputs)
    def process_user(name: str, age: int) -> str:
        return f"User: {name}, Age: {age}"

    result = process_user("Alice", 25)
    # Function returns stubbed value
    assert result == "processed"
    # Side effect validated the inputs
    assert len(validation_results) == 1
    assert validation_results[0] is True


def test_mock_output_side_effect_divides_int_result(simulation_env):
    """Test output side effect that processes int result (divide by 2 case)."""
    divided_results = []

    def divide_by_2(result: int):
        """Side effect that divides the int result by 2."""
        divided = result / 2
        divided_results.append(divided)

    @veris.mock(mode="function", output_callback=divide_by_2)
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    mock_response = 100  # Mocked return value

    with patch.object(get_api_client(), "post", return_value=mock_response):
        # Call the function
        result = add(10, 20)

        # Function returns the mocked value (100, not 30)
        assert result == 100

        # Side effect divided the mocked result by 2
        assert len(divided_results) == 1
        assert divided_results[0] == 50.0  # 100 / 2


@pytest.mark.asyncio
async def test_mock_output_side_effect_processes_int_async(simulation_env):
    """Test async output side effect that processes int result."""
    processed_results = []

    async def divide_by_2(result: int):
        """Async side effect that divides the int result by 2."""
        divided = result / 2
        processed_results.append(divided)

    @veris.mock(mode="function", output_callback=divide_by_2)
    async def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    mock_response = 80  # Mocked return value

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        # Call the function
        result = await add(15, 25)

        # Function returns the mocked value (80, not 40)
        assert result == 80

        # Wait for background task to complete
        await asyncio.sleep(0.01)

        # Side effect divided the mocked result by 2
        assert len(processed_results) == 1
        assert processed_results[0] == 40.0  # 80 / 2


@pytest.mark.asyncio
async def test_mock_side_effect_with_string_operations(simulation_env):
    """Test side effect performing string operations on inputs."""
    formatted_logs = []

    async def log_formatted(**kwargs):
        """Side effect that formats parameters as a log message."""
        log_msg = f"Calling multiply with x={kwargs['x']}, y={kwargs['y']}"
        formatted_logs.append(log_msg)

    @veris.mock(mode="function", input_callback=log_formatted)
    async def multiply(x: int, y: int) -> int:
        return x * y

    mock_response = 42

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await multiply(7, 8)
        assert result == 42
        await asyncio.sleep(0.01)
        assert len(formatted_logs) == 1
        assert formatted_logs[0] == "Calling multiply with x=7, y=8"


@pytest.mark.asyncio
async def test_stub_side_effect_with_complex_computation(simulation_env):
    """Test side effect performing complex computation on both inputs and outputs."""
    metrics = []

    async def record_metrics(**kwargs):
        """Side effect that computes metrics from inputs."""
        total = sum(kwargs["values"])
        avg = total / len(kwargs["values"]) if kwargs["values"] else 0
        metrics.append({"total": total, "avg": avg, "count": len(kwargs["values"])})

    @veris.stub(return_value={"status": "ok"}, input_callback=record_metrics)
    async def process_values(values: list[int]) -> dict:
        return {"result": sum(values)}

    result = await process_values([10, 20, 30, 40])
    assert result == {"status": "ok"}
    await asyncio.sleep(0.01)
    assert len(metrics) == 1
    assert metrics[0]["total"] == 100
    assert metrics[0]["avg"] == 25.0
    assert metrics[0]["count"] == 4


def test_mock_side_effect_end_to_end_with_real_function_signature(simulation_env):
    """Test complete end-to-end flow with realistic function."""
    # Track what the side effect computed
    computed_differences = []

    def compute_difference(**kwargs):
        """Side effect computes difference of inputs."""
        diff = kwargs["a"] - kwargs["b"]
        computed_differences.append(diff)

    @veris.mock(mode="function", input_callback=compute_difference)
    def add_numbers(a: int, b: int) -> int:
        """This function adds two numbers."""
        return a + b

    mock_response = 999

    with patch.object(get_api_client(), "post", return_value=mock_response):
        # Call the decorated function
        result = add_numbers(50, 30)

        # Function returns mocked value (not the real a+b)
        assert result == 999

        # Side effect computed a-b correctly
        assert len(computed_differences) == 1
        assert computed_differences[0] == 20  # 50 - 30


@pytest.mark.asyncio
async def test_mock_side_effects_with_ctx_parameter_operations(simulation_env):
    """Test that side effect can access and use ctx parameter."""
    ctx_metadata = []

    async def extract_metadata(**kwargs):
        """Side effect extracts metadata from ctx."""
        ctx = kwargs.get("ctx", {})
        metadata = {
            "user": ctx.get("user"),
            "session": ctx.get("session"),
            "input_value": kwargs.get("value"),
        }
        ctx_metadata.append(metadata)

    @veris.mock(mode="function", input_callback=extract_metadata)
    async def process_data(value: int, ctx: dict) -> dict:
        return {"result": value * 2}

    mock_response = {"mocked": True}
    context = {"user": "alice", "session": "xyz789"}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await process_data(42, ctx=context)
        assert result == {"mocked": True}
        await asyncio.sleep(0.01)
        assert len(ctx_metadata) == 1
        assert ctx_metadata[0] == {
            "user": "alice",
            "session": "xyz789",
            "input_value": 42,
        }


# Test execution order


@pytest.mark.asyncio
async def test_mock_side_effects_execution_order(simulation_env):
    """Test that side effects execute after mock call as background tasks."""
    execution_order = []

    async def input_effect(**kwargs):
        execution_order.append("input")

    async def output_effect(result: Any):
        execution_order.append("output")

    @veris.mock(mode="function", input_callback=input_effect, output_callback=output_effect)
    async def test_func(x: int) -> dict:
        execution_order.append("original_func")
        return {"x": x}

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await test_func(42)
        assert result == {"mocked": True}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        # In simulation mode, original func is not called, side effects run as background tasks
        assert set(execution_order) == {"input", "output"}
        assert len(execution_order) == 2


@pytest.mark.asyncio
async def test_stub_side_effects_execution_order(simulation_env):
    """Test that side effects execute after stub as background tasks."""
    execution_order = []

    async def input_effect(**kwargs):
        execution_order.append("input")

    async def output_effect(result: Any):
        execution_order.append("output")

    @veris.stub(
        return_value={"stubbed": True},
        input_callback=input_effect,
        output_callback=output_effect,
    )
    async def test_func(x: int) -> dict:
        execution_order.append("original_func")
        return {"x": x}

    result = await test_func(42)
    assert result == {"stubbed": True}
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    # In simulation mode, original func is not called, side effects run as background tasks
    assert set(execution_order) == {"input", "output"}
    assert len(execution_order) == 2


# Test callback signature compatibility


def test_callback_with_subset_of_parameters(simulation_env):
    """Test that callback with fewer parameters than the function works correctly."""
    multiplication_results = []

    def multiply(a: int, b: int, d: int = 4):
        """Callback that only takes a, b, and d (not c)."""
        result = a * b * d
        multiplication_results.append(result)

    @veris.mock(mode="function", input_callback=multiply)
    def add(a: int, b: int, c: int = None, d: int = None) -> int:
        """Function with more parameters than the callback accepts."""
        return a + b

    mock_response = 999

    with patch.object(get_api_client(), "post", return_value=mock_response):
        # Call with all parameters
        result = add(10, 20, c=5, d=2)
        assert result == 999

        # Callback should have been called with only a, b, d (not c)
        assert len(multiplication_results) == 1
        assert multiplication_results[0] == 10 * 20 * 2  # a * b * d = 400


@pytest.mark.asyncio
async def test_async_callback_with_subset_of_parameters(simulation_env):
    """Test that async callback with fewer parameters than the function works correctly."""
    processed_results = []

    async def process_subset(x: int, z: str = "default"):
        """Callback that only takes x and z (not y)."""
        processed_results.append(f"{x}:{z}")

    @veris.mock(mode="function", input_callback=process_subset)
    async def complex_func(x: int, y: float, z: str = "test") -> dict:
        """Function with more parameters than the callback accepts."""
        return {"result": x + y}

    mock_response = {"mocked": True}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        # Call with all parameters
        result = await complex_func(42, 3.14, z="custom")
        assert result == {"mocked": True}

        # Wait for background task
        await asyncio.sleep(0.01)

        # Callback should have been called with only x and z (not y)
        assert len(processed_results) == 1
        assert processed_results[0] == "42:custom"


def test_callback_with_no_matching_parameters(simulation_env):
    """Test that callback with completely different parameters still works with **kwargs."""
    called = []

    def generic_callback(**kwargs):
        """Callback that accepts any parameters."""
        called.append(True)

    @veris.stub(return_value="result", input_callback=generic_callback)
    def some_func(a: int, b: str) -> str:
        return f"{a}:{b}"

    result = some_func(1, "test")
    assert result == "result"
    assert len(called) == 1


# Test combined_callback functionality


@pytest.mark.asyncio
async def test_mock_with_async_combined_callback(simulation_env):
    """Test mock decorator with async combined_callback."""
    captured_results = []

    async def combined_handler(a: int, b: int, d: int = None, mock_output: int = None):
        """Combined callback that uses both inputs and output."""
        # Compute sum of inputs that are not None, then multiply by mock_output
        total_input = a + b + (d if d is not None else 0)
        result = total_input * (mock_output if mock_output is not None else 1)
        captured_results.append(result)

    @veris.mock(mode="function", combined_callback=combined_handler)
    async def add(a: int, b: int, c: int = None, d: int = None) -> int:
        """Add numbers together."""
        return a + b + (c if c is not None else 0) + (d if d is not None else 0)

    mock_response = 6

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await add(1, 2, d=4)
        assert result == 6
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_results) == 1
        # (1 + 2 + 4) * 6 = 42
        assert captured_results[0] == 42


@pytest.mark.asyncio
async def test_mock_with_sync_combined_callback_async_func(simulation_env):
    """Test mock decorator with sync combined_callback on async function."""
    captured_results = []

    def multiply_by_result(a: int, b: int, mock_output: int = None):
        """Multiply inputs by the mock output."""
        result = (a + b) * (mock_output if mock_output is not None else 1)
        captured_results.append(result)

    @veris.mock(mode="function", combined_callback=multiply_by_result)
    async def add(a: int, b: int) -> int:
        return a + b

    mock_response = 10

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await add(3, 7)
        assert result == 10
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_results) == 1
        # (3 + 7) * 10 = 100
        assert captured_results[0] == 100


def test_mock_with_sync_combined_callback_sync_func(simulation_env):
    """Test mock decorator with sync combined_callback on sync function."""
    captured_results = []

    def process_combined(x: int, y: str, mock_output: dict = None):
        """Process both input and output."""
        result = {
            "input_x": x,
            "input_y": y,
            "output": mock_output,
            "combined": f"{y}:{x}:{mock_output.get('value') if mock_output else 'none'}",
        }
        captured_results.append(result)

    @veris.mock(mode="function", combined_callback=process_combined)
    def test_func(x: int, y: str) -> dict:
        return {"value": x}

    mock_response = {"value": 999}

    with patch.object(get_api_client(), "post", return_value=mock_response):
        result = test_func(42, "test")
        assert result == {"value": 999}
        assert len(captured_results) == 1
        assert captured_results[0]["input_x"] == 42
        assert captured_results[0]["input_y"] == "test"
        assert captured_results[0]["output"] == {"value": 999}
        assert captured_results[0]["combined"] == "test:42:999"


@pytest.mark.asyncio
async def test_stub_with_async_combined_callback(simulation_env):
    """Test stub decorator with async combined_callback."""
    captured_results = []

    async def combined_handler(name: str, count: int, mock_output: str = None):
        """Combine input and output."""
        result = f"{name}:{count}:{mock_output}"
        captured_results.append(result)

    @veris.stub(return_value="stubbed_value", combined_callback=combined_handler)
    async def process(name: str, count: int) -> str:
        return f"{name}_{count}"

    result = await process("test", 5)
    assert result == "stubbed_value"
    # Wait for background tasks to complete
    await asyncio.sleep(0.01)
    assert len(captured_results) == 1
    assert captured_results[0] == "test:5:stubbed_value"


def test_stub_with_sync_combined_callback_sync_func(simulation_env):
    """Test stub decorator with sync combined_callback on sync function."""
    captured_results = []

    def multiply_inputs_by_output(a: int, b: int, mock_output: int = None):
        """Multiply sum of inputs by output."""
        result = (a + b) * (mock_output if mock_output is not None else 1)
        captured_results.append(result)

    @veris.stub(return_value=5, combined_callback=multiply_inputs_by_output)
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5
    assert len(captured_results) == 1
    # (2 + 3) * 5 = 25
    assert captured_results[0] == 25


@pytest.mark.asyncio
async def test_combined_callback_with_parameter_filtering(simulation_env):
    """Test that combined callback only receives parameters it accepts."""
    captured_results = []

    async def selective_callback(a: int, mock_output: int = None):
        """Callback that only accepts 'a' and 'mock_output', not 'b' or 'c'."""
        result = a * (mock_output if mock_output is not None else 1)
        captured_results.append(result)

    @veris.mock(mode="function", combined_callback=selective_callback)
    async def complex_func(a: int, b: int, c: str = "default") -> int:
        return a + b

    mock_response = 7

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await complex_func(3, 5, c="ignored")
        assert result == 7
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)
        assert len(captured_results) == 1
        # 3 * 7 = 21 (b and c are filtered out)
        assert captured_results[0] == 21


@pytest.mark.asyncio
async def test_combined_callback_in_production_mode(production_env):
    """Test that combined_callback is not called in production mode."""
    callback_mock = Mock()

    @veris.mock(mode="function", combined_callback=callback_mock)
    async def test_func(x: int) -> int:
        return x * 2

    result = await test_func(21)
    assert result == 42

    # Combined callback should NOT have been called
    callback_mock.assert_not_called()


@pytest.mark.asyncio
async def test_combined_callback_exception_is_logged(simulation_env):
    """Test that exceptions in combined callback are caught and logged."""

    async def failing_combined_callback(x: int, mock_output: int = None):
        raise ValueError("Combined callback error")

    @veris.mock(mode="function", combined_callback=failing_combined_callback)
    async def test_func(x: int) -> int:
        return x * 2

    mock_response = 100

    with (
        patch.object(get_api_client(), "post_async", return_value=mock_response),
        patch("veris_ai.utils.logger.warning") as mock_logger,
    ):
        # Function should still work despite combined callback failure
        result = await test_func(42)
        assert result == 100

        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # Error should have been logged
        mock_logger.assert_called()
        assert "Combined callback execution failed" in str(mock_logger.call_args)


@pytest.mark.asyncio
async def test_mock_with_all_three_callbacks(simulation_env):
    """Test mock decorator with input, output, and combined callbacks."""
    captured_inputs = []
    captured_outputs = []
    captured_combined = []

    async def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    async def capture_output(result: int):
        captured_outputs.append(result)

    async def capture_combined(a: int, b: int, mock_output: int = None):
        combined = {"sum": a + b, "product": a * b, "mock": mock_output}
        captured_combined.append(combined)

    @veris.mock(
        mode="function",
        input_callback=capture_input,
        output_callback=capture_output,
        combined_callback=capture_combined,
    )
    async def add(a: int, b: int) -> int:
        return a + b

    mock_response = 50

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await add(10, 20)
        assert result == 50
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        # All callbacks should have been called
        assert len(captured_inputs) == 1
        assert captured_inputs[0] == {"a": 10, "b": 20}

        assert len(captured_outputs) == 1
        assert captured_outputs[0] == 50

        assert len(captured_combined) == 1
        assert captured_combined[0] == {"sum": 30, "product": 200, "mock": 50}


def test_stub_with_all_three_callbacks(simulation_env):
    """Test stub decorator with input, output, and combined callbacks."""
    captured_inputs = []
    captured_outputs = []
    captured_combined = []

    def capture_input(**kwargs):
        captured_inputs.append(kwargs)

    def capture_output(result: str):
        captured_outputs.append(result)

    def capture_combined(name: str, value: int, mock_output: str = None):
        combined = f"{name}_{value}_{mock_output}"
        captured_combined.append(combined)

    @veris.stub(
        return_value="stubbed",
        input_callback=capture_input,
        output_callback=capture_output,
        combined_callback=capture_combined,
    )
    def process(name: str, value: int) -> str:
        return f"{name}:{value}"

    result = process("test", 42)
    assert result == "stubbed"

    # All callbacks should have been called
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == {"name": "test", "value": 42}

    assert len(captured_outputs) == 1
    assert captured_outputs[0] == "stubbed"

    assert len(captured_combined) == 1
    assert captured_combined[0] == "test_42_stubbed"


@pytest.mark.asyncio
async def test_combined_callback_with_kwargs_accepts_all(simulation_env):
    """Test combined callback with **kwargs accepts all parameters including mock_output."""
    captured_data = []

    async def flexible_callback(**kwargs):
        """Callback that accepts any parameters via **kwargs."""
        captured_data.append(kwargs)

    @veris.mock(mode="function", combined_callback=flexible_callback)
    async def multi_param_func(a: int, b: str, c: float = 3.14) -> dict:
        return {"result": a}

    mock_response = {"result": 999}

    with patch.object(get_api_client(), "post_async", return_value=mock_response):
        result = await multi_param_func(10, "test", c=2.71)
        assert result == {"result": 999}
        # Wait for background tasks to complete
        await asyncio.sleep(0.01)

        assert len(captured_data) == 1
        # Should have all input params plus mock_output
        assert captured_data[0]["a"] == 10
        assert captured_data[0]["b"] == "test"
        assert captured_data[0]["c"] == 2.71
        assert captured_data[0]["mock_output"] == {"result": 999}


def test_combined_callback_user_example(simulation_env):
    """Test the exact example from the user: add function with multiply_by_result."""
    multiplication_results = []

    def multiply_by_result(a: int, b: int, d: int = None, mock_output: int = None):
        """Multiply sum of provided inputs by the mock output."""
        # Sum the inputs that are not None
        input_sum = a + b + (d if d is not None else 0)
        # Multiply by mock output
        result = input_sum * (mock_output if mock_output is not None else 1)
        multiplication_results.append(result)

    @veris.mock(mode="function", combined_callback=multiply_by_result)
    def add(a: int, b: int, c: int = None, d: int = None) -> int:
        """Add numbers together."""
        total = a + b
        if c is not None:
            total += c
        if d is not None:
            total += d
        return total

    # Mock the API to return 6 as the result
    mock_response = 6

    with patch.object(get_api_client(), "post", return_value=mock_response):
        # Call add(1, 2, d=4)
        # Expected: inputs are 1, 2, 4 (c is None)
        # Mock returns 6
        # Combined callback should compute: (1 + 2 + 4) * 6 = 42
        result = add(1, 2, d=4)

        # The function returns the mocked value
        assert result == 6

        # The combined callback computed (1+2+4)*6
        assert len(multiplication_results) == 1
        assert multiplication_results[0] == 42
