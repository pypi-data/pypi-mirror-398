"""Unit tests for UserStoryService.

Tests verify that:
1. list_user_stories returns correctly formatted user story list with in-memory pagination
2. list_user_stories filters by feature_id correctly
3. get_user_story_summary returns correct statistics

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.user_story_service import UserStoryService


def _create_mock_feature(
    feature_id: int,
    title: str,
    user_stories_json: str = "[]",
) -> MagicMock:
    """Create a mock Feature ORM model."""
    mock = MagicMock()
    mock.id = feature_id
    mock.title = title
    mock.user_stories = user_stories_json
    return mock


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_user_stories_returns_formatted_list_with_pagination() -> None:
    """Verify list_user_stories returns correctly formatted user story list with pagination."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Login Feature",
            user_stories_json='["As a user, I can login", "As a user, I can logout"]',
        ),
        _create_mock_feature(
            feature_id=2,
            title="Dashboard",
            user_stories_json='["As a user, I can view stats"]',
        ),
    ]

    # Create service
    service = UserStoryService(feature_repo=mock_repo)

    # Call list_user_stories
    result = await service.list_user_stories(product_id=598)

    # Verify repository called correctly
    mock_repo.get_features_for_product.assert_called_once_with(product_id=598)

    # Verify response structure
    assert result["product_id"] == 598
    assert result["feature_id"] is None
    assert result["total"] == 3  # 2 + 1

    # Verify pagination metadata
    assert result["total_count"] == 3
    assert result["offset"] == 0
    assert result["has_more"] is False

    # Verify user stories
    assert len(result["user_stories"]) == 3
    assert result["user_stories"][0]["title"] == "As a user, I can login"
    assert result["user_stories"][0]["feature_id"] == 1
    assert result["user_stories"][0]["feature_title"] == "Login Feature"

    assert result["user_stories"][2]["title"] == "As a user, I can view stats"
    assert result["user_stories"][2]["feature_id"] == 2
    assert result["user_stories"][2]["feature_title"] == "Dashboard"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_user_stories_filters_by_feature_id() -> None:
    """Verify list_user_stories filters by feature_id correctly."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Login Feature",
            user_stories_json='["As a user, I can login"]',
        ),
        _create_mock_feature(
            feature_id=2,
            title="Dashboard",
            user_stories_json='["As a user, I can view stats"]',
        ),
    ]

    # Create service
    service = UserStoryService(feature_repo=mock_repo)

    # Call list_user_stories with feature_id filter
    result = await service.list_user_stories(product_id=598, feature_id=1)

    # Verify response only contains feature 1 stories
    assert result["product_id"] == 598
    assert result["feature_id"] == 1
    assert result["total"] == 1
    assert result["total_count"] == 1

    assert len(result["user_stories"]) == 1
    assert result["user_stories"][0]["title"] == "As a user, I can login"
    assert result["user_stories"][0]["feature_id"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_user_stories_empty_product() -> None:
    """Verify list_user_stories handles products with no features."""
    # Setup: Mock repository returns empty list
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = []

    # Create service
    service = UserStoryService(feature_repo=mock_repo)

    # Call list_user_stories
    result = await service.list_user_stories(product_id=999)

    # Verify response
    assert result["product_id"] == 999
    assert result["feature_id"] is None
    assert result["total"] == 0
    assert result["total_count"] == 0
    assert result["has_more"] is False
    assert result["user_stories"] == []


# STORY-040: In-Memory Pagination Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_in_memory_pagination_slicing() -> None:
    """Test in-memory pagination slicing logic (AC11)."""
    # Setup: 3 features with 5, 3, 2 user stories = 10 total
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1",
            user_stories_json='["S1", "S2", "S3", "S4", "S5"]',
        ),
        _create_mock_feature(
            feature_id=2,
            title="Feature 2",
            user_stories_json='["S6", "S7", "S8"]',
        ),
        _create_mock_feature(
            feature_id=3,
            title="Feature 3",
            user_stories_json='["S9", "S10"]',
        ),
    ]

    service = UserStoryService(feature_repo=mock_repo)

    # Test: page=2, per_page=4 → items 4-7 (S5, S6, S7, S8)
    result = await service.list_user_stories(product_id=598, page=2, per_page=4)

    assert result["total_count"] == 10
    assert result["offset"] == 4
    assert len(result["user_stories"]) == 4
    assert result["user_stories"][0]["title"] == "S5"
    assert result["user_stories"][3]["title"] == "S8"
    assert result["has_more"] is True  # 8 < 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_in_memory_pagination_last_page() -> None:
    """Test has_more=False on last page (AC11)."""
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1",
            user_stories_json='["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]',
        ),
    ]

    service = UserStoryService(feature_repo=mock_repo)

    # Test: page=3, per_page=4 → items 8-9 (S9, S10) - last 2 items
    result = await service.list_user_stories(product_id=598, page=3, per_page=4)

    assert result["total_count"] == 10
    assert result["offset"] == 8  # (3-1)*4 = 8
    assert len(result["user_stories"]) == 2  # Only 2 remaining
    assert result["user_stories"][0]["title"] == "S9"
    assert result["user_stories"][1]["title"] == "S10"
    assert result["has_more"] is False  # 10 == 10 (end_index reached total)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_in_memory_pagination_with_feature_filter() -> None:
    """Test feature_id filter with pagination (AC11)."""
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1",
            user_stories_json='["S1", "S2", "S3", "S4", "S5"]',
        ),
        _create_mock_feature(
            feature_id=2,
            title="Feature 2",
            user_stories_json='["S6", "S7", "S8"]',
        ),
    ]

    service = UserStoryService(feature_repo=mock_repo)

    # Filter to feature 1 only (5 stories), then paginate
    result = await service.list_user_stories(product_id=598, feature_id=1, page=2, per_page=2)

    assert result["total_count"] == 5  # Only feature 1 stories
    assert result["offset"] == 2  # (2-1)*2 = 2
    assert len(result["user_stories"]) == 2
    assert result["user_stories"][0]["title"] == "S3"
    assert result["user_stories"][1]["title"] == "S4"
    assert result["has_more"] is True  # 4 < 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_in_memory_pagination_large_offset() -> None:
    """Test large offset beyond available results (AC11)."""
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1",
            user_stories_json='["S1", "S2", "S3"]',
        ),
    ]

    service = UserStoryService(feature_repo=mock_repo)

    # Request page beyond available results
    result = await service.list_user_stories(product_id=598, page=10, per_page=10)

    assert result["total_count"] == 3
    assert result["offset"] == 90  # (10-1)*10 = 90
    assert len(result["user_stories"]) == 0  # No results at this offset
    assert result["has_more"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_story_summary_returns_statistics() -> None:
    """Verify get_user_story_summary returns correct statistics."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1",
            user_stories_json='["Story 1", "Story 2", "Story 3"]',
        ),
        _create_mock_feature(
            feature_id=2,
            title="Feature 2",
            user_stories_json='["Story 4"]',
        ),
        _create_mock_feature(
            feature_id=3,
            title="Feature 3 (empty)",
            user_stories_json="[]",
        ),
    ]

    # Create service
    service = UserStoryService(feature_repo=mock_repo)

    # Call get_user_story_summary
    result = await service.get_user_story_summary(product_id=598)

    # Verify response
    assert result["product_id"] == 598
    assert result["total_user_stories"] == 4  # 3 + 1 + 0

    # by_feature should only include features with stories
    assert result["by_feature"] == {1: 3, 2: 1}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_story_summary_handles_no_stories() -> None:
    """Verify get_user_story_summary handles products with no user stories."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_features_for_product.return_value = [
        _create_mock_feature(
            feature_id=1,
            title="Feature 1 (empty)",
            user_stories_json="[]",
        ),
    ]

    # Create service
    service = UserStoryService(feature_repo=mock_repo)

    # Call get_user_story_summary
    result = await service.get_user_story_summary(product_id=598)

    # Verify response
    assert result["product_id"] == 598
    assert result["total_user_stories"] == 0
    assert result["by_feature"] is None  # No features have stories
