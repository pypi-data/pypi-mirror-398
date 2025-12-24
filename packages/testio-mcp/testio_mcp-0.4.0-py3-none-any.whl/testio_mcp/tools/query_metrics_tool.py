"""MCP tool for dynamic analytics queries.

This module implements the query_metrics tool following the service
layer pattern (ADR-011). The tool is a thin wrapper that:
1. Uses async context manager for resource cleanup
2. Delegates to AnalyticsService
3. Converts exceptions to user-friendly error format

STORY-044: Query Metrics Tool
Epic: EPIC-007 (Generic Analytics Framework)
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import ProductNotFoundException
from testio_mcp.schemas.constants import VALID_TEST_STATUSES
from testio_mcp.server import mcp
from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.utilities import ProgressReporter, get_service_context
from testio_mcp.utilities.parsing import parse_list_input


class QueryMetricsInput(BaseModel):
    """Input validation for query_metrics tool."""

    metrics: list[str] = Field(
        min_length=1,
        description="Metrics to measure",
        examples=[["bug_count"]],
    )
    dimensions: list[str] = Field(
        min_length=1,
        max_length=2,
        description="Dimensions to group by (max 2)",
        examples=[["feature"]],
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Filter by dimension values, product_id, or status. "
            "Default status filter: excludes initialized and cancelled tests. "
            "Override with status=['initialized', 'cancelled', ...] to include them."
        ),
        examples=[
            {"severity": "critical"},
            {"product_id": 598},
            {"status": ["initialized", "cancelled"]},
        ],
    )
    start_date: str | None = Field(
        default=None,
        description="Start date (ISO or natural)",
        examples=["2024-11-01", "3 months ago"],
    )
    end_date: str | None = Field(
        default=None,
        description="End date (ISO or natural)",
        examples=["today"],
    )
    sort_by: str | None = Field(
        default=None,
        description="Sort by metric/dimension",
        examples=["bug_count"],
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="asc or desc (default: desc)",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Max rows (default: 1000)",
        examples=[10],
    )
    tests_limit: int | None = Field(
        default=None,
        gt=0,
        description="Limit metrics to most recent N tests (by end_at DESC)",
        examples=[5, 10],
    )

    @field_validator("filters", mode="before")
    @classmethod
    def validate_status_values(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate status filter values if present.

        Args:
            v: Filters dictionary

        Returns:
            Original filters if valid

        Raises:
            ValueError: If status contains invalid values
        """
        if v is None:
            return v

        if "status" in v:
            status_values = v["status"]
            # Convert single string to list for validation
            if isinstance(status_values, str):
                status_values = [status_values]

            if not isinstance(status_values, list):
                raise ValueError(
                    f"status filter must be a string or list of strings, got {type(status_values)}"
                )

            # Validate each status value
            invalid = [s for s in status_values if s not in VALID_TEST_STATUSES]
            if invalid:
                raise ValueError(
                    f"Invalid status values: {invalid}. "
                    f"Valid statuses: {', '.join(VALID_TEST_STATUSES)}"
                )

        return v


