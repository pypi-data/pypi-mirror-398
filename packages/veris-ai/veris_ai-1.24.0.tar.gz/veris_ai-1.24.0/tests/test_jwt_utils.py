"""Tests for JWT utilities."""

import base64
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from veris_ai.jwt_utils import (
    JWTClaims,
    _decode_legacy_base64_token,
    _jwks_clients,
    clear_jwks_cache,
    decode_token,
)


# Generate test RSA key pair
def generate_test_keypair():
    """Generate a test RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


def create_test_jwt(claims: dict, private_key, algorithm: str = "RS256") -> str:
    """Create a test JWT with the given claims."""
    return jwt.encode(claims, private_key, algorithm=algorithm)


def create_legacy_base64_token(
    claims: dict, url_safe: bool = True, include_padding: bool = True
) -> str:
    """Create a legacy base64-encoded JSON token.

    Args:
        claims: Dictionary of claims to encode.
        url_safe: Whether to use URL-safe base64 encoding.
        include_padding: Whether to include padding (= characters).

    Returns:
        Base64-encoded JSON string.
    """
    json_str = json.dumps(claims)
    json_bytes = json_str.encode("utf-8")

    if url_safe:
        encoded = base64.urlsafe_b64encode(json_bytes).decode("utf-8")
    else:
        encoded = base64.b64encode(json_bytes).decode("utf-8")

    if not include_padding:
        encoded = encoded.rstrip("=")

    return encoded


class TestDecodeToken:
    """Tests for decode_token function."""

    def test_decode_jwt_with_all_claims(self):
        """Test decoding a valid JWT with all claims."""
        private_key, _ = generate_test_keypair()
        claims = {
            "session_id": "sess_123",
            "thread_id": "thread_456",
            "api_url": "http://localhost:8742/",
            "logfire_token": "logfire_abc",
            "sub": "agent_789",
            "iss": "http://localhost:8742/",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        token = create_test_jwt(claims, private_key)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "sess_123"
        assert result.thread_id == "thread_456"
        assert result.api_url == "http://localhost:8742/"
        assert result.logfire_token == "logfire_abc"
        assert result.sub == "agent_789"
        assert result.iss == "http://localhost:8742/"

    def test_decode_jwt_without_session_id(self):
        """Test decoding JWT without session_id works."""
        private_key, _ = generate_test_keypair()
        claims = {"thread_id": "thread_456", "sub": "agent_123"}
        token = create_test_jwt(claims, private_key)

        result = decode_token(token, verify_signature=False)
        assert result.session_id is None
        assert result.thread_id == "thread_456"

    def test_decode_jwt_minimal(self):
        """Test decoding JWT with minimal fields."""
        private_key, _ = generate_test_keypair()
        claims = {"session_id": "sess_123"}
        token = create_test_jwt(claims, private_key)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "sess_123"
        assert result.thread_id is None
        assert result.api_url is None

    def test_decode_invalid_jwt_raises_error(self):
        """Test that invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("not-a-valid-jwt", verify_signature=False)

    def test_decode_malformed_jwt_raises_error(self):
        """Test that malformed token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("not.a.valid.jwt", verify_signature=False)

    def test_decode_invalid_token_with_verify_signature_true(self):
        """Test that invalid token with verify_signature=True raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("not-a-valid-jwt", verify_signature=True)


class TestLegacyBase64Token:
    """Tests for legacy base64-encoded JSON token decoding."""

    def test_decode_legacy_base64_with_all_claims(self):
        """Test decoding a legacy base64 token with all claims."""
        claims = {
            "session_id": "legacy_sess_123",
            "thread_id": "legacy_thread_456",
            "api_url": "http://localhost:8742/",
            "logfire_token": "logfire_abc",
        }
        token = create_legacy_base64_token(claims)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "legacy_sess_123"
        assert result.thread_id == "legacy_thread_456"
        assert result.api_url == "http://localhost:8742/"
        assert result.logfire_token == "logfire_abc"

    def test_decode_legacy_base64_standard_encoding(self):
        """Test decoding legacy base64 with standard (non-URL-safe) encoding."""
        claims = {"session_id": "sess_standard", "thread_id": "thread_standard"}
        token = create_legacy_base64_token(claims, url_safe=False)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "sess_standard"
        assert result.thread_id == "thread_standard"

    def test_decode_legacy_base64_without_padding(self):
        """Test decoding legacy base64 without padding characters."""
        claims = {"session_id": "sess_nopad", "thread_id": "thread_nopad"}
        token = create_legacy_base64_token(claims, include_padding=False)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "sess_nopad"
        assert result.thread_id == "thread_nopad"

    def test_decode_legacy_base64_minimal(self):
        """Test decoding legacy base64 with minimal fields."""
        claims = {"session_id": "sess_min"}
        token = create_legacy_base64_token(claims)

        result = decode_token(token, verify_signature=False)

        assert result.session_id == "sess_min"
        assert result.thread_id is None

    def test_legacy_base64_not_accepted_with_verify_signature_true(self):
        """Test that legacy base64 is not accepted when verify_signature=True."""
        claims = {"session_id": "sess_123"}
        token = create_legacy_base64_token(claims)

        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(token, verify_signature=True)

    def test_decode_legacy_base64_helper_function(self):
        """Test the _decode_legacy_base64_token helper function directly."""
        claims = {"session_id": "direct_sess", "thread_id": "direct_thread"}
        token = create_legacy_base64_token(claims)

        result = _decode_legacy_base64_token(token)

        assert result["session_id"] == "direct_sess"
        assert result["thread_id"] == "direct_thread"

    def test_decode_legacy_base64_invalid_json(self):
        """Test that invalid JSON in base64 raises error."""
        # Encode non-JSON content
        invalid_token = base64.b64encode(b"not-valid-json").decode("utf-8")

        with pytest.raises(ValueError, match="Failed to parse base64 token as JSON"):
            _decode_legacy_base64_token(invalid_token)

    def test_decode_legacy_base64_invalid_base64(self):
        """Test that completely invalid base64 raises error."""
        with pytest.raises(ValueError, match="Failed to decode base64 token"):
            _decode_legacy_base64_token("!!!not-base64!!!")


