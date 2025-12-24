"""
Unit tests for PersistentCache (SQLite-based cache).

CRITICAL: All tests MUST use in-memory SQLite (db_path=":memory:")
to prevent test pollution and ensure fast test execution.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.database import PersistentCache


@pytest.fixture
async def mock_client() -> AsyncMock:
    """Create mock TestIO API client."""
    client = AsyncMock(spec=TestIOClient)
    return client


@pytest.fixture
async def test_cache(mock_client: AsyncMock, tmp_path: Path) -> PersistentCache:
    """Create PersistentCache for testing using a temp file.

    We use a temp file instead of :memory: because PersistentCache uses two connections
    (aiosqlite and SQLAlchemy AsyncEngine) which would point to different DBs if using :memory:.
    """
    db_file = tmp_path / "test.db"
    cache = PersistentCache(
        db_path=str(db_file),
        client=mock_client,
        customer_id=25073,
    )
    await cache.initialize()

    # Create tables manually since initialize() no longer does it (handled by migrations in prod)
    from sqlmodel import SQLModel

    # Import models to register them
    from testio_mcp.models.orm import Bug, Product, SyncEvent, SyncMetadata, Test  # noqa: F401

    async with cache.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield cache
    await cache.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_initialization(test_cache: PersistentCache) -> None:
    """Test database schema creation and initialization.

    STORY-034B: Updated to check engine instead of db (aiosqlite.Connection).
    """
    # Verify AsyncEngine is established (STORY-034B)
    assert test_cache.engine is not None

    # Verify tables exist by querying sqlite_master using ORM
    from sqlalchemy import text

    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in result.fetchall()]

    assert "tests" in tables
    assert "products" in tables
    assert "sync_metadata" in tables


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_stats_empty_db(test_cache: PersistentCache) -> None:
    """Test database statistics methods with empty database."""
    # Test counts
    assert await test_cache.count_tests() == 0
    assert await test_cache.count_products() == 0

    # Test date queries
    assert await test_cache.get_oldest_test_date() is None
    assert await test_cache.get_newest_test_date() is None

    # Test synced products info
    products_info = await test_cache.get_synced_products_info()
    assert products_info == []

    # Test problematic tests
    problematic = await test_cache.get_problematic_tests()
    assert problematic == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_customer_id_isolation(test_cache: PersistentCache) -> None:
    """Test that customer_id is properly set and used for data isolation."""
    assert test_cache.customer_id == 25073


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.unit
async def test_wal_mode_enabled(test_cache: PersistentCache) -> None:
    """Test that WAL mode is requested (file-based DBs use WAL).

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    async with test_cache.engine.connect() as conn:
        result = await conn.execute(text("PRAGMA journal_mode"))
        row = result.fetchone()
        assert row is not None
        # File-based databases use 'wal'
        assert row[0].lower() == "wal"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_key_generation(test_cache: PersistentCache) -> None:
    """Test cache key generation helper method."""
    key = test_cache._make_cache_key("test", 123, "status")
    assert key == "test:123:status"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.unit
async def test_clear_database(test_cache: PersistentCache) -> None:
    """Test database clearing for current customer.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    # Insert test data directly
    async with test_cache.engine.begin() as conn:
        # STORY-054: Removed created_at, added title field
        await conn.execute(
            text(
                """
                INSERT INTO tests (id, customer_id, product_id, data, status, title)
                VALUES (1, 25073, 100, '{}', 'running', 'Test 1')
                """
            )
        )

    # Verify data exists
    assert await test_cache.count_tests() == 1

    # Clear database
    await test_cache.clear_database()

    # Verify data is gone
    assert await test_cache.count_tests() == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_product_tests(test_cache: PersistentCache) -> None:
    """Test deleting tests for specific product.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    # Insert test data for two products
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO tests (id, customer_id, product_id, data, status)
                VALUES
                    (1, 25073, 100, '{}', 'running'),
                    (2, 25073, 200, '{}', 'running')
                """
            )
        )

    # Verify both tests exist
    assert await test_cache.count_tests() == 2

    # Delete product 100 tests
    await test_cache.delete_product_tests(100)

    # Verify only product 200 test remains
    assert await test_cache.count_tests() == 1

    # Verify it's the correct test
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT product_id FROM tests WHERE customer_id = :customer_id"),
            {"customer_id": 25073},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 200


# ============================================================================
# Incremental Sync Algorithm Tests (STORY-021, Task 2)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.unit
async def test_insert_test(test_cache: PersistentCache) -> None:
    """Test inserting a single test into database via repository.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    test_data = {
        "id": 12345,
        "title": "Test Payment Flow",
        "status": "running",
        "start_at": "2025-01-01T01:00:00Z",
        "end_at": None,
    }

    # Use repository method (repository pattern)
    await test_cache._repo.insert_test(test_data, product_id=100)
    await test_cache._repo.commit()  # STORY-032B: Explicit commit required

    # Verify test was inserted
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, status, product_id FROM tests WHERE id = :id"), {"id": 12345}
        )
        row = result.fetchone()

    assert row is not None
    assert row[0] == 12345
    assert row[1] == "running"
    assert row[2] == 100


