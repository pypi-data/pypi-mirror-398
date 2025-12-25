import os
from unittest.mock import patch

import pytest

from .fixtures.http_server import *
from .fixtures.simple_app import *


class MockContext:
    class RequestContext:
        class LifespanContext:
            def __init__(self):
                self.session_id = "test-session"

        def __init__(self):
            self.lifespan_context = self.LifespanContext()

    def __init__(self):
        self.request_context = self.RequestContext()


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.fixture
def simulation_env():
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    from veris_ai import veris

    # Generate a test RSA key pair and create a JWT token
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {"session_id": "test-session-123", "thread_id": "test-thread-123"},
        private_key,
        algorithm="RS256",
    )
    veris.parse_token(token, verify_signature=False)

    with patch.dict(
        os.environ,
        {
            "VERIS_ENDPOINT_URL": "http://test-endpoint",
        },
    ):
        yield
        # Clean up session context after test
        veris.clear_context()


@pytest.fixture
def production_env():
    from veris_ai import veris

    # Clear session context to ensure production mode (no simulation)
    veris.clear_context()

    with patch.dict(
        os.environ,
        {
            "VERIS_ENDPOINT_URL": "http://test-endpoint",
        },
    ):
        yield
