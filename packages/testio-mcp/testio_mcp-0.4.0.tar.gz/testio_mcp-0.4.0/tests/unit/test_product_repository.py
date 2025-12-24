"""Unit tests for ProductRepository.

Tests SQLModel-based product queries with AsyncSession.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Product
from testio_mcp.repositories.product_repository import ProductRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_product_repository_inherits_base_repository():
    """Verify ProductRepository is subclass of BaseRepository."""
    from testio_mcp.repositories.base_repository import BaseRepository

    # Assert
    assert issubclass(ProductRepository, BaseRepository)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_products_uses_sqlmodel_query():
    """Verify count_products() uses select(func.count()).select_from(Product)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Mock the query result - exec returns awaitable, one() returns value
    mock_result = MagicMock()
    mock_result.one.return_value = 5
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    count = await repo.count_products()

    # Assert
    assert count == 5
    mock_session.exec.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_info_uses_sqlmodel_query():
    """Verify get_product_info() uses select(Product).where(Product.id == product_id)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123
    product_id = 456

    # Create a mock product
    mock_product = Product(
        id=product_id,
        customer_id=customer_id,
        data=json.dumps({"name": "Test Product", "type": "website"}),
        last_synced=datetime.now(UTC),
    )

    # Mock the query result - exec returns awaitable, first() returns value
    mock_result = MagicMock()
    mock_result.first.return_value = mock_product
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    product_info = await repo.get_product_info(product_id)

    # Assert
    assert product_info is not None
    assert product_info["id"] == product_id
    assert product_info["name"] == "Test Product"
    assert product_info["type"] == "website"
    mock_session.exec.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_info_returns_none_when_not_found():
    """Verify get_product_info() returns None when product doesn't exist."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123
    product_id = 999

    # Mock the query result (no product found)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    product_info = await repo.get_product_info(product_id)

    # Assert
    assert product_info is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_synced_products_info_returns_list():
    """Verify get_synced_products_info() returns list of product dicts."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Create mock products
    product1_data = json.dumps({"name": "Product 1", "type": "website"})
    product2_data = json.dumps({"name": "Product 2", "type": "mobile_app_ios"})

    last_synced1 = datetime.now(UTC)
    last_synced2 = datetime.now(UTC)

    # Mock the products query result (STORY-062: simplified - only last_synced)
    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (1, product1_data, last_synced1),
        (2, product2_data, last_synced2),
    ]

    # Mock the test count query results
    mock_test_count_result1 = MagicMock()
    mock_test_count_result1.one.return_value = 5

    mock_test_count_result2 = MagicMock()
    mock_test_count_result2.one.return_value = 3

    # Set up exec to return different results for different calls
    mock_session.exec.side_effect = [
        mock_products_result,
        mock_test_count_result1,
        mock_test_count_result2,
    ]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    products_info = await repo.get_synced_products_info()

    # Assert
    assert len(products_info) == 2
    assert products_info[0]["id"] == 1
    assert products_info[0]["name"] == "Product 1"
    assert products_info[0]["test_count"] == 5
    assert products_info[0]["last_synced"] is not None  # STORY-062
    assert products_info[1]["id"] == 2
    assert products_info[1]["name"] == "Product 2"
    assert products_info[1]["test_count"] == 3
    assert products_info[1]["last_synced"] is not None  # STORY-062


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_product_last_synced_updates_existing_product():
    """Verify update_product_last_synced() updates existing product's last_synced timestamp."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123
    product_id = 456

    # Create a mock existing product
    mock_product = Product(
        id=product_id,
        customer_id=customer_id,
        data=json.dumps({"name": "Test Product"}),
        last_synced=datetime(2024, 1, 1, tzinfo=UTC),
    )

    # Mock the query result (product exists)
    mock_result = MagicMock()
    mock_result.first.return_value = mock_product
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    await repo.update_product_last_synced(product_id)

    # Assert
    mock_session.add.assert_called_once_with(mock_product)
    mock_session.commit.assert_called_once()
    # Verify last_synced was updated (should be recent)
    assert mock_product.last_synced > datetime(2024, 1, 1, tzinfo=UTC)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_product_last_synced_creates_new_product():
    """Verify update_product_last_synced() creates minimal product record if doesn't exist."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123
    product_id = 456

    # Mock the query result (product doesn't exist)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    await repo.update_product_last_synced(product_id)

    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    # Verify a Product was added
    added_product = mock_session.add.call_args[0][0]
    assert isinstance(added_product, Product)
    assert added_product.id == product_id
    assert added_product.customer_id == customer_id
    assert added_product.data == "{}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_all_products_deletes_customer_products():
    """Verify delete_all_products() deletes all products for customer."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Create mock products
    product1 = Product(id=1, customer_id=customer_id, data="{}", last_synced=None)
    product2 = Product(id=2, customer_id=customer_id, data="{}", last_synced=None)

    # Mock the query result
    mock_result = MagicMock()
    mock_result.all.return_value = [product1, product2]
    mock_session.exec.return_value = mock_result

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    await repo.delete_all_products()

    # Assert
    assert mock_session.delete.call_count == 2
    mock_session.commit.assert_called_once()


