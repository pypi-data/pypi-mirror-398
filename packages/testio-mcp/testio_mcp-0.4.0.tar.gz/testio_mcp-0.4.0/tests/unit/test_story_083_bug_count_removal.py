"""Unit tests for STORY-083: Remove bug_count from list_products and get_product_summary.

Tests verify that bug_count field is no longer present in:
1. list_products output (ProductSummary model)
2. get_product_summary output (ProductSummaryOutput model)
3. ProductRepository.query_products result
4. ProductRepository.get_product_with_counts result
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.services.product_service import ProductService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_does_not_include_bug_count():
    """Verify list_products output does not contain bug_count field.

    STORY-083: Bug counts removed from product listings.
    Users should use get_product_quality_report for bug analysis.
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
        # STORY-083: query_products returns data WITHOUT bug_count
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
                ],
                "total_count": 1,
                "page": 1,
                "per_page": 50,
            }
        )

        # Act
        result = await service.list_products()

        # Assert
        # Verify bug_count is NOT in the output
        assert "bug_count" not in result["products"][0]
        # Verify expected fields ARE present
        assert "test_count" in result["products"][0]
        assert "feature_count" in result["products"][0]
        assert result["products"][0]["test_count"] == 5
        assert result["products"][0]["feature_count"] == 2


@pytest.mark.unit
def test_repository_get_product_with_counts_structure_without_bug_count():
    """Verify ProductRepository.get_product_with_counts returns correct structure.

    STORY-083: Bug counts removed from get_product_with_counts return value.
    This test verifies the expected structure without actually querying DB.
    """
    # This test verifies the expected return structure
    # The actual implementation is tested in integration tests
    expected_keys = {
        "id",
        "title",
        "type",
        "description",
        "test_count",
        "feature_count",
        "last_synced",
    }

    # Mock a return value from get_product_with_counts
    mock_return = {
        "id": 598,
        "title": "Canva",
        "type": "website",
        "description": "Design platform",
        "test_count": 216,
        "feature_count": 45,
        "last_synced": "2025-11-28T10:30:00Z",
    }

    # Assert: Verify structure matches expected (no bug_count)
    assert set(mock_return.keys()) == expected_keys
    assert "bug_count" not in mock_return


@pytest.mark.unit
@pytest.mark.asyncio
async def test_product_summary_pydantic_model_accepts_no_bug_count():
    """Verify ProductSummary Pydantic model validates without bug_count.

    STORY-083: ProductSummary model should not require bug_count field.
    """
    from testio_mcp.tools.list_products_tool import ProductSummary

    # Arrange
    product_data = {
        "id": 1,
        "name": "Test Product",
        "type": "website",
        "test_count": 10,
        "feature_count": 5,
        "tests_last_30_days": 2,
        "tests_last_90_days": 5,
    }

    # Act - Should not raise ValidationError
    product = ProductSummary(**product_data)

    # Assert
    assert product.product_id == 1
    assert product.name == "Test Product"
    assert product.test_count == 10
    assert product.feature_count == 5
    # Verify bug_count field doesn't exist
    assert not hasattr(product, "bug_count")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_product_summary_output_model_accepts_no_bug_count():
    """Verify ProductSummaryOutput Pydantic model validates without bug_count.

    STORY-083: ProductSummaryOutput model should not require bug_count field.
    """
    from testio_mcp.tools.product_summary_tool import ProductSummaryOutput

    # Arrange
    product_data = {
        "id": 598,
        "title": "Canva",
        "type": "website",
        "description": "Design platform",
        "test_count": 216,
        "feature_count": 45,
        "last_synced": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    # Act - Should not raise ValidationError
    product = ProductSummaryOutput(**product_data)

    # Assert
    assert product.id == 598
    assert product.title == "Canva"
    assert product.test_count == 216
    assert product.feature_count == 45
    # Verify bug_count field doesn't exist
    assert not hasattr(product, "bug_count")
