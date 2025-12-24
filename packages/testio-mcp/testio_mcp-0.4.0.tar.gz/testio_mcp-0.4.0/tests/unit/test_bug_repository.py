"""Unit tests for BugRepository.

Tests the bug repository data access layer with mocked AsyncSession and API client.
Updated for STORY-032C: ORM refactor (aiosqlite → SQLModel + AsyncSession).
Updated for STORY-047: Status enrichment (auto_accepted as distinct status).
"""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm.bug import Bug
from testio_mcp.repositories.bug_repository import BugRepository, _enrich_bug_status

# STORY-047: Status Enrichment Helper Tests


@pytest.mark.unit
def test_enrich_bug_status_auto_accepted():
    """Verify auto_accepted=True with accepted status returns 'auto_accepted'."""
    result = _enrich_bug_status("accepted", True)
    assert result == "auto_accepted"


@pytest.mark.unit
def test_enrich_bug_status_active_accepted():
    """Verify auto_accepted=False with accepted status returns 'accepted'."""
    result = _enrich_bug_status("accepted", False)
    assert result == "accepted"


@pytest.mark.unit
def test_enrich_bug_status_accepted_none_auto():
    """Verify auto_accepted=None with accepted status returns 'accepted'."""
    result = _enrich_bug_status("accepted", None)
    assert result == "accepted"


@pytest.mark.unit
def test_enrich_bug_status_rejected():
    """Verify rejected status is unchanged regardless of auto_accepted."""
    assert _enrich_bug_status("rejected", True) == "rejected"
    assert _enrich_bug_status("rejected", False) == "rejected"
    assert _enrich_bug_status("rejected", None) == "rejected"


@pytest.mark.unit
def test_enrich_bug_status_forwarded():
    """Verify forwarded status is unchanged regardless of auto_accepted."""
    assert _enrich_bug_status("forwarded", True) == "forwarded"
    assert _enrich_bug_status("forwarded", False) == "forwarded"
    assert _enrich_bug_status("forwarded", None) == "forwarded"


