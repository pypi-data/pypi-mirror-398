"""Unit tests for STORY-008: Comprehensive Error Handling & Polish.

Tests new error handling features:
- AC1: Authentication errors (401/403)
- AC2: Retry logic with exponential backoff
- AC3: Rate limiting (429)
- AC8: Request timeout handling
"""

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.exceptions import TestIOAPIError


class TestAuthenticationErrors:
    """Test authentication error handling (STORY-008 AC1)."""

    @pytest.mark.asyncio
    async def test_401_authentication_error_message(self):
        """Test 401 error raises TestIOAPIError with helpful message."""
        # Create test client
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Mock the internal _client to raise HTTPStatusError
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = Exception("Unauthorized")

            # Create HTTPStatusError-like exception
            from httpx import Request, Response

            mock_request = Request("GET", "https://api.test.io/customer/v2/products")
            mock_response_obj = Response(401, request=mock_request)

            import httpx

            http_error = httpx.HTTPStatusError(
                message="Unauthorized",
                request=mock_request,
                response=mock_response_obj,
            )

            client._client.get = AsyncMock(side_effect=http_error)

            # Test that 401 raises TestIOAPIError with helpful message
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("products")

            # Verify error message contains helpful guidance
            error_msg = exc_info.value.message
            assert "❌" in error_msg
            assert "401" in error_msg
            assert "authentication failed" in error_msg.lower()
            assert ".env" in error_msg.lower()
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_403_forbidden_error_message(self):
        """Test 403 error raises TestIOAPIError with helpful message."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Create HTTPStatusError for 403
            from httpx import Request, Response

            mock_request = Request("GET", "https://api.test.io/customer/v2/products")
            mock_response = Response(403, request=mock_request)

            import httpx

            http_error = httpx.HTTPStatusError(
                message="Forbidden", request=mock_request, response=mock_response
            )

            client._client.get = AsyncMock(side_effect=http_error)

            # Test that 403 raises TestIOAPIError with helpful message
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("products")

            # Verify error message
            error_msg = exc_info.value.message
            assert "❌" in error_msg
            assert "403" in error_msg
            assert "forbidden" in error_msg.lower()
            assert "permission" in error_msg.lower()
            assert exc_info.value.status_code == 403


class TestRateLimiting:
    """Test rate limiting error handling (STORY-008 AC3)."""

    @pytest.mark.asyncio
    async def test_429_rate_limit_with_retry_after_header(self):
        """Test 429 error parses Retry-After header."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Create HTTPStatusError for 429 with Retry-After header
            from httpx import Request, Response

            mock_request = Request("GET", "https://api.test.io/customer/v2/products")
            mock_response = Response(429, request=mock_request, headers={"Retry-After": "60"})

            import httpx

            http_error = httpx.HTTPStatusError(
                message="Too Many Requests", request=mock_request, response=mock_response
            )

            client._client.get = AsyncMock(side_effect=http_error)

            # Test that 429 raises TestIOAPIError with Retry-After info
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("products")

            # Verify error message includes Retry-After time
            error_msg = exc_info.value.message
            assert "❌" in error_msg
            assert "429" in error_msg
            assert "rate limit" in error_msg.lower()
            assert "60 seconds" in error_msg
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_429_rate_limit_default_retry_after(self):
        """Test 429 error defaults to 30s when no Retry-After header."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Create HTTPStatusError for 429 WITHOUT Retry-After header
            from httpx import Request, Response

            mock_request = Request("GET", "https://api.test.io/customer/v2/products")
            mock_response = Response(429, request=mock_request, headers={})

            import httpx

            http_error = httpx.HTTPStatusError(
                message="Too Many Requests", request=mock_request, response=mock_response
            )

            client._client.get = AsyncMock(side_effect=http_error)

            # Test that 429 defaults to 30 seconds
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("products")

            error_msg = exc_info.value.message
            assert "30 seconds" in error_msg

    @pytest.mark.asyncio
    async def test_429_rate_limit_http_date_retry_after(self):
        """Test 429 error parses HTTP-date format Retry-After header."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Create HTTPStatusError for 429 with HTTP-date Retry-After
            # HTTP-date format: "Wed, 21 Oct 2015 07:28:00 GMT"
            # Use a date 120 seconds in the future
            from datetime import datetime, timedelta
            from email.utils import format_datetime

            from httpx import Request, Response

            future_time = datetime.now(UTC) + timedelta(seconds=120)
            http_date = format_datetime(future_time, usegmt=True)

            mock_request = Request("GET", "https://api.test.io/customer/v2/products")
            mock_response = Response(429, request=mock_request, headers={"Retry-After": http_date})

            import httpx

            http_error = httpx.HTTPStatusError(
                message="Too Many Requests", request=mock_request, response=mock_response
            )

            client._client.get = AsyncMock(side_effect=http_error)

            # Test that 429 parses HTTP-date
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get("products")

            error_msg = exc_info.value.message
            # Should be approximately 120 seconds (allow ±5s for test execution time)
            assert (
                "120 seconds" in error_msg
                or "119 seconds" in error_msg
                or "118 seconds" in error_msg
            )


