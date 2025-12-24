"""
Database utility functions.

Contains maintenance and configuration utilities for SQLite database.

STORY-034B: Refactored to use AsyncEngine instead of aiosqlite.Connection.
All database configuration now uses SQLAlchemy's AsyncEngine.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def vacuum_database(engine: "AsyncEngine") -> None:
    """Compact database and reclaim space.

    Args:
        engine: Active AsyncEngine instance

    STORY-034B: Refactored from aiosqlite.Connection to AsyncEngine.
    """
    async with engine.begin() as conn:
        await conn.execute(text("VACUUM"))
    logger.debug("Database vacuumed successfully")


async def configure_wal_mode(engine: "AsyncEngine") -> None:
    """Configure Write-Ahead Logging for concurrent reads.

    WAL mode allows background writes without blocking read queries.
    Also configures checkpointing and busy timeout.

    Args:
        engine: Active AsyncEngine instance

    STORY-034B: Refactored from aiosqlite.Connection to AsyncEngine.
    """
    async with engine.begin() as conn:
        # Enable WAL mode for concurrent reads
        await conn.execute(text("PRAGMA journal_mode=WAL"))

        # WAL checkpointing configuration (prevent disk bloat)
        # Checkpoint after 1000 pages (~4MB)
        await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))

        # Wait 5 seconds before failing on lock
        await conn.execute(text("PRAGMA busy_timeout=5000"))

    logger.debug("WAL mode configured successfully")
