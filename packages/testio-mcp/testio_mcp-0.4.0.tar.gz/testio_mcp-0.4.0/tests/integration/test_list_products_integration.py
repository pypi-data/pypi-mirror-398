"""Integration tests for list_products tool with real TestIO API.

Tests the complete flow from tool → service → API with real data.

Uses shared_client and shared_cache fixtures from conftest.py for faster
test execution and more accurate simulation of production server behavior.

These tests require:
- TESTIO_CUSTOMER_API_TOKEN environment variable

Usage:
    # Run with real API token
    uv run pytest tests/integration/test_list_products_integration.py -m integration
"""

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.config import settings
from testio_mcp.database import PersistentCache
from testio_mcp.services.product_service import ProductService


@pytest.mark.integration
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
@pytest.mark.asyncio
async def test_list_products_with_real_api(
    shared_client: TestIOClient,
    shared_cache: PersistentCache,
) -> None:
    """Integration test with real API - list all products.

    This test verifies the complete flow:
    1. Service fetches from real API
    2. Data is correctly parsed
    3. Response matches expected structure

    Usage:
        uv run pytest -m integration
    """
    # Create service with real dependencies
    service = ProductService(client=shared_client, cache=shared_cache)

    # Execute
    result = await service.list_products()

    # Verify: Response structure
    assert "total_count" in result
    assert "filters_applied" in result
    assert "products" in result

    # Verify: Total count matches products list length
    assert result["total_count"] == len(result["products"])
    assert result["total_count"] > 0  # Should have at least some products

    # Verify: Filters applied correctly (no filters)
    assert result["filters_applied"]["search"] is None
    assert result["filters_applied"]["product_type"] is None

    # Verify: Product structure
    if result["products"]:
        product = result["products"][0]
        assert "id" in product
        assert "name" in product
        assert "type" in product
        # description is optional


@pytest.mark.integration
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
@pytest.mark.asyncio
async def test_list_products_with_search_filter(
    shared_client: TestIOClient,
    shared_cache: PersistentCache,
) -> None:
    """Test filtering products by search term.

    Note: This test assumes there's at least one product in the account.
    We'll search for a term that should exist in at least one product name.

    Usage:
        uv run pytest -m integration
    """
    service = ProductService(client=shared_client, cache=shared_cache)

    # First, get all products to find a valid search term
    all_products = await service.list_products()
    assert all_products["total_count"] > 0, "Account must have at least one product"

    # Extract first word from first product name for searching
    first_product_name = all_products["products"][0]["name"]
    # Use first 4+ characters or first word as search term
    search_term = first_product_name[:4].lower()

    # Create new service with fresh cache to avoid cache hit
    fresh_cache = shared_cache
    service_fresh = ProductService(client=shared_client, cache=fresh_cache)

    # Execute with search filter
    result = await service_fresh.list_products(search=search_term)

    # Verify: Response structure
    assert "total_count" in result
    assert "products" in result

    # Verify: Search filter was applied
    assert result["filters_applied"]["search"] == search_term

    # Verify: All results contain search term (case-insensitive)
    for product in result["products"]:
        name_lower = (product.get("name") or "").lower()
        desc_lower = (product.get("description") or "").lower()
        assert search_term in name_lower or search_term in desc_lower, (
            f"Product {product['name']} does not contain search term '{search_term}'"
        )


@pytest.mark.integration
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
@pytest.mark.asyncio
async def test_list_products_with_type_filter(
    shared_client: TestIOClient,
    shared_cache: PersistentCache,
) -> None:
    """Test filtering products by product type.

    Usage:
        uv run pytest -m integration
    """
    service = ProductService(client=shared_client, cache=shared_cache)

    # First, get all products to find a valid product type
    all_products = await service.list_products()
    assert all_products["total_count"] > 0, "Account must have at least one product"

    # Extract product type from first product
    product_type = all_products["products"][0]["type"]

    # Create new service with fresh cache
    fresh_cache = shared_cache
    service_fresh = ProductService(client=shared_client, cache=fresh_cache)

    # Execute with product_type filter
    result = await service_fresh.list_products(product_type=product_type)

    # Verify: Response structure
    assert "total_count" in result
    assert "products" in result

    # Verify: Type filter was applied
    assert result["filters_applied"]["product_type"] == product_type

    # Verify: All results have the specified type
    for product in result["products"]:
        assert product["type"] == product_type, (
            f"Product {product['name']} has type {product['type']}, expected {product_type}"
        )


@pytest.mark.integration
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
@pytest.mark.asyncio
async def test_list_products_no_results_for_nonexistent_search(
    shared_client: TestIOClient,
    shared_cache: PersistentCache,
) -> None:
    """Test that searching for nonexistent term returns empty list (not an error).

    This test always runs when TESTIO_CUSTOMER_API_TOKEN is available,
    as it uses a search term guaranteed not to exist.

    Usage:
        uv run pytest -m integration
    """
    service = ProductService(client=shared_client, cache=shared_cache)

    # Execute with search term that definitely won't match
    result = await service.list_products(search="xyznonexistent123456789")

    # Verify: Empty result (not an error)
    assert result["total_count"] == 0
    assert result["products"] == []
    assert result["filters_applied"]["search"] == "xyznonexistent123456789"


# REMOVED: test_list_products_different_cache_keys_for_different_filters
# This test is now INVALID - cache-raw pattern intentionally uses the SAME
# cache key for all filter combinations to maximize cache hit rate.
# See: test_cache_raw_pattern_with_filters in test_cache_integration.py for
# the correct behavior verification.
