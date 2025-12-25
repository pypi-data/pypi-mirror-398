"""Centralized API client for VERIS simulation endpoints."""

import logging
import os
from contextvars import ContextVar
from typing import Any

import httpx
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# Context variable to store base_url for per-request multi-tenant scenarios
_base_url_context: ContextVar[str | None] = ContextVar("veris_base_url", default=None)


class SimulatorAPIClient:
    """Centralized client for making requests to VERIS simulation endpoints.

    Note:
        This client intentionally reads configuration (base URL and API key)
        from environment variables at call-time instead of at construction
        time. This allows tests to patch environment variables and have those
        changes reflected without recreating the singleton.
    """

    def __init__(self, timeout: float | None = None) -> None:
        """Initialize the API client with static timeout configuration."""
        self._timeout = timeout or float(os.getenv("VERIS_MOCK_TIMEOUT", "300.0"))

    @property
    def base_url(self) -> str:
        """Get the resolved base URL."""
        return self._get_base_url()

    def _get_base_url(self) -> str:
        """Resolve the base URL from context, environment, or default.

        Priority order:
            1. Context variable (for per-request multi-tenant scenarios)
            2. VERIS_API_URL environment variable
            3. Default production URL

        Behavior:
            - If VERIS_API_URL is unset, default to the dev simulator URL.
            - If VERIS_API_URL is set to an empty string, treat it as empty
              (do not fall back). This supports tests expecting connection
              failures when an invalid endpoint is provided.
        """
        # Priority: context > env var > default
        context_url = _base_url_context.get()
        return context_url or os.getenv("VERIS_API_URL") or "https://simulator.api.veris.ai"

    def _build_headers(self) -> dict[str, str] | None:
        """Build headers including OpenTelemetry tracing and API key."""
        headers: dict[str, str] | None = None
        # Add API key header if available
        api_key = os.getenv("VERIS_API_KEY")
        if api_key:
            if headers is None:
                headers = {}
            headers["x-api-key"] = api_key

        return headers

    def get(self, endpoint: str, headers: dict[str, str] | None = None) -> Any:  # noqa: ANN401
        """Make a synchronous GET request to the specified endpoint."""
        base_headers = self._build_headers() or {}
        if headers:
            base_headers.update(headers)

        if not endpoint.startswith(("http://", "https://")):
            error_msg = f"Invalid endpoint URL (not absolute): {endpoint}"
            raise httpx.ConnectError(error_msg)

        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(endpoint, headers=base_headers)
            response.raise_for_status()
            return response.json() if response.content else None

    def post(self, endpoint: str, payload: dict[str, Any]) -> Any:  # noqa: ANN401
        """Make a synchronous POST request to the specified endpoint."""
        headers = self._build_headers()
        # Validate endpoint URL; raise ConnectError for non-absolute URLs to
        # mirror connection failures in tests when base URL is intentionally invalid.
        if not endpoint.startswith(("http://", "https://")):
            error_msg = f"Invalid endpoint URL (not absolute): {endpoint}"
            raise httpx.ConnectError(error_msg)

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else None

    async def get_async(self, endpoint: str, headers: dict[str, str] | None = None) -> Any:  # noqa: ANN401
        """Make an asynchronous GET request to the specified endpoint."""
        base_headers = self._build_headers() or {}
        if headers:
            base_headers.update(headers)

        if not endpoint.startswith(("http://", "https://")):
            error_msg = f"Invalid endpoint URL (not absolute): {endpoint}"
            raise httpx.ConnectError(error_msg)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(endpoint, headers=base_headers)
            response.raise_for_status()
            return response.json() if response.content else None

    async def post_async(self, endpoint: str, payload: dict[str, Any]) -> Any:  # noqa: ANN401
        """Make an asynchronous POST request to the specified endpoint.

        This method uses httpx.AsyncClient and is safe to call from async functions
        without blocking the event loop.
        """
        headers = self._build_headers()
        # Validate endpoint URL; raise ConnectError for non-absolute URLs to
        # mirror connection failures in tests when base URL is intentionally invalid.
        if not endpoint.startswith(("http://", "https://")):
            error_msg = f"Invalid endpoint URL (not absolute): {endpoint}"
            raise httpx.ConnectError(error_msg)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else None

    @property
    def tool_mock_endpoint(self) -> str:
        """Get the tool mock endpoint URL."""
        return urljoin(self.base_url, "v3/tool_mock")

    def get_log_tool_call_endpoint(self, session_id: str) -> str:
        """Get the log tool call endpoint URL."""
        return urljoin(self.base_url, f"v3/log_tool_call?session_id={session_id}")

    def get_log_tool_response_endpoint(self, session_id: str) -> str:
        """Get the log tool response endpoint URL."""
        return urljoin(self.base_url, f"v3/log_tool_response?session_id={session_id}")

    def get_simulation_config_endpoint(self, session_id: str) -> str:
        """Get the simulation config endpoint URL."""
        return urljoin(self.base_url, f"v3/simulation_config?session_id={session_id}")


# Global singleton instance
_api_client = SimulatorAPIClient()


def get_api_client() -> SimulatorAPIClient:
    """Get the global API client instance."""
    return _api_client


def set_api_client_params(timeout: float | None = None) -> None:
    """Set the global API client instance for testing purposes."""
    global _api_client  # noqa: PLW0603
    _api_client = SimulatorAPIClient(timeout=timeout)
