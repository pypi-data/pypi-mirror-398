"""MCP tool for listing tests with status filtering.

This module implements the list_tests tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to TestService (STORY-023d: moved from ProductService)
4. Converts exceptions to user-friendly error format
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BeforeValidator, Field

from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError
from testio_mcp.schemas.api import (
    ListTestsOutput,
    PaginationInfo,
    ProductInfoSummary,
)
from testio_mcp.server import mcp
from testio_mcp.services.test_service import TestService
from testio_mcp.transformers import to_test_summary_list
from testio_mcp.utilities import get_service_context, parse_status_input
from testio_mcp.utilities.schema_utils import inline_schema_refs

# MCP Tool (AC1)


@mcp.tool(output_schema=inline_schema_refs(ListTestsOutput.model_json_schema()))
async def list_tests(
    product_id: Annotated[
        int,
        Field(gt=0, description="Product ID (use list_products to find)", examples=[25073]),
    ],
    ctx: Context,
    page: Annotated[int, Field(ge=1, description="Page number (1-indexed)")] = 1,
    per_page: Annotated[
        int,
        Field(ge=1, le=200, description="Items per page (default: 100, max: 200)"),
    ] = 0,  # 0 means use settings default
    offset: Annotated[
        int,
        Field(
            ge=0,
            description="Starting offset (0-indexed). "
            "Combines with page: offset + (page-1)*per_page. "
            "Example: To get items 50-99, use offset=50, per_page=50",
        ),
    ] = 0,
    statuses: Annotated[
        str | list[str] | None,  # Accept both string and list (MCP interface validation)
        BeforeValidator(parse_status_input),  # Normalize to list[str]
        Field(
            description="Filter by status. Values: running, locked, archived, cancelled, "
            'customer_finalized, initialized. Format: "running,locked" or ["running", "locked"]',
            examples=["running", "archived,locked", ["running"], ["archived", "locked"]],
        ),
    ] = None,
    testing_type: Annotated[
        str | None,
        Field(
            description="Filter by type. Values: coverage, focused, rapid",
            examples=["coverage", "focused", "rapid"],
        ),
    ] = None,
    sort_by: Annotated[
        str,
        Field(
            description="Sort field. Values: start_at, end_at, status, title",
            examples=["end_at", "title", "start_at", "status"],
        ),
    ] = "end_at",
    sort_order: Annotated[
        str,
        Field(description="Sort order. Values: asc, desc", examples=["desc", "asc"]),
    ] = "desc",
) -> dict[str, Any]:
    """List tests for a product with pagination and filtering.

    Queries local SQLite (fast, no API calls). Use get_test_status for detailed test info with bugs.
    """
    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, TestService) as service:
        # Get settings for default page size
        from testio_mcp.config import settings

        # Use default per_page from settings if not specified (0 = use default)
        effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

        # Note: Repository handles offset + page combination internally
        # No calculation needed here - just pass values through

        # Delegate to service and convert exceptions to MCP error format (AC7)
        try:
            # Parse statuses if needed (BeforeValidator handles this when called via MCP,
            # but direct calls in tests bypass validation, so we ensure parsing happens)
            from enum import Enum
            from typing import cast

            parsed_statuses = (
                parse_status_input(statuses) if isinstance(statuses, str) else statuses
            )

            service_result = await service.list_tests(
                product_id=product_id,
                page=page,
                per_page=effective_per_page,
                offset=offset,
                statuses=cast(list[str | Enum] | None, parsed_statuses),
                testing_type=testing_type,  # STORY-054 AC10
                sort_by=sort_by,  # STORY-054 AC10
                sort_order=sort_order,  # STORY-054 AC10
            )

            # Transform service result to tool output format
            product = service_result["product"]
            tests = service_result["tests"]
            statuses_filter = service_result[
                "statuses_filter"
            ]  # AC8 - Use effective statuses from service
            has_more = service_result["has_more"]  # AC3 - Pagination metadata from service

            # Transform using centralized transformer
            test_summaries = to_test_summary_list(tests)

            # STORY-008 AC7: Empty results guidance
            if len(test_summaries) == 0:
                import logging

                logger = logging.getLogger(__name__)
                status_desc = "with specified filters" if statuses else "for this product"
                logger.info(
                    f"ℹ️  No tests found {status_desc}\n"
                    f"💡 Try removing status filters or check other products using list_products"
                )

            # Build validated output with pagination metadata (AC5)
            total_count = service_result.get("total_count", 0)
            actual_offset = service_result.get("offset", 0)

            # Calculate index range for current page
            start_index = actual_offset
            end_index = actual_offset + len(test_summaries) - 1 if test_summaries else -1

            output = ListTestsOutput(
                product=ProductInfoSummary(
                    id=product["id"],  # Keep as integer from API
                    name=product["name"],
                    type=product["type"],
                ),
                statuses_filter=statuses_filter,  # AC8 - Use effective statuses from service
                pagination=PaginationInfo(
                    page=page,
                    per_page=effective_per_page,
                    offset=actual_offset,
                    start_index=start_index,
                    end_index=end_index,
                    total_count=total_count,
                    has_more=has_more,
                ),
                total_tests=len(test_summaries),
                tests=test_summaries,
            )

            return output.model_dump(by_alias=True, exclude_none=True)

        except ProductNotFoundException as e:
            # Convert domain exception to ToolError with user-friendly message
            raise ToolError(
                f"❌ Product ID '{e.product_id}' not found\n"
                f"ℹ️  This product may not exist or you don't have access to it\n"
                f"💡 Use the list_products tool to see available products"
            ) from e

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
                f"ℹ️  An unexpected error occurred while listing tests\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
