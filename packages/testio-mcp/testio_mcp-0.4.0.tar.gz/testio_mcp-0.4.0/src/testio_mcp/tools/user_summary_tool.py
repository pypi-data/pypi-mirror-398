"""MCP tool for getting user summary.

This module implements the get_user_summary tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to UserService
4. Converts exceptions to user-friendly error format

STORY-057: Add Summary Tools (Epic 008)
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import TestIOAPIError, UserNotFoundException
from testio_mcp.server import mcp
from testio_mcp.services.user_service import UserService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.validators import coerce_to_int


class GetUserSummaryInput(BaseModel):
    """Input validation for get_user_summary tool.

    Accepts user_id as int or string, coerces to int for validation.
    """

    user_id: int = Field(
        gt=0,
        description="User ID from TestIO (e.g., 123). Use list_users to find IDs.",
    )

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_user_id(cls, v: Any) -> int:
        """Coerce user_id from string to int if needed."""
        return coerce_to_int(v)


class UserSummaryOutput(BaseModel):
    """User summary with metadata and activity counts.

    This is the output model for the get_user_summary tool.
    Returns different fields based on user_type:
    - Customer: tests_created_count, tests_submitted_count
    - Tester: bugs_reported_count
    """

    id: int = Field(description="User ID", examples=[123])
    username: str = Field(description="Username", examples=["john_doe"])
    user_type: str = Field(
        description="User type (customer or tester)",
        examples=["customer"],
    )
    tests_created_count: int | None = Field(
        default=None,
        description="Total tests created by this customer user",
        ge=0,
        examples=[15],
    )
    tests_submitted_count: int | None = Field(
        default=None,
        description="Total tests submitted by this customer user",
        ge=0,
        examples=[12],
    )
    bugs_reported_count: int | None = Field(
        default=None,
        description="Total bugs reported by this tester user",
        ge=0,
        examples=[42],
    )
    last_activity: str | None = Field(
        default=None,
        description="Timestamp of most recent activity",
        examples=["2025-11-28T10:30:00Z"],
    )
    data_as_of: str = Field(
        description="Timestamp when this summary was generated",
        examples=["2025-11-28T10:30:05Z"],
    )


@mcp.tool(output_schema=inline_schema_refs(UserSummaryOutput.model_json_schema()))
async def get_user_summary(
    user_id: Annotated[
        int,
        Field(
            gt=0,
            description="User ID from TestIO (e.g., 123). Use list_users to find IDs.",
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """Get a summary of a user including metadata and activity counts.

    Returns user metadata (id, username, user_type) along with activity counts:
    - For customers: tests_created_count, tests_submitted_count, last_activity
    - For testers: bugs_reported_count, last_activity

    Uses SQLite cache (no API calls). Excludes recent activity details to prevent context bloat.
    """
    # Validate and coerce input (accepts string or int)
    try:
        validated_input = GetUserSummaryInput(user_id=user_id)
        user_id = validated_input.user_id
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid user_id: {e}\n"
            f"ℹ️  user_id must be a positive integer\n"
            f"💡 Use an integer like 123, not a string like '123.5'"
        ) from e

    # Create service with managed AsyncSession lifecycle
    async with get_service_context(ctx, UserService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            result = await service.get_user_summary(user_id)

            # Validate output with Pydantic
            validated = UserSummaryOutput(**result)
            return validated.model_dump(by_alias=True, exclude_none=True)

        except UserNotFoundException:
            # Convert domain exception to ToolError with user-friendly message
            raise ToolError(
                f"❌ User ID '{user_id}' not found\n"
                f"ℹ️  The user may not exist or has not been synced yet\n"
                f"💡 Use list_users to see available users"
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
                f"ℹ️  An unexpected error occurred while fetching user summary\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
