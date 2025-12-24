"""User Service - Business logic for user operations.

This service handles user-related business logic including:
- Query users (testers and customers)
- Get top contributors
- Format responses for MCP/REST

STORY-037: Data Serving Layer (MCP Tools + REST API)
Epic: EPIC-005 (Data Enhancement and Serving)
"""

from typing import Any

from testio_mcp.models.orm import User
from testio_mcp.repositories.user_repository import UserRepository
from testio_mcp.services.base_service import BaseService


class UserService(BaseService):
    """Service for user operations.

    Business logic for users:
    - Query users by type (tester, customer)
    - Get top contributors
    - Format responses for MCP/REST

    Inherits from BaseService for:
    - Standard constructor (client injection)

    Note: UserService uses repository pattern (not API client directly).
    """

    def __init__(self, user_repo: UserRepository) -> None:
        """Initialize service.

        Args:
            user_repo: UserRepository instance
        """
        # UserService doesn't need client (repository handles data)
        super().__init__(client=None)  # type: ignore[arg-type]
        self.user_repo = user_repo

    async def list_users(
        self,
        user_type: str | None = None,
        days: int = 365,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> dict[str, Any]:
        """List users with optional type filter, pagination, and sorting.

        STORY-055: Adds sorting support.
        STORY-058: Returns last_activity (meaningful timestamp) for all queries.

        Args:
            user_type: Optional filter ("tester", "customer"). If None, all types.
            days: Number of days to look back (default: 365, last year)
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)
            sort_by: Field to sort by, default: None
            sort_order: Sort direction (asc, desc), default: asc

        Returns:
            {
                "users": [...],
                "total": int,           # Items in current page
                "total_count": int,     # Total matching results across all pages
                "offset": int,          # Actual offset used
                "has_more": bool,       # Pagination heuristic
                "filter": {"user_type": str | null, "days": int}
            }
        """
        # STORY-058: Always use query_users (now computes last_activity for all queries)
        user_dicts = await self.user_repo.query_users(
            user_type=user_type,
            days=days,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page,
            offset=offset,
        )

        # Get total count for pagination metadata
        total_count = await self.user_repo.count_active_users(user_type=user_type, days=days)

        # Calculate actual offset
        actual_offset = offset + (page - 1) * per_page

        # Determine has_more (exact: check if more results exist beyond current page)
        has_more = (actual_offset + len(user_dicts)) < total_count

        return {
            "users": [self._format_user_with_activity(u) for u in user_dicts],
            "total": len(user_dicts),
            "total_count": total_count,
            "offset": actual_offset,
            "has_more": has_more,
            "filter": {"user_type": user_type, "days": days},
        }

    async def get_top_contributors(
        self,
        user_type: str = "tester",
        limit: int = 10,
        days: int | None = None,
    ) -> dict[str, Any]:
        """Get top contributors by activity count.

        Args:
            user_type: "tester" (bugs) or "customer" (tests)
            limit: Max number of users to return (default: 10)
            days: Optional time window (last N days). If None, all time.

        Returns:
            {
                "contributors": [
                    {
                        "user": {id, username, user_type, first_seen, last_seen},
                        "count": int
                    },
                    ...
                ],
                "total": int,
                "filter": {"user_type": str, "limit": int, "days": int | null}
            }
        """
        contributors = await self.user_repo.get_top_contributors(
            user_type=user_type, limit=limit, days=days
        )

        return {
            "contributors": [
                {"user": self._format_user(user), "count": count} for user, count in contributors
            ],
            "total": len(contributors),
            "filter": {"user_type": user_type, "limit": limit, "days": days},
        }

    async def get_user_summary(self, user_id: int) -> dict[str, Any]:
        """Get user summary with metadata and activity counts.

        STORY-057: Added for get_user_summary tool.

        SQLite-only (no API calls). Uses cached data with counts computed via subqueries.
        Returns different activity metrics based on user_type:
        - Customer: tests_created_count, tests_submitted_count
        - Tester: bugs_reported_count

        Args:
            user_id: User identifier

        Returns:
            User summary with metadata and activity counts

        Raises:
            UserNotFoundException: If user not found

        Example:
            >>> summary = await service.get_user_summary(123)
            >>> print(summary["bugs_reported_count"])
            42
        """
        from datetime import UTC, datetime

        from testio_mcp.exceptions import UserNotFoundException

        user_with_activity = await self.user_repo.get_user_with_activity(user_id)

        if not user_with_activity:
            raise UserNotFoundException(user_id)

        # Add data_as_of timestamp for staleness visibility (AC requirement)
        return {
            **user_with_activity,
            "data_as_of": datetime.now(UTC).isoformat(),
        }

    def _format_user(self, user: User) -> dict[str, Any]:
        """Format user for response (legacy - for get_top_contributors).

        Args:
            user: User ORM model

        Returns:
            Formatted user dict
        """
        return {
            "id": user.id,
            "username": user.username,
            "user_type": user.user_type,
            "first_seen": user.first_seen.isoformat(),
            "last_seen": user.last_seen.isoformat(),
        }

    def _format_user_with_activity(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        """Format user with computed last_activity for response.

        STORY-058: Replaces last_seen with meaningful last_activity timestamp.

        Args:
            user_dict: Dict with "user" (User ORM model) and "last_activity" (datetime | None)

        Returns:
            Formatted user dict with last_activity instead of last_seen
        """
        from datetime import datetime

        user = user_dict["user"]
        last_activity = user_dict["last_activity"]

        return {
            "id": user.id,
            "username": user.username,
            "user_type": user.user_type,
            "first_seen": user.first_seen.isoformat(),
            "last_activity": (
                last_activity.isoformat()
                if isinstance(last_activity, datetime)
                else user.last_seen.isoformat()
            ),
        }
