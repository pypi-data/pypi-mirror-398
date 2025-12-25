import inspect
import json
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager, suppress
from functools import wraps
from fastapi import HTTPException
import tenacity
from typing import (
    Any,
    Literal,
    TypeVar,
    get_type_hints,
)


from veris_ai.models import ResponseExpectation, SimulationConfig, ToolCallOptions
from veris_ai.api_client import _base_url_context, get_api_client
from veris_ai.context_vars import (
    _config_context,
    _logfire_token_context,
    _session_id_context,
    _target_context,
    _thread_id_context,
)
from veris_ai.jwt_utils import JWTClaims, decode_token
from veris_ai.utils import (
    convert_to_type,
    execute_callback,
    execute_combined_callback,
    extract_json_schema,
    get_function_parameters,
    get_input_parameters,
    get_self_from_args,
    launch_callback_task,
    launch_combined_callback_task,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class VerisSDK:
    """Class for mocking tool calls."""

    def __init__(self) -> None:
        """Initialize the ToolMock class."""
        self._mcp = None

    @property
    def session_id(self) -> str | None:
        """Get the session_id from context variable."""
        return _session_id_context.get()

    @property
    def thread_id(self) -> str | None:
        """Get the thread_id from context variable."""
        return _thread_id_context.get()

    @property
    def config(self) -> SimulationConfig:
        """Get the simulation config from context variable."""
        return _config_context.get() or SimulationConfig()

    @property
    def api_url(self) -> str | None:
        """Get the api_url from context variable."""
        return _base_url_context.get()

    @property
    def logfire_token(self) -> str | None:
        """Get the logfire_token from context variable."""
        return _logfire_token_context.get()

    def set_session_id(self, session_id: str) -> None:
        """Set the session_id in context variable.

        Args:
            session_id: The session ID to set.
        """
        _session_id_context.set(session_id)
        logger.info(f"Session ID set to {session_id}")

    def set_thread_id(self, thread_id: str) -> None:
        """Set the thread_id in context variable.

        Args:
            thread_id: The thread ID to set.
        """
        _thread_id_context.set(thread_id)
        logger.info(f"Thread ID set to {thread_id}")

    def set_api_url(self, api_url: str) -> None:
        """Set the API URL in context variable.

        Args:
            api_url: The API URL to set.
        """
        _base_url_context.set(api_url)
        logger.info(f"API URL set to {api_url}")

    def set_logfire_token(self, logfire_token: str) -> None:
        """Set the Logfire token in context variable.

        Args:
            logfire_token: The Logfire token to set.
        """
        _logfire_token_context.set(logfire_token)
        logger.info("Logfire token set")

    def parse_token(
        self,
        token: str,
        *,
        verify_signature: bool = True,
        audience: str | None = None,
    ) -> JWTClaims:
        """Parse and set session context from a JWT or base64-encoded token.

        This method handles both JWT tokens (RS256 signed) and legacy base64-encoded
        JSON tokens. For JWTs, the signature is verified by default using JWKS from
        the token's issuer claim (/.well-known/jwks.json).

        Args:
            token: JWT or base64-encoded JSON token.
            verify_signature: Whether to verify JWT signature (default True).
                Set to False to skip verification (useful for testing or when
                you trust the token source).
            audience: Optional expected audience claim. If provided, the token's `aud`
                claim will be validated against this value. If None (default), audience
                verification is skipped.

        Returns:
            The parsed JWT claims.

        Raises:
            ValueError: If token is invalid, verification fails, or required
                fields are missing.
        """
        claims = decode_token(
            token,
            verify_signature=verify_signature,
            audience=audience,
        )

        # Set context variables from claims
        if claims.session_id is not None:
            _session_id_context.set(claims.session_id)
        if claims.thread_id is not None:
            _thread_id_context.set(claims.thread_id)
        if claims.api_url is not None:
            _base_url_context.set(claims.api_url)
        if claims.logfire_token is not None:
            _logfire_token_context.set(claims.logfire_token)

        logger.info(
            f"Session ID set to {claims.session_id}, "
            f"Thread ID set to {claims.thread_id} - mocking enabled"
        )
        return claims

    def clear_context(self) -> None:
        """Clear all session context variables."""
        _session_id_context.set(None)
        _thread_id_context.set(None)
        _base_url_context.set(None)
        _logfire_token_context.set(None)
        _target_context.set(None)
        logger.info("Session context cleared - mocking disabled")

    def _process_config_response(self, response: dict) -> None:
        """Process and store config response."""
        config = SimulationConfig(**response)
        _config_context.set(config)
        logger.info("Simulation config fetched successfully")

    def fetch_simulation_config(self, token: str) -> None:
        """Fetch simulation config from the simulator.

        Args:
            token: The base64 token to authenticate the request
        """
        if not self.session_id:
            logger.warning("Cannot fetch simulation config: session_id is not set")
            _config_context.set(SimulationConfig())
            return

        api_client = get_api_client()
        endpoint = api_client.get_simulation_config_endpoint(self.session_id)
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = api_client.get(endpoint, headers=headers)
            self._process_config_response(response)
        except Exception as e:
            logger.warning(f"Failed to fetch simulation config: {e}")

    async def fetch_simulation_config_async(self, token: str) -> None:
        """Fetch simulation config from the simulator asynchronously.

        Args:
            token: The base64 token to authenticate the request
        """
        if not self.session_id:
            logger.warning("Cannot fetch simulation config: session_id is not set")
            _config_context.set(SimulationConfig())
            return

        api_client = get_api_client()
        endpoint = api_client.get_simulation_config_endpoint(self.session_id)
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = await api_client.get_async(endpoint, headers=headers)
            self._process_config_response(response)
        except Exception as e:
            logger.warning(f"Failed to fetch simulation config: {e}")

    @property
    def fastapi_mcp(self) -> Any | None:  # noqa: ANN401
        """Get the FastAPI MCP server."""
        return self._mcp

    def set_fastapi_mcp(
        self,
        *,
        verify_jwt_signature: bool = False,
        jwt_audience: str | None = None,
        **params_dict: Any,  # noqa: ANN401
    ) -> None:
        """Set the FastAPI MCP server with HTTP transport.

        Args:
            verify_jwt_signature: Whether to verify JWT signatures using JWKS
                (default True). Set to False for testing or when you trust
                the token source. JWKS URL is derived from the JWT's iss claim.
            jwt_audience: Optional expected audience claim. If provided, the token's
                `aud` claim will be validated against this value. If None (default),
                audience verification is skipped.
            **params_dict: Additional parameters passed to FastApiMCP.
        """
        from fastapi import Depends, Request  # noqa: PLC0415
        from fastapi.security import OAuth2PasswordBearer  # noqa: PLC0415
        from fastapi_mcp import (  # type: ignore[import-untyped] # noqa: PLC0415
            AuthConfig,
            FastApiMCP,
        )
        from veris_ai.logfire_config import configure_logfire_conditionally

        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

        async def authenticate_request(
            request: Request,  # noqa: ARG001
            token: str | None = Depends(oauth2_scheme),
        ) -> None:
            if token:
                self.parse_token(
                    token,
                    verify_signature=verify_jwt_signature,
                    audience=jwt_audience,
                )
                await self.fetch_simulation_config_async(token)
                configure_logfire_conditionally()
            else:
                # will only be cleared in the event of a missing token
                self.clear_context()
                raise HTTPException(status_code=401, detail="Unauthorized")

        auth_config = AuthConfig(dependencies=[Depends(authenticate_request)])

        if "auth_config" in params_dict:
            provided_auth_config = params_dict.pop("auth_config")
            if provided_auth_config.dependencies:
                auth_config.dependencies.extend(provided_auth_config.dependencies)
            for field, value in provided_auth_config.model_dump(exclude_none=True).items():
                if field != "dependencies" and hasattr(auth_config, field):
                    setattr(auth_config, field, value)

        self._mcp = FastApiMCP(auth_config=auth_config, **params_dict)

    def spy(self) -> Callable:
        """Decorator for spying on tool calls."""

        def decorator(func: Callable) -> Callable:
            """Decorator for spying on tool calls."""
            is_async = inspect.iscoroutinefunction(func)

            @wraps(func)
            async def async_wrapper(*args: tuple[object, ...], **kwargs: Any) -> object:  # noqa: ANN401
                """Async wrapper."""
                session_id = _session_id_context.get()
                if not session_id:
                    return await func(*args, **kwargs)
                parameters = get_function_parameters(func, args, kwargs)
                logger.info(f"Spying on function: {func.__name__}")
                await log_tool_call_async(
                    session_id=session_id,
                    function_name=func.__name__,
                    parameters=parameters,
                    docstring=inspect.getdoc(func) or "",
                )
                result = await func(*args, **kwargs)
                await log_tool_response_async(session_id=session_id, response=result)
                return result

            @wraps(func)
            def sync_wrapper(*args: tuple[object, ...], **kwargs: Any) -> object:  # noqa: ANN401
                """Sync wrapper."""
                session_id = _session_id_context.get()
                if not session_id:
                    return func(*args, **kwargs)
                parameters = get_function_parameters(func, args, kwargs)
                logger.info(f"Spying on function: {func.__name__}")
                log_tool_call(
                    session_id=session_id,
                    function_name=func.__name__,
                    parameters=parameters,
                    docstring=inspect.getdoc(func) or "",
                )
                result = func(*args, **kwargs)
                log_tool_response(session_id=session_id, response=result)
                return result

            return async_wrapper if is_async else sync_wrapper

        return decorator

    def target(self, target_name: str | None = None) -> Callable:
        """Decorator that sets target context variable for the wrapped function.

        Only sets target when session_id is present (simulation mode), following
        the same conditional pattern as the logfire configuration.

        Args:
            target_name: Optional name for the target. If not provided, uses function name.

        Returns:
            A decorator that wraps the function and sets target context variable.
        """

        def decorator(func: Callable) -> Callable:
            """Decorator that sets target context variable for the function."""
            is_async = inspect.iscoroutinefunction(func)
            target_value = target_name or func.__name__

            @wraps(func)
            async def async_wrapper(*args: tuple[object, ...], **kwargs: Any) -> object:  # noqa: ANN401
                """Async wrapper with target context."""
                session_id = _session_id_context.get()
                if not session_id:
                    # No session_id means production mode - don't set target
                    return await func(*args, **kwargs)

                # Set target in context variable
                token = _target_context.set(target_value)
                try:
                    return await func(*args, **kwargs)
                finally:
                    # Restore previous context
                    _target_context.reset(token)

            @wraps(func)
            def sync_wrapper(*args: tuple[object, ...], **kwargs: Any) -> object:  # noqa: ANN401
                """Sync wrapper with target context."""
                session_id = _session_id_context.get()
                if not session_id:
                    # No session_id means production mode - don't set target
                    return func(*args, **kwargs)

                # Set target in context variable
                token = _target_context.set(target_value)
                try:
                    return func(*args, **kwargs)
                finally:
                    # Restore previous context
                    _target_context.reset(token)

            return async_wrapper if is_async else sync_wrapper

        return decorator

    @contextmanager
    def target_context(self, target_name: str) -> Any:  # noqa: ANN401
        """Context manager that sets target context variable for the duration of the context.

        Only sets target when session_id is present (simulation mode), following
        the same conditional pattern as the logfire configuration.

        Args:
            target_name: Name for the target.

        Yields:
            None - the context manager doesn't yield a value, just sets target context.

        Example:
            ```python
            with veris.target_context("my_target"):
                # All spans created here will have veris_ai.target=my_target attribute
                result = some_function()
            ```
        """
        session_id = _session_id_context.get()
        if not session_id:
            # No session_id means production mode - don't set target
            yield
            return

        # Set target in context variable
        token = _target_context.set(target_name)
        try:
            yield
        finally:
            # Restore previous context
            _target_context.reset(token)

    @asynccontextmanager
    async def target_context_async(self, target_name: str) -> Any:  # noqa: ANN401
        """Async context manager that sets target context variable for the duration of the context.

        Only sets target when session_id is present (simulation mode), following
        the same conditional pattern as the logfire configuration.

        Args:
            target_name: Name for the target.

        Yields:
            None - the context manager doesn't yield a value, just sets target context.

        Example:
            ```python
            async with veris.target_context_async("my_target"):
                # All spans created here will have veris_ai.target=my_target attribute
                result = await some_function()
            ```
        """
        session_id = _session_id_context.get()
        if not session_id:
            # No session_id means production mode - don't set target
            yield
            return

        # Set target in context variable
        token = _target_context.set(target_name)
        try:
            yield
        finally:
            # Restore previous context
            _target_context.reset(token)

    def mock(  # noqa: C901, PLR0915, PLR0913
        self,
        mode: Literal["tool", "function"] = "tool",
        expects_response: bool | None = None,
        cache_response: bool | None = None,
        input_callback: Callable[..., Any] | None = None,
        output_callback: Callable[[Any], Any] | None = None,
        combined_callback: Callable[..., Any] | None = None,
    ) -> Callable:
        """Decorator for mocking tool calls.

        Args:
            mode: Whether to treat the function as a tool or function
            expects_response: Whether the function expects a response
            cache_response: Whether to cache the response
            input_callback: Callable that receives input parameters as individual arguments
            output_callback: Callable that receives the output value
            combined_callback: Callable that receives both input parameters and mock_output
        """
        response_expectation = (
            ResponseExpectation.NONE
            if (expects_response is False or (expects_response is None and mode == "function"))
            else ResponseExpectation.REQUIRED
            if expects_response is True
            else ResponseExpectation.AUTO
        )
        cache_response = cache_response or False
        options = ToolCallOptions(
            mode=mode, response_expectation=response_expectation, cache_response=cache_response
        )

        def decorator(func: Callable) -> Callable:  # noqa: C901, PLR0915
            """Decorator for mocking tool calls."""
            is_async = inspect.iscoroutinefunction(func)

            @wraps(func)
            async def async_wrapper(
                *args: tuple[object, ...],
                **kwargs: Any,  # noqa: ANN401
            ) -> object:
                """Async wrapper."""
                session_id = _session_id_context.get()
                if not session_id:
                    logger.info(
                        f"No session ID found, executing original function: {func.__name__}"
                    )
                    return await func(*args, **kwargs)

                # Perform the mock call first
                parameters = get_function_parameters(func, args, kwargs)
                thread_id = _thread_id_context.get()
                result = await mock_tool_call_async(
                    func,
                    session_id,
                    parameters,
                    options,
                    thread_id,
                )

                # Launch callbacks as background tasks (non-blocking)
                input_params = get_input_parameters(func, args, kwargs)
                instance = get_self_from_args(func, args, kwargs)
                launch_callback_task(input_callback, input_params, unpack=True, instance=instance)
                launch_callback_task(output_callback, result, unpack=False, instance=instance)
                launch_combined_callback_task(
                    combined_callback, input_params, result, instance=instance
                )

                return result

            @wraps(func)
            def sync_wrapper(
                *args: tuple[object, ...],
                **kwargs: Any,  # noqa: ANN401
            ) -> object:
                """Sync wrapper."""
                session_id = _session_id_context.get()
                if not session_id:
                    logger.info(
                        f"No session ID found, executing original function: {func.__name__}"
                    )
                    return func(*args, **kwargs)

                # Perform the mock call first
                parameters = get_function_parameters(func, args, kwargs)
                thread_id = _thread_id_context.get()
                result = mock_tool_call(
                    func,
                    session_id,
                    parameters,
                    options,
                    thread_id,
                )

                # Execute callbacks synchronously (can't use async tasks in sync context)
                input_params = get_input_parameters(func, args, kwargs)
                instance = get_self_from_args(func, args, kwargs)
                execute_callback(input_callback, input_params, unpack=True, instance=instance)
                execute_callback(output_callback, result, unpack=False, instance=instance)
                execute_combined_callback(
                    combined_callback, input_params, result, instance=instance
                )

                return result

            # Return the appropriate wrapper based on whether the function is async
            return async_wrapper if is_async else sync_wrapper

        return decorator

    def stub(
        self,
        return_value: Any,  # noqa: ANN401
        input_callback: Callable[..., Any] | None = None,
        output_callback: Callable[[Any], Any] | None = None,
        combined_callback: Callable[..., Any] | None = None,
    ) -> Callable:
        """Decorator for stubbing tool calls.

        Args:
            return_value: The value to return when the function is stubbed
            input_callback: Callable that receives input parameters as individual arguments
            output_callback: Callable that receives the output value
            combined_callback: Callable that receives both input parameters and mock_output
        """

        def decorator(func: Callable) -> Callable:
            # Check if the original function is async
            is_async = inspect.iscoroutinefunction(func)

            @wraps(func)
            async def async_wrapper(
                *args: tuple[object, ...],
                **kwargs: Any,  # noqa: ANN401
            ) -> object:
                if not self.session_id:
                    logger.info(
                        f"No session ID found, executing original function: {func.__name__}"
                    )
                    return await func(*args, **kwargs)

                logger.info(f"Stubbing function: {func.__name__}")

                # Launch callbacks as background tasks (non-blocking)
                input_params = get_input_parameters(func, args, kwargs)
                instance = get_self_from_args(func, args, kwargs)
                launch_callback_task(input_callback, input_params, unpack=True, instance=instance)
                launch_callback_task(output_callback, return_value, unpack=False, instance=instance)
                launch_combined_callback_task(
                    combined_callback, input_params, return_value, instance=instance
                )

                return return_value

            @wraps(func)
            def sync_wrapper(*args: tuple[object, ...], **kwargs: Any) -> object:  # noqa: ANN401
                if not self.session_id:
                    logger.info(
                        f"No session ID found, executing original function: {func.__name__}"
                    )
                    return func(*args, **kwargs)

                logger.info(f"Stubbing function: {func.__name__}")

                # Execute callbacks synchronously (can't use async tasks in sync context)
                input_params = get_input_parameters(func, args, kwargs)
                instance = get_self_from_args(func, args, kwargs)
                execute_callback(input_callback, input_params, unpack=True, instance=instance)
                execute_callback(output_callback, return_value, unpack=False, instance=instance)
                execute_combined_callback(
                    combined_callback, input_params, return_value, instance=instance
                )

                return return_value

            # Return the appropriate wrapper based on whether the function is async
            return async_wrapper if is_async else sync_wrapper

        return decorator


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
def mock_tool_call(
    func: Callable,
    session_id: str,  # noqa: ARG001
    parameters: dict[str, dict[str, str]],
    options: ToolCallOptions | None = None,
    thread_id: str | None = None,
) -> object:
    """Mock tool call (synchronous).

    Args:
        func: Function being mocked
        session_id: Session ID (kept for backwards compatibility, not used)
        parameters: Function parameters
        options: Tool call options
        thread_id: Thread ID to use as session_id in API request (required)

    Raises:
        ValueError: If thread_id is not provided
    """
    if thread_id is None:
        raise ValueError(
            "thread_id is required for mocking. "
            "Use parse_token() to set both session_id and thread_id."
        )

    options = options or ToolCallOptions()
    api_client = get_api_client()
    endpoint = api_client.tool_mock_endpoint

    logger.info(f"Simulating function: {func.__name__}")

    type_hints = get_type_hints(func)

    # Extract return type object (not just the name)
    return_type_obj = type_hints.pop("return", Any)
    # Get function docstring
    docstring = inspect.getdoc(func) or ""

    # Use thread_id as session_id in the payload
    payload_session_id = thread_id
    # Clean up parameters for V3 - just send values, not the nested dict
    clean_params: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, dict) and "value" in value:
            # Extract just the value from the nested structure
            clean_params[key] = value["value"]
        else:
            # Already clean or unexpected format
            clean_params[key] = value

    # Determine response expectation
    payload = {
        "session_id": payload_session_id,
        "response_expectation": options.response_expectation.value,
        "cache_response": bool(options.cache_response),
        "tool_call": {
            "function_name": func.__name__,
            "parameters": clean_params,
            "return_type": json.dumps(extract_json_schema(return_type_obj)),
            "docstring": docstring,
        },
    }

    mock_result = api_client.post(endpoint, payload)
    logger.info(f"Mock response: {mock_result}")

    if isinstance(mock_result, str):
        with suppress(json.JSONDecodeError):
            mock_result = json.loads(mock_result)
            return convert_to_type(mock_result, return_type_obj)
    return convert_to_type(mock_result, return_type_obj)


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def mock_tool_call_async(
    func: Callable,
    session_id: str,  # noqa: ARG001
    parameters: dict[str, dict[str, str]],
    options: ToolCallOptions | None = None,
    thread_id: str | None = None,
) -> object:
    """Mock tool call (asynchronous).

    Args:
        func: Function being mocked
        session_id: Session ID (kept for backwards compatibility, not used)
        parameters: Function parameters
        options: Tool call options
        thread_id: Thread ID to use as session_id in API request (required)

    Raises:
        ValueError: If thread_id is not provided
    """
    if thread_id is None:
        raise ValueError(
            "thread_id is required for mocking. "
            "Use parse_token() to set both session_id and thread_id."
        )

    options = options or ToolCallOptions()
    api_client = get_api_client()
    endpoint = api_client.tool_mock_endpoint

    logger.info(f"Simulating function: {func.__name__}")

    type_hints = get_type_hints(func)

    # Extract return type object (not just the name)
    return_type_obj = type_hints.pop("return", Any)
    # Get function docstring
    docstring = inspect.getdoc(func) or ""

    # Use thread_id as session_id in the payload
    payload_session_id = thread_id
    # Clean up parameters for V3 - just send values, not the nested dict
    clean_params: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, dict) and "value" in value:
            # Extract just the value from the nested structure
            clean_params[key] = value["value"]
        else:
            # Already clean or unexpected format
            clean_params[key] = value

    # Determine response expectation
    payload = {
        "session_id": payload_session_id,
        "response_expectation": options.response_expectation.value,
        "cache_response": bool(options.cache_response),
        "tool_call": {
            "function_name": func.__name__,
            "parameters": clean_params,
            "return_type": json.dumps(extract_json_schema(return_type_obj)),
            "docstring": docstring,
        },
    }

    mock_result = await api_client.post_async(endpoint, payload)
    logger.info(f"Mock response: {mock_result}")

    if isinstance(mock_result, str):
        with suppress(json.JSONDecodeError):
            mock_result = json.loads(mock_result)
            return convert_to_type(mock_result, return_type_obj)
    return convert_to_type(mock_result, return_type_obj)


