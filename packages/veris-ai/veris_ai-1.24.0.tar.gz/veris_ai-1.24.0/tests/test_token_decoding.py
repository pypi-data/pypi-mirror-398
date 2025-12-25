"""Tests for token decoding functionality."""

import base64
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from veris_ai import veris


def generate_test_keypair():
    """Generate a test RSA key pair."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def create_test_jwt(claims: dict, private_key) -> str:
    """Create a test JWT with the given claims."""
    return jwt.encode(claims, private_key, algorithm="RS256")


def create_legacy_base64_token(claims: dict) -> str:
    """Create a legacy base64-encoded JSON token."""
    json_str = json.dumps(claims)
    return base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")


class TestTokenDecoding:
    """Test token decoding via parse_token()."""

    def test_decode_valid_token_with_both_ids(self):
        """Test decoding a valid token with both session_id and thread_id."""
        private_key = generate_test_keypair()
        token = create_test_jwt(
            {"session_id": "test-session-123", "thread_id": "thread-456"},
            private_key,
        )

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == "test-session-123"
            assert veris.thread_id == "thread-456"
        finally:
            veris.clear_context()

    def test_decode_valid_token_with_only_session_id(self):
        """Test decoding a token with only session_id (no thread_id)."""
        private_key = generate_test_keypair()
        token = create_test_jwt({"session_id": "test-session-789"}, private_key)

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == "test-session-789"
            assert veris.thread_id is None
        finally:
            veris.clear_context()

    def test_decode_token_with_uuid_format(self):
        """Test decoding token with UUID-formatted IDs."""
        private_key = generate_test_keypair()
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        thread_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        token = create_test_jwt(
            {"session_id": session_id, "thread_id": thread_id},
            private_key,
        )

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == session_id
            assert veris.thread_id == thread_id
        finally:
            veris.clear_context()

    def test_decode_invalid_token_raises_error(self):
        """Test that invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            veris.parse_token("not-valid-jwt!!!", verify_signature=False)

    def test_decode_token_without_session_id(self):
        """Test that token without session_id still works (session_id is optional)."""
        private_key = generate_test_keypair()
        token = create_test_jwt({"thread_id": "thread-only"}, private_key)

        try:
            claims = veris.parse_token(token, verify_signature=False)
            assert claims.session_id is None
            assert claims.thread_id == "thread-only"
        finally:
            veris.clear_context()

    def test_clear_context_clears_all_values(self):
        """Test that clear_context clears session_id, thread_id, etc."""
        private_key = generate_test_keypair()
        token = create_test_jwt(
            {"session_id": "test-session", "thread_id": "test-thread"},
            private_key,
        )

        veris.parse_token(token, verify_signature=False)
        assert veris.session_id == "test-session"
        assert veris.thread_id == "test-thread"

        veris.clear_context()
        assert veris.session_id is None
        assert veris.thread_id is None

    def test_decode_token_with_additional_fields(self):
        """Test that additional fields in token don't break parsing."""
        private_key = generate_test_keypair()
        token = create_test_jwt(
            {
                "session_id": "test-session",
                "thread_id": "test-thread",
                "extra_field": "ignored",
                "another": 123,
            },
            private_key,
        )

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == "test-session"
            assert veris.thread_id == "test-thread"
        finally:
            veris.clear_context()


class TestParseToken:
    """Test parse_token method."""

    def test_parse_token_returns_claims(self):
        """Test that parse_token returns JWTClaims model."""
        private_key = generate_test_keypair()
        token = create_test_jwt(
            {
                "session_id": "sess_claims",
                "thread_id": "thread_claims",
                "api_url": "http://localhost/",
            },
            private_key,
        )

        try:
            claims = veris.parse_token(token, verify_signature=False)

            assert claims.session_id == "sess_claims"
            assert claims.thread_id == "thread_claims"
            assert claims.api_url == "http://localhost/"
        finally:
            veris.clear_context()


class TestLegacyBase64TokenDecoding:
    """Test legacy base64 token decoding via parse_token()."""

    def test_decode_legacy_base64_token(self):
        """Test decoding a legacy base64-encoded JSON token."""
        claims = {"session_id": "legacy_sess", "thread_id": "legacy_thread"}
        token = create_legacy_base64_token(claims)

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == "legacy_sess"
            assert veris.thread_id == "legacy_thread"
        finally:
            veris.clear_context()

    def test_decode_legacy_base64_token_with_api_url(self):
        """Test decoding a legacy base64 token with api_url."""
        claims = {
            "session_id": "sess_api",
            "thread_id": "thread_api",
            "api_url": "http://custom-api.example.com/",
        }
        token = create_legacy_base64_token(claims)

        try:
            result = veris.parse_token(token, verify_signature=False)
            assert result.session_id == "sess_api"
            assert result.api_url == "http://custom-api.example.com/"
            assert veris.api_url == "http://custom-api.example.com/"
        finally:
            veris.clear_context()

    def test_legacy_base64_token_requires_verify_signature_false(self):
        """Test that legacy base64 tokens require verify_signature=False."""
        claims = {"session_id": "sess_123"}
        token = create_legacy_base64_token(claims)

        with pytest.raises(ValueError, match="Invalid token"):
            veris.parse_token(token, verify_signature=True)

    def test_jwt_still_works_with_verify_signature_false(self):
        """Test that JWT tokens still work when verify_signature=False."""
        private_key = generate_test_keypair()
        token = create_test_jwt(
            {"session_id": "jwt_sess", "thread_id": "jwt_thread"},
            private_key,
        )

        try:
            veris.parse_token(token, verify_signature=False)
            assert veris.session_id == "jwt_sess"
            assert veris.thread_id == "jwt_thread"
        finally:
            veris.clear_context()
