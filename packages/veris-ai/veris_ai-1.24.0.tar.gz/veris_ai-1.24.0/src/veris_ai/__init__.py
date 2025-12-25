"""Veris AI Python SDK."""

from typing import Any

__version__ = "0.1.0"

# Import lightweight modules that only use base dependencies
from .jaeger_interface import JaegerClient
from .jwt_utils import JWTClaims, decode_token
from .models import ResponseExpectation, SimulationConfig, ToolCallOptions
from .observability import init_observability, instrument_fastapi_app
from .tool_mock import veris

# Lazy import for modules with heavy dependencies
_Runner = None
_VerisConfig = None


def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Lazy load Runner and VerisConfig classes."""
    global _Runner, _VerisConfig  # noqa: PLW0603
    if name == "Runner":
        if _Runner is None:
            try:
                from .agents_wrapper import Runner as _Runner_impl  # noqa: PLC0415

                _Runner = _Runner_impl
            except ImportError as e:
                error_msg = (
                    "The 'Runner' class requires additional dependencies. "
                    "Please install them with: pip install veris-ai[agents]"
                )
                raise ImportError(error_msg) from e
        return _Runner
    if name == "VerisConfig":
        if _VerisConfig is None:
            try:
                from .agents_wrapper import VerisConfig as _VerisConfig_impl  # noqa: PLC0415

                _VerisConfig = _VerisConfig_impl
            except ImportError as e:
                error_msg = (
                    "The 'VerisConfig' class requires additional dependencies. "
                    "Please install them with: pip install veris-ai[agents]"
                )
                raise ImportError(error_msg) from e
        return _VerisConfig
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "veris",
    "JaegerClient",
    "JWTClaims",
    "decode_token",
    "ResponseExpectation",
    "SimulationConfig",
    "ToolCallOptions",
    "init_observability",
    "instrument_fastapi_app",
    "Runner",
    "VerisConfig",
]
