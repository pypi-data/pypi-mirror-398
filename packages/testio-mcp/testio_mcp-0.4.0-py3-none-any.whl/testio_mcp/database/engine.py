"""
SQLAlchemy async engine and session factory for ORM operations.

This module provides:
- Async engine creation with SQLite+aiosqlite driver
- Session factory for database operations
- Proper async context management

Reference: STORY-030 (ORM Infrastructure Setup), AC2
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.config import settings


def create_async_engine_for_sqlite(db_path: str | Path) -> AsyncEngine:
    """Create async engine for SQLite database.

    Args:
        db_path: Path to SQLite database file (or ":memory:" for in-memory)

    Returns:
        AsyncEngine configured for SQLite with aiosqlite driver

    Note:
        - Uses NullPool for SQLite (connection pooling not beneficial for file-based DB)
        - Sets check_same_thread=False for async compatibility
        - WAL mode is set separately in PersistentCache.initialize()
    """
    # Convert Path to string for SQLAlchemy
    db_path_str = str(db_path) if isinstance(db_path, Path) else db_path

    # SQLite connection string for async
    # Format: sqlite+aiosqlite:///path/to/db.sqlite
    if db_path_str == ":memory:":
        connection_string = "sqlite+aiosqlite:///:memory:"
    else:
        # Absolute path required for SQLite
        abs_path = Path(db_path_str).resolve()
        connection_string = f"sqlite+aiosqlite:///{abs_path}"

    return create_async_engine(
        connection_string,
        echo=settings.LOG_LEVEL == "DEBUG",  # Log SQL statements in debug mode
        future=True,  # Use SQLAlchemy 2.0 style
        poolclass=NullPool,  # No connection pooling for SQLite
        connect_args={
            "check_same_thread": False,  # Required for async SQLite
            "timeout": 30.0,  # Wait up to 30 seconds for database lock (STORY-034A fix)
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session factory for database operations.

    Args:
        engine: AsyncEngine instance

    Returns:
        async_sessionmaker that creates AsyncSession instances

    Usage:
        async with session_factory() as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep objects accessible after commit
        autoflush=False,  # Explicit flushing for better control
        autocommit=False,  # Explicit commits (standard SQLAlchemy pattern)
    )


@asynccontextmanager
async def get_async_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Context manager for async database sessions.

    Args:
        session_factory: Session factory created by create_session_factory()

    Yields:
        AsyncSession instance

    Example:
        async with get_async_session(session_factory) as session:
            result = await session.execute(select(Test).where(Test.id == 123))
            test = result.scalar_one_or_none()

    Note:
        - Automatically commits on success
        - Automatically rolls back on exception
        - Closes session when exiting context
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def initialize_database(engine: AsyncEngine) -> None:
    """Initialize database schema using SQLModel metadata.

    Args:
        engine: AsyncEngine instance

    Note:
        This creates all tables defined in SQLModel classes.
        In production, use Alembic migrations instead (see STORY-034A).
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