@pytest.mark.unit
def test_enrich_bug_status_none():
    """Verify None status returns None."""
    assert _enrich_bug_status(None, True) is None
    assert _enrich_bug_status(None, False) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_returns_deserialized_bugs_with_enriched_status():
    """Verify get_bugs returns deserialized bug data with enriched status from ORM.

    STORY-047: Status is injected from ORM status column, not raw_data.
    """
    # Setup: Mock AsyncSession with bug data
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()

    # raw_data has original API status, but ORM status column has enriched value
    bug1_raw = {"id": 1, "title": "Bug 1", "status": "accepted", "auto_accepted": True}
    bug2_raw = {"id": 2, "title": "Bug 2", "status": "rejected"}

    bug_orm1 = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Bug 1",
        status="auto_accepted",  # Enriched status in ORM
        raw_data=json.dumps(bug1_raw),
        synced_at=datetime.now(UTC),
    )
    bug_orm2 = Bug(
        id=2,
        customer_id=123,
        test_id=456,
        title="Bug 2",
        status="rejected",  # Same in ORM as raw_data
        raw_data=json.dumps(bug2_raw),
        synced_at=datetime.now(UTC),
    )

    mock_result.all.return_value = [bug_orm1, bug_orm2]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    result = await repo.get_bugs(test_id=456)

    # Verify: Status is enriched from ORM column
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["title"] == "Bug 1"
    assert result[0]["status"] == "auto_accepted"  # Enriched from ORM, not raw_data

    assert result[1]["id"] == 2
    assert result[1]["title"] == "Bug 2"
    assert result[1]["status"] == "rejected"

    # Verify session.exec was called
    mock_session.exec.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_returns_empty_list_when_no_bugs():
    """Verify get_bugs returns empty list when test has no bugs."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    result = await repo.get_bugs(test_id=456)

    assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_stats_aggregates_by_status():
    """Verify get_bug_stats correctly aggregates bugs by status."""
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock status query result
    status_result = MagicMock()
    status_result.all.return_value = [
        ("accepted", 5),
        ("rejected", 2),
        ("forwarded", 3),
    ]

    # Mock severity query result
    severity_result = MagicMock()
    severity_result.all.return_value = [
        ("critical", 2),
        ("high", 3),
        ("medium", 5),
    ]

    # Mock total count query result
    count_result = MagicMock()
    count_result.one.return_value = 10

    # Return different results for each exec call (removed acceptance_state query)
    mock_session.exec.side_effect = [
        status_result,
        severity_result,
        count_result,
    ]

    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    result = await repo.get_bug_stats(test_id=456)

    # Verify (removed by_acceptance_state check)
    assert result["total"] == 10
    assert result["by_status"] == {"accepted": 5, "rejected": 2, "forwarded": 3}
    assert result["by_severity"] == {"critical": 2, "high": 3, "medium": 5}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_stats_returns_zero_when_no_bugs():
    """Verify get_bug_stats returns zero total when test has no bugs."""
    mock_session = AsyncMock(spec=AsyncSession)

    # All queries return empty results
    empty_result = MagicMock()
    empty_result.all.return_value = []

    count_result = MagicMock()
    count_result.one.return_value = 0

    mock_session.exec.side_effect = [
        empty_result,  # status
        empty_result,  # severity
        count_result,  # total (removed acceptance_state)
    ]

    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    result = await repo.get_bug_stats(test_id=456)

    assert result["total"] == 0
    assert result["by_status"] == {}
    assert result["by_severity"] == {}
    # Removed by_acceptance_state assertion


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_fetches_from_api_and_upserts():
    """Verify refresh_bugs fetches from API and inserts into SQLite."""
    # Setup: Mock API response
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "bugs": [
            {
                "id": 1,
                "title": "Critical bug",
                "severity": "critical",
                "status": "accepted",
                "acceptance_state": "accepted",
                "start_at": "2025-01-01T00:00:00Z",
                "test": {"id": 456},
            },
            {
                "id": 2,
                "title": "Minor bug",
                "severity": "low",
                "status": "rejected",
                "acceptance_state": "rejected",
                "start_at": "2025-01-01T00:00:00Z",
                "test": {"id": 456},
            },
        ]
    }

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    count = await repo.refresh_bugs(test_id=456)

    # Verify API call
    mock_client.get.assert_called_once_with("bugs?filter_test_cycle_ids=456")

    # Verify session.exec called for UPSERT (batch INSERT ON CONFLICT)
    # Note: Uses bulk UPSERT pattern (pre-fetch users approach), not individual add calls
    assert mock_session.exec.call_count == 1

    # Verify count
    assert count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_handles_empty_api_response():
    """Verify refresh_bugs handles empty bug list from API."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {"bugs": []}

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    count = await repo.refresh_bugs(test_id=456)

    # Early return - no session.exec calls (no UPSERT needed for empty list)
    mock_session.exec.assert_not_called()

    # No inserts (no bugs)
    mock_session.add.assert_not_called()

    assert count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_handles_missing_optional_fields():
    """Verify refresh_bugs handles bugs with missing optional fields."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "bugs": [
            {
                "id": 1,
                # title missing - should default to "Untitled"
                # severity missing - should be None
                # other fields missing
                "test": {"id": 456},
            }
        ]
    }

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    count = await repo.refresh_bugs(test_id=456)

    # Verify session.exec called once for UPSERT (batch INSERT ON CONFLICT)
    # Note: Uses bulk UPSERT pattern, can't inspect individual Bug objects via add()
    # The UPSERT values are passed to sqlite_insert().values(bug_rows)
    mock_session.exec.assert_called_once()

    assert count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_bugs_for_test_deletes():
    """Verify delete_bugs_for_test correctly deletes bugs."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    await repo.delete_bugs_for_test(test_id=456)

    # Verify DELETE query executed
    mock_session.exec.assert_called_once()


