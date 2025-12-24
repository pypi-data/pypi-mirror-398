"""
Unit tests for authentication and API client initialization.

These tests use pytest-httpx to mock HTTP responses, so they don't
require actual API credentials and can run in CI/CD environments.
"""

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from testio_mcp.client import TestIOClient
from testio_mcp.exceptions import TestIOAPIError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_client_initialization() -> None:
    """Test TestIOClient initializes with correct configuration."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="test_token_12345",
        max_concurrent_requests=5,
        max_connections=50,
        max_keepalive_connections=10,
        timeout=15.0,
    )

    assert client.base_url == "https://api.test.io/customer/v2"
    assert client._api_token == "test_token_12345"

    # Verify semaphore is assigned (global semaphore from ADR-002)
    # Note: The semaphore value may be from a previous test due to global singleton.
    # This is expected behavior for a global semaphore that limits ALL requests.
    assert client._semaphore is not None
    assert hasattr(client._semaphore, "_value")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_successful_authentication(httpx_mock: HTTPXMock) -> None:
    """Test successful API authentication with mocked response."""
    # Mock the products endpoint (used for health checks)
    httpx_mock.add_response(
        method="GET",
        url="https://api.test.io/customer/v2/products",
        json={
            "products": [
                {"id": 1, "name": "Product 1"},
                {"id": 2, "name": "Product 2"},
            ]
        },
        status_code=200,
    )

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="valid_token",
    ) as client:
        response = await client.get("products")

        assert "products" in response
        assert len(response["products"]) == 2
        assert response["products"][0]["name"] == "Product 1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failed_authentication_401(httpx_mock: HTTPXMock) -> None:
    """Test authentication failure with 401 Unauthorized."""
    httpx_mock.add_response(
        method="GET",
        url="https://api.test.io/customer/v2/products",
        status_code=401,
        json={"error": "Invalid token"},
    )

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="invalid_token",
    ) as client:
        with pytest.raises(TestIOAPIError) as exc_info:
            await client.get("products")

        assert exc_info.value.status_code == 401
        assert "401" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failed_authentication_403(httpx_mock: HTTPXMock) -> None:
    """Test authentication failure with 403 Forbidden."""
    httpx_mock.add_response(
        method="GET",
        url="https://api.test.io/customer/v2/products",
        status_code=403,
        json={"error": "Token expired"},
    )

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="expired_token",
    ) as client:
        with pytest.raises(TestIOAPIError) as exc_info:
            await client.get("products")

        assert exc_info.value.status_code == 403
        assert "403" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_not_in_error_messages(httpx_mock: HTTPXMock) -> None:
    """Test that API tokens are sanitized from error messages (SEC-002)."""
    secret_token = "super_secret_token_12345"  # pragma: allowlist secret

    httpx_mock.add_response(
        method="GET",
        url="https://api.test.io/customer/v2/products",
        status_code=401,
        json={"error": "Invalid token"},
    )

    async with TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token=secret_token,
    ) as client:
        with pytest.raises(TestIOAPIError) as exc_info:
            await client.get("products")

        error_message = str(exc_info.value)

        # Critical security check: token must NOT appear in error
        assert secret_token not in error_message
        assert "[REDACTED]" in error_message or "401" in error_message


@pytest.mark.unit
@pytest.mark.asyncio
async def test_context_manager_cleanup() -> None:
    """Test that async context manager properly cleans up client."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="test_token",
    )

    # Client should be None before entering context
    assert client._client is None

    async with client:
        # Client should exist inside context
        assert client._client is not None
        assert isinstance(client._client, AsyncClient)

    # Client should be cleaned up after exiting context
    assert client._client is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_without_context_manager() -> None:
    """Test that requests fail if context manager not used."""
    client = TestIOClient(
        base_url="https://api.test.io/customer/v2",
        api_token="test_token",
    )

    # Attempting request without entering context should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        await client.get("products")

    assert "not initialized" in str(exc_info.value).lower()
    assert "async with" in str(exc_info.value).lower()
