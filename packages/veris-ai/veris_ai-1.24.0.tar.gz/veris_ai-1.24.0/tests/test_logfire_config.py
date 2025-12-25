"""Tests for Logfire configuration and conditional tracing."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from opentelemetry.sdk.trace.sampling import Decision

from veris_ai.context_vars import (
    _logfire_token_context,
    _session_id_context,
    _thread_id_context,
)
from veris_ai.logfire_config import (
    VerisBaggageSpanProcessor,
    VerisConditionalSampler,
    configure_logfire_conditionally,
)


class TestVerisConditionalSampler:
    """Test VerisConditionalSampler."""

    def test_sampler_samples_when_session_exists(self):
        """Test that sampler returns RECORD_AND_SAMPLE when session_id is present."""
        sampler = VerisConditionalSampler()
        _session_id_context.set("test-session-123")

        result = sampler.should_sample()

        assert result.decision == Decision.RECORD_AND_SAMPLE
        assert result.decision.is_sampled() is True

    def test_sampler_drops_when_no_session(self):
        """Test that sampler returns DROP when session_id is None."""
        sampler = VerisConditionalSampler()
        _session_id_context.set(None)

        result = sampler.should_sample()

        assert result.decision == Decision.DROP
        assert result.decision.is_sampled() is False


class TestVerisBaggageSpanProcessor:
    """Test VerisBaggageSpanProcessor."""

    def test_processor_adds_attributes_when_session_exists(self):
        """Test that processor adds veris_ai.session_id and veris_ai.thread_id attributes."""
        processor = VerisBaggageSpanProcessor()
        mock_span = Mock()
        mock_span.set_attribute = Mock()

        _session_id_context.set("test-session-123")
        _thread_id_context.set("test-thread-456")

        processor.on_start(mock_span)

        mock_span.set_attribute.assert_any_call("veris_ai.session_id", "test-session-123")
        mock_span.set_attribute.assert_any_call("veris_ai.thread_id", "test-thread-456")

    def test_processor_does_nothing_when_no_session(self):
        """Test that processor does nothing when session_id is None."""
        processor = VerisBaggageSpanProcessor()
        mock_span = Mock()
        mock_span.set_attribute = Mock()

        _session_id_context.set(None)
        _thread_id_context.set("test-thread-456")

        processor.on_start(mock_span)

        mock_span.set_attribute.assert_not_called()


class TestConfigureLogfireConditionally:
    """Test configure_logfire_conditionally function."""

    def test_configure_logfire_when_token_present(self):
        """Test that logfire is configured when logfire_token is present."""
        _logfire_token_context.set("test-token-123")

        mock_logfire = MagicMock()
        mock_logfire.configure = MagicMock()
        mock_logfire.instrument_openai_agents = MagicMock()
        mock_default_instance = MagicMock()
        mock_default_instance._config = MagicMock()
        mock_default_instance._config.token = None
        mock_logfire.DEFAULT_LOGFIRE_INSTANCE = mock_default_instance

        mock_sampling_options = MagicMock()
        mock_sampling_module = MagicMock()
        mock_sampling_module.SamplingOptions = mock_sampling_options

        mock_parent_based = MagicMock()

        with (
            patch.dict(
                "sys.modules", {"logfire": mock_logfire, "logfire.sampling": mock_sampling_module}
            ),
            patch("veris_ai.logfire_config.ParentBased", mock_parent_based),
            patch("veris_ai.logfire_config.VerisConditionalSampler") as mock_sampler_class,
            patch("veris_ai.logfire_config.VerisBaggageSpanProcessor") as mock_processor_class,
        ):
            mock_sampler_instance = MagicMock()
            mock_sampler_class.return_value = mock_sampler_instance
            mock_processor_instance = MagicMock()
            mock_processor_class.return_value = mock_processor_instance

            configure_logfire_conditionally()

            # Verify logfire.configure was called with correct parameters
            mock_logfire.configure.assert_called_once()
            call_kwargs = mock_logfire.configure.call_args[1]

            assert call_kwargs["token"] == "test-token-123"
            assert call_kwargs["service_name"] == "target_agent"
            assert mock_processor_instance in call_kwargs["additional_span_processors"]
            mock_logfire.instrument_openai_agents.assert_called_once()

    def test_configure_logfire_skips_when_token_missing(self):
        """Test that logfire configuration is skipped when logfire_token is None."""
        _logfire_token_context.set(None)

        mock_logfire = MagicMock()

        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            configure_logfire_conditionally()

            # Should not configure logfire
            mock_logfire.configure.assert_not_called()

    def test_configure_logfire_skips_when_same_token_already_configured(self):
        """Test that logfire configuration is skipped when same token is already configured."""
        _logfire_token_context.set("test-token-123")

        mock_logfire = MagicMock()
        mock_logfire.configure = MagicMock()
        mock_logfire.instrument_openai_agents = MagicMock()
        mock_default_instance = MagicMock()
        mock_config = MagicMock()
        mock_config.token = "test-token-123"  # Same token already configured
        mock_default_instance._config = mock_config
        mock_logfire.DEFAULT_LOGFIRE_INSTANCE = mock_default_instance

        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            configure_logfire_conditionally()

            # Should not reconfigure when token matches
            mock_logfire.configure.assert_not_called()
            mock_logfire.instrument_openai_agents.assert_not_called()

    def test_configure_logfire_reconfigures_when_token_changes(self):
        """Test that logfire is reconfigured when a different token is provided."""
        _logfire_token_context.set("new-token-456")

        mock_logfire = MagicMock()
        mock_logfire.configure = MagicMock()
        mock_logfire.instrument_openai_agents = MagicMock()
        mock_default_instance = MagicMock()
        mock_config = MagicMock()
        mock_config.token = "old-token-123"  # Different token already configured
        mock_default_instance._config = mock_config
        mock_logfire.DEFAULT_LOGFIRE_INSTANCE = mock_default_instance

        mock_sampling_options = MagicMock()
        mock_sampling_module = MagicMock()
        mock_sampling_module.SamplingOptions = mock_sampling_options

        mock_parent_based = MagicMock()

        with (
            patch.dict(
                "sys.modules", {"logfire": mock_logfire, "logfire.sampling": mock_sampling_module}
            ),
            patch("veris_ai.logfire_config.ParentBased", mock_parent_based),
            patch("veris_ai.logfire_config.VerisConditionalSampler") as mock_sampler_class,
            patch("veris_ai.logfire_config.VerisBaggageSpanProcessor") as mock_processor_class,
        ):
            mock_sampler_instance = MagicMock()
            mock_sampler_class.return_value = mock_sampler_instance
            mock_processor_instance = MagicMock()
            mock_processor_class.return_value = mock_processor_instance

            configure_logfire_conditionally()

            # Should reconfigure with new token
            mock_logfire.configure.assert_called_once()
            call_kwargs = mock_logfire.configure.call_args[1]

            assert call_kwargs["token"] == "new-token-456"
            assert call_kwargs["service_name"] == "target_agent"
            assert mock_processor_instance in call_kwargs["additional_span_processors"]
            mock_logfire.instrument_openai_agents.assert_called_once()


class TestLogfireIntegration:
    """Integration tests for logfire configuration with session context."""

    def test_traces_sampled_when_session_exists(self):
        """Test that traces are sampled and attributes added when session exists."""
        sampler = VerisConditionalSampler()
        processor = VerisBaggageSpanProcessor()
        mock_span = Mock()
        mock_span.set_attribute = Mock()

        _session_id_context.set("integration-session-123")
        _thread_id_context.set("integration-thread-456")

        # Sampler should sample when session_id exists
        sampling_result = sampler.should_sample()
        assert sampling_result.decision == Decision.RECORD_AND_SAMPLE

        # Processor should add attributes to sampled spans
        processor.on_start(mock_span)
        mock_span.set_attribute.assert_any_call("veris_ai.session_id", "integration-session-123")
        mock_span.set_attribute.assert_any_call("veris_ai.thread_id", "integration-thread-456")

    def test_no_traces_when_no_session(self):
        """Test that no traces are sampled when session_id is not set."""
        sampler = VerisConditionalSampler()
        processor = VerisBaggageSpanProcessor()
        mock_span = Mock()
        mock_span.set_attribute = Mock()

        _session_id_context.set(None)

        # Sampler should drop traces
        sampling_result = sampler.should_sample()
        assert sampling_result.decision == Decision.DROP

        # Processor should not add attributes
        processor.on_start(mock_span)
        mock_span.set_attribute.assert_not_called()
