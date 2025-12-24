"""Search Repository - Data access layer for FTS5 full-text search.

This repository handles all FTS5 queries using raw SQL (SQLModel doesn't support
virtual tables). It delegates query building to FTS5QueryBuilder for clean separation.
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.base_repository import BaseRepository
from testio_mcp.repositories.fts5_query_builder import FTS5QueryBuilder

logger = logging.getLogger(__name__)


class SearchResult:
    """Single search result from FTS5 query.

    Attributes:
        entity_type: Type of entity (product, feature, test, bug)
        entity_id: ID of the entity in its source table
        title: Entity title/name
        score: BM25 relevance score (lower is better - SQLite FTS5 convention)
    """

    def __init__(self, entity_type: str, entity_id: int, title: str, score: float):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.title = title
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "score": self.score,
        }


class SearchRepository(BaseRepository):
    """Repository for FTS5 full-text search operations.

    Uses raw SQL for FTS5 queries since SQLModel doesn't support virtual tables.
    Delegates SQL generation to FTS5QueryBuilder (SRP).

    Attributes:
        session: AsyncSession for raw SQL execution (inherited from BaseRepository)
        client: TestIO API client (inherited, unused for search)
        customer_id: Customer identifier (inherited, currently unused for search)
        query_builder: FTS5QueryBuilder for SQL generation
    """

    # Override type hint to indicate session is always present
    session: AsyncSession

    def __init__(
        self,
        session: AsyncSession,
        client: TestIOClient,
        customer_id: int,
        query_builder: FTS5QueryBuilder | None = None,
    ) -> None:
        """Initialize repository with async session and query builder.

        Args:
            session: Active AsyncSession for database operations
            client: TestIO API client (unused for search)
            customer_id: Stable customer identifier
            query_builder: Optional FTS5QueryBuilder (defaults to new instance)
        """
        super().__init__(session, client, customer_id)
        self.query_builder = query_builder or FTS5QueryBuilder()

    async def search(
        self,
        query: str,
        entities: list[str] | None = None,
        product_ids: list[int] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Execute FTS5 search with filters and BM25 ranking.

        Args:
            query: Search query string (FTS5 syntax, pre-sanitized by service)
            entities: Optional list of entity types to filter (e.g., ["feature", "test"])
            product_ids: Optional list of product IDs to scope search
            start_date: Optional start date (ISO format, e.g., "2024-01-01T00:00:00Z")
            end_date: Optional end date (ISO format, e.g., "2024-12-31T23:59:59Z")
            limit: Maximum results to return (default: 20)

        Returns:
            List of SearchResult objects ordered by relevance (best first)

        Raises:
            ValueError: If entity types are invalid (raised by query builder)
            sqlite3.OperationalError: If FTS5 query syntax is invalid

        Note:
            Date filtering implicitly excludes Products and Features since their
            timestamp is NULL. Only Tests (end_at) and Bugs (reported_at) have timestamps.

        Example:
            results = await repo.search("borders", entities=["feature"], limit=10)
            for result in results:
                print(f"{result.entity_type} {result.entity_id}: {result.title} ({result.score})")
        """
        # Build SQL query via query builder
        sql, params = self.query_builder.build_search_query(
            query, entities, product_ids, start_date, end_date, limit
        )

        logger.debug(f"Executing FTS5 search: query={query}, entities={entities}, limit={limit}")

        # Execute raw SQL query using execute() with text()
        # Convert params list to dict for bindparam support
        param_dict = {f"param{i}": p for i, p in enumerate(params)}

        # Replace ? placeholders with named :param0, :param1, etc.
        sql_named = sql
        for i in range(len(params)):
            sql_named = sql_named.replace("?", f":param{i}", 1)

        conn = await self.session.connection()
        result = await conn.execute(text(sql_named), param_dict)
        rows = result.fetchall()

        # Convert rows to SearchResult objects
        search_results = [
            SearchResult(
                entity_type=row[0],
                entity_id=row[1],
                title=row[2],
                score=row[3],
            )
            for row in rows
        ]

        logger.info(
            f"FTS5 search completed: query={query}, entities={entities}, "
            f"product_ids={product_ids}, results={len(search_results)}"
        )

        return search_results

    async def optimize_index(self) -> None:
        """Optimize FTS5 index to reduce fragmentation.

        Should be called after bulk operations (nuke sync, large backfills) to
        improve query performance. Safe to call anytime but has overhead.
        """
        sql = self.query_builder.build_optimize_query()
        conn = await self.session.connection()
        await conn.execute(text(sql))
        await self.session.commit()

        logger.info("FTS5 search index optimized")
