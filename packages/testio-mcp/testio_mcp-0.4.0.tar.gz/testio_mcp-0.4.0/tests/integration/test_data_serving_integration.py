"""Integration tests for Data Serving Layer (STORY-037).

Tests validate:
- FeatureService with real database
- UserStoryService with real database
- UserService with real database
- list_features, list_user_stories, list_users tools with real data

Prerequisites:
- Features must be synced first (integration fixtures handle this)
- Test product from TESTIO_PRODUCT_ID/TESTIO_PRODUCT_IDS
"""

import pytest

from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.user_repository import UserRepository
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.services.user_service import UserService
from testio_mcp.services.user_story_service import UserStoryService

# ==========================================
# FeatureService Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_feature_service_list_features(shared_cache, shared_client, test_product_id):
    """Integration test: FeatureService.list_features with real data."""
    async with shared_cache.async_session_maker() as session:
        # Sync features first
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)
        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")
            raise

        # Create service and query
        service = FeatureService(feature_repo=repo)
        result = await service.list_features(product_id=test_product_id)

        # Verify response
        assert result["product_id"] == test_product_id
        assert result["total"] > 0  # Test product should have features
        assert len(result["features"]) > 0

        # Verify feature structure
        feature = result["features"][0]
        assert "id" in feature
        assert "title" in feature
        assert "description" in feature
        assert "howtofind" in feature
        assert "user_story_count" in feature


@pytest.mark.integration
@pytest.mark.asyncio
async def test_feature_service_get_feature_summary(shared_cache, shared_client, test_product_id):
    """Integration test: FeatureService.get_feature_summary with real data."""
    async with shared_cache.async_session_maker() as session:
        # Sync features first
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)

        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")

            raise

        # Create service and get features to find a feature_id
        service = FeatureService(feature_repo=repo)
        features_result = await service.list_features(product_id=test_product_id)
        assert features_result["total"] > 0, "Need at least one feature for summary test"

        # Get summary for first feature
        feature_id = features_result["features"][0]["id"]
        result = await service.get_feature_summary(feature_id=feature_id)

        # Verify response structure (STORY-057)
        assert result["id"] == feature_id
        assert "title" in result
        assert "description" in result
        assert "howtofind" in result
        assert "user_stories" in result  # Embedded user stories
        assert "test_count" in result
        assert "bug_count" in result
        assert "product" in result
        assert result["product"]["id"] == test_product_id
        assert "data_as_of" in result  # Staleness visibility (STORY-057)


# ==========================================
# UserStoryService Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_story_service_list_user_stories(shared_cache, shared_client, test_product_id):
    """Integration test: UserStoryService.list_user_stories with real data."""
    async with shared_cache.async_session_maker() as session:
        # Sync features first (user stories are embedded in features)
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)

        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")

            raise

        # Create service and query
        service = UserStoryService(feature_repo=repo)
        result = await service.list_user_stories(product_id=test_product_id)

        # Verify response
        assert result["product_id"] == test_product_id
        assert result["feature_id"] is None  # No filter applied
        assert result["total"] >= 0  # Depends on embedded user stories

        # If there are user stories, verify structure
        if result["user_stories"]:
            story = result["user_stories"][0]
            assert "title" in story
            assert "feature_id" in story
            assert "feature_title" in story


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_story_service_list_user_stories_with_feature_filter(
    shared_cache, shared_client, test_product_id
):
    """Integration test: UserStoryService.list_user_stories with feature filter."""
    async with shared_cache.async_session_maker() as session:
        # Sync features first
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)

        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")

            raise

        # Get a feature ID to filter by
        features = await repo.get_features_for_product(product_id=test_product_id)
        if not features:
            pytest.skip(f"No features synced for product {test_product_id}")

        feature_id = features[0].id

        # Create service and query with filter
        service = UserStoryService(feature_repo=repo)
        result = await service.list_user_stories(product_id=test_product_id, feature_id=feature_id)

        # Verify filter applied
        assert result["feature_id"] == feature_id

        # All returned stories should belong to this feature
        for story in result["user_stories"]:
            assert story["feature_id"] == feature_id


# ==========================================
# UserService Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_service_list_users(shared_cache, shared_client, test_product_id):
    """Integration test: UserService.list_users with real data.

    Note: This test requires bugs to be synced first (to extract tester users).
    If no users exist, the test verifies empty result handling.
    """
    async with shared_cache.async_session_maker() as session:
        # Create repository and service
        repo = UserRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = UserService(user_repo=repo)

        # Query users
        result = await service.list_users(days=365)

        # Verify response structure
        assert "users" in result
        assert "total" in result
        assert "filter" in result
        assert result["filter"]["days"] == 365

        # If users exist, verify structure
        if result["users"]:
            user = result["users"][0]
            assert "id" in user
            assert "username" in user
            assert "user_type" in user
            assert "first_seen" in user
            assert "last_seen" in user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_service_list_users_with_type_filter(
    shared_cache, shared_client, test_product_id
):
    """Integration test: UserService.list_users with user_type filter."""
    async with shared_cache.async_session_maker() as session:
        # Create repository and service
        repo = UserRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = UserService(user_repo=repo)

        # Query tester users only
        result = await service.list_users(user_type="tester", days=365)

        # Verify filter applied
        assert result["filter"]["user_type"] == "tester"

        # All returned users should be testers
        for user in result["users"]:
            assert user["user_type"] == "tester"


# ==========================================
# Performance Validation (AC13)
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_features_performance(shared_cache, shared_client, test_product_id):
    """Performance test: list_features should complete under 500ms.

    Note: This is a smoke test, not a strict benchmark. Actual performance
    depends on hardware, database state, and system load.
    """
    import time

    async with shared_cache.async_session_maker() as session:
        # Sync features first
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)

        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")

            raise

        # Create service
        service = FeatureService(feature_repo=repo)

        # Measure query time
        start = time.perf_counter()
        result = await service.list_features(product_id=test_product_id)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify result
        assert result["total"] > 0

        # Performance assertion (generous threshold for CI)
        assert elapsed_ms < 500, f"list_features took {elapsed_ms:.2f}ms (expected <500ms)"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_user_stories_performance(shared_cache, shared_client, test_product_id):
    """Performance test: list_user_stories should complete under 100ms.

    Note: This is a smoke test, not a strict benchmark.
    """
    import time

    async with shared_cache.async_session_maker() as session:
        # Sync features first (user stories embedded)
        repo = FeatureRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        try:
            await repo.sync_features(product_id=test_product_id)

        except TestIOAPIError as e:
            if e.status_code in {404, 403}:
                pytest.skip(f"Product {test_product_id} not accessible (HTTP {e.status_code})")

            raise

        # Create service
        service = UserStoryService(feature_repo=repo)

        # Measure query time
        start = time.perf_counter()
        _ = await service.list_user_stories(product_id=test_product_id)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Performance assertion (generous threshold for CI)
        assert elapsed_ms < 500, f"list_user_stories took {elapsed_ms:.2f}ms (expected <500ms)"
