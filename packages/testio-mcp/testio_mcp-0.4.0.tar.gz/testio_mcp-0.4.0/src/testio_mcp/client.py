"""TestIO Customer API HTTP client with security, connection pooling, and concurrency control.

This module provides a secure, async HTTP client wrapper for the TestIO Customer API
with the following features:

- Token sanitization (SEC-002): API tokens are redacted from all logs and error messages
- Global concurrency limiting (ADR-002): Semaphore limits concurrent requests across all instances
- Connection pooling (ADR-001): Reuses HTTP connections for performance
- Automatic retries: Handles transient failures with exponential backoff
- Type safety: Full type hints for static analysis

Security:
    - API tokens are NEVER exposed in error messages or logs
    - All httpx debug output is sanitized via event hooks
    - Tokens stored as private attributes with underscore prefix
"""

import asyncio
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, cast

import httpx

from .exceptions import TestIOAPIError


class TestIOClient:
    """Secure HTTP client for TestIO Customer API with connection pooling and concurrency control.

    This client enforces security best practices and performance optimizations:

    Security (SEC-002):
        - API tokens are sanitized from all error messages
        - httpx debug logging is sanitized via event hooks
        - Tokens never appear in exception messages or logs

    Performance (ADR-001):
        - Connection pooling reuses HTTP connections
        - Keep-alive connections reduce latency by 50-200ms
        - Configurable pool size and timeout

    Concurrency (ADR-002):
        - Global semaphore limits concurrent requests
        - Shared across all client instances
        - Prevents API rate limiting

    Example:
        ```python
        async with TestIOClient(
            base_url="https://api.test.io/customer/v2",
            api_token=settings.TESTIO_CUSTOMER_API_TOKEN
        ) as client:
            data = await client.get("exploratory_tests/12345")
        ```

    Attributes:
        base_url: TestIO API base URL
        _api_token: API token (private, for sanitization only)
        _client: httpx.AsyncClient instance (connection pooling)
        _semaphore: Global semaphore for concurrency control
        _token_pattern: Compiled regex for fast token replacement
    """

    __test__ = False  # Not a pytest test class

    def __init__(
        self,
        base_url: str,
        api_token: str,
        max_concurrent_requests: int = 10,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 30.0,
        semaphore: asyncio.Semaphore | None = None,
    ):
        """Initialize TestIO API client with security and performance settings.

        Args:
            base_url: Base URL for TestIO Customer API
            api_token: Authentication token (will be sanitized in logs/errors)
            max_concurrent_requests: Max concurrent requests (used if no semaphore)
            max_connections: Maximum number of concurrent connections
            max_keepalive_connections: Maximum number of idle connections to maintain
            timeout: Request timeout in seconds
            semaphore: Optional shared semaphore for global concurrency control (ADR-002).
                      If not provided, creates a new semaphore with max_concurrent_requests limit.
                      For production: server should pass a shared semaphore.
                      For tests: pass None to get isolated semaphores per client.

        Security:
            The api_token is stored privately and used ONLY for sanitization.
            It is NEVER logged or included in error messages.
        """
        self.base_url = base_url
        self._api_token = api_token  # Private: for sanitization only
        self._client: httpx.AsyncClient | None = None

        # Dependency injection: use provided semaphore or create new one (ADR-002)
        # Production: server passes shared semaphore for global limiting
        # Tests: each client gets its own semaphore (no test pollution)
        self._semaphore = semaphore or asyncio.Semaphore(max_concurrent_requests)

        # Pre-compile regex pattern for fast token sanitization
        self._token_pattern = re.compile(re.escape(api_token))

        # Store typed httpx configuration objects (avoids dict[str, object] type issues)
        self._timeout = httpx.Timeout(timeout)
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._headers = {
            "Authorization": f"Token {api_token}",
            "User-Agent": "TestIO-MCP-Server/1.0",
        }
        self._event_hooks: dict[str, list[Any]] = {
            # SEC-002: Log sanitization hooks (for observability, not request modification)
            "request": [self._log_request],
            "response": [self._log_response],
        }

    async def __aenter__(self) -> "TestIOClient":
        """Create HTTP client on context enter.

        Returns:
            Self for use in async with statement
        """
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self._timeout,
            limits=self._limits,
            event_hooks=self._event_hooks,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Clean up HTTP client on context exit.

        Properly closes all connections and releases resources.
        """
        if self._client:
            await self._client.aclose()
            self._client = None

    def _sanitize_token_for_logging(self, message: str) -> str:
        """Replace API token with [REDACTED] in log messages.

        This is a critical security function (SEC-002) that ensures API tokens
        NEVER appear in logs, error messages, or any user-facing output.

        The function performs two passes:
        1. Replace exact token string with [REDACTED]
        2. Replace Authorization header format with sanitized version

        Args:
            message: Log message or error string that might contain token

        Returns:
            Sanitized message with token replaced by [REDACTED]

        Example:
            >>> client._sanitize_token_for_logging("Error: Token abc123 invalid")
            "Error: Token [REDACTED] invalid"
        """
        if not message:
            return message

        # Pass 1: Replace full token with redacted marker (fast regex)
        sanitized = self._token_pattern.sub("[REDACTED]", message)

        # Pass 2: Also check Authorization header format
        # Matches: "Authorization: Token <anything>" or "Authorization: Bearer <anything>"
        sanitized = re.sub(
            r"Authorization:\s*(Token|Bearer)\s+\S+",
            r"Authorization: \1 [REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )

        return sanitized

    async def _log_request(self, request: httpx.Request) -> None:
        """Event hook: Log outgoing requests with sanitized tokens (SEC-002).

        This hook is called by httpx for observability purposes. It logs
        request details with tokens redacted, but does NOT modify the actual
        request that gets sent to the API.

        Critical: The request object should NOT be modified here, as that would
        break actual API calls (causing 401 errors).

        Args:
            request: httpx Request object (read-only for logging)
        """
        # Sanitize the request URL and headers for safe logging
        safe_url = self._sanitize_token_for_logging(str(request.url))

        # Log request with sanitized information (tokens redacted)
        # This satisfies SEC-002 without modifying the actual request
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"HTTP Request: {request.method} {safe_url}")

    async def _log_response(self, response: httpx.Response) -> None:
        """Event hook: Log API responses with sanitized tokens (SEC-002).

        This hook is called by httpx for observability purposes. It logs
        response details with any token appearances redacted.

        Args:
            response: httpx Response object (read-only for logging)
        """
        import logging

        logger = logging.getLogger(__name__)
        safe_url = self._sanitize_token_for_logging(str(response.url))
        logger.debug(f"HTTP Response: {response.status_code} from {safe_url}")

    async def get_with_retry(
        self, endpoint: str, retries: int = 4, **kwargs: Any
    ) -> dict[str, Any]:
        """Make GET request with automatic retry and exponential backoff.

        Retries requests that fail due to:
        - Timeouts (httpx.TimeoutException)
        - Server errors (5xx status codes)

        Does NOT retry:
        - Client errors (4xx except 429 which is handled separately)
        - Connection errors (fail immediately)

        Args:
            endpoint: API endpoint path (e.g., "exploratory_tests/12345")
            retries: Maximum number of attempts including initial (default: 4)
            **kwargs: Additional arguments passed to get()

        Returns:
            JSON response as dictionary

        Raises:
            TestIOAPIError: If all retry attempts fail or non-retryable error occurs

        Example:
            ```python
            # Automatically retries on timeout or 5xx errors (4 total attempts)
            data = await client.get_with_retry("exploratory_tests/12345", retries=4)
            ```

        Retry Strategy (STORY-008 AC2):
            - Attempt 1: Immediate
            - Attempt 2: Wait 1 second (2^0) then retry
            - Attempt 3: Wait 2 seconds (2^1) then retry
            - Attempt 4: Wait 4 seconds (2^2) then retry
        """
        last_exception: Exception | None = None

        for attempt in range(retries):
            try:
                return await self.get(endpoint, **kwargs)

            except TestIOAPIError as e:
                # Retry on timeouts (408) and server errors (5xx)
                is_retryable = e.status_code == 408 or (500 <= e.status_code < 600)

                if is_retryable:
                    last_exception = e

                    if attempt == retries - 1:
                        # Final attempt failed - raise with retry context
                        error_type = "timeout" if e.status_code == 408 else "API error"
                        raise TestIOAPIError(
                            message=(
                                f"❌ Request {error_type} (HTTP {e.status_code}) "
                                f"after {retries} attempts\n"
                                f"ℹ️  The TestIO API may be slow or experiencing issues\n"
                                f"💡 Please try again later. If the issue persists, "
                                "contact TestIO support."
                            ),
                            status_code=e.status_code,
                        ) from e

                    # Wait before retrying (exponential backoff: 1s, 2s, 4s)
                    wait_time = 2**attempt
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"API error {e.status_code} on attempt {attempt + 1}/{retries}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Non-retryable error (4xx, 401, 403, 404, 429, etc.) - raise immediately
                raise

            except Exception as e:
                # Unexpected error - don't retry, raise immediately
                last_exception = e
                raise

        # Should never reach here, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed unexpectedly")

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make GET request to TestIO API with concurrency control and token sanitization.

        This method:
        1. Acquires global semaphore slot (limits concurrent requests)
        2. Makes HTTP GET request via connection pool
        3. Handles errors with sanitized messages (tokens redacted)
        4. Returns JSON response

        Args:
            endpoint: API endpoint path (e.g., "exploratory_tests/12345")
            **kwargs: Additional arguments passed to httpx.get()

        Returns:
            JSON response as dictionary

        Raises:
            RuntimeError: If client not initialized (use 'async with' context manager)
            TestNotFoundException: If endpoint returns 404
            TestIOAPIError: If response status is 4xx or 5xx

        Example:
            ```python
            async with client:
                data = await client.get("exploratory_tests/12345")
                bugs = await client.get("bugs", params={"filter_test_cycle_ids": "12345"})
            ```

        Security:
            All error messages are sanitized before raising exceptions.
            API tokens NEVER appear in error messages or logs.
        """
        if not self._client:
            raise RuntimeError(
                "TestIOClient not initialized. Use 'async with TestIOClient(...) as client:'"
            )

        # Acquire semaphore slot (ADR-002: global concurrency limiting)
        # This blocks if semaphore limit reached, ensuring we don't overwhelm API
        async with self._semaphore:
            try:
                response = await self._client.get(endpoint, **kwargs)
                response.raise_for_status()

                # Validate JSON response shape and cast to expected type
                data = response.json()
                if not isinstance(data, dict):
                    data_type = type(data).__name__
                    raise TestIOAPIError(
                        message=f"Unexpected API response: expected dict, got {data_type}",
                        status_code=response.status_code,
                    )
                return cast(dict[str, Any], data)

            except httpx.HTTPStatusError as e:
                # SEC-002: Sanitize all error messages before raising
                safe_message = self._sanitize_token_for_logging(str(e))
                safe_url = self._sanitize_token_for_logging(str(e.request.url))

                # Special handling for authentication errors (STORY-008 AC1)
                if e.response.status_code == 401:
                    raise TestIOAPIError(
                        message=(
                            "❌ Customer API authentication failed (HTTP 401 Unauthorized)\n"
                            "ℹ️  Your API token is invalid or has expired\n"
                            "💡 Please verify TESTIO_CUSTOMER_API_TOKEN in .env file"
                        ),
                        status_code=401,
                    ) from e

                if e.response.status_code == 403:
                    raise TestIOAPIError(
                        message=(
                            "❌ Access forbidden (HTTP 403 Forbidden)\n"
                            "ℹ️  Your API token does not have permission to access this resource\n"
                            "💡 Contact your TestIO administrator to verify your "
                            "API token permissions"
                        ),
                        status_code=403,
                    ) from e

                # Special handling for rate limiting (STORY-008 AC3)
                if e.response.status_code == 429:
                    # Parse Retry-After header (seconds or HTTP-date format)
                    retry_after = e.response.headers.get("Retry-After", "30")
                    try:
                        # Try parsing as integer seconds first
                        wait_time = int(retry_after)
                    except ValueError:
                        # If not an integer, try parsing as HTTP-date
                        try:
                            retry_datetime = parsedate_to_datetime(retry_after)
                            now = datetime.now(UTC)
                            wait_time = max(int((retry_datetime - now).total_seconds()), 0)
                        except (TypeError, ValueError):
                            # If both parsing methods fail, default to 30s
                            wait_time = 30

                    raise TestIOAPIError(
                        message=(
                            f"❌ Rate limit reached (HTTP 429 Too Many Requests)\n"
                            f"ℹ️  You've made too many requests to the TestIO API\n"
                            f"💡 Please wait {wait_time} seconds before retrying. "
                            "Consider reducing query frequency."
                        ),
                        status_code=429,
                    ) from e

                # Always raise TestIOAPIError for HTTP errors
                # Let service layer translate to domain-specific exceptions
                # (e.g., TestNotFoundException, ProductNotFoundException)
                raise TestIOAPIError(
                    message=f"HTTP {e.response.status_code}: {safe_message} (URL: {safe_url})",
                    status_code=e.response.status_code,
                ) from e

            except httpx.TimeoutException as e:
                # SEC-002: Sanitize timeout errors
                safe_message = self._sanitize_token_for_logging(str(e))
                # Access timeout from typed attribute
                timeout_sec = self._timeout.read if self._timeout.read is not None else 30.0
                raise TestIOAPIError(
                    message=f"Request timeout after {timeout_sec}s: {safe_message}",
                    status_code=408,
                ) from e

            except httpx.RequestError as e:
                # SEC-002: Sanitize connection errors
                safe_message = self._sanitize_token_for_logging(str(e))
                raise TestIOAPIError(
                    message=f"Request failed: {safe_message}",
                    status_code=0,  # No HTTP status for connection errors
                ) from e
