"""Unit tests for FeatureService.

Tests verify that:
1. list_features returns correctly formatted feature list with pagination
2. get_feature_summary returns correct statistics
3. _format_feature correctly parses embedded user stories

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.feature_service import FeatureService


def _create_mock_feature(
    feature_id: int,
    title: str,
    description: str | None = None,
    howtofind: str | None = None,
    user_stories_json: str = "[]",
) -> MagicMock:
    """Create a mock Feature ORM model."""
    mock = MagicMock()
    mock.id = feature_id
    mock.title = title
    mock.description = description
    mock.howtofind = howtofind
    mock.user_stories = user_stories_json
    return mock


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_returns_formatted_list_with_pagination() -> None:
    """Verify list_features returns correctly formatted feature list with pagination metadata."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    # STORY-055 Fix: Now query_features returns dicts with feature + counts
    mock_repo.query_features.return_value = [
        {
            "feature": _create_mock_feature(
                feature_id=1,
                title="Login Feature",
                description="User authentication",
                howtofind="Go to login page",
                user_stories_json='["As a user, I can login", "As a user, I can logout"]',
            ),
            "test_count": 5,
            "bug_count": 3,
        },
        {
            "feature": _create_mock_feature(
                feature_id=2,
                title="Dashboard",
                description=None,
                howtofind=None,
                user_stories_json="[]",
            ),
            "test_count": 0,
            "bug_count": 0,
        },
    ]
    mock_repo.count_features.return_value = 2

    # Create service
    service = FeatureService(feature_repo=mock_repo)

    # Call list_features
    result = await service.list_features(product_id=598)

    # Verify repository called correctly with pagination params
    # STORY-058: Added has_user_stories parameter
    mock_repo.query_features.assert_called_once_with(
        product_id=598,
        sort_by=None,
        sort_order="asc",
        page=1,
        per_page=100,
        offset=0,
        has_user_stories=None,
    )
    # FIX: count_features now receives has_user_stories for accurate total_count
    mock_repo.count_features.assert_called_once_with(product_id=598, has_user_stories=None)

    # Verify response structure
    assert result["product_id"] == 598
    assert result["total"] == 2
    assert len(result["features"]) == 2

    # Verify pagination metadata (AC10)
    assert result["total_count"] == 2
    assert result["offset"] == 0
    assert result["has_more"] is False  # 2 features < per_page (100)

    # Verify first feature (STORY-055 Fix: Now includes test_count and bug_count)
    assert result["features"][0]["id"] == 1
    assert result["features"][0]["title"] == "Login Feature"
    assert result["features"][0]["description"] == "User authentication"
    assert result["features"][0]["howtofind"] == "Go to login page"
    assert result["features"][0]["user_story_count"] == 2
    assert result["features"][0]["test_count"] == 5
    assert result["features"][0]["bug_count"] == 3

    # Verify second feature (with nulls)
    assert result["features"][1]["id"] == 2
    assert result["features"][1]["title"] == "Dashboard"
    assert result["features"][1]["description"] is None
    assert result["features"][1]["howtofind"] is None
    assert result["features"][1]["user_story_count"] == 0
    assert result["features"][1]["test_count"] == 0
    assert result["features"][1]["bug_count"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_empty_product() -> None:
    """Verify list_features handles products with no features."""
    # Setup: Mock repository returns empty list
    mock_repo = AsyncMock()
    mock_repo.query_features.return_value = []
    mock_repo.count_features.return_value = 0

    # Create service
    service = FeatureService(feature_repo=mock_repo)

    # Call list_features
    result = await service.list_features(product_id=999)

    # Verify response
    assert result["product_id"] == 999
    assert result["total"] == 0
    assert result["features"] == []
    # Verify pagination for empty result
    assert result["total_count"] == 0
    assert result["has_more"] is False


# STORY-040: Pagination Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_pagination_delegation() -> None:
    """Test pagination parameters are passed to repository (AC10)."""
    mock_repo = AsyncMock()
    mock_repo.query_features.return_value = []
    mock_repo.count_features.return_value = 150

    service = FeatureService(feature_repo=mock_repo)

    await service.list_features(product_id=598, page=2, per_page=50, offset=10)

    # Verify repository called with pagination params
    # STORY-058: Added has_user_stories parameter
    mock_repo.query_features.assert_called_once_with(
        product_id=598,
        sort_by=None,
        sort_order="asc",
        page=2,
        per_page=50,
        offset=10,
        has_user_stories=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_offset_calculation() -> None:
    """Test offset calculation: offset + (page-1)*per_page (AC10)."""
    mock_repo = AsyncMock()
    mock_repo.query_features.return_value = []
    mock_repo.count_features.return_value = 150

    service = FeatureService(feature_repo=mock_repo)

    # page=3, per_page=50, offset=10 → actual_offset = 10 + (3-1)*50 = 110
    result = await service.list_features(product_id=598, page=3, per_page=50, offset=10)

    assert result["offset"] == 110


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_has_more_exact_calculation() -> None:
    """Test has_more exact calculation: (offset + len) < total_count (AC10)."""
    mock_repo = AsyncMock()
    mock_repo.count_features.return_value = 150

    service = FeatureService(feature_repo=mock_repo)

    # Case 1: More results exist → has_more = True
    mock_repo.query_features.return_value = [
        {
            "feature": _create_mock_feature(feature_id=i, title=f"Feature {i}"),
            "test_count": 0,
            "bug_count": 0,
        }
        for i in range(50)
    ]

    result = await service.list_features(product_id=598, page=1, per_page=50)
    # offset=0, len=50, total=150 → (0+50) < 150 = True
    assert result["has_more"] is True

    # Reset mock
    mock_repo.query_features.reset_mock()

    # Case 2: Last page (no more results) → has_more = False
    mock_repo.query_features.return_value = [
        {
            "feature": _create_mock_feature(feature_id=i, title=f"Feature {i}"),
            "test_count": 0,
            "bug_count": 0,
        }
        for i in range(50)
    ]

    result = await service.list_features(product_id=598, page=3, per_page=50)
    # offset=100, len=50, total=150 → (100+50) < 150 = False
    assert result["has_more"] is False


# STORY-057: Removed test_get_feature_summary_returns_statistics
# The old get_feature_summary(product_id) method was replaced with
# get_feature_summary(feature_id) per AC2. The new implementation is
# tested in tests/unit/test_tools_feature_summary.py


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_features_total_count_reflects_filtered_results() -> None:
    """Verify total_count reflects filtered results when has_user_stories=True.

    FIX: Before this fix, total_count was returning count of ALL features,
    not just those matching the has_user_stories filter.

    Example:
    - 100 total features for product
    - 25 have user stories (has_user_stories=True)
    - Page 1 returns 10 items
    - total_count should be 25, NOT 100
    """
    mock_repo = AsyncMock()

    # Repository returns 10 items on page 1
    mock_repo.query_features.return_value = [
        {
            "feature": _create_mock_feature(
                feature_id=i,
                title=f"Feature {i}",
                user_stories_json='["Story A"]',  # Has user stories
            ),
            "test_count": 1,
            "bug_count": 0,
        }
        for i in range(10)
    ]
    # Repository count returns 25 (total features with user stories)
    mock_repo.count_features.return_value = 25

    service = FeatureService(feature_repo=mock_repo)

    # Filter by has_user_stories=True with pagination
    result = await service.list_features(product_id=598, page=1, per_page=10, has_user_stories=True)

    # Verify total_count is 25 (filtered count), not 100 (all features)
    assert result["total_count"] == 25, (
        f"total_count should be 25 (filtered), got {result['total_count']}"
    )
    assert len(result["features"]) == 10  # Page has 10 items

    # Verify has_user_stories was passed to count_features for accurate count
    mock_repo.count_features.assert_called_once_with(product_id=598, has_user_stories=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_feature_parses_user_stories() -> None:
    """Verify _format_feature correctly parses embedded user stories."""
    # Setup: Mock repository not needed for this test
    mock_repo = AsyncMock()

    # Create service
    service = FeatureService(feature_repo=mock_repo)

    # Create mock feature with user stories
    mock_feature = _create_mock_feature(
        feature_id=1,
        title="Test Feature",
        user_stories_json='["Story A", "Story B"]',
    )

    # Call _format_feature
    result = service._format_feature(mock_feature)

    # Verify
    assert result["id"] == 1
    assert result["title"] == "Test Feature"
    assert result["user_story_count"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_feature_handles_empty_string() -> None:
    """Verify _format_feature handles empty user_stories string gracefully."""
    # Setup: Mock repository not needed for this test
    mock_repo = AsyncMock()

    # Create service
    service = FeatureService(feature_repo=mock_repo)

    # Create mock feature with empty string (falsy value)
    mock_feature = _create_mock_feature(
        feature_id=1,
        title="Test Feature",
        user_stories_json="",  # Empty string is falsy, returns []
    )

    # Call _format_feature - empty string is handled gracefully (returns [])
    result = service._format_feature(mock_feature)

    # Empty string evaluates to False, so code returns empty list
    assert result["user_story_count"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_feature_handles_none_user_stories() -> None:
    """Verify _format_feature handles None user_stories gracefully."""
    # Setup: Mock repository not needed for this test
    mock_repo = AsyncMock()

    # Create service
    service = FeatureService(feature_repo=mock_repo)

    # Create mock feature with None user_stories
    mock_feature = MagicMock()
    mock_feature.id = 1
    mock_feature.title = "Test Feature"
    mock_feature.description = None
    mock_feature.howtofind = None
    mock_feature.user_stories = None  # None value

    # Call _format_feature - None is handled gracefully (returns [])
    result = service._format_feature(mock_feature)

    # None evaluates to False, so code returns empty list
    assert result["user_story_count"] == 0
