"""MCP tool for listing features.

This module implements the list_features tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Uses async context manager for resource cleanup
2. Delegates to FeatureService
3. Converts exceptions to user-friendly error format

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
Epic: EPIC-005 (Data Enhancement and Serving)
"""

from typing import Annotated, Any, Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from testio_mcp.schemas.api import PaginationInfo
from testio_mcp.server import mcp
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs


# Pydantic Models for output schema
class FeatureSummary(BaseModel):
    """Feature summary."""

    id: int = Field(description="Feature ID")
    title: str = Field(description="Feature name")
    description: str | None = Field(default=None, description="Description")
    howtofind: str | None = Field(default=None, description="How to find")
    user_story_count: int = Field(description="User story count")
    test_count: int = Field(description="Test count", ge=0)
    bug_count: int = Field(description="Bug count", ge=0)


class ListFeaturesOutput(BaseModel):
    """List features output."""

    product_id: int = Field(description="Product ID")
    pagination: PaginationInfo = Field(description="Pagination metadata")
    features: list[FeatureSummary] = Field(description="Feature list")
    total: int = Field(description="Total features in page", ge=0)


# MCP Tool


@mcp.tool(output_schema=inline_schema_refs(ListFeaturesOutput.model_json_schema()))
async def list_features(
    ctx: Context,
    product_id: Annotated[int, Field(description="Product ID", gt=0, examples=[25073])],
    page: Annotated[int, Field(ge=1, description="Page number (1-indexed)")] = 1,
    per_page: Annotated[
        int, Field(ge=1, le=200, description="Items per page (default: 100, max: 200)")
    ] = 0,  # 0 means use settings default
    offset: Annotated[
        int,
        Field(
            ge=0,
            description="Starting offset (0-indexed). "
            "Combines with page: offset + (page-1)*per_page",
        ),
    ] = 0,
    sort_by: Annotated[
        Literal["title", "test_count", "bug_count", "last_synced"] | None,
        Field(description="Sort field. Values: title, test_count, bug_count, last_synced"),
    ] = None,
    sort_order: Annotated[
        Literal["asc", "desc"], Field(description="Sort order. Values: asc, desc")
    ] = "asc",
    has_user_stories: Annotated[
        bool | None,
        Field(
            description="Filter by user story presence. "
            "True: only features with user stories. False/None: all features."
        ),
    ] = None,
) -> dict[str, Any]:
    """List features for a product with pagination and sorting.

    Returns feature ID, title, description, how-to-find, user story/test/bug counts.
    Filter by has_user_stories to find features with documented user stories.
    """
    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, FeatureService) as service:
        try:
            # Get settings for default page size
            from testio_mcp.config import settings

            # Use default per_page from settings if not specified (0 = use default)
            effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

            result = await service.list_features(
                product_id=product_id,
                page=page,
                per_page=effective_per_page,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
                has_user_stories=has_user_stories,
            )

            # Build PaginationInfo
            total_count = result.get("total_count", 0)
            actual_offset = result.get("offset", 0)
            has_more = result.get("has_more", False)
            features = result.get("features", [])

            start_index = actual_offset
            end_index = actual_offset + len(features) - 1 if features else -1

            output = ListFeaturesOutput(
                product_id=product_id,
                pagination=PaginationInfo(
                    page=page,
                    per_page=effective_per_page,
                    offset=actual_offset,
                    start_index=start_index,
                    end_index=end_index,
                    total_count=total_count,
                    has_more=has_more,
                ),
                features=[FeatureSummary(**f) for f in features],
                total=len(features),
            )

            return output.model_dump(exclude_none=True)

        except Exception as e:
            # Convert to ToolError with user-friendly message
            raise ToolError(
                f"❌ Failed to list features for product {product_id}\n"
                f"ℹ️  Error: {str(e)}\n"
                f"💡 Ensure features have been synced for this product"
            ) from e
