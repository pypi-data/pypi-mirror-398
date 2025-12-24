"""Unit tests for UserService.

Tests verify that:
1. list_users returns correctly formatted user list with pagination
2. list_users filters by user_type correctly
3. get_top_contributors returns correct statistics

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.user_service import UserService


def _create_mock_user(
    user_id: int,
    username: str,
    user_type: str = "tester",
    first_seen: datetime | None = None,
    last_seen: datetime | None = None,
) -> MagicMock:
    """Create a mock User ORM model."""
    mock = MagicMock()
    mock.id = user_id
    mock.username = username
    mock.user_type = user_type
    mock.first_seen = first_seen or datetime(2024, 1, 1, tzinfo=UTC)
    mock.last_seen = last_seen or datetime(2024, 6, 15, tzinfo=UTC)
    return mock


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_returns_formatted_list_with_pagination() -> None:
    """Verify list_users returns correctly formatted user list with pagination."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    # STORY-058: query_users returns list[dict[str, Any]] with
    # {"user": User, "last_activity": datetime | None}
    mock_repo.query_users.return_value = [
        {
            "user": _create_mock_user(
                user_id=1,
                username="john_tester",
                user_type="tester",
                first_seen=datetime(2024, 1, 1, tzinfo=UTC),
                last_seen=datetime(2024, 6, 15, tzinfo=UTC),
            ),
            "last_activity": datetime(2024, 6, 15, tzinfo=UTC),
        },
        {
            "user": _create_mock_user(
                user_id=2,
                username="jane_customer",
                user_type="customer",
                first_seen=datetime(2024, 3, 1, tzinfo=UTC),
                last_seen=datetime(2024, 6, 10, tzinfo=UTC),
            ),
            "last_activity": datetime(2024, 6, 10, tzinfo=UTC),
        },
    ]
    mock_repo.count_active_users.return_value = 2

    # Create service
    service = UserService(user_repo=mock_repo)

    # Call list_users
    result = await service.list_users()

    # Verify repository called correctly with pagination params
    mock_repo.query_users.assert_called_once_with(
        user_type=None, days=365, sort_by=None, sort_order="asc", page=1, per_page=100, offset=0
    )
    mock_repo.count_active_users.assert_called_once_with(user_type=None, days=365)

    # Verify response structure
    assert result["total"] == 2
    assert result["total_count"] == 2
    assert result["offset"] == 0
    assert result["has_more"] is False
    assert result["filter"]["user_type"] is None
    assert result["filter"]["days"] == 365

    # Verify users (STORY-058: now has last_activity instead of last_seen)
    assert len(result["users"]) == 2
    assert result["users"][0]["id"] == 1
    assert result["users"][0]["username"] == "john_tester"
    assert result["users"][0]["user_type"] == "tester"
    assert result["users"][0]["first_seen"] == "2024-01-01T00:00:00+00:00"
    assert result["users"][0]["last_activity"] == "2024-06-15T00:00:00+00:00"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_filters_by_user_type() -> None:
    """Verify list_users filters by user_type correctly."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    # STORY-058: query_users returns list[dict[str, Any]]
    mock_repo.query_users.return_value = [
        {
            "user": _create_mock_user(user_id=1, username="john_tester", user_type="tester"),
            "last_activity": datetime(2024, 6, 15, tzinfo=UTC),
        },
    ]
    mock_repo.count_active_users.return_value = 1

    # Create service
    service = UserService(user_repo=mock_repo)

    # Call list_users with type filter
    result = await service.list_users(user_type="tester", days=30)

    # Verify repository called with filter and pagination
    mock_repo.query_users.assert_called_once_with(
        user_type="tester", days=30, sort_by=None, sort_order="asc", page=1, per_page=100, offset=0
    )
    mock_repo.count_active_users.assert_called_once_with(user_type="tester", days=30)

    # Verify response
    assert result["total"] == 1
    assert result["total_count"] == 1
    assert result["filter"]["user_type"] == "tester"
    assert result["filter"]["days"] == 30


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_empty_result() -> None:
    """Verify list_users handles empty result."""
    # Setup: Mock repository returns empty list
    mock_repo = AsyncMock()
    # STORY-058: query_users returns list[dict[str, Any]]
    mock_repo.query_users.return_value = []
    mock_repo.count_active_users.return_value = 0

    # Create service
    service = UserService(user_repo=mock_repo)

    # Call list_users
    result = await service.list_users()

    # Verify response
    assert result["total"] == 0
    assert result["total_count"] == 0
    assert result["has_more"] is False
    assert result["users"] == []


# STORY-040: Pagination Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_pagination_delegation() -> None:
    """Test pagination parameters are passed to repository (AC12)."""
    mock_repo = AsyncMock()
    # STORY-058: query_users returns list[dict[str, Any]]
    mock_repo.query_users.return_value = []
    mock_repo.count_active_users.return_value = 78

    service = UserService(user_repo=mock_repo)

    await service.list_users(user_type="tester", days=365, page=2, per_page=20, offset=10)

    # Verify repository called with pagination params (STORY-058: added sort_by, sort_order)
    mock_repo.query_users.assert_called_once_with(
        user_type="tester", days=365, sort_by=None, sort_order="asc", page=2, per_page=20, offset=10
    )
    mock_repo.count_active_users.assert_called_once_with(user_type="tester", days=365)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_offset_calculation() -> None:
    """Test offset calculation: offset + (page-1)*per_page (AC12)."""
    mock_repo = AsyncMock()
    mock_repo.get_active_users.return_value = []
    mock_repo.count_active_users.return_value = 78

    service = UserService(user_repo=mock_repo)

    # page=3, per_page=20, offset=10 → actual_offset = 10 + (3-1)*20 = 50
    result = await service.list_users(page=3, per_page=20, offset=10)

    assert result["offset"] == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_users_has_more_heuristic() -> None:
    """Test has_more heuristic: exact calculation (actual_offset + len(results)) < total_count."""
    mock_repo = AsyncMock()
    mock_repo.count_active_users.return_value = 78

    service = UserService(user_repo=mock_repo)

    # Case 1: Full page returned, more pages exist → has_more = True
    # STORY-058: query_users returns list[dict[str, Any]]
    mock_repo.query_users.return_value = [
        {
            "user": _create_mock_user(user_id=i, username=f"user{i}"),
            "last_activity": datetime(2024, 6, 15, tzinfo=UTC),
        }
        for i in range(20)
    ]

    result = await service.list_users(page=1, per_page=20)
    # offset=0, len=20 → 0+20=20 < 78 → has_more=True
    assert result["has_more"] is True

    # Reset mock
    mock_repo.query_users.reset_mock()
    mock_repo.count_active_users.reset_mock()
    mock_repo.count_active_users.return_value = 78

    # Case 2: Last partial page → has_more = False
    mock_repo.query_users.return_value = [
        {
            "user": _create_mock_user(user_id=i, username=f"user{i}"),
            "last_activity": datetime(2024, 6, 15, tzinfo=UTC),
        }
        for i in range(18)
    ]

    result = await service.list_users(page=4, per_page=20)
    # offset=60, len=18 → 60+18=78 == 78 → has_more=False
    assert result["has_more"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_contributors_returns_statistics() -> None:
    """Verify get_top_contributors returns correct statistics."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_top_contributors.return_value = [
        (_create_mock_user(user_id=1, username="top_tester"), 50),
        (_create_mock_user(user_id=2, username="active_tester"), 30),
        (_create_mock_user(user_id=3, username="new_tester"), 10),
    ]

    # Create service
    service = UserService(user_repo=mock_repo)

    # Call get_top_contributors
    result = await service.get_top_contributors(user_type="tester", limit=10)

    # Verify repository called correctly
    mock_repo.get_top_contributors.assert_called_once_with(user_type="tester", limit=10, days=None)

    # Verify response structure
    assert result["total"] == 3
    assert result["filter"]["user_type"] == "tester"
    assert result["filter"]["limit"] == 10
    assert result["filter"]["days"] is None

    # Verify contributors
    assert len(result["contributors"]) == 3
    assert result["contributors"][0]["user"]["username"] == "top_tester"
    assert result["contributors"][0]["count"] == 50
    assert result["contributors"][1]["count"] == 30
    assert result["contributors"][2]["count"] == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_contributors_with_days_filter() -> None:
    """Verify get_top_contributors respects days filter."""
    # Setup: Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_top_contributors.return_value = []

    # Create service
    service = UserService(user_repo=mock_repo)

    # Call get_top_contributors with days filter
    result = await service.get_top_contributors(user_type="customer", limit=5, days=30)

    # Verify repository called with days
    mock_repo.get_top_contributors.assert_called_once_with(user_type="customer", limit=5, days=30)

    # Verify filter in response
    assert result["filter"]["days"] == 30
