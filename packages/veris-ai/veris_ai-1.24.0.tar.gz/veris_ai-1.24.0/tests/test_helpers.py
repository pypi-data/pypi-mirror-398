"""Helper functions for tests."""

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate a test RSA key pair for JWT signing
_test_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def create_test_token(
    session_id: str = "test-session", thread_id: str | None = "test-thread"
) -> str:
    """Create a JWT test token.

    Args:
        session_id: Session ID to include in token
        thread_id: Thread ID to include in token (optional)

    Returns:
        JWT token string
    """
    token_data = {"session_id": session_id}
    if thread_id is not None:
        token_data["thread_id"] = thread_id

    return jwt.encode(token_data, _test_private_key, algorithm="RS256")
