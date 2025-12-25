"""Observability helpers for services using veris-ai.

Provides optional-safe initialization for OpenTelemetry propagation/export and
client/server instrumentation. Services can import and call these helpers to
enable consistent tracing without duplicating setup code.
"""

from __future__ import annotations

from fastapi import FastAPI
from logging import getLogger

logger = getLogger(__name__)


def init_observability() -> None:  # noqa: PLR0912
    """Initialize tracing/export and set W3C propagation.

    - Initializes Traceloop if available (acts as OTel bootstrap/exporter)
    - Sets global propagator to TraceContext + Baggage (W3C)
    - Instruments MCP, requests, httpx if instrumentation packages are present
    - Adds a request hook to capture outbound traceparent for debugging

    This function is safe to call even if instrumentation packages are not installed.
    """
    try:
        import logfire

        logfire.configure(scrubbing=False)
        logfire.instrument_openai_agents()
        try:
            logfire.instrument_redis()
        except Exception:
            logger.warning("Failed to instrument redis")
        logfire.instrument_mcp()

    except Exception as e:
        # Tracing is optional; continue without Traceloop
        msg = "Logfire not found: " + str(e)
        raise RuntimeError(msg) from e

    # Ensure W3C propagation (TraceContext + optional Baggage), tolerant to OTel versions
    try:
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from collections.abc import Mapping  # noqa: TC003
        from opentelemetry.trace import Span
        from requests import PreparedRequest
        import httpx

        # Import baggage propagator
        baggage = None
        try:
            from opentelemetry.baggage.propagation import W3CBaggagePropagator

            baggage = W3CBaggagePropagator()
        except Exception as e:
            msg = "OpenTelemetry not found: " + str(e)
            raise RuntimeError(msg) from e

        # Import composite propagator
        try:
            from opentelemetry.propagators.composite import CompositeHTTPPropagator

            propagators: list[W3CBaggagePropagator | TraceContextTextMapPropagator] = [
                TraceContextTextMapPropagator()
            ]
            if baggage:
                propagators.append(baggage)
            set_global_textmap(CompositeHTTPPropagator(propagators))
        except Exception as e:
            msg = "OpenTelemetry not found: " + str(e)
            raise RuntimeError(msg) from e
    except Exception as e:
        # OpenTelemetry not installed or incompatible; continue without changing global propagator
        msg = "OpenTelemetry not found: " + str(e)
        raise RuntimeError(msg) from e

    # Instrument HTTP clients and capture outbound traceparent for debugging
    def _log_request_headers(
        span: Span, request: PreparedRequest | httpx.Request | dict[str, Mapping[str, str]]
    ) -> None:
        try:
            traceparent = None
            if hasattr(request, "headers"):
                traceparent = request.headers.get("traceparent")
            elif isinstance(request, dict):
                traceparent = request.get("headers", {}).get("traceparent")
            if traceparent:
                span.set_attribute("debug.traceparent", traceparent)
        except Exception as e:
            msg = "OpenTelemetry not found: " + str(e)
            raise RuntimeError(msg) from e

    try:
        from opentelemetry.instrumentation.requests import (
            RequestsInstrumentor,  # type: ignore[import-not-found]
        )

        RequestsInstrumentor().instrument(request_hook=_log_request_headers)
    except Exception as e:
        msg = "OpenTelemetry not found: " + str(e)
        raise RuntimeError(msg) from e


def instrument_fastapi_app(app: FastAPI) -> None:
    """Instrument a FastAPI app so inbound HTTP requests continue W3C traces.

    Safe to call even if the fastapi instrumentation package is not installed.
    """

    import logfire

    logfire.instrument_fastapi(app)
