"""
Unit tests for logging security and token sanitization (AC14).

These tests verify that API tokens never appear in log output,
which is a critical security requirement (SEC-002).
"""

import logging
from io import StringIO

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.utilities.logging import JSONFormatter, configure_logging


@pytest.mark.unit
def test_token_sanitization_in_messages() -> None:
    """Test that tokens are sanitized from arbitrary messages."""
    secret_token = "sk_test_1234567890abcdef"  # pragma: allowlist secret

    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token=secret_token,
    )

    # Test various message formats
    test_messages = [
        f"Error with token: {secret_token}",
        f"Authorization: Token {secret_token}",
        f"Failed request: Authorization: Bearer {secret_token}",
        f"Debug: token={secret_token} status=failed",
    ]

    for message in test_messages:
        sanitized = client._sanitize_token_for_logging(message)

        # Token must not appear in sanitized output
        assert secret_token not in sanitized, f"Token leaked in: {message}"
        # Should contain redaction marker
        assert "[REDACTED]" in sanitized


@pytest.mark.unit
def test_authorization_header_sanitization() -> None:
    """Test that Authorization headers are sanitized in logs."""
    secret_token = "sk_test_abcd1234"  # pragma: allowlist secret

    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token=secret_token,
    )

    # Test Authorization header formats
    headers_to_test = [
        f"Authorization: Token {secret_token}",
        f"authorization: Token {secret_token}",
        f"Authorization: Bearer {secret_token}",
        f"AUTHORIZATION: token {secret_token}",
    ]

    for header in headers_to_test:
        sanitized = client._sanitize_token_for_logging(header)

        # Token must be redacted
        assert secret_token not in sanitized
        # Authorization keyword should remain
        assert "Authorization" in sanitized or "authorization" in sanitized.lower()
        # Should have redaction marker
        assert "[REDACTED]" in sanitized


@pytest.mark.unit
def test_empty_message_sanitization() -> None:
    """Test that empty messages don't cause errors."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="test_token",
    )

    # Empty and None messages should be handled gracefully
    assert client._sanitize_token_for_logging("") == ""
    assert client._sanitize_token_for_logging(None) is None


@pytest.mark.unit
def test_message_without_token() -> None:
    """Test that messages without tokens pass through unchanged."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="secret_token_xyz",
    )

    safe_messages = [
        "Request completed successfully",
        "Error: Invalid product ID",
        "Fetching data from endpoint",
    ]

    for message in safe_messages:
        sanitized = client._sanitize_token_for_logging(message)
        # Message without token should be unchanged (except no [REDACTED] added)
        assert message == sanitized


@pytest.mark.unit
def test_json_formatter_structure() -> None:
    """Test that JSONFormatter produces valid JSON output."""
    formatter = JSONFormatter()

    # Create a test log record
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    # Capture formatted output
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/test/path.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    # Should be valid JSON
    import json

    log_data = json.loads(formatted)

    # Check expected fields
    assert "timestamp" in log_data
    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "test_logger"
    assert log_data["message"] == "Test message"
    assert log_data["line"] == 42


@pytest.mark.unit
def test_configure_logging_json_format() -> None:
    """Test that configure_logging sets up JSON format correctly."""
    from testio_mcp.config import settings

    # Save original settings
    original_format = settings.LOG_FORMAT
    original_level = settings.LOG_LEVEL

    try:
        # Set to JSON format
        settings.LOG_FORMAT = "json"
        settings.LOG_LEVEL = "DEBUG"

        configure_logging()

        # Get root logger
        root_logger = logging.getLogger()

        # Should have handlers configured
        assert len(root_logger.handlers) > 0

        # Handler should use JSONFormatter
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

        # Log level should be DEBUG
        assert root_logger.level == logging.DEBUG

    finally:
        # Restore original settings
        settings.LOG_FORMAT = original_format
        settings.LOG_LEVEL = original_level


@pytest.mark.unit
def test_configure_logging_text_format() -> None:
    """Test that configure_logging sets up text format correctly."""
    from testio_mcp.config import settings

    original_format = settings.LOG_FORMAT
    original_level = settings.LOG_LEVEL

    try:
        settings.LOG_FORMAT = "text"
        settings.LOG_LEVEL = "INFO"

        configure_logging()

        root_logger = logging.getLogger()

        # Should have handlers
        assert len(root_logger.handlers) > 0

        # Handler should use standard Formatter (not JSON)
        handler = root_logger.handlers[0]
        assert not isinstance(handler.formatter, JSONFormatter)
        assert isinstance(handler.formatter, logging.Formatter)

    finally:
        settings.LOG_FORMAT = original_format
        settings.LOG_LEVEL = original_level


@pytest.mark.unit
def test_no_token_leaks_in_actual_logs() -> None:
    """Integration test: Verify tokens don't leak in actual log output."""
    secret_token = "sk_prod_super_secret_xyz"  # pragma: allowlist secret

    # Create a string buffer to capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    test_logger = logging.getLogger("token_leak_test")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.DEBUG)

    # Create client
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token=secret_token,
    )

    # Log a message that includes the token (simulate an error scenario)
    error_message = f"Request failed with token {secret_token}"
    sanitized = client._sanitize_token_for_logging(error_message)
    test_logger.error(sanitized)

    # Get logged output
    log_output = log_stream.getvalue()

    # CRITICAL: Token must NOT appear in logs
    assert secret_token not in log_output, "SECURITY FAILURE: Token leaked in logs!"
    assert "[REDACTED]" in log_output, "Token sanitization marker not found"
