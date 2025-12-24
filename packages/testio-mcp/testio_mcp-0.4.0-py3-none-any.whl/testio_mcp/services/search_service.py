"""Search Service - Business logic for full-text search operations.

This service handles search-related business logic including:
- Query validation (non-empty, minimum length)
- Entity type validation using SEARCHABLE_ENTITIES constant
- Date range parsing (ISO and natural language via parse_flexible_date)
- FTS5 query sanitization ("simple" vs "raw" match modes)
- Result formatting with scores and ranks

STORY-065: Search MCP Tool
Epic: EPIC-010 (Full-Text Search)
"""

import logging
import re
from typing import Any

from testio_mcp.exceptions import InvalidSearchQueryError
from testio_mcp.repositories.search_repository import SearchRepository, SearchResult
from testio_mcp.schemas.constants import SEARCHABLE_ENTITIES
from testio_mcp.services.base_service import BaseService
from testio_mcp.utilities.date_utils import parse_flexible_date

logger = logging.getLogger(__name__)

# Minimum query length for non-prefix searches
MIN_QUERY_LENGTH = 2


class SearchService(BaseService):
    """Service for full-text search operations.

    Business logic for searching across TestIO entities:
    - Query validation and sanitization
    - Date range filtering
    - Result formatting with relevance scores

    Inherits from BaseService for consistency with other services.

    Note: SearchService uses repository pattern (not API client directly).
    """

    def __init__(self, search_repo: SearchRepository) -> None:
        """Initialize service.

        Args:
            search_repo: SearchRepository instance for FTS5 queries
        """
        # SearchService doesn't need client (repository handles data)
        super().__init__(client=None)  # type: ignore[arg-type]
        self.search_repo = search_repo

    async def search(
        self,
        query: str,
        entities: list[str] | None = None,
        product_ids: list[int] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
        match_mode: str = "simple",
    ) -> dict[str, Any]:
        """Execute full-text search with filters and BM25 ranking.

        Args:
            query: Search query string
            entities: Optional list of entity types to filter (product, feature, test, bug)
            product_ids: Optional list of product IDs to scope search
            start_date: Optional start date (ISO format or natural language)
            end_date: Optional end date (ISO format or natural language)
            limit: Maximum results to return (default: 20, max: 100)
            match_mode: Query mode - "simple" (sanitized) or "raw" (FTS5 syntax)

        Returns:
            Dict with results, total, and query metadata:
            {
                "query": str,                    # Original query as provided
                "sanitized_query": str,          # (Optional) Sanitized query if different
                "total": int,
                "results": [
                    {
                        "entity_type": str,
                        "entity_id": int,
                        "title": str,
                        "score": float,
                        "rank": int
                    },
                    ...
                ]
            }

        Raises:
            InvalidSearchQueryError: If query is empty, too short, or has invalid syntax
            ValueError: If entity types are invalid

        Example:
            result = await service.search("borders", entities=["feature"], limit=10)
            for item in result["results"]:
                print(f"{item['rank']}. {item['entity_type']} - {item['title']}")
        """
        # Validate query
        self._validate_query(query)

        # Validate entities if provided
        if entities:
            self._validate_entities(entities)

        # Validate and clamp limit
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        # Validate match_mode
        if match_mode not in ("simple", "raw"):
            raise InvalidSearchQueryError("Invalid match_mode. Must be 'simple' or 'raw'.")

        # Parse dates if provided
        parsed_start_date: str | None = None
        parsed_end_date: str | None = None

        if start_date:
            parsed_start_date = parse_flexible_date(start_date, start_of_day=True)

        if end_date:
            parsed_end_date = parse_flexible_date(end_date, start_of_day=False)

        # Sanitize query based on match_mode
        search_query = self._prepare_query(query, match_mode)

        # Execute search
        try:
            results = await self.search_repo.search(
                query=search_query,
                entities=entities,
                product_ids=product_ids,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                limit=limit,
            )
        except Exception as e:
            # Catch FTS5 syntax errors and convert to friendly message
            error_msg = str(e).lower()
            if "fts5" in error_msg or "syntax error" in error_msg or "malformed" in error_msg:
                raise InvalidSearchQueryError(
                    f"Invalid search syntax: {str(e)}. "
                    "Try simpler terms or use match_mode='simple'."
                ) from None
            raise

        # Format results with ranks (include sanitized query for transparency)
        return self._format_results(query, search_query, results)

    async def optimize_index(self) -> None:
        """Optimize FTS5 index to reduce fragmentation.

        Should be called after bulk operations (nuke sync, large backfills) to
        improve query performance. Safe to call anytime but has overhead.
        """
        await self.search_repo.optimize_index()
        logger.info("FTS5 search index optimized")

    def _validate_query(self, query: str) -> None:
        """Validate search query.

        Args:
            query: Search query string

        Raises:
            InvalidSearchQueryError: If query is empty or too short
        """
        if not query or not query.strip():
            raise InvalidSearchQueryError("Search query cannot be empty.")

        # Strip and check minimum length (unless it's a prefix query like "a*")
        stripped = query.strip()
        if len(stripped) < MIN_QUERY_LENGTH and not stripped.endswith("*"):
            raise InvalidSearchQueryError(
                f"Search query must be at least {MIN_QUERY_LENGTH} characters."
            )

    def _validate_entities(self, entities: list[str]) -> None:
        """Validate entity types.

        Args:
            entities: List of entity types to validate

        Raises:
            ValueError: If any entity type is invalid
        """
        invalid_entities = [e for e in entities if e not in SEARCHABLE_ENTITIES]
        if invalid_entities:
            raise ValueError(
                f"Invalid entity types: {invalid_entities}. "
                f"Valid types: {list(SEARCHABLE_ENTITIES)}"
            )

    def _prepare_query(self, query: str, match_mode: str) -> str:
        """Prepare query for FTS5 execution.

        Args:
            query: Raw user query
            match_mode: "simple" (sanitized) or "raw" (FTS5 syntax)

        Returns:
            Query string ready for FTS5 MATCH clause
        """
        stripped = query.strip()

        if match_mode == "raw":
            # Pass through as-is (user knows FTS5 syntax)
            return stripped

        # Simple mode: sanitize to prevent FTS5 syntax errors
        # Strategy: Keep only safe characters (alphanumeric, spaces, hyphens, underscores)
        # Remove ALL FTS5 special characters: ! @ # $ % ^ & * ( ) [ ] { } + = | \ / ? < > ~ `
        # Also removes: " ' : ; , .
        # This is the safest approach for user-facing search

        # Remove boolean operators first (case-insensitive)
        sanitized = re.sub(r"\b(AND|OR|NOT)\b", "", stripped, flags=re.IGNORECASE)

        # Remove column filters (e.g., "title:term") - colon with preceding word
        sanitized = re.sub(r"\w+:", "", sanitized)

        # Remove ALL special characters except spaces, hyphens, and underscores
        # This handles: ! @ # $ % ^ & * ( ) [ ] { } + = | \ / ? < > ~ ` " ' : ; , .
        sanitized = re.sub(r"[^\w\s\-]", " ", sanitized)

        # Collapse multiple spaces
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        if not sanitized:
            # If sanitization removed everything, return a safe fallback
            # Use a generic search term that won't crash
            return "error"

        return sanitized

    def _format_results(
        self, query: str, sanitized_query: str, results: list[SearchResult]
    ) -> dict[str, Any]:
        """Format search results for API response.

        Args:
            query: Original search query (as provided by user)
            sanitized_query: Sanitized query (actually sent to FTS5)
            results: List of SearchResult objects from repository

        Returns:
            Formatted response dict with results, total, and query metadata
        """
        formatted_results = []
        for rank, result in enumerate(results, start=1):
            formatted_results.append(
                {
                    "entity_type": result.entity_type,
                    "entity_id": result.entity_id,
                    "title": result.title,
                    "score": round(result.score, 4),
                    "rank": rank,
                }
            )

        response: dict[str, Any] = {
            "query": query,
            "total": len(formatted_results),
            "results": formatted_results,
        }

        # Add sanitized_query only if it differs from original (transparency)
        if sanitized_query != query:
            response["sanitized_query"] = sanitized_query

        return response
