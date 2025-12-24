"""
Unit tests for FeatureRepository.get_features_cached_or_refresh() staleness method.

Tests the intelligent caching logic that decides when to use cached feature data
vs. refreshing from API based on staleness.

Pattern: Mock TestIOClient and AsyncSession to avoid API calls and DB access.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.repositories.feature_repository import FeatureRepository


def create_mock_cache():
    """Create a mock cache with all required methods for decoupled API/DB pattern."""
    mock_cache = MagicMock()
    mock_cache.get_refresh_lock = MagicMock(return_value=asyncio.Lock())
    mock_cache._write_semaphore = asyncio.Semaphore(5)

    # Create isolated session mock for cache.async_session_maker()
    mock_isolated_session = AsyncMock(spec=AsyncSession)
    mock_isolated_session.exec = AsyncMock()  # Will be configured per test for final read
    mock_isolated_session.commit = AsyncMock()
    mock_isolated_session.add = MagicMock()
    mock_isolated_session.rollback = AsyncMock()  # For Issue #5 rollback fix

    # Mock async context manager for session maker
    @asynccontextmanager
    async def mock_session_maker():
        yield mock_isolated_session

    mock_cache.async_session_maker = mock_session_maker
    mock_cache._mock_isolated_session = mock_isolated_session  # Expose for test configuration
    return mock_cache


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_empty_list() -> None:
    """Test with empty product_ids list returns empty dict and zero stats."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = FeatureRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    features_dict, cache_stats = await repo.get_features_cached_or_refresh([])

    # Assert
    assert features_dict == {}
    assert cache_stats == {
        "total_products": 0,
        "cache_hits": 0,
        "api_calls": 0,
        "cache_hit_rate": 0.0,
        "breakdown": {},
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_fresh_features() -> None:
    """Test that fresh features are served from cache (no API calls)."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = FeatureRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    product_ids = [598, 1024]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=30)  # 30 minutes ago (fresh)

    # Mock product metadata query (features_synced_at)
    mock_product_result = MagicMock()
    mock_product_result.all.return_value = [
        (598, fresh_timestamp),  # Fresh
        (1024, fresh_timestamp),  # Fresh
    ]

    # Create mock Feature ORM objects
    from testio_mcp.models.orm.feature import Feature

    mock_feature_598 = MagicMock(spec=Feature)
    mock_feature_598.id = 1
    mock_feature_598.product_id = 598
    mock_feature_598.title = "Login"
    mock_feature_598.description = "User login"
    mock_feature_598.howtofind = "Click login"
    mock_feature_598.user_stories = "[]"
    mock_feature_598.section_ids = "[]"

    mock_feature_1024 = MagicMock(spec=Feature)
    mock_feature_1024.id = 2
    mock_feature_1024.product_id = 1024
    mock_feature_1024.title = "Dashboard"
    mock_feature_1024.description = "Main dashboard"
    mock_feature_1024.howtofind = "Go to home"
    mock_feature_1024.user_stories = "[]"
    mock_feature_1024.section_ids = "[]"

    mock_feature_result_598 = MagicMock()
    mock_feature_result_598.all.return_value = [mock_feature_598]
    mock_feature_result_1024 = MagicMock()
    mock_feature_result_1024.all.return_value = [mock_feature_1024]

    # Configure session.exec to return different results based on query
    mock_session.exec.side_effect = [
        mock_product_result,  # First call: product metadata query
        mock_feature_result_598,  # Second call: features for product 598
        mock_feature_result_1024,  # Third call: features for product 1024
    ]

    # Act
    features_dict, cache_stats = await repo.get_features_cached_or_refresh(product_ids)

    # Assert
    assert len(features_dict) == 2
    assert 598 in features_dict
    assert 1024 in features_dict
    assert len(features_dict[598]) == 1
    assert len(features_dict[1024]) == 1
    assert features_dict[598][0]["title"] == "Login"
    assert features_dict[1024][0]["title"] == "Dashboard"

    # Verify cache stats (100% cache hit, no API calls)
    assert cache_stats["total_products"] == 2
    assert cache_stats["cache_hits"] == 2
    assert cache_stats["api_calls"] == 0
    assert cache_stats["cache_hit_rate"] == 100.0
    assert cache_stats["breakdown"]["fresh_cached"] == 2

    # Verify no API calls made
    mock_client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_stale_features() -> None:
    """Test that stale features trigger API refresh."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    mock_cache = create_mock_cache()
    repo = FeatureRepository(
        session=mock_session, client=mock_client, customer_id=customer_id, cache=mock_cache
    )

    product_ids = [598, 1024]
    now = datetime.now(UTC)
    stale_timestamp = now - timedelta(hours=2)  # 2 hours ago (stale, assuming 1h TTL)

    # Mock product metadata query
    mock_product_result = MagicMock()
    mock_product_result.all.return_value = [
        (598, stale_timestamp),  # Stale
        (1024, stale_timestamp),  # Stale
    ]

    # Mock feature data query (after refresh)
    from testio_mcp.models.orm.feature import Feature

    mock_feature_598 = MagicMock(spec=Feature)
    mock_feature_598.id = 1
    mock_feature_598.product_id = 598
    mock_feature_598.title = "Login Refreshed"
    mock_feature_598.description = "User login updated"
    mock_feature_598.howtofind = "Click login"
    mock_feature_598.user_stories = "[]"
    mock_feature_598.section_ids = "[]"

    mock_feature_1024 = MagicMock(spec=Feature)
    mock_feature_1024.id = 2
    mock_feature_1024.product_id = 1024
    mock_feature_1024.title = "Dashboard Refreshed"
    mock_feature_1024.description = "Main dashboard updated"
    mock_feature_1024.howtofind = "Go to home"
    mock_feature_1024.user_stories = "[]"
    mock_feature_1024.section_ids = "[]"

    mock_feature_result_598 = MagicMock()
    mock_feature_result_598.all.return_value = [mock_feature_598]
    mock_feature_result_1024 = MagicMock()
    mock_feature_result_1024.all.return_value = [mock_feature_1024]

    # Configure session.exec on main session (product metadata only)
    # Flow: product metadata query → features queries NOW USE fresh_session after refresh
    mock_session.exec.side_effect = [
        mock_product_result,  # Product metadata query
    ]

    # Configure isolated session.exec for final fresh reads (Issue #2 fix)
    # Note: side_effect creates a call-count dependent list, so we need one result per product
    # But since the same mock session is reused, we need to handle multiple calls
    mock_cache._mock_isolated_session.exec.side_effect = [
        mock_feature_result_598,  # Features for product 598 (fresh session read)
        mock_feature_result_1024,  # Features for product 1024 (fresh session read)
    ] * 2  # Multiply to handle potential extra calls during refresh/writes

    # Mock session.add and session.commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    # Mock _fetch_features_from_api to avoid actual API calls
    with patch.object(repo, "_fetch_features_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []  # Empty features, we just care about the flow
        # Act
        features_dict, cache_stats = await repo.get_features_cached_or_refresh(product_ids)

    # Assert
    assert len(features_dict) == 2
    assert features_dict[598][0]["title"] == "Login Refreshed"
    assert features_dict[1024][0]["title"] == "Dashboard Refreshed"

    # Verify cache stats (0% cache hit, 2 API calls)
    assert cache_stats["total_products"] == 2
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 2
    assert cache_stats["cache_hit_rate"] == 0.0
    assert cache_stats["breakdown"]["stale_refresh"] == 2

    # Verify _fetch_features_from_api was called for both products
    assert mock_fetch.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_force_refresh() -> None:
    """Test that force_refresh=True bypasses cache for all products."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    mock_cache = create_mock_cache()
    repo = FeatureRepository(
        session=mock_session, client=mock_client, customer_id=customer_id, cache=mock_cache
    )

    product_ids = [598]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=5)  # Very fresh

    # Mock product metadata query
    mock_product_result = MagicMock()
    mock_product_result.all.return_value = [
        (598, fresh_timestamp),  # Fresh
    ]

    # Mock feature data query (after refresh)
    from testio_mcp.models.orm.feature import Feature

    mock_feature = MagicMock(spec=Feature)
    mock_feature.id = 1
    mock_feature.product_id = 598
    mock_feature.title = "Login Force Refreshed"
    mock_feature.description = "User login force updated"
    mock_feature.howtofind = "Click login"
    mock_feature.user_stories = "[]"
    mock_feature.section_ids = "[]"

    mock_feature_result = MagicMock()
    mock_feature_result.all.return_value = [mock_feature]

    # Configure session.exec on main session (product metadata only)
    mock_session.exec.side_effect = [
        mock_product_result,  # Product metadata query
    ]

    # Configure isolated session.exec for final fresh reads (Issue #2 fix)
    mock_cache._mock_isolated_session.exec.return_value = mock_feature_result

    # Mock session.add and session.commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch.object(repo, "_fetch_features_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        # Act
        features_dict, cache_stats = await repo.get_features_cached_or_refresh(
            product_ids, force_refresh=True
        )

    # Assert
    assert len(features_dict) == 1
    assert features_dict[598][0]["title"] == "Login Force Refreshed"

    # Verify cache stats (0% cache hit due to force refresh)
    assert cache_stats["total_products"] == 1
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 1
    assert cache_stats["cache_hit_rate"] == 0.0
    assert cache_stats["breakdown"]["force_refresh"] == 1

    # Verify _fetch_features_from_api called even though features were fresh
    mock_fetch.assert_called_once_with(598)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_batch_processing() -> None:
    """Test efficient batch processing of multiple products."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    mock_cache = create_mock_cache()
    repo = FeatureRepository(
        session=mock_session, client=mock_client, customer_id=customer_id, cache=mock_cache
    )

    # 5 products, all stale
    product_ids = [598, 1024, 2048, 4096, 8192]
    now = datetime.now(UTC)
    stale_timestamp = now - timedelta(hours=2)

    # All products are stale
    metadata_rows = [(product_id, stale_timestamp) for product_id in product_ids]

    mock_product_result = MagicMock()
    mock_product_result.all.return_value = metadata_rows

    # Mock feature data queries (after refresh)
    from testio_mcp.models.orm.feature import Feature

    feature_results = []
    for product_id in product_ids:
        mock_feature = MagicMock(spec=Feature)
        mock_feature.id = product_id
        mock_feature.product_id = product_id
        mock_feature.title = f"Feature {product_id}"
        mock_feature.description = f"Description {product_id}"
        mock_feature.howtofind = "How to find"
        mock_feature.user_stories = "[]"
        mock_feature.section_ids = "[]"

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_feature]
        feature_results.append(mock_result)

    # Configure session.exec on main session (product metadata only)
    mock_session.exec.side_effect = [mock_product_result]

    # Configure isolated session.exec for final fresh reads (Issue #2 fix)
    mock_cache._mock_isolated_session.exec.side_effect = (
        feature_results * 2
    )  # Extra buffer for multiple calls

    # Mock session.add and session.commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch.object(repo, "_fetch_features_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        # Act
        features_dict, cache_stats = await repo.get_features_cached_or_refresh(product_ids)

    # Assert
    assert len(features_dict) == 5

    # Verify cache stats
    assert cache_stats["total_products"] == 5
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 5
    assert cache_stats["cache_hit_rate"] == 0.0

    # Verify all products refreshed (batch processing)
    assert mock_fetch.call_count == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_features_cached_or_refresh_mixed_staleness() -> None:
    """Test mixed scenarios: some fresh, some stale."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    mock_cache = create_mock_cache()
    repo = FeatureRepository(
        session=mock_session, client=mock_client, customer_id=customer_id, cache=mock_cache
    )

    product_ids = [598, 1024, 2048, 4096]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=30)
    stale_timestamp = now - timedelta(hours=2)

    # Mock product metadata query
    mock_product_result = MagicMock()
    mock_product_result.all.return_value = [
        (598, fresh_timestamp),  # Fresh → cache
        (1024, stale_timestamp),  # Stale → API
        (2048, fresh_timestamp),  # Fresh → cache
        (4096, stale_timestamp),  # Stale → API
    ]

    # Mock feature data queries
    from testio_mcp.models.orm.feature import Feature

    mock_features = []
    for product_id in product_ids:
        mock_feature = MagicMock(spec=Feature)
        mock_feature.id = product_id
        mock_feature.product_id = product_id
        mock_feature.title = f"Feature {product_id}"
        mock_feature.description = f"Description {product_id}"
        mock_feature.howtofind = "How to find"
        mock_feature.user_stories = "[]"
        mock_feature.section_ids = "[]"

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_feature]
        mock_features.append(mock_result)

    # Configure session.exec on main session (product metadata only)
    mock_session.exec.side_effect = [mock_product_result]

    # Configure isolated session.exec for final fresh reads (Issue #2 fix)
    # Even though only 2 products need refresh, all 4 will use fresh session for reads
    mock_cache._mock_isolated_session.exec.side_effect = (
        mock_features * 2
    )  # Extra buffer for multiple calls

    # Mock session.add and session.commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch.object(repo, "_fetch_features_from_api", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        # Act
        features_dict, cache_stats = await repo.get_features_cached_or_refresh(product_ids)

    # Assert
    assert len(features_dict) == 4

    # Verify cache stats (50% cache hit)
    assert cache_stats["total_products"] == 4
    assert cache_stats["cache_hits"] == 2  # 598 + 2048 (fresh)
    assert cache_stats["api_calls"] == 2  # 1024 + 4096 (stale)
    assert cache_stats["cache_hit_rate"] == 50.0
    assert cache_stats["breakdown"]["fresh_cached"] == 2  # 598 + 2048
    assert cache_stats["breakdown"]["stale_refresh"] == 2  # 1024 + 4096

    # Verify _fetch_features_from_api only for stale products
    assert mock_fetch.call_count == 2