# ============================================================================
# Active Test Refresh Tests (STORY-021, Task 4 - AC4)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_test_modifies_existing_record(test_cache: PersistentCache) -> None:
    """Test update_test updates data and status fields.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    # Insert initial test
    await test_cache._repo.insert_test(
        {
            "id": 123,
            "title": "Old Title",
            "status": "running",
            "start_at": "2025-01-01T00:00:00Z",
        },
        product_id=100,
    )
    await test_cache._repo.commit()  # STORY-032B: Explicit commit required

    # Update test with new data
    updated_data = {
        "id": 123,
        "title": "New Title",
        "status": "completed",
        "start_at": "2025-01-01T01:00:00Z",
        "end_at": "2025-01-01T02:00:00Z",
    }
    await test_cache._repo.update_test(updated_data, product_id=100)
    await test_cache._repo.commit()  # STORY-032B: Explicit commit required

    # Verify update
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT data, status FROM tests WHERE id = :id AND customer_id = :customer_id"),
            {"id": 123, "customer_id": 25073},
        )
        row = result.fetchone()

    assert row is not None
    import json

    data = json.loads(row[0])
    assert data["title"] == "New Title"
    assert row[1] == "completed"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.unit
async def test_refresh_active_tests_empty_database(test_cache: PersistentCache) -> None:
    """Test refresh_active_tests with no active tests still updates last_synced.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from sqlalchemy import text

    # Insert product without mutable tests
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO products (id, customer_id, title, data, last_synced)
                VALUES (
                    100, 25073, 'Test Product',
                    '{"id": 100, "name": "Test Product"}',
                    '2024-01-01 00:00:00'
                )
                """
            )
        )

    result = await test_cache.refresh_active_tests(product_id=100)

    assert result["tests_checked"] == 0
    assert result["tests_updated"] == 0
    assert result["errors"] == []

    # Verify last_synced was updated despite no mutable tests (staleness fix)
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT last_synced FROM products WHERE id = 100 AND customer_id = 25073")
        )
        row = result.fetchone()
    assert row is not None
    assert row[0] != "2024-01-01 00:00:00"  # Timestamp should be updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_active_tests_updates_from_api(
    test_cache: PersistentCache, mock_client: AsyncMock
) -> None:
    """Test refresh_active_tests fetches and updates tests from API.

    STORY-034B: Updated to use ORM models instead of raw SQL for data insertion.
    """
    import json
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    from testio_mcp.models.orm.test import Test

    # Insert 2 active tests using ORM models (STORY-034B fix)
    recent = datetime.now(UTC) - timedelta(days=2)
    async with test_cache.async_session_maker() as session:
        session.add(
            Test(
                id=1,
                customer_id=25073,
                product_id=100,
                data=json.dumps({"id": 1}),
                status="running",
                created_at=recent,
            )
        )
        session.add(
            Test(
                id=2,
                customer_id=25073,
                product_id=100,
                data=json.dumps({"id": 2}),
                status="running",
                created_at=recent,
            )
        )
        await session.commit()

    # Mock API responses (updated status)
    # Note: refresh_test() expects {"exploratory_test": {...}} wrapper (correct API format)
    mock_client.get.side_effect = [
        {
            "exploratory_test": {
                "id": 1,
                "title": "Test 1",
                "status": "completed",
                "end_at": "2025-01-07T00:00:00Z",
                "product": {"id": 100},
            }
        },
        {
            "exploratory_test": {
                "id": 2,
                "title": "Test 2",
                "status": "completed",
                "end_at": "2025-01-07T01:00:00Z",
                "product": {"id": 100},
            }
        },
    ]

    # Run refresh
    result = await test_cache.refresh_active_tests(product_id=100)

    # Verify result
    assert result["tests_checked"] == 2
    assert result["tests_updated"] == 2  # Both tests successfully refreshed
    assert result["status_changed"] == 2  # Both statuses changed (running → completed)
    assert result["errors"] == []

    # Verify API calls
    assert mock_client.get.call_count == 2

    # Verify database updates
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, status FROM tests WHERE customer_id = :customer_id ORDER BY id"),
            {"customer_id": 25073},
        )
        rows = result.fetchall()

    assert len(rows) == 2
    assert rows[0][1] == "completed"  # Test 1 updated
    assert rows[1][1] == "completed"  # Test 2 updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_active_tests_handles_api_errors(
    test_cache: PersistentCache, mock_client: AsyncMock
) -> None:
    """Test refresh_active_tests handles partial API failures gracefully.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    # Insert 2 active tests
    recent = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
                INSERT INTO tests (id, customer_id, product_id, data, status, end_at)
                VALUES
                    (1, 25073, 100, '{{"id": 1}}', 'running', '{recent}'),
                    (2, 25073, 100, '{{"id": 2}}', 'running', '{recent}')
                """
            )
        )

    # Mock API: test 1 succeeds, test 2 fails
    # Note: refresh_test() expects {"exploratory_test": {...}} wrapper
    # Use a function to return responses based on endpoint (test ID)
    def mock_get(endpoint, **kwargs):
        test_id = int(endpoint.split("/")[-1])
        if test_id == 1:
            return {
                "exploratory_test": {
                    "id": 1,
                    "title": "Test 1",
                    "status": "completed",  # Status changed from 'running' to 'completed'
                    "end_at": "2025-01-07T00:00:00Z",
                    "product": {"id": 100},
                }
            }
        elif test_id == 2:
            raise Exception("API Error: 500 Internal Server Error")
        raise ValueError(f"Unexpected endpoint: {endpoint}")

    mock_client.get.side_effect = mock_get

    # Run refresh
    result = await test_cache.refresh_active_tests(product_id=100)

    # Verify partial success
    assert result["tests_checked"] == 2
    assert result["tests_updated"] == 1  # One test successfully refreshed
    assert result["status_changed"] == 1  # One test status changed
    assert len(result["errors"]) == 1
    # Error could be for either test (asyncio.gather doesn't guarantee order)
    assert result["errors"][0]["test_id"] in (1, 2)
    assert "API Error: 500" in result["errors"][0]["error"]


# ============================================================================
# Query Interface Tests (STORY-021, Task 3 - AC3)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_basic_no_filters(test_cache: PersistentCache) -> None:
    """Test basic query with no filters (pagination and ordering only)."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    # Insert 3 tests with different created_at timestamps
    now = datetime.now(UTC)
    day3 = (now - timedelta(days=3)).isoformat()
    day2 = (now - timedelta(days=2)).isoformat()
    day1 = (now - timedelta(days=1)).isoformat()
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, end_at)
        VALUES
            (1, 25073, 100, '{{"id": 1}}', 'running', '{day3}'),
            (2, 25073, 100, '{{"id": 2}}', 'running', '{day2}'),
            (3, 25073, 100, '{{"id": 3}}', 'running', '{day1}')
        """
            )
        )

    # Query page 1, per_page=2 (should return 2 tests, newest first)
    results = await test_cache.query_tests(product_id=100, page=1, per_page=2, date_field="end_at")

    assert len(results) == 2
    assert results[0]["id"] == 3  # Newest
    assert results[1]["id"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_status_filter_single(test_cache: PersistentCache) -> None:
    """Test query with single status filter."""
    from sqlalchemy import text

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
        INSERT INTO tests (id, customer_id, product_id, data, status)
        VALUES
            (1, 25073, 100, '{"id": 1}', 'running'),
            (2, 25073, 100, '{"id": 2}', 'completed'),
            (3, 25073, 100, '{"id": 3}', 'archived')
        """
            )
        )

    # Query with statuses=['running']
    results = await test_cache.query_tests(product_id=100, statuses=["running"])

    assert len(results) == 1
    assert results[0]["id"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_status_filter_multiple(test_cache: PersistentCache) -> None:
    """Test query with multiple status filters."""

    from sqlalchemy import text

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
        INSERT INTO tests (id, customer_id, product_id, data, status)
        VALUES
            (1, 25073, 100, '{"id": 1}', 'running'),
            (2, 25073, 100, '{"id": 2}', 'completed'),
            (3, 25073, 100, '{"id": 3}', 'archived')
        """
            )
        )

    # Query with statuses=['running', 'completed']
    results = await test_cache.query_tests(product_id=100, statuses=["running", "completed"])

    assert len(results) == 2
    assert {r["id"] for r in results} == {1, 2}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_date_range_start_only(test_cache: PersistentCache) -> None:
    """Test query with start_date filter only."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=5)

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, start_at)
        VALUES
            (1, 25073, 100, '{{"id": 1, "start_at": "{(now - timedelta(days=10)).isoformat()}"}}',
             'running',  '{(now - timedelta(days=10)).isoformat()}'),
            (2, 25073, 100, '{{"id": 2, "start_at": "{(now - timedelta(days=2)).isoformat()}"}}',
             'running',  '{(now - timedelta(days=2)).isoformat()}')
        """
            )
        )

    # Query with start_date=cutoff (only test 2 should match)
    results = await test_cache.query_tests(product_id=100, start_date=cutoff, date_field="start_at")

    assert len(results) == 1
    assert results[0]["id"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_date_range_end_only(test_cache: PersistentCache) -> None:
    """Test query with end_date filter only."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=5)

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, end_at)
        VALUES
            (1, 25073, 100, '{{"id": 1, "end_at": "{(now - timedelta(days=10)).isoformat()}"}}',
             'completed',  '{(now - timedelta(days=10)).isoformat()}'),
            (2, 25073, 100, '{{"id": 2, "end_at": "{(now - timedelta(days=2)).isoformat()}"}}',
             'completed',  '{(now - timedelta(days=2)).isoformat()}')
        """
            )
        )

    # Query with end_date=cutoff (only test 1 should match)
    results = await test_cache.query_tests(product_id=100, end_date=cutoff, date_field="end_at")

    assert len(results) == 1
    assert results[0]["id"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_date_range_both(test_cache: PersistentCache) -> None:
    """Test query with both start_date and end_date filters."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    now = datetime.now(UTC)
    start_cutoff = now - timedelta(days=10)
    end_cutoff = now - timedelta(days=3)

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, start_at)
        VALUES
            (1, 25073, 100, '{{"id": 1, "start_at": "{(now - timedelta(days=15)).isoformat()}"}}',
             'running',  '{(now - timedelta(days=15)).isoformat()}'),
            (2, 25073, 100, '{{"id": 2, "start_at": "{(now - timedelta(days=5)).isoformat()}"}}',
             'running',  '{(now - timedelta(days=5)).isoformat()}'),
            (3, 25073, 100, '{{"id": 3, "start_at": "{(now - timedelta(days=1)).isoformat()}"}}',
             'running',  '{(now - timedelta(days=1)).isoformat()}')
        """
            )
        )

    # Query with date range (only test 2 should match)
    results = await test_cache.query_tests(
        product_id=100, start_date=start_cutoff, end_date=end_cutoff, date_field="start_at"
    )

    assert len(results) == 1
    assert results[0]["id"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_date_field_variants(test_cache: PersistentCache) -> None:
    """Test query with different date fields (start_at, end_at, created_at)."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=5)

    # Build data separately to keep lines short
    start_at_val = (now - timedelta(days=2)).isoformat()
    end_at_val = (now - timedelta(days=10)).isoformat()
    data = f'{{"id": 1, "start_at": "{start_at_val}", "end_at": "{end_at_val}"}}'

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, start_at, end_at)
        VALUES
            (1, 25073, 100, '{data}', 'completed', '{start_at_val}', '{end_at_val}')
        """
            )
        )

    # Query by start_at (test 1 is after cutoff)
    results_start = await test_cache.query_tests(
        product_id=100, start_date=cutoff, date_field="start_at"
    )
    assert len(results_start) == 1

    # Query by end_at (test 1 is before cutoff)
    results_end = await test_cache.query_tests(
        product_id=100, start_date=cutoff, date_field="end_at"
    )
    assert len(results_end) == 0

    # STORY-054: created_at removed (never from API, always NULL)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_pagination_page_2(test_cache: PersistentCache) -> None:
    """Test pagination with page=2."""
    from sqlalchemy import text

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
        INSERT INTO tests (id, customer_id, product_id, data, status)
        VALUES
            (1, 25073, 100, '{"id": 1}', 'running'),
            (2, 25073, 100, '{"id": 2}', 'running'),
            (3, 25073, 100, '{"id": 3}', 'running'),
            (4, 25073, 100, '{"id": 4}', 'running'),
            (5, 25073, 100, '{"id": 5}', 'running')
        """
            )
        )

    # Page 1 (first 2 tests)
    page1 = await test_cache.query_tests(product_id=100, page=1, per_page=2)
    assert len(page1) == 2

    # Page 2 (next 2 tests)
    page2 = await test_cache.query_tests(product_id=100, page=2, per_page=2)
    assert len(page2) == 2

    # Page 3 (last 1 test)
    page3 = await test_cache.query_tests(product_id=100, page=3, per_page=2)
    assert len(page3) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_combined_filters(test_cache: PersistentCache) -> None:
    """Test query with status + date range + pagination."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=5)

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                f"""
        INSERT INTO tests (id, customer_id, product_id, data, status, start_at)
        VALUES
            (1, 25073, 100, '{{"id": 1, "start_at": "{(now - timedelta(days=2)).isoformat()}"}}',
             'running', '{(now - timedelta(days=2)).isoformat()}'),
            (2, 25073, 100, '{{"id": 2, "start_at": "{(now - timedelta(days=3)).isoformat()}"}}',
             'running', '{(now - timedelta(days=3)).isoformat()}'),
            (3, 25073, 100, '{{"id": 3, "start_at": "{(now - timedelta(days=10)).isoformat()}"}}',
             'running', '{(now - timedelta(days=10)).isoformat()}'),
            (4, 25073, 100, '{{"id": 4, "start_at": "{(now - timedelta(days=1)).isoformat()}"}}',
             'archived', '{(now - timedelta(days=1)).isoformat()}')
        """
            )
        )

    # Query: status=running, start_date >= cutoff, page=1, per_page=5
    results = await test_cache.query_tests(
        product_id=100,
        statuses=["running"],
        start_date=cutoff,
        date_field="start_at",
        page=1,
        per_page=5,
    )

    # Should only return tests 1 and 2 (running + within date range)
    assert len(results) == 2
    assert {r["id"] for r in results} == {1, 2}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_empty_results(test_cache: PersistentCache) -> None:
    """Test query returns empty list when no matches."""
    from sqlalchemy import text

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
        INSERT INTO tests (id, customer_id, product_id, data, status)
        VALUES
            (1, 25073, 100, '{"id": 1}', 'archived')
        """
            )
        )

    # Query with statuses=['running'] (no matches)
    results = await test_cache.query_tests(product_id=100, statuses=["running"])

    assert results == []  # Empty list, not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_customer_isolation(test_cache: PersistentCache) -> None:
    """Test customer_id isolation prevents cross-customer data leakage."""
    from datetime import UTC, datetime

    from sqlalchemy import text

    datetime.now(UTC).isoformat()
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
        INSERT INTO tests (id, customer_id, product_id, data, status)
        VALUES
            (1, 25073, 100, '{"id": 1}', 'running'),
            (2, 99999, 100, '{"id": 2}', 'running')
        """
            )
        )

    # Query for product 100 (should only return customer 25073 test)
    results = await test_cache.query_tests(product_id=100)

    assert len(results) == 1
    assert results[0]["id"] == 1  # Only customer 25073 test


# ============================================================================
# Repository Coverage Gap Tests (REPO-001)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_tests_with_product_filter(
    test_cache: PersistentCache,
) -> None:
    """Test get_problematic_tests with product_id filter.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value)
                """
            ),
            {
                "value": json.dumps(
                    [
                        {"product_id": 100, "test_id": None, "page": 1},
                        {"product_id": 200, "test_id": None, "page": 2},
                    ]
                )
            },
        )

    # Query with product_id filter
    problematic = await test_cache._repo.get_problematic_tests(product_id=100)

    # Should only return product 100
    assert len(problematic) == 1
    assert problematic[0]["product_id"] == 100


# ============================================================================
# Problematic Tests Management (STORY-021e)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_events_empty_database(test_cache: PersistentCache) -> None:
    """Test get_problematic_events returns empty list when no events exist."""
    events = await test_cache.get_problematic_events()
    assert events == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_events_with_mappings(test_cache: PersistentCache) -> None:
    """Test get_problematic_events merges events with mapped test IDs.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Insert a problematic test event
    event_id = "test-event-123"
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value)
                """
            ),
            {
                "value": json.dumps(
                    [
                        {
                            "event_id": event_id,
                            "product_id": 100,
                            "page": 2,
                            "position_range": "25-49",
                            "recovery_attempts": 3,
                            "boundary_before_id": 12345,
                            "boundary_before_end_at": "2025-01-01T00:00:00Z",
                        }
                    ]
                )
            },
        )

        # Insert test ID mappings for this event
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_test_mappings', :value)
                """
            ),
            {"value": json.dumps({event_id: [101, 102, 103]})},
        )

    # Query events
    events = await test_cache.get_problematic_events()

    # Verify event with mappings
    assert len(events) == 1
    assert events[0]["event_id"] == event_id
    assert events[0]["product_id"] == 100
    assert events[0]["page"] == 2
    assert events[0]["mapped_test_ids"] == [101, 102, 103]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_events_product_filter(test_cache: PersistentCache) -> None:
    """Test get_problematic_events filters by product_id.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Insert events for multiple products
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value)
                """
            ),
            {
                "value": json.dumps(
                    [
                        {"event_id": "event-1", "product_id": 100, "page": 1},
                        {"event_id": "event-2", "product_id": 200, "page": 2},
                    ]
                )
            },
        )

    # Query with product filter
    events = await test_cache.get_problematic_events(product_id=100)

    # Should only return product 100 event
    assert len(events) == 1
    assert events[0]["event_id"] == "event-1"
    assert events[0]["product_id"] == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_map_test_ids_to_event_new_mapping(test_cache: PersistentCache) -> None:
    """Test map_test_ids_to_event creates new mapping.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Insert a problematic event
    event_id = "test-event-456"
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value)
                """
            ),
            {"value": json.dumps([{"event_id": event_id, "product_id": 100, "page": 1}])},
        )

    # Map test IDs to event
    await test_cache.map_test_ids_to_event(event_id, [201, 202, 203])

    # Verify mapping was created
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT value FROM sync_metadata WHERE key = 'problematic_test_mappings'")
        )
        row = result.fetchone()
    assert row is not None

    mappings = json.loads(row[0])
    assert event_id in mappings
    assert mappings[event_id] == [201, 202, 203]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_map_test_ids_to_event_append_to_existing(test_cache: PersistentCache) -> None:
    """Test map_test_ids_to_event appends to existing mapping.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Setup: Event + existing mapping
    event_id = "test-event-789"
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value1), ('problematic_test_mappings', :value2)
                """
            ),
            {
                "value1": json.dumps([{"event_id": event_id, "product_id": 100, "page": 1}]),
                "value2": json.dumps({event_id: [301, 302]}),
            },
        )

    # Map additional test IDs
    await test_cache.map_test_ids_to_event(event_id, [303, 304])

    # Verify mapping was appended (deduplicated)
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT value FROM sync_metadata WHERE key = 'problematic_test_mappings'")
        )
        row = result.fetchone()
    assert row is not None
    mappings = json.loads(row[0])

    assert set(mappings[event_id]) == {301, 302, 303, 304}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_map_test_ids_to_event_invalid_event_id(test_cache: PersistentCache) -> None:
    """Test map_test_ids_to_event raises ValueError for invalid event_id."""
    with pytest.raises(ValueError, match="Event ID 'invalid-event' not found"):
        await test_cache.map_test_ids_to_event("invalid-event", [111, 222])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_problematic_tests_success(
    test_cache: PersistentCache, mock_client: AsyncMock
) -> None:
    """Test retry_problematic_tests successfully fetches and removes mapping.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Setup: Event + mapping
    event_id = "retry-event-1"
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value1), ('problematic_test_mappings', :value2)
                """
            ),
            {
                "value1": json.dumps([{"event_id": event_id, "product_id": 100, "page": 1}]),
                "value2": json.dumps({event_id: [401, 402]}),
            },
        )

    # Mock API success for both tests
    mock_client.get.side_effect = [
        {"id": 401, "title": "Test 401", "status": "running"},
        {"id": 402, "title": "Test 402", "status": "completed"},
    ]

    # Retry
    result = await test_cache.retry_problematic_tests(product_id=100)

    # Verify result
    assert result["tests_retried"] == 2
    assert result["tests_succeeded"] == 2
    assert result["tests_failed"] == 0
    assert result["errors"] == []

    # Verify mapping was cleared
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT value FROM sync_metadata WHERE key = 'problematic_test_mappings'")
        )
        row = result.fetchone()
    mappings = json.loads(row[0])
    assert event_id not in mappings  # Mapping removed after success


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_problematic_tests_partial_failure(
    test_cache: PersistentCache, mock_client: AsyncMock
) -> None:
    """Test retry_problematic_tests handles partial failures.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Setup: Event + mapping with 3 test IDs
    event_id = "retry-event-2"
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value1), ('problematic_test_mappings', :value2)
                """
            ),
            {
                "value1": json.dumps([{"event_id": event_id, "product_id": 100, "page": 1}]),
                "value2": json.dumps({event_id: [501, 502, 503]}),
            },
        )

    # Mock API: test 501 succeeds, 502 fails, 503 succeeds
    mock_client.get.side_effect = [
        {"id": 501, "title": "Test 501", "status": "running"},
        Exception("500 Internal Server Error"),  # Test 502 fails
        {"id": 503, "title": "Test 503", "status": "completed"},
    ]

    # Retry
    result = await test_cache.retry_problematic_tests(product_id=100)

    # Verify partial success
    assert result["tests_retried"] == 3
    assert result["tests_succeeded"] == 2
    assert result["tests_failed"] == 1
    assert len(result["errors"]) == 1
    assert "Test 502" in result["errors"][0]  # Error format: "Test {id}: {exception}"

    # Verify only failed test ID kept in mapping
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT value FROM sync_metadata WHERE key = 'problematic_test_mappings'")
        )
        row = result.fetchone()
    mappings = json.loads(row[0])
    assert mappings[event_id] == [502]  # Only failed test ID remains


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_problematic_tests_no_mappings(test_cache: PersistentCache) -> None:
    """Test retry_problematic_tests returns empty result when no mappings exist."""
    result = await test_cache.retry_problematic_tests(product_id=100)

    assert result["tests_retried"] == 0
    assert result["tests_succeeded"] == 0
    assert result["tests_failed"] == 0
    assert result["errors"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clear_problematic_tests_removes_all_records(
    test_cache: PersistentCache,
) -> None:
    """Test clear_problematic_tests removes both events and mappings.

    STORY-034B: Updated to use AsyncEngine instead of aiosqlite.Connection.
    """
    import json

    from sqlalchemy import text

    # Insert events and mappings
    async with test_cache.engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sync_metadata (key, value)
                VALUES ('problematic_tests', :value1), ('problematic_test_mappings', :value2)
                """
            ),
            {
                "value1": json.dumps(
                    [
                        {"event_id": "clear-event-1", "product_id": 100, "page": 1},
                        {"event_id": "clear-event-2", "product_id": 200, "page": 2},
                    ]
                ),
                "value2": json.dumps({"clear-event-1": [601, 602], "clear-event-2": [603]}),
            },
        )

    # Clear
    result = await test_cache.clear_problematic_tests()

    # Verify result
    assert result["position_ranges_cleared"] == 2
    assert result["test_ids_cleared"] == 3  # Total test IDs: 601, 602, 603

    # Verify both records cleared
    async with test_cache.engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT COUNT(*) FROM sync_metadata
                WHERE key IN ('problematic_tests', 'problematic_test_mappings')
                """
            )
        )
        row = result.fetchone()
    assert row is not None
    count = row[0]
    assert count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clear_problematic_tests_empty_database(test_cache: PersistentCache) -> None:
    """Test clear_problematic_tests returns zero counts when nothing to clear."""
    result = await test_cache.clear_problematic_tests()

    assert result["position_ranges_cleared"] == 0
    assert result["test_ids_cleared"] == 0
