"""MCP tool for listing users.

This module implements the list_users tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Uses async context manager for resource cleanup
2. Delegates to UserService
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
from testio_mcp.services.user_service import UserService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs

# Type alias for user types
UserType = Literal["tester", "customer"]


# Pydantic Models for output schema
class UserSummary(BaseModel):
    """User summary with activity timestamp (STORY-058)."""

    id: int = Field(description="User ID")
    username: str = Field(description="Username")
    user_type: str = Field(description="Type: tester or customer")
    first_seen: str = Field(
        description="First seen timestamp (ISO8601, cache-based - when user first synced)"
    )
    last_activity: str = Field(
        description="Last activity timestamp (ISO8601). "
        "For customers: MAX(tests.end_at) where created/submitted. "
        "For testers: MAX(tests.end_at) via bugs reported."
    )


class ListUsersFilter(BaseModel):
    """Filter information for list_users query."""

    user_type: str | None = Field(default=None, description="User type filter")
    days: int = Field(description="Days lookback period")


class ListUsersOutput(BaseModel):
    """List users output."""

    users: list[UserSummary] = Field(description="User list")
    pagination: PaginationInfo = Field(description="Pagination metadata")
    total: int = Field(description="Total users in page", ge=0)
    filter: ListUsersFilter = Field(description="Applied filters")
    hint: str | None = Field(default=None, description="Guidance when empty")


# MCP Tool


@mcp.tool(output_schema=inline_schema_refs(ListUsersOutput.model_json_schema()))
async def list_users(
    ctx: Context,
    user_type: Annotated[
        UserType | None,
        Field(
            description="Filter by type. Values: tester (bug reporters), customer (test creators)"
        ),
    ] = None,
    days: Annotated[int, Field(description="Days lookback for active users", gt=0)] = 365,
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
        Literal["username", "user_type", "last_activity", "first_seen"] | None,
        Field(description="Sort field. Values: username, user_type, last_activity, first_seen"),
    ] = None,
    sort_order: Annotated[
        Literal["asc", "desc"], Field(description="Sort order. Values: asc, desc")
    ] = "asc",
) -> dict[str, Any]:
    """List users (testers and customers) with filtering, pagination, and sorting.

    Extracted from bug reports (testers) and test metadata (customers).
    """
    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, UserService) as service:
        try:
            # Get settings for default page size
            from testio_mcp.config import settings

            # Use default per_page from settings if not specified (0 = use default)
            effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

            result = await service.list_users(
                user_type=user_type,
                days=days,
                page=page,
                per_page=effective_per_page,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            # Build PaginationInfo
            total_count = result.get("total_count", 0)
            actual_offset = result.get("offset", 0)
            has_more = result.get("has_more", False)
            users = result.get("users", [])

            start_index = actual_offset
            end_index = actual_offset + len(users) - 1 if users else -1

            # Add helpful hint when results are empty (FIX: Usability Test Task 8)
            hint = None
            if not users and user_type == "tester":
                # No testers found
                hint = (
                    "ℹ️  No testers found. Testers are extracted from bug reports. "
                    "💡 Ensure bugs have been synced (bugs must have 'author' "
                    "field in API response)"
                )
            elif not users and user_type == "customer":
                # No customers found
                hint = (
                    "ℹ️  No customers found. Customers are extracted from test metadata. "
                    "💡 Ensure tests have been synced for this product"
                )
            elif not users and not user_type:
                # No users at all
                hint = (
                    "ℹ️  No users found in the system. "
                    "💡 Users are extracted during bug and test sync"
                )

            output = ListUsersOutput(
                users=[UserSummary(**u) for u in users],
                pagination=PaginationInfo(
                    page=page,
                    per_page=effective_per_page,
                    offset=actual_offset,
                    start_index=start_index,
                    end_index=end_index,
                    total_count=total_count,
                    has_more=has_more,
                ),
                total=len(users),
                filter=ListUsersFilter(
                    user_type=user_type,
                    days=days,
                ),
                hint=hint,
            )

            return output.model_dump(exclude_none=True)

        except Exception as e:
            # Convert to ToolError with user-friendly message
            raise ToolError(
                f"❌ Failed to list users\n"
                f"ℹ️  Error: {str(e)}\n"
                f"💡 Ensure bug data has been synced to extract user metadata"
            ) from e
