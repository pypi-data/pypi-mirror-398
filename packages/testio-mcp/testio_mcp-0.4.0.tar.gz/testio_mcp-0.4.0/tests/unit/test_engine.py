"""Unit tests for database engine module (STORY-030).

These tests verify:
- Async engine creation for SQLite
- Session factory creation
- Async session context manager
- Database initialization

Reference: STORY-030 AC5, AC8

Note: These tests intentionally use session.execute(text(...)) for raw SQL
instead of session.exec(select(...)) because they test the async engine
infrastructure itself, not ORM operations. SQLModel's deprecation warning
is suppressed via pytestmark below.
"""

import pytest

from testio_mcp.database.engine import (
    create_async_engine_for_sqlite,
    create_session_factory,
    get_async_session,
)

# Suppress SQLModel's deprecation warning about session.execute() vs session.exec()
# These tests intentionally use execute() for raw SQL (CREATE TABLE, INSERT, SELECT 1)
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.mark.unit
def test_create_async_engine_for_memory_db():
    """Verify async engine can be created for in-memory database."""
    engine = create_async_engine_for_sqlite(":memory:")

    assert engine is not None
    assert str(engine.url) == "sqlite+aiosqlite:///:memory:"


@pytest.mark.unit
def test_create_async_engine_for_file_db(tmp_path):
    """Verify async engine can be created for file-based database."""
    db_path = tmp_path / "test.db"
    engine = create_async_engine_for_sqlite(db_path)

    assert engine is not None
    # URL should contain absolute path
    assert "sqlite+aiosqlite:///" in str(engine.url)
    assert "test.db" in str(engine.url)


@pytest.mark.unit
def test_create_session_factory():
    """Verify session factory can be created from engine."""
    engine = create_async_engine_for_sqlite(":memory:")
    session_factory = create_session_factory(engine)

    assert session_factory is not None
    # Verify it's an async_sessionmaker (callable)
    assert callable(session_factory)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_async_session():
    """Verify async session context manager works."""
    from sqlalchemy import text

    engine = create_async_engine_for_sqlite(":memory:")
    session_factory = create_session_factory(engine)

    # Verify we can create and use a session
    async with get_async_session(session_factory) as session:
        # Verify session is created
        assert session is not None

        # Verify we can execute a simple query (must use text())
        result = await session.execute(text("SELECT 1 AS value"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1

    await engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_session_basic_operations(tmp_path):
    """Verify async session can perform basic database operations.

    Uses file-based database to ensure data persists across sessions.
    """
    from sqlalchemy import text

    db_path = tmp_path / "test.db"
    engine = create_async_engine_for_sqlite(db_path)
    session_factory = create_session_factory(engine)

    # Create table and insert data
    async with get_async_session(session_factory) as session:
        await session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"))
        await session.execute(text("INSERT INTO test (id, name) VALUES (1, 'Alice')"))

    # Verify data persists (query in new session)
    async with get_async_session(session_factory) as session:
        result = await session.execute(text("SELECT id, name FROM test WHERE id = 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1
        assert row[1] == "Alice"

    await engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_session_rolls_back_on_exception(tmp_path):
    """Verify async session rolls back on exception."""
    from sqlalchemy import text

    db_path = tmp_path / "test_rollback.db"
    engine = create_async_engine_for_sqlite(db_path)
    session_factory = create_session_factory(engine)

    # Create table
    async with get_async_session(session_factory) as session:
        await session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))

    # Try to insert data but raise exception
    with pytest.raises(ValueError):
        async with get_async_session(session_factory) as session:
            await session.execute(text("INSERT INTO test (id) VALUES (2)"))
            raise ValueError("Test exception")

    # Verify data was NOT committed (rolled back)
    async with get_async_session(session_factory) as session:
        result = await session.execute(text("SELECT id FROM test WHERE id = 2"))
        row = result.fetchone()
        assert row is None

    await engine.dispose()
