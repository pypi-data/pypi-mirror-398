"""Unit tests for ProductService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.services.product_service import ProductService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_fetches_from_api_and_queries_db():
    """Verify list_products fetches from API, upserts, and queries DB with counts.

    STORY-058: Service always uses database query path to return enriched counts.
    """
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(return_value=mock_session)
    # Make session context manager work
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    customer_id = 123

    # Mock API response
    products_data = [
        {"id": 1, "name": "Product 1", "type": "website"},
        {"id": 2, "name": "Product 2", "type": "mobile_app_ios"},
    ]
    mock_client.get.return_value = {"products": products_data}

    service = ProductService(
        client=mock_client,
        cache=mock_cache,
        session_factory=mock_session_factory,
        customer_id=customer_id,
    )

    # Mock ProductRepository
    with patch("testio_mcp.services.product_service.ProductRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.upsert_product = AsyncMock()
        mock_repo_instance.commit = AsyncMock()
        # STORY-058: query_products returns enriched data with counts
        # STORY-083: bug_count removed
        mock_repo_instance.query_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "id": 1,
                        "name": "Product 1",
                        "type": "website",
                        "test_count": 5,
                        "feature_count": 2,
                        "tests_last_30_days": 1,
                        "tests_last_90_days": 3,
                        "last_test_end_at": None,
                    },
                    {
                        "id": 2,
                        "name": "Product 2",
                        "type": "mobile_app_ios",
                        "test_count": 3,
                        "feature_count": 1,
                        "tests_last_30_days": 0,
                        "tests_last_90_days": 2,
                        "last_test_end_at": None,
                    },
                ],
                "total_count": 2,
                "page": 1,
                "per_page": 50,
            }
        )

        # Act
        result = await service.list_products()

        # Assert
        # Verify API call
        mock_client.get.assert_called_once_with("products")

        # Verify DB upsert interaction (first session context)
        assert mock_repo_instance.upsert_product.call_count == 2
        mock_repo_instance.upsert_product.assert_any_call(products_data[0])
        mock_repo_instance.upsert_product.assert_any_call(products_data[1])
        mock_repo_instance.commit.assert_called_once()

        # Verify DB query interaction (second session context) - STORY-058
        # FIX: query_products now receives search and product_type for SQL filtering
        mock_repo_instance.query_products.assert_called_once_with(
            sort_by="title",  # Default sort_by when not specified
            sort_order="asc",
            page=1,
            per_page=50,
            offset=0,
            search=None,
            product_type=None,
        )

        # Verify result has enriched counts
        assert result["total_count"] == 2
        assert len(result["products"]) == 2
        assert result["products"][0]["test_count"] == 5
        # STORY-083: bug_count removed
        assert result["products"][0]["feature_count"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_handles_db_error_gracefully():
    """Verify list_products continues if DB update fails."""
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()
    mock_session_factory = MagicMock(side_effect=Exception("DB Connection Failed"))

    customer_id = 123

    # Mock API response
    products_data = [{"id": 1, "name": "Product 1"}]
    mock_client.get.return_value = {"products": products_data}

    service = ProductService(
        client=mock_client,
        cache=mock_cache,
        session_factory=mock_session_factory,
        customer_id=customer_id,
    )

    # Act
    # Should not raise exception
    result = await service.list_products()

    # Assert
    mock_client.get.assert_called_once()
    # Verify we still got results
    assert result["total_count"] == 1
    assert result["products"] == products_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_works_without_session_factory():
    """Verify list_products works when session_factory is None."""
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()

    # Mock API response
    products_data = [{"id": 1, "name": "Product 1"}]
    mock_client.get.return_value = {"products": products_data}

    service = ProductService(
        client=mock_client, cache=mock_cache, session_factory=None, customer_id=123
    )

    # Act
    result = await service.list_products()

    # Assert
    mock_client.get.assert_called_once()
    assert result["total_count"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_total_count_reflects_all_filtered_results():
    """Verify total_count reflects ALL filtered products, not just page size.

    FIX: Before this fix, total_count was returning len(page_items) instead of
    the total count of products matching the filter across all pages.

    Example:
    - 100 total products
    - 25 match search="studio"
    - Page 1 returns 10 items
    - total_count should be 25, NOT 10
    """
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    customer_id = 123

    # API returns many products (not all matching our filter)
    mock_client.get.return_value = {
        "products": [{"id": i, "name": f"Product {i}", "type": "website"} for i in range(100)]
    }

    service = ProductService(
        client=mock_client,
        cache=mock_cache,
        session_factory=mock_session_factory,
        customer_id=customer_id,
    )

    with patch("testio_mcp.services.product_service.ProductRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.upsert_product = AsyncMock()
        mock_repo_instance.commit = AsyncMock()

        # Repository returns: 10 items on page 1, but 25 TOTAL match the filter
        mock_repo_instance.query_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "id": i,
                        "name": f"Studio {i}",
                        "type": "website",
                        "test_count": 1,
                        "feature_count": 0,
                        "tests_last_30_days": 0,
                        "tests_last_90_days": 0,
                        "last_test_end_at": None,
                    }
                    for i in range(10)  # Only 10 items on this page
                ],
                "total_count": 25,  # But 25 total match the search filter
                "page": 1,
                "per_page": 10,
            }
        )

        # Act - search with pagination
        result = await service.list_products(search="studio", page=1, per_page=10)

        # Assert - total_count should be 25 (all matching), not 10 (page size)
        assert result["total_count"] == 25, (
            f"total_count should be 25 (all filtered products), got {result['total_count']}"
        )
        assert len(result["products"]) == 10  # Page has 10 items

        # Verify filters were passed to repository for SQL filtering
        mock_repo_instance.query_products.assert_called_once_with(
            sort_by="title",
            sort_order="asc",
            page=1,
            per_page=10,
            offset=0,
            search="studio",
            product_type=None,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_passes_product_type_filter_to_repo():
    """Verify product_type filter is passed to repository for SQL filtering."""
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_client.get.return_value = {"products": []}

    service = ProductService(
        client=mock_client,
        cache=mock_cache,
        session_factory=mock_session_factory,
        customer_id=123,
    )

    with patch("testio_mcp.services.product_service.ProductRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.upsert_product = AsyncMock()
        mock_repo_instance.commit = AsyncMock()
        mock_repo_instance.query_products = AsyncMock(
            return_value={
                "products": [],
                "total_count": 0,
                "page": 1,
                "per_page": 50,
            }
        )

        # Act - filter by product_type (list)
        await service.list_products(product_type=["website", "mobile_app_ios"])

        # Assert - product_type list passed to repository
        mock_repo_instance.query_products.assert_called_once_with(
            sort_by="title",
            sort_order="asc",
            page=1,
            per_page=50,
            offset=0,
            search=None,
            product_type=["website", "mobile_app_ios"],
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_normalizes_single_product_type_to_list():
    """Verify single product_type string is normalized to list for repository."""
    # Arrange
    mock_client = AsyncMock(spec=TestIOClient)
    mock_cache = MagicMock()
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_client.get.return_value = {"products": []}

    service = ProductService(
        client=mock_client,
        cache=mock_cache,
        session_factory=mock_session_factory,
        customer_id=123,
    )

    with patch("testio_mcp.services.product_service.ProductRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.upsert_product = AsyncMock()
        mock_repo_instance.commit = AsyncMock()
        mock_repo_instance.query_products = AsyncMock(
            return_value={
                "products": [],
                "total_count": 0,
                "page": 1,
                "per_page": 50,
            }
        )

        # Act - filter by single product_type (string)
        await service.list_products(product_type="website")

        # Assert - string converted to list for SQL IN clause
        mock_repo_instance.query_products.assert_called_once_with(
            sort_by="title",
            sort_order="asc",
            page=1,
            per_page=50,
            offset=0,
            search=None,
            product_type=["website"],  # String converted to list
        )
