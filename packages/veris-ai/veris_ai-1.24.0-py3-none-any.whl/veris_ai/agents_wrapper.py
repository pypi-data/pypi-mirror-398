"""OpenAI Agents wrapper for automatic tool mocking via Veris SDK."""

import inspect
import json
import logging
from collections.abc import Callable
from typing import Any

from agents import RunContextWrapper, RunResult, Runner as OpenAIRunner
from pydantic import BaseModel

from veris_ai import veris
from veris_ai.tool_mock import mock_tool_call, mock_tool_call_async
from veris_ai.models import ToolCallOptions

logger = logging.getLogger(__name__)


def _wrap(
    include_tools: list[str] | None = None,
    exclude_tools: list[str] | None = None,
    tool_options: dict[str, ToolCallOptions] | None = None,
) -> Callable:
    """Private wrapper for OpenAI agents Runner to intercept tool calls through Veris SDK.

    This function transparently intercepts tool calls from OpenAI agents and
    routes them through the Veris SDK's mocking infrastructure.

    Args:
        include_tools: Optional list of tool names to intercept (only these if provided)
        exclude_tools: Optional list of tool names to NOT intercept (these run normally)
        tool_options: Optional per-tool configuration for mocking behavior

    Returns:
        A wrapped Runner.run function

    Raises:
        ValueError: If both include_tools and exclude_tools are specified
        ImportError: If agents package is not installed
    """
    if include_tools and exclude_tools:
        msg = "Cannot specify both include_tools and exclude_tools"
        raise ValueError(msg)
    if not tool_options:
        tool_options = {}

    def wrapped_run_func(run_func: Callable) -> Callable:
        """Inner wrapper that takes the actual Runner.run function."""
        try:
            from agents import FunctionTool  # type: ignore[import-untyped] # noqa: PLC0415
        except ImportError as e:
            msg = "openai-agents package not installed. Install with: pip install veris-ai[agents]"
            raise ImportError(msg) from e

        async def wrapped_run(starting_agent: Any, input_text: str, **kwargs: Any) -> Any:  # noqa: ANN401
            """Wrapped version of Runner.run that intercepts tool calls."""
            # Store a mapping of tools to their original functions
            tool_functions = {}

            if hasattr(starting_agent, "tools") and starting_agent.tools:
                for tool in starting_agent.tools:
                    if isinstance(tool, FunctionTool):
                        tool_name = getattr(tool, "name", None)

                        # Check if we should patch this tool
                        if tool_name and _should_intercept_tool(
                            tool_name, include_tools, exclude_tools
                        ):
                            # Extract the original function before patching
                            original_func = _extract_the_func(tool.on_invoke_tool)
                            if original_func:
                                tool_functions[id(tool)] = original_func

                            # Store original on_invoke_tool
                            original_on_invoke = tool.on_invoke_tool

                            def make_wrapped_on_invoke_tool(
                                tool_id: int, orig_invoke: Callable, tool_name_inner: str
                            ) -> Callable:
                                """Create a wrapped on_invoke_tool with proper closure."""

                                async def wrapped_on_invoke_tool(
                                    ctx: RunContextWrapper[Any], parameters: str
                                ) -> Any:  # noqa: ANN401
                                    """Wrapped on_invoke_tool that intercepts the tool function."""
                                    session_id = veris.session_id
                                    thread_id = veris.thread_id
                                    the_func = tool_functions.get(tool_id)
                                    if the_func and session_id:
                                        # Check if async or sync, call appropriate version
                                        if inspect.iscoroutinefunction(the_func):
                                            # Use async version (non-blocking)
                                            return await mock_tool_call_async(
                                                the_func,
                                                session_id,
                                                json.loads(parameters),
                                                tool_options.get(tool_name_inner),
                                                thread_id=thread_id,
                                            )
                                        # Use sync version for sync functions
                                        return mock_tool_call(
                                            the_func,
                                            session_id,
                                            json.loads(parameters),
                                            tool_options.get(tool_name_inner),
                                            thread_id=thread_id,
                                        )
                                    # Fall back to original if we couldn't extract the function
                                    return await orig_invoke(ctx, parameters)

                                return wrapped_on_invoke_tool

                            tool.on_invoke_tool = make_wrapped_on_invoke_tool(
                                id(tool), original_on_invoke, tool_name
                            )
            return await run_func(starting_agent, input_text, **kwargs)

        return wrapped_run

    return wrapped_run_func


def _should_intercept_tool(
    tool_name: str,
    include_tools: list[str] | None,
    exclude_tools: list[str] | None,
) -> bool:
    """Determine if a tool should be intercepted based on include/exclude lists.

    Args:
        tool_name: Name of the tool
        include_tools: If provided, only these tools are intercepted
        exclude_tools: If provided, these tools are NOT intercepted

    Returns:
        True if the tool should be intercepted, False otherwise
    """
    if include_tools:
        return tool_name in include_tools
    if exclude_tools:
        return tool_name not in exclude_tools
    return True