def log_tool_call(
    session_id: str,
    function_name: str,
    parameters: dict[str, dict[str, str]],
    docstring: str,
) -> None:
    """Log tool call synchronously to the VERIS logging endpoint."""
    api_client = get_api_client()
    endpoint = api_client.get_log_tool_call_endpoint(session_id)

    # Clean up parameters for V3 - just send values, not the nested dict
    clean_params: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, dict) and "value" in value:
            # Extract just the value from the nested structure
            clean_params[key] = value["value"]
        else:
            # Already clean or unexpected format
            clean_params[key] = value

    payload = {
        "function_name": function_name,
        "parameters": clean_params,
        "docstring": docstring,
    }
    try:
        api_client.post(endpoint, payload)
        logger.debug(f"Tool call logged for {function_name}")
    except Exception as e:
        logger.warning(f"Failed to log tool call for {function_name}: {e}")


async def log_tool_call_async(
    session_id: str,
    function_name: str,
    parameters: dict[str, dict[str, str]],
    docstring: str,
) -> None:
    """Log tool call asynchronously to the VERIS logging endpoint."""
    api_client = get_api_client()
    endpoint = api_client.get_log_tool_call_endpoint(session_id)

    # Clean up parameters for V3 - just send values, not the nested dict
    clean_params: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, dict) and "value" in value:
            # Extract just the value from the nested structure
            clean_params[key] = value["value"]
        else:
            # Already clean or unexpected format
            clean_params[key] = value

    payload = {
        "function_name": function_name,
        "parameters": clean_params,
        "docstring": docstring,
    }
    try:
        await api_client.post_async(endpoint, payload)
        logger.debug(f"Tool call logged for {function_name}")
    except Exception as e:
        logger.warning(f"Failed to log tool call for {function_name}: {e}")


def log_tool_response(session_id: str, response: Any) -> None:  # noqa: ANN401
    """Log tool response synchronously to the VERIS logging endpoint."""
    api_client = get_api_client()
    endpoint = api_client.get_log_tool_response_endpoint(session_id)

    payload = {
        "response": json.dumps(response, default=str),
    }

    try:
        api_client.post(endpoint, payload)
        logger.debug("Tool response logged")
    except Exception as e:
        logger.warning(f"Failed to log tool response: {e}")


async def log_tool_response_async(session_id: str, response: Any) -> None:  # noqa: ANN401
    """Log tool response asynchronously to the VERIS logging endpoint."""
    api_client = get_api_client()
    endpoint = api_client.get_log_tool_response_endpoint(session_id)

    payload = {
        "response": json.dumps(response, default=str),
    }

    try:
        await api_client.post_async(endpoint, payload)
        logger.debug("Tool response logged")
    except Exception as e:
        logger.warning(f"Failed to log tool response: {e}")


veris = VerisSDK()
