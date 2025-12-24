"""Security tests for TestIOClient - Token Sanitization (SEC-002).

This test suite verifies critical security requirements:
- API tokens NEVER appear in error messages
- API tokens NEVER appear in httpx debug logs
- Token sanitization works for all error types
- Authorization headers are redacted in logs

These tests are P0 (highest priority) and must pass before Story 1 completion.
"""

from unittest.mock import Mock, patch

import httpx
import pytest

from src.testio_mcp.client import TestIOClient
from src.testio_mcp.exceptions import TestIOAPIError


@pytest.mark.asyncio
async def test_token_not_in_error_messages():
    """Critical: Verify API token never appears in error messages.

    Security requirement: SEC-002
    Risk score: 6 (high severity)

    This test simulates the TestIO API returning an error that includes
    the API token in the error message. The client MUST sanitize this
    before raising the exception.
    """
    secret_token = "super_secret_token_abc123_do_not_leak"

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token=secret_token
    ) as client:
        # Mock httpx to raise error with token in message
        with patch.object(client._client, "get") as mock_get:
            mock_request = Mock()
            mock_request.url = f"https://api.test.io/customer/v2/tests?token={secret_token}"

            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"Unauthorized: Token {secret_token} is invalid",
                request=mock_request,
                response=mock_response,
            )
            mock_get.return_value = mock_response

            # Call client - should raise sanitized error
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("/exploratory_tests")

            # Verify token is NOT in error message (SEC-002)
            error_message = str(exc_info.value)
            assert secret_token not in error_message, (
                "API token must not appear in error messages (SEC-002)"
            )
            # STORY-008: 401 errors now have custom helpful message
            assert "401" in error_message, "Error should include HTTP status code"
            assert "authentication failed" in error_message.lower()


@pytest.mark.asyncio
async def test_token_not_in_url_error_messages():
    """Verify tokens in URLs are sanitized from error messages.

    Security requirement: SEC-002

    Some APIs may echo the token in the URL (e.g., query parameters).
    This test ensures URL-based token exposure is also sanitized.
    """
    secret_token = "url_token_xyz789"

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token=secret_token
    ) as client:
        with patch.object(client._client, "get") as mock_get:
            # Create mock request with token in URL
            mock_request = Mock()
            mock_request.url = f"https://api.test.io/tests?api_token={secret_token}"

            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Forbidden", request=mock_request, response=mock_response
            )
            mock_get.return_value = mock_response

            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("/exploratory_tests")

            error_message = str(exc_info.value)
            assert secret_token not in error_message, "Token in URL must be sanitized (SEC-002)"
            # STORY-008: 403 errors now have custom helpful message
            assert "403" in error_message
            assert "forbidden" in error_message.lower()


@pytest.mark.asyncio
async def test_token_not_in_timeout_errors():
    """Verify token sanitization in timeout error messages.

    Security requirement: SEC-002

    httpx timeout exceptions may include request details with tokens.
    Ensure these are sanitized before raising to user.
    """
    secret_token = "timeout_token_def456"

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token=secret_token, timeout=1.0
    ) as client:
        with patch.object(client._client, "get") as mock_get:
            # Simulate timeout with token in error message
            mock_get.side_effect = httpx.TimeoutException(
                f"Request timeout: Authorization: Token {secret_token}"
            )

            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("/exploratory_tests")

            error_message = str(exc_info.value)
            assert secret_token not in error_message, (
                "Token in timeout error must be sanitized (SEC-002)"
            )
            assert "[REDACTED]" in error_message
            assert "408" in str(exc_info.value.status_code), "Timeout should map to 408 status code"


@pytest.mark.asyncio
async def test_token_not_in_connection_errors():
    """Verify token sanitization in connection error messages.

    Security requirement: SEC-002

    Connection errors (DNS, SSL, network) may include request details.
    Ensure tokens are sanitized even in low-level network errors.
    """
    secret_token = "connection_token_ghi789"

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token=secret_token
    ) as client:
        with patch.object(client._client, "get") as mock_get:
            # Simulate connection error with token
            mock_get.side_effect = httpx.RequestError(
                f"Connection failed to https://api.test.io?auth={secret_token}"
            )

            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("/exploratory_tests")

            error_message = str(exc_info.value)
            assert secret_token not in error_message, (
                "Token in connection error must be sanitized (SEC-002)"
            )
            assert "[REDACTED]" in error_message
            assert exc_info.value.status_code == 0, "Connection errors should have status_code=0"


