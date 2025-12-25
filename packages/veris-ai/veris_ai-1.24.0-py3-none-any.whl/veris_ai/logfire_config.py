"""Logfire configuration for conditional trace collection.

This module handles automatic Logfire configuration that only sends traces
when a session_id exists (simulation mode). It uses a custom OpenTelemetry
sampler to conditionally create spans based on session context.
"""

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from opentelemetry.sdk.trace import Span, SpanProcessor
from opentelemetry.sdk.trace.sampling import (
    Decision,
    ParentBased,
    Sampler,
    SamplingResult,
)

if TYPE_CHECKING:
    from opentelemetry.context import Context
    from opentelemetry.trace import Link, SpanKind
    from opentelemetry.trace.span import TraceState
    from opentelemetry.util.types import Attributes

from veris_ai.context_vars import (
    _logfire_token_context,
    _session_id_context,
    _target_context,
    _thread_id_context,
)

logger = logging.getLogger(__name__)


class VerisConditionalSampler(Sampler):
    """Custom OpenTelemetry sampler that only samples traces when session_id exists.

    This sampler checks if a Veris session_id is present in the context.
    If present, it samples the trace (simulation mode). If not, it drops
    the trace (production mode).
    """

    def should_sample(  # noqa: PLR0913
        self,
        parent_context: "Context | None" = None,  # noqa: ARG002
        trace_id: int | None = None,  # noqa: ARG002
        name: str | None = None,  # noqa: ARG002
        kind: "SpanKind | None" = None,  # noqa: ARG002
        attributes: "Attributes | None" = None,  # noqa: ARG002
        links: Sequence["Link"] | None = None,  # noqa: ARG002
        trace_state: "TraceState | None" = None,  # noqa: ARG002
    ) -> SamplingResult:
        """Determine whether to sample a trace based on session_id presence.

        Args:
            parent_context: Parent span context (unused)
            trace_id: Trace ID (unused)
            name: Span name (unused)
            kind: Span kind (unused)
            attributes: Span attributes (unused)
            links: Span links (unused)
            trace_state: Trace state (unused)

        Returns:
            SamplingResult with RECORD_AND_SAMPLE if session_id exists,
            DROP otherwise
        """
        session_id = _session_id_context.get()
        if session_id:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        return SamplingResult(Decision.DROP)

    def get_description(self) -> str:
        """Return description of the sampler."""
        return "VerisConditionalSampler"

    def __repr__(self) -> str:
        """Return string representation of the sampler."""
        return f"{self.__class__.__name__}()"


class VerisBaggageSpanProcessor(SpanProcessor):
    """Span processor that adds Veris session_id, thread_id, and target as span attributes.

    This processor reads session_id, thread_id, and target from context variables and
    sets them as span attributes with prefixed keys 'veris_ai.session_id',
    'veris_ai.thread_id', and 'veris_ai.target'. This only runs for spans that are being sampled.
    """

    def on_start(
        self,
        span: Span,
        parent_context: "Context | None" = None,  # noqa: ARG002
    ) -> None:
        """Add Veris attributes to span when it starts."""
        session_id = _session_id_context.get()
        thread_id = _thread_id_context.get()
        target = _target_context.get()

        if session_id:
            span.set_attribute("veris_ai.session_id", str(session_id))
            if thread_id:
                span.set_attribute("veris_ai.thread_id", str(thread_id))
            if target:
                span.set_attribute("veris_ai.target", str(target))


def configure_logfire_conditionally() -> None:
    """Configure Logfire with conditional sampling based on session_id.

    If logfire_token is present, configures Logfire with:
    - Custom sampler that only samples spans when session_id exists
    - Span processor that adds veris_ai.session_id and veris_ai.thread_id attributes
    """
    logfire_token = _logfire_token_context.get()
    if not logfire_token:
        # Backwards compatible: if no token, do nothing
        return

    try:
        import logfire
        from logfire.sampling import SamplingOptions
    except ImportError:
        # Logfire is optional dependency - handle gracefully
        logger.debug("Logfire not available, skipping configuration")
        return

    # Check if logfire is already configured with the same token to avoid re-instrumentation
    try:
        from logfire import DEFAULT_LOGFIRE_INSTANCE

        if hasattr(DEFAULT_LOGFIRE_INSTANCE, "_config"):
            config = DEFAULT_LOGFIRE_INSTANCE._config  # noqa: SLF001
            if hasattr(config, "token") and config.token:
                # Only skip if the token matches - allow reconfiguration with different token
                if config.token == logfire_token:
                    logger.debug("Logfire already configured with same token, skipping")
                    return
                logger.debug(
                    f"Logfire token changed from ...{config.token[:-3]} to "
                    f"...{logfire_token[:3]}..., reconfiguring"
                )
    except Exception as e:
        # If we can't check, proceed with configuration anyway
        # This is expected if logfire internals change or aren't accessible
        logger.debug(f"Could not check logfire configuration state: {e}")

    # Configure logfire with conditional sampler and span processor
    # The sampler filters spans (only samples when session_id exists)
    # The span processor adds attributes to sampled spans
    logfire.configure(
        scrubbing=False,
        service_name="target_agent",
        sampling=SamplingOptions(head=ParentBased(VerisConditionalSampler())),
        token=logfire_token,
        add_baggage_to_attributes=True,
        send_to_logfire=True,
        additional_span_processors=[VerisBaggageSpanProcessor()],
    )

    # Instrument common libraries - each wrapped independently so failures don't block others
    logger.info("Instrumenting libraries to collect during veris-ai simulations:")
    try:
        logfire.instrument_openai()
        logger.info("  - OpenAI")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    try:
        logfire.instrument_anthropic()
        logger.info("  - Anthropic")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    try:
        logfire.instrument_google_genai()
        logger.info("  - Google GenAI")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    try:
        logfire.instrument_litellm()
        logger.info("  - LiteLLM")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    try:
        logfire.instrument_openai_agents()
        logger.info("  - OpenAI agents")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    try:
        logfire.instrument_pydantic_ai()
        logger.info("  - Pydantic AI")
    except Exception:  # noqa: S110 - Silently fail if library not available
        pass

    logger.info("Simulation logs are being piped to Veris via Logfire")
