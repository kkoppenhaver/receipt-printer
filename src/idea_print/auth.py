"""HMAC signature verification for request authentication."""

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass
class AuthResult:
    """Result of authentication verification."""

    success: bool
    error: str | None = None


def verify_signature(
    body: bytes,
    signature: str,
    timestamp: str,
    secret: str,
    window_seconds: int = 300,
) -> AuthResult:
    """
    Verify HMAC-SHA256 signature of request body.

    Args:
        body: Raw request body bytes
        signature: Hex-encoded HMAC signature from X-Signature header
        timestamp: Unix timestamp string from X-Timestamp header
        secret: HMAC secret key
        window_seconds: Maximum age of timestamp in seconds

    Returns:
        AuthResult with success status and optional error message
    """
    if not secret:
        return AuthResult(success=False, error="HMAC secret not configured")

    if not signature:
        return AuthResult(success=False, error="Missing signature")

    if not timestamp:
        return AuthResult(success=False, error="Missing timestamp")

    # Verify timestamp is within window
    try:
        ts = int(timestamp)
    except ValueError:
        return AuthResult(success=False, error="Invalid timestamp format")

    now = int(time.time())
    age = abs(now - ts)

    if age > window_seconds:
        return AuthResult(
            success=False,
            error=f"Timestamp too old: {age}s > {window_seconds}s",
        )

    # Compute expected signature
    # Sign: timestamp + body
    message = timestamp.encode() + body
    expected = hmac.new(
        secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    if not hmac.compare_digest(signature, expected):
        return AuthResult(success=False, error="Invalid signature")

    return AuthResult(success=True)


def generate_signature(body: bytes, timestamp: int, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for request body.

    Args:
        body: Raw request body bytes
        timestamp: Unix timestamp
        secret: HMAC secret key

    Returns:
        Hex-encoded HMAC signature
    """
    message = str(timestamp).encode() + body
    return hmac.new(
        secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()