# STORY-055: Tests for query_products() method


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_default_sort_by_title_asc():
    """Verify query_products() defaults to sorting by title ascending."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Create mock products (sorted by title)
    product1 = Product(
        id=1,
        customer_id=customer_id,
        title="A Product",
        product_type="website",
        data=json.dumps({"name": "A Product", "type": "website"}),
        last_synced=datetime.now(UTC),
    )
    product2 = Product(
        id=2,
        customer_id=customer_id,
        title="B Product",
        product_type="mobile_app_ios",
        data=json.dumps({"name": "B Product", "type": "mobile_app_ios"}),
        last_synced=datetime.now(UTC),
    )

    # Mock count query
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 2

    # STORY-058 N+1 Fix + Recency: Mock products query with all subqueries
    # STORY-083: Removed bug_count from tuple
    # Tuple: (Product, test_count, feature_count, tests_30d, tests_90d, last_end_at)

    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (product1, 5, 3, 2, 4, datetime(2025, 11, 28, tzinfo=UTC)),
        (product2, 8, 4, 3, 6, datetime(2025, 11, 27, tzinfo=UTC)),
    ]

    mock_session.exec.side_effect = [
        mock_count_result,  # Total count query
        mock_products_result,  # Products query with counts (subqueries)
    ]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    result = await repo.query_products()

    # Assert
    assert result["total_count"] == 2
    assert result["page"] == 1
    assert result["per_page"] == 50
    assert len(result["products"]) == 2
    assert result["products"][0]["name"] == "A Product"
    assert result["products"][0]["test_count"] == 5
    # STORY-083: bug_count removed
    assert result["products"][0]["feature_count"] == 3
    assert result["products"][0]["tests_last_30_days"] == 2
    assert result["products"][0]["tests_last_90_days"] == 4
    assert result["products"][0]["last_test_end_at"] == "2025-11-28T00:00:00+00:00"
    assert result["products"][1]["name"] == "B Product"
    assert result["products"][1]["test_count"] == 8
    # STORY-083: bug_count removed
    assert result["products"][1]["feature_count"] == 4
    assert result["products"][1]["tests_last_30_days"] == 3
    assert result["products"][1]["tests_last_90_days"] == 6
    assert result["products"][1]["last_test_end_at"] == "2025-11-27T00:00:00+00:00"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_sort_by_product_type():
    """Verify query_products() supports sorting by product_type."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    product1 = Product(
        id=1,
        customer_id=customer_id,
        title="Product 1",
        product_type="website",
        data=json.dumps({"name": "Product 1", "type": "website"}),
        last_synced=datetime.now(UTC),
    )

    # Mock count query
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 1

    # STORY-058 N+1 Fix + Recency: Mock products query with all subqueries
    # STORY-083: Removed bug_count from tuple

    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (product1, 3, 2, 1, 2, datetime(2025, 11, 28, tzinfo=UTC)),
    ]

    mock_session.exec.side_effect = [
        mock_count_result,  # Total count
        mock_products_result,  # Products query with counts
    ]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    result = await repo.query_products(sort_by="product_type", sort_order="asc")

    # Assert
    assert result["total_count"] == 1
    assert result["products"][0]["test_count"] == 3
    # STORY-083: bug_count removed
    assert result["products"][0]["feature_count"] == 2
    assert result["products"][0]["type"] == "website"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_sort_by_last_synced_desc():
    """Verify query_products() supports sorting by last_synced descending."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    old_time = datetime(2024, 1, 1, tzinfo=UTC)
    new_time = datetime(2024, 12, 1, tzinfo=UTC)

    # Products ordered by last_synced desc (newest first)
    product1 = Product(
        id=1,
        customer_id=customer_id,
        title="New Product",
        product_type="website",
        data=json.dumps({"name": "New Product", "type": "website"}),
        last_synced=new_time,
    )
    product2 = Product(
        id=2,
        customer_id=customer_id,
        title="Old Product",
        product_type="website",
        data=json.dumps({"name": "Old Product", "type": "website"}),
        last_synced=old_time,
    )

    # Mock count query
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 2

    # STORY-058 N+1 Fix + Recency: Mock products query with all subqueries
    # STORY-083: Removed bug_count from tuple
    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (product1, 0, 0, 0, 0, None),
        (product2, 0, 0, 0, 0, None),
    ]

    mock_session.exec.side_effect = [mock_count_result, mock_products_result]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    result = await repo.query_products(sort_by="last_synced", sort_order="desc")

    # Assert
    assert result["total_count"] == 2
    assert result["products"][0]["name"] == "New Product"
    assert result["products"][1]["name"] == "Old Product"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_raises_value_error_for_invalid_sort_field():
    """Verify query_products() raises ValueError for invalid sort_by field."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid sort_by: invalid_field"):
        await repo.query_products(sort_by="invalid_field")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_pagination_with_page():
    """Verify query_products() respects page and per_page parameters."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Create mock products for page 2 with per_page=2
    product1 = Product(
        id=3,
        customer_id=customer_id,
        title="Product 3",
        product_type="website",
        data=json.dumps({"name": "Product 3", "type": "website"}),
        last_synced=datetime.now(UTC),
    )
    product2 = Product(
        id=4,
        customer_id=customer_id,
        title="Product 4",
        product_type="website",
        data=json.dumps({"name": "Product 4", "type": "website"}),
        last_synced=datetime.now(UTC),
    )

    # Mock count query (total 10 products)
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 10

    # STORY-058 N+1 Fix + Recency: Mock products query with all subqueries
    # STORY-083: Removed bug_count from tuple
    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (product1, 0, 0, 0, 0, None),
        (product2, 0, 0, 0, 0, None),
    ]

    mock_session.exec.side_effect = [mock_count_result, mock_products_result]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    result = await repo.query_products(page=2, per_page=2)

    # Assert
    assert result["total_count"] == 10
    assert result["page"] == 2
    assert result["per_page"] == 2
    assert len(result["products"]) == 2
    assert result["products"][0]["name"] == "Product 3"
    assert result["products"][1]["name"] == "Product 4"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_products_pagination_with_offset():
    """Verify query_products() respects offset parameter."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Create mock products starting at offset 5
    product1 = Product(
        id=6,
        customer_id=customer_id,
        title="Product 6",
        product_type="website",
        data=json.dumps({"name": "Product 6", "type": "website"}),
        last_synced=datetime.now(UTC),
    )

    # Mock count query
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 10

    # STORY-058 N+1 Fix + Recency: Mock products query with all subqueries
    # STORY-083: Removed bug_count from tuple
    mock_products_result = MagicMock()
    mock_products_result.all.return_value = [
        (product1, 0, 0, 0, 0, None),
    ]

    mock_session.exec.side_effect = [mock_count_result, mock_products_result]

    repo = ProductRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    result = await repo.query_products(offset=5, per_page=1)

    # Assert
    assert result["total_count"] == 10
    assert result["page"] == 1  # page is still 1 when using offset
    assert result["per_page"] == 1
    assert len(result["products"]) == 1
    assert result["products"][0]["name"] == "Product 6"
