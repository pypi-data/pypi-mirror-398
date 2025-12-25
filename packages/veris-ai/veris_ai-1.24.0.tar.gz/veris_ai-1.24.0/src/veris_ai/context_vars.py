"""Context variables for Veris SDK.

This module contains context variables used across the SDK to track
session state, thread state, and configuration. These are extracted
to a separate module to avoid circular imports.
"""

from contextvars import ContextVar

from veris_ai.models import SimulationConfig

# Context variables to store session_id and thread_id for each call
_session_id_context: ContextVar[str | None] = ContextVar("veris_session_id", default=None)
_thread_id_context: ContextVar[str | None] = ContextVar("veris_thread_id", default=None)
_config_context: ContextVar[SimulationConfig | None] = ContextVar("veris_config", default=None)
_logfire_token_context: ContextVar[str | None] = ContextVar("veris_logfire_token", default=None)
_target_context: ContextVar[str | None] = ContextVar("veris_target", default=None)

__all__ = [
    "_session_id_context",
    "_thread_id_context",
    "_config_context",
    "_logfire_token_context",
    "_target_context",
]
