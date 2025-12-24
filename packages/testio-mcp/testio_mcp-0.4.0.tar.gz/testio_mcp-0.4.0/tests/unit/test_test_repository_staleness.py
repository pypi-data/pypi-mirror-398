"""
Unit tests for TestRepository.get_tests_cached_or_refresh() staleness method.

Tests the intelligent caching logic that decides when to use cached test data
vs. refreshing from API based on test mutability and staleness.

Pattern: Mock TestIOClient and AsyncSession to avoid API calls and DB access.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.repositories.test_repository import TestRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_empty_list() -> None:
    """Test with empty test_ids list returns empty dict and zero stats."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)  # Use MagicMock for session
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    tests_dict, cache_stats = await repo.get_tests_cached_or_refresh([])

    # Assert
    assert tests_dict == {}
    assert cache_stats == {
        "total_tests": 0,
        "cache_hits": 0,
        "api_calls": 0,
        "cache_hit_rate": 0.0,
        "breakdown": {},
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_fresh_tests() -> None:
    """Test that fresh mutable tests are served from cache (no API calls)."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)  # Use MagicMock instead of AsyncMock for session
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    test_ids = [101, 102]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=30)  # 30 minutes ago (fresh)

    # Mock test metadata query (status + synced_at)
    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = [
        (101, "running", fresh_timestamp),  # Mutable, fresh
        (102, "locked", fresh_timestamp),  # Mutable, fresh
    ]

    # Mock test data query (returns JSON for each test)
    test_data_101 = {"id": 101, "status": "running", "title": "Test 101"}
    test_data_102 = {"id": 102, "status": "locked", "title": "Test 102"}

    mock_data_result_101 = MagicMock()
    mock_data_result_101.first.return_value = json.dumps(test_data_101)
    mock_data_result_102 = MagicMock()
    mock_data_result_102.first.return_value = json.dumps(test_data_102)

    # Configure session.exec to return different results based on query
    mock_session.exec.side_effect = [
        mock_metadata_result,  # First call: metadata query
        mock_data_result_101,  # Second call: test 101 data
        mock_data_result_102,  # Third call: test 102 data
    ]

    # Act
    tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(test_ids)

    # Assert
    assert len(tests_dict) == 2
    assert tests_dict[101] == test_data_101
    assert tests_dict[102] == test_data_102

    # Verify cache stats (100% cache hit, no API calls)
    assert cache_stats["total_tests"] == 2
    assert cache_stats["cache_hits"] == 2
    assert cache_stats["api_calls"] == 0
    assert cache_stats["cache_hit_rate"] == 100.0
    assert cache_stats["breakdown"]["mutable_fresh"] == 2

    # Verify no API calls made
    mock_client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_stale_tests() -> None:
    """Test that stale mutable tests trigger API refresh."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    test_ids = [201, 202]
    now = datetime.now(UTC)
    stale_timestamp = now - timedelta(hours=2)  # 2 hours ago (stale, assuming 1h TTL)

    # Mock test metadata query
    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = [
        (201, "running", stale_timestamp),  # Mutable, stale
        (202, "locked", stale_timestamp),  # Mutable, stale
    ]

    # Mock API responses for refresh
    test_data_201 = {"id": 201, "status": "running", "title": "Test 201 refreshed"}
    test_data_202 = {"id": 202, "status": "locked", "title": "Test 202 refreshed"}

    mock_client.get.side_effect = [
        {"exploratory_test": {**test_data_201, "product": {"id": 999}}},
        {"exploratory_test": {**test_data_202, "product": {"id": 999}}},
    ]

    # Mock test data query (after refresh)
    mock_data_result_201 = MagicMock()
    mock_data_result_201.first.return_value = json.dumps(test_data_201)
    mock_data_result_202 = MagicMock()
    mock_data_result_202.first.return_value = json.dumps(test_data_202)

    # Mock bulk update query (for synced_at timestamps)
    mock_update_result = MagicMock()
    mock_update_result.all.return_value = []

    # Configure session.exec
    mock_session.exec.side_effect = [
        mock_metadata_result,  # Metadata query
        mock_update_result,  # Bulk update synced_at
        mock_data_result_201,  # Test 201 data
        mock_data_result_202,  # Test 202 data
    ]

    # Mock session.no_autoflush context manager
    mock_session.no_autoflush = MagicMock()
    mock_session.no_autoflush.__enter__ = MagicMock()
    mock_session.no_autoflush.__exit__ = MagicMock()

    # Mock test_exists to return True (existing tests)
    with patch.object(repo, "test_exists", new_callable=AsyncMock) as mock_test_exists:
        mock_test_exists.return_value = True

        # Mock update_test to avoid DB write logic
        with patch.object(repo, "update_test", new_callable=AsyncMock):
            # Act
            tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(test_ids)

    # Assert
    assert len(tests_dict) == 2
    assert tests_dict[201] == test_data_201
    assert tests_dict[202] == test_data_202

    # Verify cache stats (0% cache hit, 2 API calls)
    assert cache_stats["total_tests"] == 2
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 2
    assert cache_stats["cache_hit_rate"] == 0.0
    assert cache_stats["breakdown"]["mutable_stale"] == 2

    # Verify API calls made
    assert mock_client.get.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_immutable_always_cached() -> None:
    """Test that immutable tests (archived/cancelled) always use cache."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    test_ids = [301, 302]
    now = datetime.now(UTC)
    very_old_timestamp = now - timedelta(days=30)  # 30 days ago (very stale)

    # Mock test metadata query
    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = [
        (301, "archived", very_old_timestamp),  # Immutable, very old but still cached
        (302, "cancelled", very_old_timestamp),  # Immutable, very old but still cached
    ]

    # Mock test data query
    test_data_301 = {"id": 301, "status": "archived", "title": "Test 301"}
    test_data_302 = {"id": 302, "status": "cancelled", "title": "Test 302"}

    mock_data_result_301 = MagicMock()
    mock_data_result_301.first.return_value = json.dumps(test_data_301)
    mock_data_result_302 = MagicMock()
    mock_data_result_302.first.return_value = json.dumps(test_data_302)

    mock_session.exec.side_effect = [
        mock_metadata_result,
        mock_data_result_301,
        mock_data_result_302,
    ]

    # Act
    tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(test_ids)

    # Assert
    assert len(tests_dict) == 2
    assert tests_dict[301]["status"] == "archived"
    assert tests_dict[302]["status"] == "cancelled"

    # Verify cache stats (100% cache hit, no API calls)
    assert cache_stats["total_tests"] == 2
    assert cache_stats["cache_hits"] == 2
    assert cache_stats["api_calls"] == 0
    assert cache_stats["cache_hit_rate"] == 100.0
    assert cache_stats["breakdown"]["immutable_cached"] == 2

    # Verify no API calls made (even though synced_at is very old)
    mock_client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_force_refresh_bypasses_cache() -> None:
    """Test that force_refresh=True bypasses cache for all tests."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    test_ids = [401]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=5)  # Very fresh

    # Mock test metadata query
    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = [
        (401, "running", fresh_timestamp),  # Mutable, fresh
    ]

    # Mock API response
    test_data_401 = {"id": 401, "status": "running", "title": "Test 401 force refreshed"}
    mock_client.get.return_value = {"exploratory_test": {**test_data_401, "product": {"id": 999}}}

    # Mock test data query
    mock_data_result_401 = MagicMock()
    mock_data_result_401.first.return_value = json.dumps(test_data_401)

    # Mock bulk update query
    mock_update_result = MagicMock()
    mock_update_result.all.return_value = []

    mock_session.exec.side_effect = [
        mock_metadata_result,
        mock_update_result,
        mock_data_result_401,
    ]

    # Mock session.no_autoflush
    mock_session.no_autoflush = MagicMock()
    mock_session.no_autoflush.__enter__ = MagicMock()
    mock_session.no_autoflush.__exit__ = MagicMock()

    with patch.object(repo, "test_exists", new_callable=AsyncMock) as mock_test_exists:
        mock_test_exists.return_value = True

        with patch.object(repo, "update_test", new_callable=AsyncMock):
            # Act
            tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(
                test_ids, force_refresh=True
            )

    # Assert
    assert len(tests_dict) == 1
    assert tests_dict[401] == test_data_401

    # Verify cache stats (0% cache hit due to force refresh)
    assert cache_stats["total_tests"] == 1
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 1
    assert cache_stats["cache_hit_rate"] == 0.0
    assert cache_stats["breakdown"]["force_refresh"] == 1

    # Verify API call made even though test was fresh
    mock_client.get.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_batch_processing() -> None:
    """Test efficient batch processing of multiple tests."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # 20 tests (> BATCH_SIZE of 15)
    test_ids = list(range(501, 521))
    now = datetime.now(UTC)
    stale_timestamp = now - timedelta(hours=2)

    # All tests are stale and need refresh
    metadata_rows = [(test_id, "running", stale_timestamp) for test_id in test_ids]

    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = metadata_rows

    # Mock API responses
    api_responses = [
        {"exploratory_test": {"id": test_id, "status": "running", "product": {"id": 999}}}
        for test_id in test_ids
    ]
    mock_client.get.side_effect = api_responses

    # Mock test data queries (after refresh)
    data_results = []
    for test_id in test_ids:
        mock_data_result = MagicMock()
        mock_data_result.first.return_value = json.dumps({"id": test_id, "status": "running"})
        data_results.append(mock_data_result)

    # Mock bulk update query
    mock_update_result = MagicMock()
    mock_update_result.all.return_value = []

    mock_session.exec.side_effect = [mock_metadata_result, mock_update_result] + data_results

    # Mock session.no_autoflush
    mock_session.no_autoflush = MagicMock()
    mock_session.no_autoflush.__enter__ = MagicMock()
    mock_session.no_autoflush.__exit__ = MagicMock()

    with patch.object(repo, "test_exists", new_callable=AsyncMock) as mock_test_exists:
        mock_test_exists.return_value = True

        with patch.object(repo, "update_test", new_callable=AsyncMock):
            # Act
            tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(test_ids)

    # Assert
    assert len(tests_dict) == 20

    # Verify cache stats
    assert cache_stats["total_tests"] == 20
    assert cache_stats["cache_hits"] == 0
    assert cache_stats["api_calls"] == 20
    assert cache_stats["cache_hit_rate"] == 0.0

    # Verify all tests refreshed (batch processing)
    assert mock_client.get.call_count == 20


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tests_cached_or_refresh_mixed_staleness() -> None:
    """Test mixed scenarios: some fresh, some stale, some immutable."""
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_client = AsyncMock()
    customer_id = 123
    repo = TestRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    test_ids = [601, 602, 603, 604]
    now = datetime.now(UTC)
    fresh_timestamp = now - timedelta(minutes=30)
    stale_timestamp = now - timedelta(hours=2)
    very_old_timestamp = now - timedelta(days=30)

    # Mock test metadata query
    mock_metadata_result = MagicMock()
    mock_metadata_result.all.return_value = [
        (601, "running", fresh_timestamp),  # Mutable, fresh → cache
        (602, "locked", stale_timestamp),  # Mutable, stale → API
        (603, "archived", very_old_timestamp),  # Immutable → cache
        (604, "running", stale_timestamp),  # Mutable, stale → API
    ]

    # Mock API responses (only for stale tests)
    test_data_602 = {"id": 602, "status": "locked", "title": "Test 602 refreshed"}
    test_data_604 = {"id": 604, "status": "running", "title": "Test 604 refreshed"}
    mock_client.get.side_effect = [
        {"exploratory_test": {**test_data_602, "product": {"id": 999}}},
        {"exploratory_test": {**test_data_604, "product": {"id": 999}}},
    ]

    # Mock test data queries
    test_data_601 = {"id": 601, "status": "running", "title": "Test 601"}
    test_data_603 = {"id": 603, "status": "archived", "title": "Test 603"}

    mock_data_results = [
        MagicMock(),  # 601
        MagicMock(),  # 602
        MagicMock(),  # 603
        MagicMock(),  # 604
    ]
    mock_data_results[0].first.return_value = json.dumps(test_data_601)
    mock_data_results[1].first.return_value = json.dumps(test_data_602)
    mock_data_results[2].first.return_value = json.dumps(test_data_603)
    mock_data_results[3].first.return_value = json.dumps(test_data_604)

    # Mock bulk update query
    mock_update_result = MagicMock()
    mock_update_result.all.return_value = []

    mock_session.exec.side_effect = [
        mock_metadata_result,
        mock_update_result,
    ] + mock_data_results

    # Mock session.no_autoflush
    mock_session.no_autoflush = MagicMock()
    mock_session.no_autoflush.__enter__ = MagicMock()
    mock_session.no_autoflush.__exit__ = MagicMock()

    with patch.object(repo, "test_exists", new_callable=AsyncMock) as mock_test_exists:
        mock_test_exists.return_value = True

        with patch.object(repo, "update_test", new_callable=AsyncMock):
            # Act
            tests_dict, cache_stats = await repo.get_tests_cached_or_refresh(test_ids)

    # Assert
    assert len(tests_dict) == 4

    # Verify cache stats (50% cache hit)
    assert cache_stats["total_tests"] == 4
    assert cache_stats["cache_hits"] == 2  # 601 (fresh) + 603 (immutable)
    assert cache_stats["api_calls"] == 2  # 602 + 604 (stale)
    assert cache_stats["cache_hit_rate"] == 50.0
    assert cache_stats["breakdown"]["mutable_fresh"] == 1  # 601
    assert cache_stats["breakdown"]["immutable_cached"] == 1  # 603
    assert cache_stats["breakdown"]["mutable_stale"] == 2  # 602 + 604

    # Verify API calls only for stale tests
    assert mock_client.get.call_count == 2