@mcp.tool()
async def query_metrics(
    metrics: Annotated[
        list[str] | str,
        Field(
            description=(
                "Metrics to measure. "
                "Accepts: list ['bug_count'], comma-separated 'bug_count,test_count', "
                "or single 'bug_count'"
            ),
            examples=[["bug_count"], "bug_count", "bug_count,test_count"],
        ),
    ],
    dimensions: Annotated[
        list[str] | str,
        Field(
            description=(
                "Dimensions to group by (max 2). "
                "Accepts: list ['feature', 'severity'], comma-separated 'feature,severity', "
                "or single 'feature'"
            ),
            examples=[["feature"], "feature", "feature,severity"],
        ),
    ],
    ctx: Context,
    filters: Annotated[
        dict[str, Any] | None,
        Field(
            description=(
                "Filter by dimension values, product_id, or status. "
                "Default status filter: excludes initialized and cancelled tests. "
                "Override with status=['initialized', 'cancelled', ...] to include them."
            ),
            examples=[
                {"severity": "critical"},
                {"product_id": 598},
                {"status": ["initialized", "cancelled"]},
            ],
        ),
    ] = None,
    start_date: Annotated[
        str | None,
        Field(description="Start date (ISO or natural)", examples=["2024-11-01", "3 months ago"]),
    ] = None,
    end_date: Annotated[
        str | None,
        Field(description="End date (ISO or natural)", examples=["today"]),
    ] = None,
    sort_by: Annotated[
        str | None,
        Field(description="Sort by metric/dimension", examples=["bug_count"]),
    ] = None,
    sort_order: Annotated[
        str,
        Field(pattern="^(asc|desc)$", description="asc or desc (default: desc)"),
    ] = "desc",
    limit: Annotated[
        int | None,
        Field(ge=1, description="Max rows (default: 1000)", examples=[10]),
    ] = None,
    tests_limit: Annotated[
        int | None,
        Field(
            gt=0,
            description=(
                "Limit metrics to most recent N tests (by end_at DESC). "
                "If combined with date filters, applies limit after date filtering."
            ),
            examples=[5, 10, 20],
        ),
    ] = None,
) -> dict[str, Any]:
    """Generate custom analytics report (pivot table).

    Default behavior: Excludes initialized and cancelled tests (unexecuted tests)
    to match get_product_quality_report behavior. Override with filters={'status': [...]}.
    Date filtering is based on test end_at (when test completed).

    Common patterns:
    - Most fragile features: dims=['feature'], metrics=['bugs_per_test']
    - Tester leaderboard: dims=['tester'], metrics=['bug_count']
    - Monthly trend: dims=['month'], metrics=['test_count']
    - Platform breakdown: dims=['platform'], metrics=['bug_count']
    - Product-specific: filters={'product_id': 598}, dims=['feature']
    - Recent activity: filters={'product_id': 598}, tests_limit=5 (last 5 tests)
    - Include all tests: filters={'status': ['running', 'locked', 'archived', 'cancelled',
      'customer_finalized', 'initialized']}

    Use get_analytics_capabilities() to see available dimensions/metrics.
    """
    # Normalize input formats (AI-friendly)
    parsed_metrics = parse_list_input(metrics)
    parsed_dimensions = parse_list_input(dimensions)

    if not parsed_metrics:
        raise ToolError(
            "❌ Invalid argument 'metrics': At least one metric is required\n"
            "💡 Provide metrics as: ['bug_count'], 'bug_count', or 'bug_count,test_count'"
        )
    if not parsed_dimensions:
        raise ToolError(
            "❌ Invalid argument 'dimensions': At least one dimension is required\n"
            "💡 Provide dimensions as: ['feature'], 'feature', or 'feature,severity'"
        )
    if len(parsed_dimensions) > 2:
        raise ToolError(
            f"❌ Too many dimensions: {len(parsed_dimensions)} provided, max 2 allowed\n"
            "💡 Use at most 2 dimensions for grouping"
        )

    # Validate input with Pydantic model
    try:
        validated_input = QueryMetricsInput(
            metrics=parsed_metrics,
            dimensions=parsed_dimensions,
            filters=filters,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            tests_limit=tests_limit,
        )
    except ValueError as e:
        # Pydantic validation error (including status validation)
        raise ToolError(
            f"❌ Invalid input: {str(e)}\n"
            f"ℹ️  Check your parameter values\n"
            f"💡 Ensure all parameters are in the correct format"
        ) from e

    reporter = ProgressReporter.from_context(ctx)

    async with get_service_context(ctx, AnalyticsService) as service:
        try:
            result = await service.query_metrics(
                metrics=parsed_metrics,
                dimensions=parsed_dimensions,
                filters=filters or {},
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                progress=reporter,
                tests_limit=validated_input.tests_limit,
            )
            # Convert QueryResponse to dict for MCP transport
            return result.model_dump(exclude_none=True)
        except ProductNotFoundException as e:
            # Product ID filter specified but product doesn't exist
            if isinstance(e.product_id, list):
                ids_str = ", ".join(str(pid) for pid in e.product_id)
                raise ToolError(
                    f"❌ Products not found: {ids_str}\n"
                    f"ℹ️  These products may not exist or you don't have access to them\n"
                    f"💡 Use the list_products tool to see available products"
                ) from None
            else:
                raise ToolError(
                    f"❌ Product ID '{e.product_id}' not found\n"
                    f"ℹ️  This product may not exist or you don't have access to it\n"
                    f"💡 Use the list_products tool to see available products"
                ) from None
        except ValueError as e:
            # Validation errors (too many dimensions, invalid keys, etc.)
            raise ToolError(f"❌ Invalid query parameters\nℹ️  {str(e)}") from None
        except Exception as e:
            # Unexpected errors
            raise ToolError(
                f"❌ Failed to execute analytics query\n"
                f"ℹ️  Error: {str(e)}\n"
                f"💡 Try simplifying your query or narrowing the date range"
            ) from None