class TestRetryLogic:
    """Test retry logic with exponential backoff (STORY-008 AC2)."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_success_on_third_attempt(self):
        """Test retry succeeds after 2 timeouts."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Mock get() to fail twice with timeout, then succeed
            successful_response = {"products": [{"id": 1, "name": "Test"}]}

            call_count = 0

            async def mock_get_with_timeouts(endpoint, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count <= 2:
                    # First two calls: raise timeout error
                    raise TestIOAPIError(message="Request timeout after 30s", status_code=408)
                else:
                    # Third call: succeed
                    return successful_response

            client.get = mock_get_with_timeouts

            # Test retry logic
            with patch("asyncio.sleep", new=AsyncMock()):  # Speed up test
                result = await client.get_with_retry("products", retries=3)

            # Verify success after retries
            assert result == successful_response
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_5xx_server_error(self):
        """Test retry on 5xx server errors."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            successful_response = {"products": []}

            call_count = 0

            async def mock_get_with_5xx(endpoint, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    # First call: 503 Service Unavailable
                    raise TestIOAPIError(message="Service Unavailable", status_code=503)
                else:
                    # Second call: succeed
                    return successful_response

            client.get = mock_get_with_5xx

            # Test retry logic
            with patch("asyncio.sleep", new=AsyncMock()):
                result = await client.get_with_retry("products", retries=3)

            assert result == successful_response
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff_timing(self):
        """Test exponential backoff delays (1s, 2s, 4s)."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Mock get() to always raise timeout
            async def mock_get_timeout(endpoint, **kwargs):
                raise TestIOAPIError(message="Timeout", status_code=408)

            client.get = mock_get_timeout

            # Track sleep calls
            sleep_calls = []

            async def mock_sleep(seconds):
                sleep_calls.append(seconds)

            # Test retry logic fails after all attempts (4 total attempts = default)
            with patch("asyncio.sleep", new=mock_sleep):
                with pytest.raises(TestIOAPIError):
                    await client.get_with_retry("products")  # Uses default retries=4

            # Verify exponential backoff: 2^0=1, 2^1=2, 2^2=4
            # (4th attempt fails immediately without sleep)
            assert sleep_calls == [1, 2, 4]

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_client_errors(self):
        """Test that 4xx errors are NOT retried."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            call_count = 0

            async def mock_get_404(endpoint, **kwargs):
                nonlocal call_count
                call_count += 1
                raise TestIOAPIError(message="Not Found", status_code=404)

            client.get = mock_get_404

            # Test that 404 is NOT retried
            with pytest.raises(TestIOAPIError) as exc_info:
                await client.get_with_retry("products/999", retries=3)

            # Should only call once (no retries for 4xx)
            assert call_count == 1
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_failure_message(self):
        """Test final error message after all retries exhausted."""
        client = TestIOClient(base_url="https://api.test.io/customer/v2", api_token="test-token")

        async with client:
            # Mock get() to always fail with 503
            async def mock_get_503(endpoint, **kwargs):
                raise TestIOAPIError(message="Service Unavailable", status_code=503)

            client.get = mock_get_503

            # Test retry exhaustion with default retries=4
            with patch("asyncio.sleep", new=AsyncMock()):
                with pytest.raises(TestIOAPIError) as exc_info:
                    await client.get_with_retry("products")  # Uses default retries=4

            # Verify final error message mentions retries
            error_msg = exc_info.value.message
            assert "after 4 attempts" in error_msg
            assert "❌" in error_msg
            assert exc_info.value.status_code == 503


class TestTimeoutHandling:
    """Test request timeout handling (STORY-008 AC8)."""
