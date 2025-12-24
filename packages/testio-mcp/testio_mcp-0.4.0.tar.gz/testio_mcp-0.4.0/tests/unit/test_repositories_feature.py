"""Unit tests for FeatureRepository.

Tests validate CRUD operations, section-aware sync logic, and upsert behavior.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm import Feature
from testio_mcp.repositories.feature_repository import FeatureRepository


@pytest_asyncio.fixture(scope="function")
async def feature_test_engine():
    """Create dedicated async engine with StaticPool for feature tests.

    Uses StaticPool instead of NullPool to maintain single in-memory database
    across all connections in the same test. This fixes the async session
    isolation issue where NullPool created separate databases per connection.

    Yields:
        AsyncEngine configured with StaticPool
    """
    from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,  # Single in-memory DB shared across connections
        connect_args={"check_same_thread": False},
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session_with_tables(feature_test_engine):
    """Async session with tables created for feature tests.

    Uses dedicated feature_test_engine with StaticPool to ensure tables
    created in this fixture are visible to the repository's session.

    Args:
        feature_test_engine: Dedicated async engine for this test

    Yields:
        AsyncSession with all ORM tables created
    """
    # Import all ORM models to ensure they're registered in metadata
    from testio_mcp.models.orm import Feature, Product  # noqa: F401

    # Create all tables before each test
    async with feature_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Now create sessions for tests
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(
        feature_test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

    # Drop all tables after each test
    async with feature_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create mock TestIO API client."""
    return AsyncMock()


