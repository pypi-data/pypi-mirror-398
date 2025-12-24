"""FTS5 Query Builder - Generates SQLite FTS5 queries with filters.

This module isolates all FTS5-specific SQL generation in one place (SRP).
If we migrate to PostgreSQL, only this module needs rewriting.

Design Principles:
- Single Responsibility: SQL generation only (no execution)
- Open/Closed: Extend with new query types without modifying existing
- Dependency Inversion: SearchRepository depends on builder interface

STORY-065: Added date range filtering support via timestamp column.
- Tests: filtered by end_at
- Bugs: filtered by reported_at
- Products/Features: excluded from date filtering (timestamp is NULL)
"""

import logging
from typing import Any

from testio_mcp.schemas.constants import SEARCHABLE_ENTITIES

logger = logging.getLogger(__name__)


class FTS5QueryBuilder:
    """Builds FTS5 SQL queries from search parameters.

    Centralizes all FTS5-specific SQL to enable future migration to PostgreSQL.
    All queries use BM25 ranking with column weights (title=5.0, content=1.0).

    STORY-065: Supports date range filtering via timestamp column.
    Note: Products and Features have NULL timestamps and will be excluded
    when date filters are applied.
    """

    # Column weights for BM25 ranking
    TITLE_WEIGHT = 5.0
    CONTENT_WEIGHT = 1.0

    def build_search_query(
        self,
        query: str,
        entities: list[str] | None = None,
        product_ids: list[int] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
    ) -> tuple[str, list[Any]]:
        """Build FTS5 search query with filters and BM25 ranking.

        Args:
            query: FTS5 match query (user input, pre-sanitized)
            entities: Optional list of entity types to filter (e.g., ["feature", "test"])
            product_ids: Optional list of product IDs to scope search
            start_date: Optional start date (ISO format, e.g., "2024-01-01T00:00:00Z")
            end_date: Optional end date (ISO format, e.g., "2024-12-31T23:59:59Z")
            limit: Maximum results to return

        Returns:
            Tuple of (sql, params) for execution with aiosqlite

        Note:
            Date filtering implicitly excludes Products and Features since their
            timestamp is NULL. Only Tests (end_at) and Bugs (reported_at) have timestamps.

        Example:
            sql, params = builder.build_search_query("borders", entities=["feature"])
            # Returns:
            # SELECT entity_type, entity_id, title, bm25(search_index, 5.0, 1.0) as score
            # FROM search_index
            # WHERE search_index MATCH ?
            #   AND entity_type IN (?)
            # ORDER BY score
            # LIMIT ?
        """
        # Build WHERE clause components
        where_clauses = ["search_index MATCH ?"]
        params: list[Any] = [query]

        # Add entity type filter if specified
        if entities:
            # Validate entity types
            invalid_entities = [e for e in entities if e not in SEARCHABLE_ENTITIES]
            if invalid_entities:
                raise ValueError(
                    f"Invalid entity types: {invalid_entities}. Valid types: {SEARCHABLE_ENTITIES}"
                )

            placeholders = ", ".join(["?" for _ in entities])
            where_clauses.append(f"entity_type IN ({placeholders})")
            params.extend(entities)

        # Add product_id filter if specified
        if product_ids:
            placeholders = ", ".join(["?" for _ in product_ids])
            where_clauses.append(f"product_id IN ({placeholders})")
            params.extend(product_ids)

        # Add date range filter if specified (STORY-065)
        # Note: This will exclude Products and Features since their timestamp is NULL
        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(end_date)

        # Combine WHERE clauses
        where_sql = " AND ".join(where_clauses)

        # Build complete query with BM25 ranking and column weights
        sql = f"""
            SELECT
                entity_type,
                entity_id,
                title,
                bm25(search_index, {self.TITLE_WEIGHT}, {self.CONTENT_WEIGHT}) as score
            FROM search_index
            WHERE {where_sql}
            ORDER BY score
            LIMIT ?
        """

        params.append(limit)

        logger.debug(f"Built FTS5 query: {sql} with params: {params}")
        return sql, params

    def build_optimize_query(self) -> str:
        """Build query to optimize FTS5 index.

        Should be run after bulk operations (nuke sync, large backfills) to
        reduce index fragmentation and improve query performance.

        Returns:
            SQL string for index optimization
        """
        return "INSERT INTO search_index(search_index) VALUES('optimize')"
