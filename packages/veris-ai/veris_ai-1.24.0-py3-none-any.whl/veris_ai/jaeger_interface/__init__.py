"""Jaeger interface for searching and retrieving traces.

This sub-package provides a thin synchronous wrapper around the Jaeger
Query Service HTTP API with client-side span filtering capabilities.

Typical usage example::

    from veris_ai.jaeger_interface import JaegerClient

    client = JaegerClient("http://localhost:16686")

    # Search traces with trace-level filters
    traces = client.search(
        service="veris-agent",
        limit=20,
        tags={"error": "true"}  # AND logic at trace level
    )

    # Search with span-level filtering
    traces_filtered = client.search(
        service="veris-agent",
        limit=20,
        span_tags={
            "http.status_code": 404,
            "db.error": "timeout"
        }  # OR logic: spans with either tag are included
    )

    # Get a specific trace
    trace = client.get_trace(traces.data[0].traceID)

The implementation uses *requests* under the hood and all public functions
are fully typed using *pydantic* models so that IDEs can provide proper
autocomplete and type checking.
"""

from .client import JaegerClient

__all__ = ["JaegerClient"]
