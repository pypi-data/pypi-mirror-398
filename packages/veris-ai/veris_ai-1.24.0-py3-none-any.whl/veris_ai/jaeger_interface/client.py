"""Synchronous Jaeger Query Service client built on **requests**.

This implementation keeps dependencies minimal while providing fully-typed
*pydantic* models for both **request** and **response** bodies.
"""

import json
import types
from typing import Any, Self

import requests

from .models import GetTraceResponse, SearchResponse, Span, Trace

__all__ = ["JaegerClient"]


class JaegerClient:  # noqa: D101
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float | None = 10.0,
        session: requests.Session | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Create a new *JaegerClient* instance.

        Args:
            base_url: Base URL of the Jaeger Query Service (e.g. ``http://localhost:16686``).
            timeout: Request timeout in **seconds** (applied to every call).
            session: Optional pre-configured :class:`requests.Session` to reuse.
            headers: Optional default headers to send with every request.
        """
        # Normalise to avoid trailing slash duplicates
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._external_session = session  # If provided we won't close it
        self._headers = headers or {}

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _make_session(self) -> tuple[requests.Session, bool]:  # noqa: D401
        """Return a *(session, should_close)* tuple.

        If an external session was supplied we **must not** close it after the
        request, hence the boolean flag letting callers know whether they are
        responsible for closing the session.
        """
        if self._external_session is not None:
            return self._external_session, False

        # Reuse the session opened via the context manager if available
        if hasattr(self, "_session_ctx"):
            return self._session_ctx, False

        session = requests.Session()
        session.headers.update(self._headers)
        return session, True

    def _span_matches_tags(self, span: Span, span_tags: dict[str, Any]) -> bool:
        """Check if a span matches any of the provided tags (OR logic)."""
        if not span.tags or not span_tags:
            return False

        # Convert span tags to a dict for easier lookup
        span_tag_dict = {tag.key: tag.value for tag in span.tags}

        # OR logic: return True if ANY tag matches
        return any(span_tag_dict.get(key) == value for key, value in span_tags.items())

    def _filter_spans(
        self,
        traces: list[Trace],
        span_tags: dict[str, Any] | None,
        span_operations: list[str] | None = None,
    ) -> list[Trace]:
        """Filter spans within traces based on span_tags and/or span_operations.

        Uses OR logic within each filter type. If both are provided, a span must
        match at least one tag AND at least one operation.
        """
        if not span_tags and not span_operations:
            return traces

        filtered_traces = []
        for trace in traces:
            filtered_spans = []
            for span in trace.spans:
                tag_match = True
                op_match = True

                if span_tags:
                    tag_match = self._span_matches_tags(span, span_tags)
                if span_operations:
                    op_match = span.operationName in span_operations

                # If both filters are provided, require both to match (AND logic)
                if tag_match and op_match:
                    filtered_spans.append(span)

            if filtered_spans:
                filtered_trace = Trace(
                    traceID=trace.traceID,
                    spans=filtered_spans,
                    process=trace.process,
                    warnings=trace.warnings,
                )
                filtered_traces.append(filtered_trace)

        return filtered_traces

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def search(  # noqa: PLR0913
        self,
        service: str | None = None,
        *,
        limit: int | None = None,
        tags: dict[str, Any] | None = None,
        operation: str | None = None,
        span_tags: dict[str, Any] | None = None,
        span_operations: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> SearchResponse:  # noqa: D401
        """Search traces using the *v1* ``/api/traces`` endpoint with optional span filtering.

        Args:
            service: Service name to search for. If not provided, searches across all services.
            limit: Maximum number of traces to return.
            tags: Dictionary of tag filters for trace-level filtering (AND-combined).
            operation: Operation name to search for.
            span_tags: Dictionary of tag filters for span-level filtering.
                      Uses OR logic. Combined with span_operations using AND.
                      Applied client-side after retrieving traces.
            span_operations: List of operation names to search for.
                            Uses OR logic. Combined with span_tags using AND.
            **kwargs: Additional parameters to pass to the Jaeger API.

        Returns:
            Parsed :class:`~veris_ai.jaeger_interface.models.SearchResponse` model
            with spans filtered according to span_tags if provided.
        """
        # Build params for the Jaeger API (excluding span_tags)
        params: dict[str, Any] = {}

        if service is not None:
            params["service"] = service

        if limit is not None:
            params["limit"] = limit

        if operation is not None:
            params["operation"] = operation

        if tags:
            # Convert tags to JSON string as expected by Jaeger API
            params["tags"] = json.dumps(tags)

        # Add any additional parameters
        params.update(kwargs)

        session, should_close = self._make_session()
        try:
            url = f"{self._base_url}/api/traces"
            response = session.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        finally:
            if should_close:
                session.close()

        # Parse the response
        search_response = SearchResponse.model_validate(data)  # type: ignore[arg-type]

        # Apply span-level filtering if span_tags is provided
        if (
            (span_tags or span_operations)
            and search_response.data
            and isinstance(search_response.data, list)
        ):
            filtered_traces = self._filter_spans(search_response.data, span_tags, span_operations)
            search_response.data = filtered_traces
            # Update the total to reflect filtered results
            if search_response.total is not None:
                search_response.total = len(filtered_traces)

        return search_response

    def get_trace(self, trace_id: str) -> GetTraceResponse:  # noqa: D401
        """Retrieve a single trace by *trace_id*.

        Args:
            trace_id: The Jaeger trace identifier.

        Returns:
            Parsed :class:`~veris_ai.jaeger_interface.models.GetTraceResponse` model.
        """
        if not trace_id:
            error_msg = "trace_id must be non-empty"
            raise ValueError(error_msg)

        session, should_close = self._make_session()
        try:
            url = f"{self._base_url}/api/traces/{trace_id}"
            response = session.get(url, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        finally:
            if should_close:
                session.close()
        return GetTraceResponse.model_validate(data)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Context-manager helpers (optional but convenient)
    # ------------------------------------------------------------------

    def __enter__(self) -> Self:
        """Enter the context manager."""
        self._session_ctx, self._should_close_ctx = self._make_session()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        """Exit the context manager."""
        # Only close if we created the session
        if getattr(self, "_should_close_ctx", False):
            self._session_ctx.close()
