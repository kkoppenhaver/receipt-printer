"""Tests for HMAC authentication."""

import time

import pytest

from idea_print.auth import AuthResult, generate_signature, verify_signature


class TestVerifySignature:
    """Tests for signature verification."""

    def test_valid_signature(self):
        """Test verification of valid signature."""
        secret = "test-secret-key"
        body = b'{"idea_text": "Hello"}'
        timestamp = str(int(time.time()))
        signature = generate_signature(body, int(timestamp), secret)

        result = verify_signature(
            body=body,
            signature=signature,
            timestamp=timestamp,
            secret=secret,
        )

        assert result.success is True
        assert result.error is None

    def test_invalid_signature(self):
        """Test rejection of invalid signature."""
        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="invalid-signature",
            timestamp=str(int(time.time())),
            secret="test-secret",
        )

        assert result.success is False
        assert result.error == "Invalid signature"

    def test_missing_signature(self):
        """Test rejection when signature is missing."""
        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="",
            timestamp=str(int(time.time())),
            secret="test-secret",
        )

        assert result.success is False
        assert "Missing signature" in result.error

    def test_missing_timestamp(self):
        """Test rejection when timestamp is missing."""
        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="some-signature",
            timestamp="",
            secret="test-secret",
        )

        assert result.success is False
        assert "Missing timestamp" in result.error

    def test_invalid_timestamp_format(self):
        """Test rejection of non-numeric timestamp."""
        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="some-signature",
            timestamp="not-a-number",
            secret="test-secret",
        )

        assert result.success is False
        assert "Invalid timestamp format" in result.error

    def test_expired_timestamp(self):
        """Test rejection of old timestamp."""
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago

        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="some-signature",
            timestamp=old_timestamp,
            secret="test-secret",
            window_seconds=300,
        )

        assert result.success is False
        assert "too old" in result.error

    def test_future_timestamp_rejected(self):
        """Test rejection of future timestamp beyond window."""
        future_timestamp = str(int(time.time()) + 600)  # 10 minutes in future

        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="some-signature",
            timestamp=future_timestamp,
            secret="test-secret",
            window_seconds=300,
        )

        assert result.success is False
        assert "too old" in result.error

    def test_no_secret_configured(self):
        """Test rejection when secret is not configured."""
        result = verify_signature(
            body=b'{"idea_text": "Hello"}',
            signature="some-signature",
            timestamp=str(int(time.time())),
            secret="",
        )

        assert result.success is False
        assert "not configured" in result.error

    def test_custom_window(self):
        """Test custom timestamp window."""
        secret = "test-secret"
        body = b'{"idea_text": "Hello"}'
        # Timestamp 10 seconds ago
        timestamp = str(int(time.time()) - 10)
        signature = generate_signature(body, int(timestamp), secret)

        # Should pass with 60 second window
        result = verify_signature(
            body=body,
            signature=signature,
            timestamp=timestamp,
            secret=secret,
            window_seconds=60,
        )
        assert result.success is True

        # Should fail with 5 second window
        result = verify_signature(
            body=body,
            signature=signature,
            timestamp=timestamp,
            secret=secret,
            window_seconds=5,
        )
        assert result.success is False


class TestGenerateSignature:
    """Tests for signature generation."""

    def test_signature_format(self):
        """Test that signature is hex-encoded."""
        signature = generate_signature(
            body=b"test",
            timestamp=12345,
            secret="secret",
        )

        # Should be 64 hex characters (256 bits / 4 bits per hex char)
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_signature_deterministic(self):
        """Test that same inputs produce same signature."""
        body = b'{"test": "data"}'
        timestamp = 1234567890
        secret = "my-secret"

        sig1 = generate_signature(body, timestamp, secret)
        sig2 = generate_signature(body, timestamp, secret)

        assert sig1 == sig2

    def test_different_body_different_signature(self):
        """Test that different body produces different signature."""
        timestamp = 1234567890
        secret = "my-secret"

        sig1 = generate_signature(b"body1", timestamp, secret)
        sig2 = generate_signature(b"body2", timestamp, secret)

        assert sig1 != sig2

    def test_different_timestamp_different_signature(self):
        """Test that different timestamp produces different signature."""
        body = b"test body"
        secret = "my-secret"

        sig1 = generate_signature(body, 1000, secret)
        sig2 = generate_signature(body, 2000, secret)

        assert sig1 != sig2

    def test_different_secret_different_signature(self):
        """Test that different secret produces different signature."""
        body = b"test body"
        timestamp = 1234567890

        sig1 = generate_signature(body, timestamp, "secret1")
        sig2 = generate_signature(body, timestamp, "secret2")

        assert sig1 != sig2


class TestAuthResult:
    """Tests for AuthResult dataclass."""

    def test_success_result(self):
        """Test successful auth result."""
        result = AuthResult(success=True)
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        """Test failed auth result."""
        result = AuthResult(success=False, error="Some error")
        assert result.success is False
        assert result.error == "Some error"
