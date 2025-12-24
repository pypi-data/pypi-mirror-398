"""MCP tool for full-text search across TestIO entities.

This module implements the search tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Uses async context manager for resource cleanup
2. Delegates to SearchService
3. Converts exceptions to user-friendly error format

STORY-065: Search MCP Tool
Epic: EPIC-010 (Full-Text Search)
"""

from typing import Annotated, Any, Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from testio_mcp.exceptions import InvalidSearchQueryError
from testio_mcp.schemas.constants import SEARCHABLE_ENTITIES
from testio_mcp.server import mcp
from testio_mcp.services.search_service import SearchService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.parsing import parse_int_list_input, parse_list_input
from testio_mcp.utilities.schema_utils import inline_schema_refs


# Pydantic Models for output schema
class SearchResultItem(BaseModel):
    """Individual search result."""

    entity_type: Literal["product", "feature", "test", "bug"] = Field(
        description="Entity type (product, feature, test, bug)"
    )
    entity_id: int = Field(description="Entity ID in source table")
    title: str = Field(description="Entity title")
    score: float = Field(description="BM25 relevance score (lower = more relevant)")
    rank: int = Field(description="Result rank (1 = best match)")


class SearchOutput(BaseModel):
    """Search output with results and metadata."""

    query: str = Field(description="Original search query")
    sanitized_query: str | None = Field(
        default=None,
        description="Sanitized query sent to FTS5 (only present if different from original)",
    )
    total: int = Field(description="Number of results returned")
    results: list[SearchResultItem] = Field(description="Ranked search results")


# MCP Tool


@mcp.tool(output_schema=inline_schema_refs(SearchOutput.model_json_schema()))
async def search(
    ctx: Context,
    query: Annotated[
        str,
        Field(
            description="Search query. Supports phrases, prefix* matching. "
            "Examples: 'borders', 'video mode', 'login*'",
            min_length=1,
            examples=["borders", "video mode", "login*"],
        ),
    ],
    entities: Annotated[
        list[Literal["product", "feature", "test", "bug"]] | str | None,
        Field(
            description=(
                "Filter by entity types. Default: all. Values: product, feature, test, bug. "
                "Accepts: list ['feature', 'bug'], comma-separated 'feature,bug', or single 'bug'"
            ),
            examples=[["feature", "bug"], "feature,bug", "bug"],
        ),
    ] = None,
    product_ids: Annotated[
        list[int] | str | int | None,
        Field(
            description=(
                "Scope search to specific products. "
                "Accepts: list [598, 601], single int 598, "
                "comma-separated '598,601', or JSON array '[598, 601]'"
            ),
            examples=[[598, 601], "598", "598,601"],
        ),
    ] = None,
    start_date: Annotated[
        str | None,
        Field(
            description="Filter by date (ISO or natural language). "
            "Examples: '2024-01-01', 'last week', '3 months ago'. "
            "Note: Products/Features excluded from date filtering.",
            examples=["2024-01-01", "last week"],
        ),
    ] = None,
    end_date: Annotated[
        str | None,
        Field(
            description="Filter by date (ISO or natural language). "
            "Examples: 'today', '2024-12-31'. "
            "Note: Products/Features excluded from date filtering.",
            examples=["today", "2024-12-31"],
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(ge=1, le=100, description="Maximum results to return (default: 20, max: 100)"),
    ] = 20,
    match_mode: Annotated[
        Literal["simple", "raw"],
        Field(
            description="Query mode. 'simple': sanitized for safety (default). "
            "'raw': full FTS5 syntax (AND, OR, NOT, phrases)."
        ),
    ] = "simple",
) -> dict[str, Any]:
    """Search across TestIO entities using full-text search.

    Returns ranked results sorted by BM25 relevance. Searches across
    products, features, tests, and bugs with optional filtering.

    Date filtering note: Products and Features don't have timestamps,
    so they are excluded when start_date or end_date is specified.
    Only Tests (by end_at) and Bugs (by reported_at) support date filtering.
    """
    # Normalize input formats (AI-friendly)
    # Cast entities for mypy: Literal types are str-compatible at runtime
    from typing import cast

    parsed_entities = parse_list_input(cast("str | list[str] | None", entities))
    parsed_product_ids = parse_int_list_input(product_ids)

    # Validate entity types if provided
    if parsed_entities:
        invalid = [e for e in parsed_entities if e not in SEARCHABLE_ENTITIES]
        if invalid:
            valid_types = ", ".join(SEARCHABLE_ENTITIES)
            raise ToolError(f"❌ Invalid entity types: {invalid}\n💡 Valid types: {valid_types}")

    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, SearchService) as service:
        try:
            result = await service.search(
                query=query,
                entities=parsed_entities,
                product_ids=parsed_product_ids,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                match_mode=match_mode,
            )

            # Validate output against schema
            output = SearchOutput(**result)
            return output.model_dump(exclude_none=True)

        except InvalidSearchQueryError as e:
            raise ToolError(
                f"❌ Invalid search query\n"
                f"ℹ️ {e.message}\n"
                f"💡 Try simpler terms or use match_mode='raw' for FTS5 syntax"
            ) from None

        except ValueError as e:
            # Entity type validation errors
            valid_types = ", ".join(SEARCHABLE_ENTITIES)
            raise ToolError(
                f"❌ Invalid entity type\nℹ️ {str(e)}\n💡 Valid types: {valid_types}"
            ) from None

        except Exception as e:
            # Unexpected errors
            raise ToolError(
                f"❌ Search failed\nℹ️ {str(e)}\n💡 Try a simpler query or check if data is synced"
            ) from None