# STORY-024: Intelligent Bug Caching Tests (Updated for ORM)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_cached_or_refresh_immutable_uses_cache(monkeypatch):
    """Verify immutable tests (archived) always use cache (no API call)."""
    from testio_mcp.config import settings

    # Mock settings to enable caching
    monkeypatch.setattr(settings, "BUG_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "BUG_CACHE_BYPASS", False)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()

    # Mock test status query result: archived (immutable), with old bugs_synced_at
    old_sync_time = "2024-01-01T00:00:00+00:00"  # 10 days ago (ISO format)
    test_result = MagicMock()
    test_result.all.return_value = [
        (456, "archived", old_sync_time),  # test_id, status, bugs_synced_at
    ]

    # Mock bug query result (cache hit)
    bug = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Cached Bug",
        raw_data=json.dumps({"id": 1, "title": "Cached Bug"}),
        synced_at=datetime.now(UTC),
    )
    bugs_result = MagicMock()
    bugs_result.all.return_value = [bug]

    # Return different results for each exec call
    mock_session.exec.side_effect = [test_result, bugs_result]

    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    bugs_dict, cache_stats = await repo.get_bugs_cached_or_refresh(test_ids=[456])

    # Verify: No API call (immutable test uses cache)
    mock_client.get.assert_not_called()

    # Verify: Bugs returned from cache
    assert 456 in bugs_dict
    assert len(bugs_dict[456]) == 1
    assert bugs_dict[456][0]["title"] == "Cached Bug"

    # Verify: Cache stats show 100% hit rate
    assert cache_stats["total_tests"] == 1
    assert cache_stats["cache_hits"] == 1
    assert cache_stats["api_calls"] == 0
    assert cache_stats["cache_hit_rate"] == 100.0
    assert cache_stats["breakdown"]["immutable_cached"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_cached_or_refresh_mutable_refreshes_when_stale(monkeypatch):
    """Verify mutable tests (running) refresh if bugs are stale (>1 hour)."""
    import asyncio

    from testio_mcp.config import settings

    # Mock settings
    monkeypatch.setattr(settings, "BUG_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "BUG_CACHE_BYPASS", False)
    monkeypatch.setattr(settings, "CACHE_TTL_SECONDS", 3600)  # 1 hour

    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()

    # Mock test status query: running (mutable), with stale bugs_synced_at (2 hours ago)
    stale_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    test_result = MagicMock()
    test_result.all.return_value = [
        (456, "running", stale_time),
    ]

    # Mock API response
    mock_client.get.return_value = {
        "bugs": [
            {"id": 1, "title": "Fresh Bug", "test": {"id": 456}},
        ]
    }

    # Mock bug query result (after refresh)
    bug = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Fresh Bug",
        raw_data=json.dumps({"id": 1, "title": "Fresh Bug"}),
        synced_at=datetime.now(UTC),
    )
    bugs_result = MagicMock()
    bugs_result.all.return_value = [bug]

    # Mock cache with required methods for decoupled API/DB pattern
    mock_cache = MagicMock()
    mock_cache.get_refresh_lock = MagicMock(return_value=asyncio.Lock())
    mock_cache._write_semaphore = asyncio.Semaphore(5)

    # Create isolated session mock for cache.async_session_maker()
    mock_isolated_session = AsyncMock(spec=AsyncSession)
    mock_isolated_session.exec = AsyncMock(return_value=bugs_result)  # For final fresh session read
    mock_isolated_session.commit = AsyncMock()
    mock_isolated_session.add = MagicMock()
    mock_isolated_session.rollback = AsyncMock()  # For Issue #5 rollback fix

    # Mock async context manager for session maker
    @asynccontextmanager
    async def mock_session_maker():
        yield mock_isolated_session

    mock_cache.async_session_maker = mock_session_maker

    # Return different results for each exec call on main session
    # Flow: test status query only (final read now uses fresh session after refresh)
    mock_session.exec.side_effect = [
        test_result,  # Test status query
    ]

    repo = BugRepository(
        session=mock_session, client=mock_client, customer_id=123, cache=mock_cache
    )

    # Execute
    bugs_dict, cache_stats = await repo.get_bugs_cached_or_refresh(test_ids=[456])

    # Verify: API called (stale mutable test)
    mock_client.get.assert_called_once()

    # Verify: Fresh bugs returned
    assert 456 in bugs_dict
    assert len(bugs_dict[456]) == 1
    assert bugs_dict[456][0]["title"] == "Fresh Bug"

    # Verify: Cache stats show API call
    assert cache_stats["total_tests"] == 1
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 1
    assert cache_stats["cache_hit_rate"] == 0.0
    assert cache_stats["breakdown"]["mutable_stale"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_cached_or_refresh_force_refresh_bypasses_cache(monkeypatch):
    """Verify force_refresh always fetches from API."""
    import asyncio

    from testio_mcp.config import settings

    monkeypatch.setattr(settings, "BUG_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "BUG_CACHE_BYPASS", False)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()

    # Mock test status: archived (immutable) with fresh bugs
    fresh_time = "2024-12-31T23:59:59+00:00"
    test_result = MagicMock()
    test_result.all.return_value = [
        (456, "archived", fresh_time),
    ]

    # Mock API response
    mock_client.get.return_value = {
        "bugs": [
            {"id": 1, "title": "Forced Fresh Bug", "test": {"id": 456}},
        ]
    }

    # Mock bug query result
    bug = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Forced Fresh Bug",
        raw_data=json.dumps({"id": 1, "title": "Forced Fresh Bug"}),
        synced_at=datetime.now(UTC),
    )
    bugs_result = MagicMock()
    bugs_result.all.return_value = [bug]

    # Mock cache with required methods for decoupled API/DB pattern
    mock_cache = MagicMock()
    mock_cache.get_refresh_lock = MagicMock(return_value=asyncio.Lock())
    mock_cache._write_semaphore = asyncio.Semaphore(5)

    # Create isolated session mock for cache.async_session_maker()
    mock_isolated_session = AsyncMock(spec=AsyncSession)
    mock_isolated_session.exec = AsyncMock(return_value=bugs_result)  # For final fresh session read
    mock_isolated_session.commit = AsyncMock()
    mock_isolated_session.add = MagicMock()
    mock_isolated_session.rollback = AsyncMock()  # For Issue #5 rollback fix

    # Mock async context manager for session maker
    @asynccontextmanager
    async def mock_session_maker():
        yield mock_isolated_session

    mock_cache.async_session_maker = mock_session_maker

    # Return different results for each exec call on main session
    # Flow: test status query only (final read now uses fresh session after refresh)
    mock_session.exec.side_effect = [
        test_result,  # Test status query
    ]

    repo = BugRepository(
        session=mock_session, client=mock_client, customer_id=123, cache=mock_cache
    )

    # Execute with force_refresh
    bugs_dict, cache_stats = await repo.get_bugs_cached_or_refresh(
        test_ids=[456], force_refresh=True
    )

    # Verify: API called despite fresh cache
    mock_client.get.assert_called_once()

    # Verify: Bugs returned
    assert 456 in bugs_dict
    assert bugs_dict[456][0]["title"] == "Forced Fresh Bug"

    # Verify: Cache stats show force refresh
    assert cache_stats["total_tests"] == 1
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 1
    assert cache_stats["breakdown"]["force_refresh"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_cached_or_refresh_never_synced_fetches_from_api(monkeypatch):
    """Verify tests with NULL bugs_synced_at are always refreshed."""
    import asyncio

    from testio_mcp.config import settings

    monkeypatch.setattr(settings, "BUG_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "BUG_CACHE_BYPASS", False)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()

    # Mock test status: status=locked, bugs_synced_at=NULL (never synced)
    test_result = MagicMock()
    test_result.all.return_value = [
        (456, "locked", None),  # NULL bugs_synced_at
    ]

    # Mock API response
    mock_client.get.return_value = {
        "bugs": [
            {"id": 1, "title": "First Sync Bug", "test": {"id": 456}},
        ]
    }

    # Mock bug query result
    bug = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="First Sync Bug",
        raw_data=json.dumps({"id": 1, "title": "First Sync Bug"}),
        synced_at=datetime.now(UTC),
    )
    bugs_result = MagicMock()
    bugs_result.all.return_value = [bug]

    # Mock cache with required methods for decoupled API/DB pattern
    mock_cache = MagicMock()
    mock_cache.get_refresh_lock = MagicMock(return_value=asyncio.Lock())
    mock_cache._write_semaphore = asyncio.Semaphore(5)

    # Create isolated session mock for cache.async_session_maker()
    mock_isolated_session = AsyncMock(spec=AsyncSession)
    mock_isolated_session.exec = AsyncMock(return_value=bugs_result)  # For final fresh session read
    mock_isolated_session.commit = AsyncMock()
    mock_isolated_session.add = MagicMock()
    mock_isolated_session.rollback = AsyncMock()  # For Issue #5 rollback fix

    # Mock async context manager for session maker
    @asynccontextmanager
    async def mock_session_maker():
        yield mock_isolated_session

    mock_cache.async_session_maker = mock_session_maker

    # Return different results for each exec call on main session
    # Flow: test status query only (final read now uses fresh session after refresh)
    mock_session.exec.side_effect = [
        test_result,  # Test status query
    ]

    repo = BugRepository(
        session=mock_session, client=mock_client, customer_id=123, cache=mock_cache
    )

    # Execute
    bugs_dict, cache_stats = await repo.get_bugs_cached_or_refresh(test_ids=[456])

    # Verify: API called (never synced)
    mock_client.get.assert_called_once()

    # Verify: Bugs returned
    assert 456 in bugs_dict
    assert bugs_dict[456][0]["title"] == "First Sync Bug"

    # Verify: Cache stats show never synced
    assert cache_stats["total_tests"] == 1
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 1
    assert cache_stats["breakdown"]["never_synced"] == 1


# STORY-032C AC5: Relationship Loading Test


@pytest.mark.unit
@pytest.mark.asyncio
async def test_relationship_loading_test_bugs():
    """Verify test.bugs ORM relationship is properly configured and accessible.

    This test validates AC5 from STORY-032C: Relationship queries work (test.bugs).
    While this is a unit test with mocks, it verifies the relationship is defined
    and can be accessed without errors.
    """
    from testio_mcp.models.orm.test import Test

    # Create a mock Test object with bugs relationship
    # In real usage, this would be loaded via session.get(Test, test_id)
    mock_test = Test(
        id=456,
        customer_id=123,
        product_id=789,
        title="Test with bugs",
        status="running",
    )

    # Create Bug objects that would be related via test.bugs
    bug1 = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Bug 1",
        raw_data=json.dumps({"id": 1, "title": "Bug 1"}),
        synced_at=datetime.now(UTC),
    )
    bug2 = Bug(
        id=2,
        customer_id=123,
        test_id=456,
        title="Bug 2",
        raw_data=json.dumps({"id": 2, "title": "Bug 2"}),
        synced_at=datetime.now(UTC),
    )

    # Simulate relationship loading (in real ORM, this would be lazy-loaded)
    # The relationship is defined in models/orm/test.py as:
    # bugs: list["Bug"] = Relationship(back_populates="test")
    mock_test.bugs = [bug1, bug2]

    # Verify relationship access works
    assert hasattr(mock_test, "bugs"), "Test model should have 'bugs' relationship"
    assert len(mock_test.bugs) == 2, "Should have 2 bugs in relationship"
    assert mock_test.bugs[0].title == "Bug 1"
    assert mock_test.bugs[1].title == "Bug 2"
    assert all(bug.test_id == mock_test.id for bug in mock_test.bugs), (
        "All bugs should reference the same test_id"
    )

    # Verify reverse relationship (bug.test) is accessible
    # In real ORM: bug.test would lazy-load the Test object
    assert hasattr(bug1, "test"), "Bug model should have 'test' back-reference"


# STORY-085: get_bug_by_id Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_by_id_returns_bug_with_related_entities():
    """Verify get_bug_by_id returns bug with joined user, test, and feature."""
    # Setup: Mock AsyncSession with bug and related entities
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()
    mock_result = MagicMock()

    # Create mock entities
    from testio_mcp.models.orm import Test, TestFeature, User

    mock_bug = Bug(
        id=12345,
        customer_id=123,
        test_id=109363,
        title="Login button not clickable",
        severity="critical",
        status="rejected",
        known=False,
        actual_result="Button does not respond to clicks",
        expected_result="Button should navigate to dashboard",
        steps="1. Navigate to login page\n2. Click login button",
        rejection_reason="test_is_invalid",
        reported_at=datetime(2025, 11, 28, 10, 30, 0, tzinfo=UTC),
        raw_data=json.dumps({"id": 12345}),
        synced_at=datetime.now(UTC),
        reported_by_user_id=456,
        test_feature_id=789,
    )

    mock_user = User(
        id=456,
        customer_id=123,
        username="john_doe",
        user_type="tester",
        first_seen=datetime(2024, 1, 1, tzinfo=UTC),
        last_seen=datetime(2024, 6, 15, tzinfo=UTC),
    )

    mock_test = Test(
        id=109363,
        customer_id=123,
        product_id=598,
        data={"title": "Homepage Navigation Test"},
        status="archived",
        synced_at=datetime.now(UTC),
    )

    mock_feature = TestFeature(
        id=789,
        customer_id=123,
        product_id=598,
        title="User Login",
    )

    # Mock query result - returns tuple of (Bug, User, Test, TestFeature)
    mock_result.first.return_value = (mock_bug, mock_user, mock_test, mock_feature)
    mock_session.exec.return_value = mock_result

    # Create repository
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Call get_bug_by_id
    result = await repo.get_bug_by_id(12345)

    # Assert
    assert result is not None
    assert result["id"] == 12345
    assert result["title"] == "Login button not clickable"
    assert result["severity"] == "critical"
    assert result["status"] == "rejected"
    assert result["known"] is False
    assert result["actual_result"] == "Button does not respond to clicks"
    assert result["expected_result"] == "Button should navigate to dashboard"
    assert result["steps"] == "1. Navigate to login page\n2. Click login button"
    assert result["rejection_reason"] == "test_is_invalid"
    assert result["reported_at"] == "2025-11-28T10:30:00+00:00"

    # Verify related entities (AC2)
    assert result["reported_by_user"] == {"id": 456, "username": "john_doe"}
    assert result["test"] == {"id": 109363, "title": "Homepage Navigation Test"}
    assert result["feature"] == {"id": 789, "title": "User Login"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_by_id_returns_none_when_not_found():
    """Verify get_bug_by_id returns None when bug not found."""
    # Setup: Mock AsyncSession with no results
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()
    mock_result = MagicMock()

    mock_result.first.return_value = None  # Bug not found
    mock_session.exec.return_value = mock_result

    # Create repository
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Call get_bug_by_id
    result = await repo.get_bug_by_id(99999)

    # Assert
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_by_id_with_null_user_and_feature():
    """Verify get_bug_by_id handles NULL user and feature (LEFT JOIN)."""
    # Setup: Mock AsyncSession with bug but no user/feature
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()
    mock_result = MagicMock()

    # Create mock entities
    from testio_mcp.models.orm import Test

    mock_bug = Bug(
        id=12345,
        customer_id=123,
        test_id=109363,
        title="Login button not clickable",
        severity="critical",
        status="rejected",
        known=False,
        actual_result="Button does not respond to clicks",
        expected_result="Button should navigate to dashboard",
        steps="1. Navigate to login page\n2. Click login button",
        rejection_reason="test_is_invalid",
        reported_at=datetime(2025, 11, 28, 10, 30, 0, tzinfo=UTC),
        raw_data=json.dumps({"id": 12345}),
        synced_at=datetime.now(UTC),
        reported_by_user_id=None,  # No user
        test_feature_id=None,  # No feature
    )

    mock_test = Test(
        id=109363,
        customer_id=123,
        product_id=598,
        data={"title": "Homepage Navigation Test"},
        status="archived",
        synced_at=datetime.now(UTC),
    )

    # Mock query result - User and TestFeature are None (LEFT JOIN)
    mock_result.first.return_value = (mock_bug, None, mock_test, None)
    mock_session.exec.return_value = mock_result

    # Create repository
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Call get_bug_by_id
    result = await repo.get_bug_by_id(12345)

    # Assert
    assert result is not None
    assert result["id"] == 12345
    assert result["reported_by_user"] is None
    assert result["test"] == {"id": 109363, "title": "Homepage Navigation Test"}
    assert result["feature"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_by_id_with_null_detail_fields():
    """Verify get_bug_by_id handles NULL detail fields gracefully."""
    # Setup: Mock AsyncSession with bug missing detail fields
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock()
    mock_result = MagicMock()

    # Create mock entities
    from testio_mcp.models.orm import Test, User

    mock_bug = Bug(
        id=12345,
        customer_id=123,
        test_id=109363,
        title="Login button not clickable",
        severity=None,  # NULL severity
        status=None,  # NULL status
        known=False,
        actual_result=None,  # NULL
        expected_result=None,  # NULL
        steps=None,  # NULL
        rejection_reason=None,  # NULL
        reported_at=None,  # NULL
        raw_data=json.dumps({"id": 12345}),
        synced_at=datetime.now(UTC),
        reported_by_user_id=456,
        test_feature_id=None,
    )

    mock_user = User(
        id=456,
        customer_id=123,
        username="john_doe",
        user_type="tester",
        first_seen=datetime(2024, 1, 1, tzinfo=UTC),
        last_seen=datetime(2024, 6, 15, tzinfo=UTC),
    )

    mock_test = Test(
        id=109363,
        customer_id=123,
        product_id=598,
        data={"title": "Homepage Navigation Test"},
        status="archived",
        synced_at=datetime.now(UTC),
    )

    # Mock query result
    mock_result.first.return_value = (mock_bug, mock_user, mock_test, None)
    mock_session.exec.return_value = mock_result

    # Create repository
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Call get_bug_by_id
    result = await repo.get_bug_by_id(12345)

    # Assert - NULL fields should be None
    assert result is not None
    assert result["id"] == 12345
    assert result["severity"] is None
    assert result["status"] is None
    assert result["actual_result"] is None
    assert result["expected_result"] is None
    assert result["steps"] is None
    assert result["rejection_reason"] is None
    assert result["reported_at"] is None
    assert result["reported_by_user"] == {"id": 456, "username": "john_doe"}
    assert result["test"] == {"id": 109363, "title": "Homepage Navigation Test"}
