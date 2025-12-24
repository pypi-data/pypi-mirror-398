"""
Integration tests for Epic-007: Generic Analytics Framework.

Tests end-to-end functionality with real database (temp file) but no API calls.
Verifies repository staleness patterns, analytics service integration, and data integrity.

Pattern: Real database operations (temp file), mocked API client.
Uses shared_cache fixture from tests/conftest.py for consistent test isolation.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from testio_mcp.database import PersistentCache
from testio_mcp.models.orm import Product, Test
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.test_repository import TestRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_test_repository_staleness_integration(shared_cache: PersistentCache) -> None:
    """Integration test for TestRepository.get_tests_cached_or_refresh().

    Verifies:
    - Fresh test data is served from cache (no API call)
    - Stale test data triggers API refresh
    - synced_at timestamp is updated after refresh
    - Cache hit on second call for same test
    """
    # Arrange
    mock_client = AsyncMock()
    customer_id = 999

    # Create async session from shared_cache
    session = shared_cache.async_session_maker()
    try:
        repo = TestRepository(session=session, client=mock_client, customer_id=customer_id)

        # Create test with stale synced_at timestamp
        test_id = 12345
        product_id = 598
        now = datetime.now(UTC)
        stale_timestamp = now - timedelta(hours=2)  # 2 hours ago (stale)

        test = Test(
            id=test_id,
            customer_id=customer_id,
            product_id=product_id,
            data=json.dumps({"id": test_id, "status": "running", "title": "Original Test"}),
            status="running",
            synced_at=stale_timestamp,  # Stale!
        )
        session.add(test)
        await session.commit()

        # Mock API response (refreshed test data)
        refreshed_test_data = {
            "id": test_id,
            "status": "running",
            "title": "Refreshed Test",
            "product": {"id": product_id},
        }
        mock_client.get.return_value = {"exploratory_test": refreshed_test_data}

        # Act - First call: Test is stale, should refresh
        tests_dict_1, cache_stats_1 = await repo.get_tests_cached_or_refresh([test_id])

        # Assert - First call: API refresh triggered
        assert len(tests_dict_1) == 1
        assert tests_dict_1[test_id]["title"] == "Refreshed Test"  # Refreshed data
        assert cache_stats_1["total_tests"] == 1
        assert cache_stats_1["cache_hits"] == 0  # Stale, so no cache hit
        assert cache_stats_1["api_calls"] == 1  # API called
        assert cache_stats_1["cache_hit_rate"] == 0.0
        assert cache_stats_1["breakdown"]["mutable_stale"] == 1

        # Verify API was called
        assert mock_client.get.call_count == 1

        # Verify synced_at was updated (should be very recent)
        await session.refresh(test)
        assert test.synced_at is not None
        # Make synced_at timezone-aware if it's naive (SQLite returns naive datetimes)
        synced_at_aware = (
            test.synced_at.replace(tzinfo=UTC) if test.synced_at.tzinfo is None else test.synced_at
        )
        time_since_sync = (datetime.now(UTC) - synced_at_aware).total_seconds()
        assert time_since_sync < 5  # Updated within last 5 seconds

        # Act - Second call: Test is now fresh, should use cache
        tests_dict_2, cache_stats_2 = await repo.get_tests_cached_or_refresh([test_id])

        # Assert - Second call: Cache hit (no API call)
        assert len(tests_dict_2) == 1
        assert tests_dict_2[test_id]["title"] == "Refreshed Test"  # Same data
        assert cache_stats_2["total_tests"] == 1
        assert cache_stats_2["cache_hits"] == 1  # Cache hit!
        assert cache_stats_2["api_calls"] == 0  # No API call
        assert cache_stats_2["cache_hit_rate"] == 100.0
        assert cache_stats_2["breakdown"]["mutable_fresh"] == 1

        # Verify no additional API calls
        assert mock_client.get.call_count == 1  # Still 1 (not called again)
    finally:
        await session.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_test_repository_immutable_always_cached(shared_cache: PersistentCache) -> None:
    """Integration test: Immutable tests always use cache regardless of staleness."""
    # Arrange
    mock_client = AsyncMock()
    customer_id = 999

    # Create async session from shared_cache
    session = shared_cache.async_session_maker()
    try:
        repo = TestRepository(session=session, client=mock_client, customer_id=customer_id)

        # Create archived test with very old synced_at
        test_id = 54321
        product_id = 598
        now = datetime.now(UTC)
        very_old_timestamp = now - timedelta(days=30)  # 30 days ago (very stale)

        test = Test(
            id=test_id,
            customer_id=customer_id,
            product_id=product_id,
            data=json.dumps({"id": test_id, "status": "archived", "title": "Archived Test"}),
            status="archived",  # Immutable status
            synced_at=very_old_timestamp,  # Very old but shouldn't matter
        )
        session.add(test)
        await session.commit()

        # Act
        tests_dict, cache_stats = await repo.get_tests_cached_or_refresh([test_id])

        # Assert - Immutable test always uses cache (no API call)
        assert len(tests_dict) == 1
        assert tests_dict[test_id]["status"] == "archived"
        assert cache_stats["total_tests"] == 1
        assert cache_stats["cache_hits"] == 1
        assert cache_stats["api_calls"] == 0  # No API call for immutable
        assert cache_stats["cache_hit_rate"] == 100.0
        assert cache_stats["breakdown"]["immutable_cached"] == 1

        # Verify no API calls made despite very old synced_at
        mock_client.get.assert_not_called()
    finally:
        await session.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_feature_repository_staleness_integration(shared_cache: PersistentCache) -> None:
    """Integration test for FeatureRepository.get_features_cached_or_refresh().

    STORY-062: Updated to use last_synced instead of features_synced_at.

    Verifies:
    - Fresh feature data is served from cache (no API call)
    - Stale feature data triggers API refresh
    - last_synced timestamp is updated after refresh
    - Cache hit on second call for same product
    """
    # Arrange
    mock_client = AsyncMock()
    customer_id = 999

    # Create async session from shared_cache
    session = shared_cache.async_session_maker()
    try:
        repo = FeatureRepository(
            session=session, client=mock_client, customer_id=customer_id, cache=shared_cache
        )

        # Create product with stale last_synced timestamp (STORY-062: simplified)
        product_id = 598
        now = datetime.now(UTC)
        stale_timestamp = now - timedelta(hours=2)  # 2 hours ago (stale)

        product = Product(
            id=product_id,
            customer_id=customer_id,
            title="Test Product",  # Required field
            data=json.dumps({"id": product_id, "title": "Test Product"}),
            last_synced=stale_timestamp,  # Stale!
        )
        session.add(product)
        await session.commit()

        # Mock _fetch_features_from_api to avoid API calls
        async def mock_fetch_features(product_id: int) -> list:
            """Mock feature fetch - returns empty features."""
            return []

        # Patch _fetch_features_from_api
        import unittest.mock

        with unittest.mock.patch.object(
            repo, "_fetch_features_from_api", side_effect=mock_fetch_features
        ) as mock_fetch:
            # Act - First call: Product features are stale, should refresh
            features_dict_1, cache_stats_1 = await repo.get_features_cached_or_refresh([product_id])

            # Assert - First call: API refresh triggered
            assert product_id in features_dict_1
            assert cache_stats_1["total_products"] == 1
            assert cache_stats_1["cache_hits"] == 0  # Stale, so no cache hit
            assert cache_stats_1["api_calls"] == 1  # API called
            assert cache_stats_1["cache_hit_rate"] == 0.0
            assert cache_stats_1["breakdown"]["stale_refresh"] == 1

            # Verify _fetch_features_from_api was called
            assert mock_fetch.call_count == 1

            # Verify last_synced was updated (should be very recent)
            await session.refresh(product)
            assert product.last_synced is not None
            # Make last_synced timezone-aware if it's naive
            synced_at_aware = (
                product.last_synced.replace(tzinfo=UTC)
                if product.last_synced.tzinfo is None
                else product.last_synced
            )
            time_since_sync = (datetime.now(UTC) - synced_at_aware).total_seconds()
            assert time_since_sync < 5  # Updated within last 5 seconds

            # Act - Second call: Features are now fresh, should use cache
            features_dict_2, cache_stats_2 = await repo.get_features_cached_or_refresh([product_id])

            # Assert - Second call: Cache hit (no API call)
            assert product_id in features_dict_2
            assert cache_stats_2["total_products"] == 1
            assert cache_stats_2["cache_hits"] == 1  # Cache hit!
            assert cache_stats_2["api_calls"] == 0  # No API call
            assert cache_stats_2["cache_hit_rate"] == 100.0
            assert cache_stats_2["breakdown"]["fresh_cached"] == 1

            # Verify no additional API calls
            assert mock_fetch.call_count == 1  # Still 1 (not called again)
    finally:
        await session.close()


# =============================================================================
# STORY-044: Query Metrics Tool - Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_metrics_basic_query(shared_cache: PersistentCache) -> None:
    """Test basic query_metrics call with direct attribution.

    Verifies:
    - query_metrics returns data, metadata, explanation, warnings
    - Direct attribution via Bug.test_feature_id (no fractional counts)
    - Rich entity context (IDs + display names)
    """
    # Arrange
    from unittest.mock import MagicMock

    from testio_mcp.services.analytics_service import AnalyticsService

    mock_client = MagicMock()  # Use MagicMock since no API calls are made in this test
    customer_id = 999

    async with shared_cache.async_session_maker() as session:
        service = AnalyticsService(session=session, customer_id=customer_id, client=mock_client)

        # Act - Simple query: bug_count by feature
        result = await service.query_metrics(
            metrics=["bug_count"], dimensions=["feature"], sort_by="bug_count", sort_order="desc"
        )

        # Assert - Response structure
        assert "data" in result.model_dump()
        assert "metadata" in result.model_dump()
        assert "query_explanation" in result.model_dump()
        assert "warnings" in result.model_dump()

        # Assert - Metadata includes required fields
        metadata = result.metadata
        assert metadata.total_rows >= 0
        assert metadata.dimensions_used == ["feature"]
        assert metadata.metrics_used == ["bug_count"]
        assert metadata.query_time_ms >= 0

        # Assert - Explanation is human-readable
        assert "bug_count" in result.query_explanation.lower()
        assert "feature" in result.query_explanation.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_analytics_capabilities(shared_cache: PersistentCache) -> None:
    """Test get_analytics_capabilities returns dimension/metric registry.

    Verifies:
    - Returns all 8 dimensions with key, description, example
    - Returns all 6 metrics with key, description, formula
    - Returns limits (max_dimensions, max_rows, timeout)
    """
    # Arrange
    from testio_mcp.services.analytics_service import AnalyticsService

    mock_client = AsyncMock()
    customer_id = 999

    session = shared_cache.async_session_maker()
    try:
        service = AnalyticsService(session=session, customer_id=customer_id, client=mock_client)

        # Act - Get capabilities from service (tool will do same)
        dimensions = [
            {"key": dim.key, "description": dim.description, "example": dim.example}
            for dim in service._dimensions.values()
        ]
        metrics = [
            {"key": metric.key, "description": metric.description, "formula": metric.formula}
            for metric in service._metrics.values()
        ]

        # Assert - Dimensions (added platform)
        assert len(dimensions) == 14
        dim_keys = [d["key"] for d in dimensions]
        assert "feature" in dim_keys
        assert "tester" in dim_keys
        assert "testing_type" in dim_keys  # STORY-054 AC11
        assert "month" in dim_keys
        assert "week" in dim_keys
        assert "quarter" in dim_keys
        assert "rejection_reason" in dim_keys
        assert "product" in dim_keys
        assert "customer" in dim_keys
        assert "severity" in dim_keys
        assert "status" in dim_keys
        assert "test_environment" in dim_keys  # STORY-075
        assert "known_bug" in dim_keys  # STORY-075

        # Verify each dimension has required fields
        for dim in dimensions:
            assert "key" in dim
            assert "description" in dim
            assert "example" in dim

        # Assert - Metrics (6 original + 2 customer engagement + 5 rate metrics from STORY-082 = 13)
        assert len(metrics) == 13
        metric_keys = [m["key"] for m in metrics]
        assert "bug_count" in metric_keys
        assert "test_count" in metric_keys
        assert "bugs_per_test" in metric_keys
        assert "bug_severity_score" in metric_keys
        assert "features_tested" in metric_keys
        assert "active_testers" in metric_keys
        assert "tests_created" in metric_keys  # STORY-045
        assert "tests_submitted" in metric_keys  # STORY-045
        assert "overall_acceptance_rate" in metric_keys  # STORY-082
        assert "rejection_rate" in metric_keys  # STORY-082
        assert "review_rate" in metric_keys  # STORY-082
        assert "active_acceptance_rate" in metric_keys  # STORY-082
        assert "auto_acceptance_rate" in metric_keys  # STORY-082

        # Verify each metric has required fields
        for metric in metrics:
            assert "key" in metric
            assert "description" in metric
            assert "formula" in metric

    finally:
        await session.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_metrics_validation_errors(shared_cache: PersistentCache) -> None:
    """Test query_metrics validation errors.

    Verifies:
    - Too many dimensions raises ValueError
    - Invalid dimension keys raise ValueError
    - Invalid metric keys raise ValueError
    """
    # Arrange
    from testio_mcp.services.analytics_service import AnalyticsService

    mock_client = AsyncMock()
    customer_id = 999

    session = shared_cache.async_session_maker()
    try:
        service = AnalyticsService(session=session, customer_id=customer_id, client=mock_client)

        # Test 1: Too many dimensions (max 2)
        with pytest.raises(ValueError, match="Too many dimensions"):
            await service.query_metrics(
                metrics=["bug_count"], dimensions=["feature", "month", "severity"]
            )

        # Test 2: Invalid dimension key
        with pytest.raises(ValueError, match="Invalid dimensions"):
            await service.query_metrics(metrics=["bug_count"], dimensions=["invalid_dimension"])

        # Test 3: Invalid metric key
        with pytest.raises(ValueError, match="Invalid metrics"):
            await service.query_metrics(metrics=["invalid_metric"], dimensions=["feature"])

    finally:
        await session.close()


# =============================================================================
# STORY-045: Customer Engagement Analytics - Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_customer_engagement_e2e(shared_cache: PersistentCache) -> None:
    """Test customer engagement metrics end-to-end (STORY-045 AC5).

    Verifies:
    - tests_created metric counts all tests by customer
    - tests_submitted metric filters by submitted_by_user_id IS NOT NULL
    - customer dimension uses denormalized Test.created_by field (no User join)
    - Query returns customer_id (created_by_user_id) and customer (created_by username)
    """
    # Arrange
    from unittest.mock import MagicMock

    from testio_mcp.services.analytics_service import AnalyticsService

    mock_client = MagicMock()  # Use MagicMock since no API calls are made in this test
    customer_id = 999

    async with shared_cache.async_session_maker() as session:
        # Create product for tests (unique ID to avoid conflicts with other tests)
        product_id = 9999  # Unique product ID for this test
        product = Product(
            id=product_id,
            customer_id=customer_id,
            title="Test Product",
            data=json.dumps({"id": product_id, "title": "Test Product"}),
        )
        session.add(product)
        await session.commit()

        # Create 3 tests for customer (2 with submitted_by_user_id, 1 without)
        # Note: Using denormalized created_by field (no User table needed)
        now = datetime.now(UTC)
        customer_user_id = 1001
        customer_username = "acme_corp"
        submitter_user_id = 2001  # User who submitted tests

        tests_data = [
            {
                "id": 10000,
                "status": "running",
                "submitted_by_user_id": submitter_user_id,
            },  # Counts in both metrics
            {
                "id": 10001,
                "status": "archived",
                "submitted_by_user_id": submitter_user_id,
            },  # Counts in both metrics
            {
                "id": 10002,
                "status": "running",
                "submitted_by_user_id": None,
            },  # Only counts in tests_created
        ]

        for test_data in tests_data:
            test = Test(
                id=test_data["id"],
                customer_id=customer_id,
                product_id=product_id,
                created_by_user_id=customer_user_id,  # ID for grouping
                created_by=customer_username,  # Denormalized username
                submitted_by_user_id=test_data[
                    "submitted_by_user_id"
                ],  # Who submitted (can be NULL)
                status=test_data["status"],
                data=json.dumps(
                    {
                        "id": test_data["id"],
                        "status": test_data["status"],
                        "title": f"Test {test_data['id']}",
                    }
                ),
                created_at=now,
                synced_at=now,
            )
            session.add(test)

        await session.commit()

        # Create TestFeatures (required as anchor table for analytics queries)
        from testio_mcp.models.orm import Feature, TestFeature

        # Create a feature first
        feature_id = 10000  # Unique feature ID
        feature = Feature(
            id=feature_id,
            customer_id=customer_id,
            product_id=product_id,
            title="Login Feature",
            raw_data=json.dumps({"id": feature_id, "title": "Login Feature"}),
        )
        session.add(feature)
        await session.commit()

        # Create TestFeatures linking tests to feature
        for test_id in [10000, 10001, 10002]:
            test_feature = TestFeature(
                id=test_id,  # Use test_id as test_feature_id for simplicity
                customer_id=customer_id,
                test_id=test_id,
                feature_id=feature_id,
                title="Login Feature",
            )
            session.add(test_feature)

        await session.commit()

        # Create service
        service = AnalyticsService(session=session, customer_id=customer_id, client=mock_client)

        # Act - Query customer engagement
        result = await service.query_metrics(
            metrics=["tests_created", "tests_submitted"], dimensions=["customer"]
        )

        # Assert - Response structure
        assert result.metadata.total_rows > 0

        # Find our customer in results (search by username since that's the dimension column)
        customer_row = next(
            (row for row in result.data if row.get("customer") == customer_username), None
        )

        # Verify customer was found
        assert customer_row is not None, "Customer should be in results"

        # Verify customer data (customer_id is Test.created_by_user_id)
        assert customer_row["customer_id"] == customer_user_id
        assert customer_row["customer"] == customer_username

        # Verify metrics (submitted_by_user_id filter)
        assert customer_row["tests_created"] == 3  # All 3 tests
        assert customer_row["tests_submitted"] == 2  # Only tests with submitted_by_user_id set
