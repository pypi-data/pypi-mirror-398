"""JWT utilities for Veris SDK.

This module provides JWT decoding and verification functionality,
including JWKS-based signature verification.
"""

import base64
import json
import logging
from urllib.parse import urljoin

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Constants
JWKS_CACHE_TTL = 300  # 5 minutes

# Module-level cache for JWKS clients (keyed by URL)
_jwks_clients: dict[str, PyJWKClient] = {}


class JWTClaims(BaseModel, extra="ignore"):
    """Parsed JWT claims with typed fields."""

    session_id: str | None = None
    thread_id: str | None = None
    api_url: str | None = None
    logfire_token: str | None = None
    run_id: str | None = None
    sub: str | None = None
    iss: str | None = None
    aud: str | list[str] | None = None
    exp: int | None = None
    iat: int | None = None
    jti: str | None = None


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Get or create a cached JWKS client for the given URL."""
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True, lifespan=JWKS_CACHE_TTL)
    return _jwks_clients[jwks_url]


def clear_jwks_cache() -> None:
    """Clear all cached JWKS clients."""
    _jwks_clients.clear()


def _decode_legacy_base64_token(token: str) -> dict:
    """Decode a legacy base64-encoded JSON token.

    Handles both standard base64 and URL-safe base64 encoding,
    with or without padding.

    Args:
        token: Base64-encoded JSON string.

    Returns:
        Decoded JSON as a dictionary.

    Raises:
        ValueError: If decoding fails.
    """
    # Add padding if missing (base64 requires padding to be multiple of 4)
    padding_needed = len(token) % 4
    if padding_needed:
        token += "=" * (4 - padding_needed)

    # Try URL-safe base64 first, then standard base64
    decoded_bytes = None
    for decode_func in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            decoded_bytes = decode_func(token)
            break
        except Exception:  # noqa: BLE001, S112
            continue

    if decoded_bytes is None:
        raise ValueError("Failed to decode base64 token")

    # Parse JSON
    try:
        return json.loads(decoded_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        msg = f"Failed to parse base64 token as JSON: {e}"
        raise ValueError(msg) from e


def _verify_jwt_signature(token: str, iss: str, audience: str | None = None) -> None:
    """Verify JWT signature using JWKS from the issuer.

    Args:
        token: The JWT token to verify.
        iss: The issuer URL to fetch JWKS from.
        audience: Optional expected audience claim. If None, audience verification is skipped.

    Raises:
        ValueError: If verification fails.
    """
    # Build JWKS URL from issuer
    base_url = iss if iss.endswith("/") else iss + "/"
    jwks_url = urljoin(base_url, ".well-known/jwks.json")

    # Get signing key from JWKS
    try:
        client = _get_jwks_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
    except PyJWKClientError as e:
        msg = f"Failed to get JWKS signing key: {e}"
        raise ValueError(msg) from e
    except httpx.HTTPError as e:
        msg = f"Failed to fetch JWKS: {e}"
        raise ValueError(msg) from e

    # Verify the token signature
    try:
        # Skip audience verification if no audience is specified
        decode_options = {"verify_aud": audience is not None}
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            options=decode_options,
        )
    except jwt.ExpiredSignatureError as e:
        raise ValueError("JWT has expired") from e
    except jwt.InvalidTokenError as e:
        msg = f"JWT verification failed: {e}"
        raise ValueError(msg) from e


def decode_token(
    token: str,
    *,
    verify_signature: bool = True,
    audience: str | None = None,
) -> JWTClaims:
    """Decode a JWT or legacy base64-encoded JSON token.

    When verify_signature is False, this function also accepts legacy base64-encoded
    JSON tokens (plain base64-encoded JSON without JWT structure). This is useful
    for backward compatibility with older token formats.

    Args:
        token: JWT or base64-encoded JSON token.
        verify_signature: Whether to verify JWT signature using JWKS (default True).
            When False, also accepts legacy base64-encoded JSON tokens.
        audience: Optional expected audience claim. If provided, the token's `aud` claim
            will be validated against this value. If None (default), audience verification
            is skipped. Only applicable to JWT tokens.

    Returns:
        Parsed claims.

    Raises:
        ValueError: If the token is invalid or verification fails.
    """
    # Step 1: Try to decode as JWT
    jwt_error = None
    try:
        claims = jwt.decode(token, options={"verify_signature": False})

        # Step 2: Optionally verify signature
        if verify_signature and claims.get("iss"):
            _verify_jwt_signature(token, claims["iss"], audience=audience)

        return JWTClaims.model_validate(claims)
    except jwt.InvalidTokenError as e:
        jwt_error = e

    # Step 3: If JWT decoding failed and verify_signature is False, try legacy base64
    if not verify_signature:
        try:
            claims = _decode_legacy_base64_token(token)
            logger.debug("Decoded token as legacy base64 JSON")
            return JWTClaims.model_validate(claims)
        except ValueError:
            # Both JWT and base64 decoding failed, raise the original JWT error
            pass

    # Raise the original JWT error
    msg = f"Invalid token: {jwt_error}"
    raise ValueError(msg) from jwt_error