class TestJWTClaims:
    """Tests for JWTClaims Pydantic model."""

    def test_jwt_claims_creation(self):
        """Test creating JWTClaims with all fields."""
        claims = JWTClaims(
            session_id="sess_123",
            thread_id="thread_456",
            api_url="http://localhost/",
            logfire_token="logfire_abc",
            run_id="run_789",
            sub="agent_001",
            iss="http://issuer/",
            aud=["client1", "client2"],
            exp=1234567890,
            iat=1234567800,
            jti="unique_id",
        )

        assert claims.session_id == "sess_123"
        assert claims.thread_id == "thread_456"
        assert claims.api_url == "http://localhost/"
        assert claims.logfire_token == "logfire_abc"
        assert claims.run_id == "run_789"
        assert claims.sub == "agent_001"
        assert claims.iss == "http://issuer/"
        assert claims.aud == ["client1", "client2"]
        assert claims.exp == 1234567890
        assert claims.iat == 1234567800
        assert claims.jti == "unique_id"

    def test_jwt_claims_minimal(self):
        """Test JWTClaims with no fields (all optional)."""
        claims = JWTClaims()

        assert claims.session_id is None
        assert claims.thread_id is None
        assert claims.api_url is None
        assert claims.logfire_token is None

    def test_jwt_claims_ignores_extra_fields(self):
        """Test that extra fields are ignored."""
        claims = JWTClaims.model_validate(
            {
                "session_id": "sess_123",
                "unknown_field": "ignored",
                "another_unknown": 123,
            }
        )

        assert claims.session_id == "sess_123"


class TestJWKSCache:
    """Tests for JWKS client caching."""

    def test_cache_stores_client_by_url(self):
        """Test that JWKS clients are cached by URL."""
        clear_jwks_cache()

        url = "http://localhost/.well-known/jwks.json"
        from jwt import PyJWKClient

        client1 = PyJWKClient(url, cache_keys=True, lifespan=300)
        _jwks_clients[url] = client1

        assert _jwks_clients.get(url) is client1

    def test_different_urls_get_different_entries(self):
        """Test that different URLs get different cache entries."""
        clear_jwks_cache()

        url1 = "http://localhost1/.well-known/jwks.json"
        url2 = "http://localhost2/.well-known/jwks.json"

        from jwt import PyJWKClient

        _jwks_clients[url1] = PyJWKClient(url1, cache_keys=True, lifespan=300)
        _jwks_clients[url2] = PyJWKClient(url2, cache_keys=True, lifespan=300)

        assert _jwks_clients[url1] is not _jwks_clients[url2]

    def test_clear_cache_removes_all_entries(self):
        """Test that clear_jwks_cache removes all cached clients."""
        url = "http://localhost/.well-known/jwks.json"
        from jwt import PyJWKClient

        _jwks_clients[url] = PyJWKClient(url, cache_keys=True, lifespan=300)
        assert len(_jwks_clients) > 0

        clear_jwks_cache()

        assert len(_jwks_clients) == 0


class TestVerisSDKJWT:
    """Tests for VerisSDK JWT-related methods."""

    def test_parse_token_jwt_without_verification(self):
        """Test parse_token with JWT and verify_signature=False."""
        from veris_ai import veris

        private_key, _ = generate_test_keypair()
        claims = {
            "session_id": "sess_sdk_test",
            "thread_id": "thread_sdk_test",
            "api_url": "http://localhost:8742/",
        }
        token = create_test_jwt(claims, private_key)

        try:
            result = veris.parse_token(token, verify_signature=False)

            assert result.session_id == "sess_sdk_test"
            assert veris.session_id == "sess_sdk_test"
            assert veris.thread_id == "thread_sdk_test"
            assert veris.api_url == "http://localhost:8742/"
        finally:
            veris.clear_context()

    def test_set_session_id(self):
        """Test set_session_id method."""
        from veris_ai import veris

        try:
            veris.set_session_id("direct_session_123")
            assert veris.session_id == "direct_session_123"
        finally:
            veris.clear_context()

    def test_set_thread_id(self):
        """Test set_thread_id method."""
        from veris_ai import veris

        try:
            veris.set_thread_id("direct_thread_456")
            assert veris.thread_id == "direct_thread_456"
        finally:
            veris.clear_context()

    def test_set_api_url(self):
        """Test set_api_url method."""
        from veris_ai import veris

        try:
            veris.set_api_url("http://custom-api.example.com/")
            assert veris.api_url == "http://custom-api.example.com/"
        finally:
            veris.clear_context()

    def test_set_logfire_token(self):
        """Test set_logfire_token method."""
        from veris_ai import veris

        try:
            veris.set_logfire_token("custom_logfire_token")
            assert veris.logfire_token == "custom_logfire_token"
        finally:
            veris.clear_context()
