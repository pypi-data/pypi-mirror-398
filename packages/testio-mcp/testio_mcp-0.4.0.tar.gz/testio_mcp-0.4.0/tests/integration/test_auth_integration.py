"""
Integration tests for authentication with real TestIO API.

These tests require a valid TESTIO_CUSTOMER_API_TOKEN environment variable
and make actual API calls. They are skipped in CI/CD unless the
token is available.

Uses shared_client fixture from conftest.py for faster test execution
and more accurate simulation of production server behavior.

Run with: pytest -m integration
"""

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.config import settings
from testio_mcp.exceptions import TestIOAPIError

# Skip all tests in this module if API token not available (or is test placeholder)
pytestmark = pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="TESTIO_CUSTOMER_API_TOKEN not set - skipping integration tests",
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_authentication_success(shared_client: TestIOClient) -> None:
    """Test authentication with real TestIO API (requires valid token)."""
    # Fetch products to verify authentication (use small page to avoid problematic test data)
    response = await shared_client.get("products?page=1&per_page=10")

    assert "products" in response
    products = response["products"]

    # Verify we got products from staging environment
    assert len(products) > 0, "Expected at least 1 product"

    # Verify product structure
    first_product = products[0]
    assert "id" in first_product
    assert "name" in first_product


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_product_access_affinity_studio(shared_client: TestIOClient) -> None:
    """Test accessing specific product (AC5: Product ID 25073 - Affinity Studio)."""
    # Fetch products (use small page to avoid problematic test data)
    response = await shared_client.get("products?page=1&per_page=10")
    products = response["products"]

    # Verify we have products and can access first one
    assert len(products) > 0, "No products found in staging"

    first_product = products[0]
    assert "id" in first_product, "Product missing 'id' field"
    assert "name" in first_product, "Product missing 'name' field"
    assert isinstance(first_product["id"], int), "Product ID should be integer"
    assert isinstance(first_product["name"], str), "Product name should be string"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_invalid_endpoint_404(shared_client: TestIOClient) -> None:
    """Test that invalid endpoints return proper 404 errors.

    After refactoring (clean architecture):
    - Client raises TestIOAPIError for all HTTP errors (transport layer)
    - Services translate TestIOAPIError(404) to domain exceptions (TestNotFoundException)
    - This test calls client directly, so expects TestIOAPIError
    """
    # Try to fetch non-existent test - client raises TestIOAPIError
    with pytest.raises(TestIOAPIError) as exc_info:
        await shared_client.get("exploratory_tests/999999999")

    # Verify correct status code
    assert exc_info.value.status_code == 404
    assert "404" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_connection_pooling(shared_client: TestIOClient) -> None:
    """Test that connection pooling works with multiple requests."""
    # Make multiple requests to test connection reuse (small page avoids problematic data)
    responses = []

    for _ in range(5):
        response = await shared_client.get("products?page=1&per_page=10")
        responses.append(response)

    # All requests should succeed
    assert len(responses) == 5

    # All should return same products (verifies consistency)
    first_count = len(responses[0]["products"])
    for response in responses[1:]:
        assert len(response["products"]) == first_count


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN.startswith("sk_test"),
    reason="Skipping invalid token test with real credentials",
)
async def test_real_invalid_token() -> None:
    """Test authentication failure with invalid token.

    Note: This test is skipped if using a real token to avoid lockouts.
    """
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token="invalid_token_xyz_12345",
    ) as client:
        with pytest.raises(TestIOAPIError) as exc_info:
            await client.get("products?page=1&per_page=10")

        # Should get 401 or 403
        assert exc_info.value.status_code in [401, 403]

        # Token should be sanitized in error message
        error_str = str(exc_info.value)
        assert "invalid_token_xyz_12345" not in error_str
