"""MCP tool for listing bugs with filtering and pagination.

This module implements the list_bugs tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to BugService
4. Converts exceptions to user-friendly error format
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BeforeValidator, Field

from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.schemas.api import ListBugsOutput
from testio_mcp.server import mcp
from testio_mcp.services.bug_service import BugService
from testio_mcp.utilities import (
    get_service_context,
)
from testio_mcp.utilities.parsing import parse_int_list_input, parse_list_input
from testio_mcp.utilities.schema_utils import inline_schema_refs


@mcp.tool(output_schema=inline_schema_refs(ListBugsOutput.model_json_schema()))
async def list_bugs(
    test_ids: Annotated[
        list[int] | str | int,
        Field(
            description=(
                "Required test IDs to scope query. "
                "Accepts: list of ints [123, 456], single int 123, "
                "comma-separated string '123,456', or JSON array '[123, 456]'"
            ),
            examples=[[123, 456], "123", "123,456"],
        ),
    ],
    ctx: Context,
    status: Annotated[
        str | list[str] | None,  # Accept both string and list (MCP interface validation)
        BeforeValidator(parse_list_input),  # Normalize to list[str]
        Field(
            description='Filter by bug status. Format: "rejected" or ["rejected", "forwarded"]',
            examples=["rejected", ["rejected", "forwarded"]],
        ),
    ] = None,
    severity: Annotated[
        str | list[str] | None,  # Accept both string and list (MCP interface validation)
        BeforeValidator(parse_list_input),  # Normalize to list[str]
        Field(
            description='Filter by severity. Format: "critical" or ["critical", "high"]',
            examples=["critical", ["critical", "high"]],
        ),
    ] = None,
    rejection_reason: Annotated[
        str | list[str] | None,  # Accept both string and list (MCP interface validation)
        BeforeValidator(parse_list_input),  # Normalize to list[str]
        Field(
            description="Filter by rejection reason",
            examples=["test_is_invalid"],
        ),
    ] = None,
    reported_by_user_id: Annotated[
        int | None,
        Field(gt=0, description="Filter by reporting user ID", examples=[12345]),
    ] = None,
    page: Annotated[
        int,
        Field(ge=1, description="Page number (1-indexed)"),
    ] = 1,
    per_page: Annotated[
        int,
        Field(
            ge=1,
            le=200,
            description="Items per page (default: 100, max: 200)",
        ),
    ] = 0,  # 0 means use settings default
    offset: Annotated[
        int,
        Field(
            ge=0,
            description="Starting offset (0-indexed). Combines with page: "
            "offset + (page-1)*per_page. "
            "Example: To get items 50-99, use offset=50, per_page=50",
        ),
    ] = 0,
    sort_by: Annotated[
        str,
        Field(
            description="Sort field. Values: reported_at, severity, status, title",
            examples=["reported_at", "severity", "status", "title"],
        ),
    ] = "reported_at",
    sort_order: Annotated[
        str,
        Field(
            description="Sort order. Values: asc, desc",
            examples=["desc", "asc"],
        ),
    ] = "desc",
) -> dict[str, Any]:
    """List bugs for specified tests with filters, pagination, and sorting.

    Returns minimal bug information for quick scanning and filtering.
    Results are scoped to the specified test_ids to prevent mass data fetch.
    """
    # Normalize test_ids from various input formats (AI-friendly)
    parsed_test_ids = parse_int_list_input(test_ids)
    if not parsed_test_ids:
        raise ToolError(
            "❌ Invalid argument 'test_ids': At least one test ID is required\n"
            "💡 Provide test IDs as: [123, 456], '123', '123,456', or '[123, 456]'"
        )

    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, BugService) as service:
        # Get settings for default page size
        from testio_mcp.config import settings

        # Use default per_page from settings if not specified (0 = use default)
        effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

        # Delegate to service and convert exceptions to MCP error format
        try:
            # BeforeValidator already normalized str -> list[str], cast for mypy
            from typing import cast

            service_result = await service.list_bugs(
                test_ids=parsed_test_ids,
                status=cast(list[str] | None, status),
                severity=cast(list[str] | None, severity),
                rejection_reason=cast(list[str] | None, rejection_reason),
                reported_by_user_id=reported_by_user_id,
                page=page,
                per_page=effective_per_page,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            # Extract components from service result
            bugs = service_result["bugs"]
            pagination = service_result["pagination"]
            filters_applied = service_result["filters_applied"]
            warnings = service_result.get("warnings")

            # Empty results guidance
            if len(bugs) == 0:
                import logging

                logger = logging.getLogger(__name__)
                filter_desc = (
                    "with specified filters"
                    if (status or severity or rejection_reason or reported_by_user_id)
                    else "for these tests"
                )
                logger.info(
                    f"ℹ️  No bugs found {filter_desc}\n"
                    f"💡 Try removing filters or checking other tests"
                )

            # Build validated output using BugListItem
            from testio_mcp.schemas.api import BugListItem

            bug_items = [
                BugListItem(
                    id=bug["id"],
                    title=bug["title"],
                    severity=bug["severity"],
                    status=bug["status"],
                    test_id=bug["test_id"],
                    reported_at=bug["reported_at"],
                )
                for bug in bugs
            ]

            output = ListBugsOutput(
                bugs=bug_items,
                pagination=pagination,
                filters_applied=filters_applied,
                warnings=warnings,
            )

            return output.model_dump(by_alias=True, exclude_none=True)

        except TestIOAPIError as e:
            # Convert API error to ToolError with user-friendly message
            raise ToolError(
                f"❌ API error: {e.message}\n"
                f"ℹ️  HTTP status code: {e.status_code}\n"
                f"💡 Check API status and try again. If the problem persists, contact support."
            ) from e

        except Exception as e:
            # Catch-all for unexpected errors
            raise ToolError(
                f"❌ Unexpected error: {str(e)}\n"
                f"ℹ️  An unexpected error occurred while listing bugs\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