@pytest.fixture
def customer_id() -> int:
    """Customer ID for tests."""
    return 123


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_non_section_product(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature sync for non-section product."""
    # Mock API response
    mock_client.get.side_effect = [
        # GET /products/21362
        {"id": 21362, "sections": []},
        # GET /products/21362/features
        {
            "features": [
                {"id": 1, "title": "Feature 1", "description": "Desc 1", "howtofind": "How 1"},
                {"id": 2, "title": "Feature 2", "description": "Desc 2", "howtofind": "How 2"},
            ]
        },
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=21362)

    # Verify stats
    assert stats["created"] == 2
    assert stats["updated"] == 0
    assert stats["total"] == 2

    # Verify database
    result = await async_session_with_tables.exec(
        select(Feature).where(Feature.product_id == 21362)
    )
    features = result.all()
    assert len(features) == 2
    assert features[0].title == "Feature 1"
    assert features[1].title == "Feature 2"

    # Verify raw_data is JSON string
    raw_data = json.loads(features[0].raw_data)
    assert raw_data["id"] == 1
    assert raw_data["title"] == "Feature 1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_section_product(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature sync for section product with deduplication.

    IMPORTANT: Features are shared across sections, so duplicate IDs
    are deduplicated by the repository.
    """
    # Pre-populate products table (Phase 1 must happen before Phase 2)
    from testio_mcp.models.orm.product import Product

    product_data = {"id": 18559, "sections": [{"id": 100}, {"id": 101}]}
    product = Product(
        id=18559,
        customer_id=customer_id,
        title="Test Product",
        data=json.dumps(product_data),
        last_synced=datetime.now(UTC),
    )
    async_session_with_tables.add(product)
    await async_session_with_tables.commit()

    # Mock API responses for feature endpoints
    mock_client.get.side_effect = [
        # GET /products/18559/sections/100/features
        {"features": [{"id": 1, "title": "Feature 1"}]},
        # GET /products/18559/sections/101/features
        {"features": [{"id": 2, "title": "Feature 2"}]},
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=18559)

    # Verify stats
    assert stats["created"] == 2
    assert stats["total"] == 2

    # Verify database
    result = await async_session_with_tables.exec(
        select(Feature).where(Feature.product_id == 18559)
    )
    features = result.all()
    assert len(features) == 2
    assert {f.id for f in features} == {1, 2}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_section_product_deduplication(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature deduplication when same feature appears in multiple sections.

    CRITICAL: Features are shared across sections. If the same feature ID
    appears in multiple section responses, only store it once.
    """
    # Pre-populate products table (Phase 1 must happen before Phase 2)
    from testio_mcp.models.orm.product import Product

    product_data = {"id": 18559, "sections": [{"id": 100}, {"id": 101}]}
    product = Product(
        id=18559,
        customer_id=customer_id,
        title="Test Product",
        data=json.dumps(product_data),
        last_synced=datetime.now(UTC),
    )
    async_session_with_tables.add(product)
    await async_session_with_tables.commit()

    # Mock API responses for feature endpoints
    mock_client.get.side_effect = [
        # GET /products/18559/sections/100/features
        {"features": [{"id": 1, "title": "Shared Feature"}, {"id": 2, "title": "Feature 2"}]},
        # GET /products/18559/sections/101/features (Feature 1 appears again!)
        {"features": [{"id": 1, "title": "Shared Feature"}, {"id": 3, "title": "Feature 3"}]},
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=18559)

    # Verify stats - Feature 1 should only be counted once
    assert stats["created"] == 3  # Features 1, 2, 3 (not 4)
    assert stats["total"] == 3

    # Verify database
    result = await async_session_with_tables.exec(
        select(Feature).where(Feature.product_id == 18559)
    )
    features = result.all()
    assert len(features) == 3  # Deduplicated
    assert {f.id for f in features} == {1, 2, 3}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_default_section_product(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature sync for default-section product (critical bug case).

    Products with sections_with_default=[single-default-section] should use
    non-section endpoint, not section endpoint.
    """
    # Mock API response
    mock_client.get.side_effect = [
        # GET /products/21362
        {
            "id": 21362,
            "sections": [],
            "sections_with_default": [{"id": 21855, "name": "default-section"}],
        },
        # GET /products/21362/features (non-section endpoint)
        {"features": [{"id": 1, "title": "Feature 1"}]},
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=21362)

    # Verify stats
    assert stats["created"] == 1

    # Verify database
    result = await async_session_with_tables.exec(
        select(Feature).where(Feature.product_id == 21362)
    )
    features = result.all()
    assert len(features) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_upsert_logic(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test upsert logic (create vs update)."""
    # Create initial feature
    feature = Feature(
        id=1,
        product_id=598,
        section_id=None,
        title="Old Title",
        description="Old Desc",
        howtofind="Old How",
        raw_data=json.dumps({"id": 1, "title": "Old Title"}),
        last_synced=datetime.now(UTC),
    )
    async_session_with_tables.add(feature)
    await async_session_with_tables.commit()

    # Mock API response with updated data
    mock_client.get.side_effect = [
        # GET /products/598
        {"id": 598, "sections": []},
        # GET /products/598/features
        {
            "features": [
                {
                    "id": 1,
                    "title": "New Title",
                    "description": "New Desc",
                    "howtofind": "New How",
                },
                {"id": 2, "title": "Feature 2"},
            ]
        },
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features (should update feature 1, create feature 2)
    stats = await repo.sync_features(product_id=598)

    # Verify stats
    assert stats["created"] == 1
    assert stats["updated"] == 1
    assert stats["total"] == 2

    # Verify database
    result = await async_session_with_tables.exec(select(Feature).where(Feature.product_id == 598))
    features = result.all()
    assert len(features) == 2

    # Verify feature 1 was updated
    feature_1 = next(f for f in features if f.id == 1)
    assert feature_1.title == "New Title"
    assert feature_1.description == "New Desc"
    assert feature_1.howtofind == "New How"

    # Verify feature 2 was created
    feature_2 = next(f for f in features if f.id == 2)
    assert feature_2.title == "Feature 2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_for_product_no_filter(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test get_features_for_product query."""
    # Create test features
    feature1 = Feature(id=1, product_id=598, title="Feature 1", raw_data=json.dumps({}))
    feature2 = Feature(id=2, product_id=598, title="Feature 2", raw_data=json.dumps({}))
    async_session_with_tables.add(feature1)
    async_session_with_tables.add(feature2)
    await async_session_with_tables.commit()

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Get all features
    features = await repo.get_features_for_product(product_id=598)
    assert len(features) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_empty_response(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature sync with empty API response."""
    # Mock API response
    mock_client.get.side_effect = [
        # GET /products/999
        {"id": 999, "sections": []},
        # GET /products/999/features (empty)
        {"features": []},
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=999)

    # Verify stats
    assert stats["created"] == 0
    assert stats["updated"] == 0
    assert stats["total"] == 0

    # Verify database
    result = await async_session_with_tables.exec(select(Feature).where(Feature.product_id == 999))
    features = result.all()
    assert len(features) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_features_missing_fields(
    async_session_with_tables: AsyncSession, mock_client: AsyncMock, customer_id: int
) -> None:
    """Test feature sync with missing optional fields."""
    # Mock API response with minimal fields
    mock_client.get.side_effect = [
        # GET /products/598
        {"id": 598, "sections": []},
        # GET /products/598/features (minimal fields)
        {"features": [{"id": 1, "title": "Feature 1"}]},
    ]

    repo = FeatureRepository(
        session=async_session_with_tables, client=mock_client, customer_id=customer_id
    )

    # Sync features
    stats = await repo.sync_features(product_id=598)

    # Verify stats
    assert stats["created"] == 1

    # Verify database
    result = await async_session_with_tables.exec(select(Feature).where(Feature.product_id == 598))
    features = result.all()
    assert len(features) == 1
    assert features[0].title == "Feature 1"
    assert features[0].description is None
    assert features[0].howtofind is None
