"""Base Repository - Shared database session logic for all repositories.

This module provides the BaseRepository class with common patterns:
- Standard dependency injection (session, client, customer_id)
- Session management (commit, rollback, close)
- Error handling for database operations

Repositories handle pure data access logic (ORM queries + API fetching).
Business logic belongs in services.
"""

import logging
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base class for all repository classes.

    Provides common dependency injection pattern for database access using SQLModel.
    All repositories are scoped to a specific customer for data isolation.

    Attributes:
        session: AsyncSession for ORM-based database operations
        client: TestIO API client for fetching fresh data
        customer_id: Stable customer identifier for data isolation
    """

    def __init__(
        self, session_or_db: Any, client: TestIOClient, customer_id: int, cache: Any | None = None
    ) -> None:
        """Initialize repository with database session/connection and API client.

        Args:
            session_or_db: AsyncSession for ORM mode, or legacy connection object
            client: TestIO API client for refresh operations
            customer_id: Stable customer identifier from TestIO system
            cache: Optional PersistentCache for per-entity refresh locks (STORY-046, AC6)
        """
        self.session: AsyncSession | None = None
        self.db: Any | None = None

        # Check type to determine if we're in ORM mode or legacy SQL mode
        # We use isinstance because hasattr() on AsyncMock always returns True,
        # which breaks legacy tests that use raw AsyncMock for db connection.
        if isinstance(session_or_db, AsyncSession):
            self.session = session_or_db
        else:
            self.db = session_or_db

        self.client = client
        self.customer_id = customer_id
        self.cache = cache  # STORY-046, AC6: For per-entity refresh locks

    async def commit(self) -> None:
        """Commit the current transaction.

        Delegates to the underlying session or connection.
        """
        if self.session:
            await self.session.commit()
        elif self.db:
            await self.db.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction.

        Delegates to the underlying session or connection.
        """
        if self.session:
            await self.session.rollback()
        elif self.db:
            await self.db.rollback()

    async def close(self) -> None:
        """Close the session.

        Delegates to the underlying session or connection.
        """
        if self.session:
            await self.session.close()
        # Note: aiosqlite connection is usually managed externally/by context manager
        # so we might not want to close it here if it was passed in, but for consistency:
        elif self.db and hasattr(self.db, "close"):
            await self.db.close()