def _extract_the_func(on_invoke_tool: Callable) -> Callable | None:
    """Extract the original user function from the on_invoke_tool closure.

    This function attempts multiple strategies to extract the original function:
    1. Direct attribute access (if the tool stores it)
    2. Closure inspection for known patterns
    3. Deep closure traversal as a fallback

    Args:
        on_invoke_tool: The on_invoke_tool function from FunctionTool

    Returns:
        The original user function if found, None otherwise
    """

    # Strategy 1: Check if the tool has stored the original function as an attribute
    # (This would be the cleanest approach if the agents library supported it)
    if hasattr(on_invoke_tool, "__wrapped__"):
        return on_invoke_tool.__wrapped__

    # Strategy 2: Look for the function in the closure using known structure
    # Based on the agents library implementation, we know:
    # - on_invoke_tool has _on_invoke_tool_impl in its closure
    # - _on_invoke_tool_impl has the_func in its closure

    if not hasattr(on_invoke_tool, "__closure__") or not on_invoke_tool.__closure__:
        return None

    # Find _on_invoke_tool_impl by looking for a function with that name pattern
    for cell in on_invoke_tool.__closure__:
        try:
            obj = cell.cell_contents
            if not callable(obj):
                continue

            # Check if this looks like _on_invoke_tool_impl
            if (
                hasattr(obj, "__name__")
                and "_on_invoke_tool_impl" in obj.__name__
                and hasattr(obj, "__closure__")
                and obj.__closure__
            ):
                # Now look for the_func in its closure
                return _find_user_function_in_closure(obj.__closure__)
        except (ValueError, AttributeError):
            continue

    # Strategy 3: Fallback - do a broader search in the closure
    return _find_user_function_in_closure(on_invoke_tool.__closure__)


def _find_user_function_in_closure(closure: tuple) -> Callable | None:
    """Find the user function in a closure by filtering out known library functions.

    Args:
        closure: The closure tuple to search

    Returns:
        The user function if found, None otherwise
    """
    # List of module prefixes that indicate library/framework code
    library_modules = ("json", "inspect", "agents", "pydantic", "openai", "typing")

    for cell in closure:
        try:
            obj = cell.cell_contents

            # Must be callable but not a class
            if not callable(obj) or isinstance(obj, type):
                continue

            # Skip private/internal functions
            if hasattr(obj, "__name__") and obj.__name__.startswith("_"):
                continue

            # Check the module to filter out library code
            module = inspect.getmodule(obj)
            if module:
                # Skip if it's from a known library
                if module.__name__.startswith(library_modules):
                    continue

                # Skip if it's from site-packages (library code)
                if (
                    hasattr(module, "__file__")
                    and module.__file__
                    and "site-packages" in module.__file__
                    # Unless it's user code installed as a package
                    # (this is a heuristic - may need adjustment)
                    and not any(pkg in module.__name__ for pkg in ["my_", "custom_", "app_"])
                ):
                    continue

            # If we made it here, this is likely the user function
            return obj

        except (ValueError, AttributeError):
            continue

    return None


class VerisConfig(BaseModel):
    """Configuration for the Veris SDK Runner.

    Attributes:
        include_tools: Optional list of tool names to intercept (only these if provided)
        exclude_tools: Optional list of tool names to NOT intercept (these run normally)
        tool_options: Optional per-tool configuration for mocking behavior
    """

    include_tools: list[str] | None = None
    exclude_tools: list[str] | None = None
    tool_options: dict[str, ToolCallOptions] | None = None


class Runner(OpenAIRunner):
    """Veris-enhanced Runner that extends OpenAI's Runner with tool interception.

    This class extends the OpenAI agents Runner to intercept tool calls
    and route them through the Veris SDK's mocking infrastructure.

    Example:
        ```python
        from veris_ai import Runner, VerisConfig
        from agents import Agent, FunctionTool

        # Define your agent with tools
        agent = Agent(...)

        # Use Veris Runner instead of OpenAI Runner
        result = await Runner.run(agent, "Process this input")

        # Or with configuration
        config = VerisConfig(include_tools=["calculator", "search"])
        result = await Runner.run(agent, "Calculate 2+2", veris_config=config)
        ```
    """

    @classmethod
    async def run(
        cls,
        starting_agent: Any,  # noqa: ANN401
        input: Any,  # noqa: ANN401, A002
        veris_config: VerisConfig | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> RunResult:  # noqa: ANN401
        """Run an agent with Veris tool interception.

        This method overrides the OpenAI Runner.run to apply tool interception
        based on the provided configuration.

        Args:
            starting_agent: The OpenAI agent to run
            input: The input text/messages to process
            veris_config: Optional configuration for tool interception
            **kwargs: Additional arguments to pass to the base Runner.run

        Returns:
            The result from the agent execution
        """
        # Use provided config or create default
        config = veris_config or VerisConfig()

        # Validate configuration
        if config.include_tools and config.exclude_tools:
            msg = "Cannot specify both include_tools and exclude_tools"
            raise ValueError(msg)

        # Apply the wrapping logic
        wrapped_run = _wrap(
            include_tools=config.include_tools,
            exclude_tools=config.exclude_tools,
            tool_options=config.tool_options or {},
        )(OpenAIRunner.run)

        # Execute the wrapped run function
        return await wrapped_run(starting_agent, input, **kwargs)
