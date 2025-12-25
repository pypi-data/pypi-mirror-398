"""Test the _extract_the_func functionality in agents_wrapper."""

import pytest

pytest.importorskip("agents")  # Skip if agents not installed

from agents import function_tool

from veris_ai.agents_wrapper import _extract_the_func, _find_user_function_in_closure


def test_extract_simple_function():
    """Test extracting a simple user function from FunctionTool."""

    def my_function(x: int, y: int) -> int:
        """Simple test function."""
        return x + y

    tool = function_tool(my_function)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    assert extracted is my_function
    assert extracted.__name__ == "my_function"
    assert extracted(2, 3) == 5


def test_extract_async_function():
    """Test extracting an async function from FunctionTool."""

    async def my_async_function(text: str) -> str:
        """Async test function."""
        return f"processed: {text}"

    tool = function_tool(my_async_function)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    assert extracted is my_async_function
    assert extracted.__name__ == "my_async_function"


def test_extract_function_with_context():
    """Test extracting a function that takes a context parameter."""
    from agents import RunContextWrapper

    def my_context_function(ctx: RunContextWrapper, value: int) -> int:
        """Function with context."""
        return value * 2

    tool = function_tool(my_context_function)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    assert extracted is my_context_function
    assert extracted.__name__ == "my_context_function"


def test_extract_lambda_function():
    """Test extracting a lambda function (edge case)."""
    # Lambda functions might behave differently
    lambda_func = lambda x, y: x + y  # noqa: E731
    tool = function_tool(lambda_func)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    assert extracted is lambda_func
    # Lambda functions have a generic name
    assert extracted(3, 4) == 7


@pytest.mark.skip(reason="Agents library has issues with decorated functions and strict schema")
def test_extract_decorated_function():
    """Test extracting a decorated function."""

    def my_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @my_decorator
    def decorated_function(x: int) -> int:
        """Decorated function."""
        return x * 2

    tool = function_tool(decorated_function)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    # Might be the wrapper or the original depending on decorator
    assert callable(extracted)
    assert extracted(5) == 10


def test_find_user_function_filters_library_code():
    """Test that _find_user_function_in_closure filters out library code."""
    import json

    # Create a closure with both user and library functions
    def user_func():
        return "user"

    library_func = json.loads  # A library function

    closure = []
    for func in [user_func, library_func]:
        # Create a closure cell-like structure
        # In reality, this is done by the Python interpreter
        # but for testing we simulate it
        class Cell:
            def __init__(self, contents):
                self.cell_contents = contents

        closure.append(Cell(func))

    # Convert to tuple to match closure structure
    closure = tuple(closure)

    result = _find_user_function_in_closure(closure)

    # Should find user_func, not json.loads
    assert result is user_func


def test_extract_returns_none_for_invalid_input():
    """Test that _extract_the_func returns None for invalid input."""

    def regular_function():
        pass

    # Not a FunctionTool's on_invoke_tool
    result = _extract_the_func(regular_function)
    assert result is None

    # None input
    result = _extract_the_func(None)
    assert result is None


def test_extract_handles_complex_closures():
    """Test extraction with nested closures."""

    def outer():
        outer_var = 10

        def middle():
            middle_var = 20

            def inner(x: int) -> int:
                return x + outer_var + middle_var

            return inner

        return middle()

    complex_func = outer()
    tool = function_tool(complex_func)
    extracted = _extract_the_func(tool.on_invoke_tool)

    assert extracted is not None
    assert extracted is complex_func
    assert extracted(5) == 35  # 5 + 10 + 20
