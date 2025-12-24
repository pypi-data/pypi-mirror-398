"""MCP tool for getting feature summary.

This module implements the get_feature_summary tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to FeatureService
4. Converts exceptions to user-friendly error format

STORY-057: Add Summary Tools (Epic 008)
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import FeatureNotFoundException, TestIOAPIError
from testio_mcp.schemas.api import ProductInfo
from testio_mcp.server import mcp
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.validators import coerce_to_int


class GetFeatureSummaryInput(BaseModel):
    """Input validation for get_feature_summary tool.

    Accepts feature_id as int or string, coerces to int for validation.
    """

    feature_id: int = Field(
        gt=0,
        description="Feature ID from TestIO (e.g., 123). Use list_features to find IDs.",
    )

    @field_validator("feature_id", mode="before")
    @classmethod
    def coerce_feature_id(cls, v: Any) -> int:
        """Coerce feature_id from string to int if needed."""
        return coerce_to_int(v)


class FeatureSummaryOutput(BaseModel):
    """Feature summary with metadata, user stories, and computed counts.

    This is the output model for the get_feature_summary tool,
    providing feature metadata and aggregated statistics.
    """

    id: int = Field(description="Feature ID", examples=[123])
    title: str = Field(description="Feature title", examples=["User Authentication"])
    description: str | None = Field(
        default=None,
        description="Feature description",
    )
    howtofind: str | None = Field(
        default=None,
        description="How to find this feature in the application",
    )
    user_stories: list[str] = Field(
        description="Embedded user stories (list of title strings)",
        examples=[["As a user, I want to log in", "As an admin, I want to manage users"]],
    )
    test_count: int = Field(
        description="Total number of tests covering this feature",
        ge=0,
        examples=[15],
    )
    bug_count: int = Field(
        description="Total number of bugs related to this feature",
        ge=0,
        examples=[42],
    )
    product: ProductInfo = Field(
        description="Associated product information",
    )
    data_as_of: str = Field(
        description="Timestamp when this summary was generated",
        examples=["2025-11-28T10:30:05Z"],
    )


@mcp.tool(output_schema=inline_schema_refs(FeatureSummaryOutput.model_json_schema()))
async def get_feature_summary(
    feature_id: Annotated[
        int,
        Field(
            gt=0,
            description="Feature ID from TestIO (e.g., 123). Use list_features to find IDs.",
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """Get a summary of a feature including metadata, user stories, and computed counts.

    Returns feature metadata (id, title, description, howtofind) along with:
    - user_stories: Embedded list of user story titles
    - test_count: Total tests covering this feature
    - bug_count: Total bugs related to this feature
    - product: Associated product information

    Uses SQLite cache (no API calls). Excludes recent bugs to prevent context bloat.
    """
    # Validate and coerce input (accepts string or int)
    try:
        validated_input = GetFeatureSummaryInput(feature_id=feature_id)
        feature_id = validated_input.feature_id
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid feature_id: {e}\n"
            f"ℹ️  feature_id must be a positive integer\n"
            f"💡 Use an integer like 123, not a string like '123.5'"
        ) from e

    # Create service with managed AsyncSession lifecycle
    async with get_service_context(ctx, FeatureService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            result = await service.get_feature_summary(feature_id)

            # Validate output with Pydantic
            validated = FeatureSummaryOutput(**result)
            return validated.model_dump(by_alias=True, exclude_none=True)

        except FeatureNotFoundException:
            # Convert domain exception to ToolError with user-friendly message
            raise ToolError(
                f"❌ Feature ID '{feature_id}' not found\n"
                f"ℹ️  The feature may not exist or has not been synced yet\n"
                f"💡 Use list_features to see available features for a product"
            ) from None

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
                f"ℹ️  An unexpected error occurred while fetching feature summary\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