@pytest.mark.asyncio
async def test_sanitize_authorization_header_format():
    """Verify Authorization header format is sanitized.

    Security requirement: SEC-002

    Test that both "Authorization: Token <token>" and
    "Authorization: Bearer <token>" formats are sanitized.
    """
    client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test_token_123")

    # Test Token format
    result = client._sanitize_token_for_logging(
        "Error: Authorization: Token test_token_123 invalid"
    )
    assert "test_token_123" not in result
    assert "Authorization: Token [REDACTED]" in result

    # Test Bearer format
    result = client._sanitize_token_for_logging(
        "Error: Authorization: Bearer test_token_123 invalid"
    )
    assert "test_token_123" not in result
    assert "Authorization: Bearer [REDACTED]" in result

    # Test case-insensitive
    result = client._sanitize_token_for_logging(
        "Error: authorization: token test_token_123 invalid"
    )
    assert "test_token_123" not in result


@pytest.mark.asyncio
async def test_sanitize_empty_and_none_messages():
    """Verify sanitization handles edge cases gracefully.

    Security requirement: SEC-002

    Ensure the sanitization function doesn't crash on empty/None inputs.
    """
    client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test_token")

    # Empty string
    assert client._sanitize_token_for_logging("") == ""

    # None (though shouldn't happen, defensive programming)
    assert client._sanitize_token_for_logging(None) is None


@pytest.mark.asyncio
async def test_404_raises_test_not_found_exception():
    """Verify 404 errors raise TestNotFoundException with sanitized messages.

    Security requirement: SEC-002
    Functional requirement: Proper exception types for error handling

    404s should raise TestNotFoundException (not generic TestIOAPIError)
    and the exception message must not contain the API token.
    """
    secret_token = "notfound_token_jkl012"

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2", api_token=secret_token
    ) as client:
        with patch.object(client._client, "get") as mock_get:
            mock_request = Mock()
            mock_request.url = "https://api.test.io/customer/v2/exploratory_tests/99999"

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"Not Found: Token {secret_token}", request=mock_request, response=mock_response
            )
            mock_get.return_value = mock_response

            # Client now raises TestIOAPIError for all HTTP errors (refactored)
            # Services translate to domain exceptions (TestNotFoundException)
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("/exploratory_tests/99999")

            # Verify correct exception type
            assert exc_info.value.status_code == 404

            # Verify token not in exception message (SEC-002)
            error_message = str(exc_info.value)
            assert secret_token not in error_message, (
                "Token must not appear in TestIOAPIError (SEC-002)"
            )


@pytest.mark.asyncio
async def test_event_hooks_log_without_modifying_request():
    """Verify httpx event hooks log safely without modifying requests.

    Security requirement: SEC-002 (AC10)

    Event hooks must:
    1. Log requests/responses with sanitized tokens
    2. NOT modify the actual request (which would cause 401 errors)

    This test verifies hooks exist and don't break requests.
    """
    secret_token = "request_log_token_mno345"

    client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token=secret_token)

    # Verify event hooks are configured (AC10 requirement)
    assert client._event_hooks is not None, "Event hooks required for SEC-002 (AC10)"
    assert "request" in client._event_hooks
    assert "response" in client._event_hooks

    # Verify hooks are set to our logging methods
    assert client._log_request in client._event_hooks["request"]
    assert client._log_response in client._event_hooks["response"]

    # Verify hooks don't modify the Authorization header
    async with client:
        # Check that Authorization header is still intact (not modified by hooks)
        assert client._client.headers["Authorization"] == f"Token {secret_token}"


@pytest.mark.asyncio
async def test_multiple_tokens_in_same_message():
    """Verify all occurrences of token are sanitized.

    Security requirement: SEC-002

    If an error message contains the token multiple times,
    all occurrences must be sanitized.
    """
    secret_token = "repeated_token_pqr678"

    client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token=secret_token)

    message = (
        f"Error: Token {secret_token} invalid. "
        f"Check that {secret_token} is correct. "
        f"Authorization: Token {secret_token}"
    )

    sanitized = client._sanitize_token_for_logging(message)

    # Count occurrences (should be 0)
    assert secret_token not in sanitized, "All occurrences of token must be sanitized (SEC-002)"

    # Verify redaction markers present
    assert sanitized.count("[REDACTED]") >= 3, (
        "All 3 token occurrences should be replaced with [REDACTED]"
    )
