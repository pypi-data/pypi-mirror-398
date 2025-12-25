"""Tests for SimulatorAPIClient endpoint URL generation and configuration."""

import os
from unittest.mock import patch

import pytest

from veris_ai.api_client import SimulatorAPIClient, get_api_client, set_api_client_params


def test_tool_mock_endpoint_default():
    """Test that tool_mock_endpoint property returns correct URL with default base_url."""
    client = SimulatorAPIClient()
    endpoint = client.tool_mock_endpoint

    # Should use default base URL
    assert endpoint == "https://simulator.api.veris.ai/v3/tool_mock"


def test_tool_mock_endpoint_with_env_var():
    """Test that tool_mock_endpoint respects VERIS_API_URL environment variable."""
    with patch.dict(os.environ, {"VERIS_API_URL": "https://test.api.veris.ai"}):
        client = SimulatorAPIClient()
        endpoint = client.tool_mock_endpoint

        assert endpoint == "https://test.api.veris.ai/v3/tool_mock"


def test_log_tool_call_endpoint():
    """Test get_log_tool_call_endpoint generates correct URL."""
    with patch.dict(os.environ, {"VERIS_API_URL": "https://test.api.com"}):
        client = SimulatorAPIClient()
        endpoint = client.get_log_tool_call_endpoint("session-123")

        assert endpoint == "https://test.api.com/v3/log_tool_call?session_id=session-123"


def test_log_tool_response_endpoint():
    """Test get_log_tool_response_endpoint generates correct URL."""
    with patch.dict(os.environ, {"VERIS_API_URL": "https://test.api.com"}):
        client = SimulatorAPIClient()
        endpoint = client.get_log_tool_response_endpoint("session-456")

        assert endpoint == "https://test.api.com/v3/log_tool_response?session_id=session-456"


def test_custom_timeout():
    """Test that custom timeout is set correctly."""
    client = SimulatorAPIClient(timeout=30.0)
    assert client._timeout == 30.0


def test_default_timeout():
    """Test that default timeout is used when not specified."""
    with patch.dict(os.environ, {"VERIS_MOCK_TIMEOUT": "120.0"}):
        client = SimulatorAPIClient()
        assert client._timeout == 120.0


def test_set_api_client_params_timeout():
    """Test that set_api_client_params reconfigures the global client timeout."""
    # Reconfigure with custom timeout
    set_api_client_params(timeout=60.0)

    # Get client and verify timeout has been updated
    client = get_api_client()
    assert client._timeout == 60.0

    # Restore original client
    set_api_client_params()


def test_empty_env_var_uses_default():
    """Test that empty VERIS_API_URL falls back to default."""
    with patch.dict(os.environ, {"VERIS_API_URL": ""}, clear=True):
        client = SimulatorAPIClient()
        # Empty string should NOT be used, should fall back to default
        assert client._get_base_url() == "https://simulator.api.veris.ai"
