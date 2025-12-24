"""User Repository - Data access layer for user-related database operations.

This repository handles user extraction from bug reports (testers) and test metadata
(customers) with unified deduplication logic.

STORY-036: User Metadata Extraction
Epic: EPIC-005 (Data Enhancement and Serving)
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import col, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import User
from testio_mcp.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for User entity operations.

    Handles user extraction from both bug reports (testers) and test metadata (customers)
    with unified deduplication logic.

    Inherits from BaseRepository for:
    - Standard constructor (session, client injection)
    - Async context manager pattern
    - Resource cleanup in finally blocks

    Attributes:
        session: AsyncSession for ORM operations (inherited from BaseRepository)
        client: TestIO API client (not used for user sync)
        customer_id: Customer ID for multi-tenant isolation
    """

    # Override type hint to indicate session is always present in this repository
    session: AsyncSession

    def __init__(self, session: AsyncSession, client: TestIOClient, customer_id: int) -> None:
        """Initialize repository.

        Args:
            session: SQLModel AsyncSession (managed by caller)
            client: TestIO API client (not used for user sync)
            customer_id: Customer ID for multi-tenant isolation
        """
        super().__init__(session, client, customer_id)

    async def bulk_upsert_users(
        self,
        usernames: set[str],
        user_type: str,
        raw_data_map: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, int]:
        """Bulk upsert users with single IN query - avoids nested flush issues.

        This method is designed for batch operations where you need to upsert many users
        at once without causing nested flush errors. It:
        1. Does a single IN query to get all existing users (O(1) DB round-trip)
        2. Creates missing users in-memory
        3. Does a single flush to persist new users
        4. Returns a username -> user_id map for foreign key references

        Args:
            usernames: Set of usernames to upsert
            user_type: "tester" or "customer" (applies to new users only)
            raw_data_map: Optional mapping of username -> raw API data

        Returns:
            Dictionary mapping username -> user.id (for all usernames, existing and new)

        Example:
            # Extract all usernames from bugs first
            usernames = {bug["author"]["name"] for bug in bugs if bug.get("author")}
            raw_data_map = {bug["author"]["name"]: bug["author"] for bug in bugs}

            # Single bulk operation
            user_id_map = await user_repo.bulk_upsert_users(
                usernames=usernames,
                user_type="tester",
                raw_data_map=raw_data_map
            )

            # Use map for bug rows
            for bug in bugs:
                user_id = user_id_map.get(bug["author"]["name"])
        """
        if not usernames:
            return {}

        raw_data_map = raw_data_map or {}
        now = datetime.now(UTC)
        user_id_map: dict[str, int] = {}

        # Step 1: Bulk-load existing users with single IN query
        result = await self.session.exec(
            select(User).where(
                col(User.username).in_(usernames),
                col(User.customer_id) == self.customer_id,
            )
        )
        existing_users = result.all()

        # Build map and update last_seen for existing users
        for user in existing_users:
            user.last_seen = now
            if user.username in raw_data_map:
                user.raw_data = json.dumps(raw_data_map[user.username])
            if user.id is not None:
                user_id_map[user.username] = user.id

        # Step 2: Create missing users in-memory
        existing_usernames = {u.username for u in existing_users}
        missing_usernames = usernames - existing_usernames

        new_users: list[User] = []
        for username in missing_usernames:
            raw_data = raw_data_map.get(username, {"name": username})
            user = User(
                customer_id=self.customer_id,
                username=username,
                user_type=user_type,
                raw_data=json.dumps(raw_data),
                first_seen=now,
                last_seen=now,
            )
            new_users.append(user)

        # Step 3: Add all new users and flush once
        if new_users:
            self.session.add_all(new_users)
            await self.session.flush()  # Single flush to get IDs

            # Add new user IDs to map
            for user in new_users:
                if user.id is not None:
                    user_id_map[user.username] = user.id

        logger.debug(
            f"Bulk upserted users: {len(existing_users)} existing, "
            f"{len(new_users)} new, total map size: {len(user_id_map)}"
        )

        return user_id_map

    async def upsert_user(
        self, username: str, user_type: str, raw_data: dict[str, str] | None = None
    ) -> User | None:
        """Extract and upsert user with deduplication by username.

        Single unified method for extracting both tester and customer users.

        Deduplication strategy:
        - Lookup by username (unique constraint)
        - If exists: Update last_seen, preserve user_type (first wins)
        - If not exists: Create new user

        Args:
            username: User's name/username (required)
            user_type: "tester" or "customer" (required)
            raw_data: Optional raw API data (defaults to {"name": username})

        Returns:
            User ORM model (created or updated), or None if username is empty

        Examples:
            # From bug.author.name
            user = await user_repo.upsert_user(
                username=bug_data["author"]["name"],
                user_type="tester",
                raw_data=bug_data["author"]
            )

            # From test.created_by
            user = await user_repo.upsert_user(
                username=test_data["created_by"],
                user_type="customer"
            )
        """
        if not username:
            return None

        # Default raw_data if not provided
        if raw_data is None:
            raw_data = {"name": username}

        # Check if user exists (deduplication by username within customer)
        result = await self.session.exec(
            select(User).where(
                col(User.username) == username, col(User.customer_id) == self.customer_id
            )
        )
        existing = result.first()

        now = datetime.now(UTC)

        if existing:
            # Update existing user
            existing.last_seen = now
            existing.raw_data = json.dumps(raw_data)
            # Preserve existing user_type (first wins)
            # Note: No commit here - caller manages transaction for batching
            return existing
        else:
            # Create new user
            user = User(
                customer_id=self.customer_id,
                username=username,
                user_type=user_type,
                raw_data=json.dumps(raw_data),
                first_seen=now,
                last_seen=now,
            )
            self.session.add(user)
            # Note: No commit here - caller manages transaction for batching
            # Flush to make user ID available for foreign key references
            await self.session.flush()
            return user

    async def get_top_contributors(
        self, user_type: str = "tester", limit: int = 10, days: int | None = None
    ) -> list[tuple[User, int]]:
        """Get top contributors by activity count (bugs for testers, tests for customers).

        Args:
            user_type: "tester" (bugs) or "customer" (tests)
            limit: Max number of users to return
            days: Optional time window (last N days). If None, all time.

        Returns:
            List of (User, count) tuples, sorted by count descending
        """
        from testio_mcp.models.orm import Bug, Test

        if user_type == "tester":
            # Count bugs for testers
            query = (
                select(User, func.count(col(Bug.id)).label("count"))
                .join(Bug, col(Bug.reported_by_user_id) == col(User.id))
                .where(
                    col(User.user_type) == "tester",
                    col(User.customer_id) == self.customer_id,
                )
                .group_by(col(User.id))
                .order_by(desc("count"))
                .limit(limit)
            )

            if days:
                from datetime import timedelta

                threshold = datetime.now(UTC) - timedelta(days=days)
                # Filter by User.last_seen as activity proxy
                query = query.where(col(User.last_seen) >= threshold)
        else:
            # Count tests created by customers
            query = (
                select(User, func.count(col(Test.id)).label("count"))
                .join(Test, col(Test.created_by_user_id) == col(User.id))
                .where(
                    col(User.user_type) == "customer",
                    col(User.customer_id) == self.customer_id,
                )
                .group_by(col(User.id))
                .order_by(desc("count"))
                .limit(limit)
            )

            if days:
                from datetime import timedelta

                threshold = datetime.now(UTC) - timedelta(days=days)
                # STORY-054: Use end_at instead of created_at (removed)
                query = query.where(col(Test.end_at) >= threshold)

        # Execute query
        result = await self.session.exec(query)
        rows = result.all()

        # Return list of (User, count) tuples
        return [(row[0], row[1]) for row in rows]

    async def get_active_users(
        self,
        user_type: str | None = None,
        days: int = 30,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Get users active in last N days with activity-based ordering via JOIN queries.

        Ordering Strategy:
        - Testers: ORDER BY last_seen DESC (activity proxy)
        - Customers: ORDER BY last_seen DESC (activity proxy)
        - Both types: ORDER BY last_seen DESC

        Note: Activity-based JOIN ordering (by MAX(bugs.created_at) or MAX(tests.end_at))
        was considered but deferred for simplicity. last_seen provides a reasonable
        activity proxy since it's updated when users report bugs or create tests.

        Args:
            user_type: Optional filter ("tester", "customer"). If None, all types.
            days: Number of days to look back
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)

        Returns:
            List of User ORM models for requested page
        """
        from datetime import timedelta

        # Calculate actual offset
        actual_offset = offset + (page - 1) * per_page

        threshold = datetime.now(UTC) - timedelta(days=days)
        query = select(User).where(
            col(User.last_seen) >= threshold, col(User.customer_id) == self.customer_id
        )

        if user_type:
            query = query.where(col(User.user_type) == user_type)

        query = query.order_by(desc(col(User.last_seen))).limit(per_page).offset(actual_offset)
        result = await self.session.exec(query)
        return list(result.all())

    async def query_users(
        self,
        user_type: str | None = None,
        days: int = 30,
        sort_by: str | None = None,
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query users with sorting support and computed last_activity.

        STORY-055: Adds sorting with computed last_activity subquery.
        STORY-058: Returns last_activity for all queries (not just for sorting).

        Args:
            user_type: Optional filter ("tester", "customer"). If None, all types.
            days: Number of days to look back
            sort_by: Field to sort by (username, user_type, last_activity, first_seen)
            sort_order: Sort direction (asc, desc), default: asc
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 100)
            offset: Additional offset (default: 0)

        Returns:
            List of dicts with User data + computed last_activity:
            {
                "user": User ORM model,
                "last_activity": datetime | None
            }

        Raises:
            ValueError: If sort_by field is invalid
        """
        from datetime import timedelta

        from testio_mcp.models.orm.bug import Bug
        from testio_mcp.models.orm.test import Test

        # Validate sort_by field
        VALID_SORT_FIELDS = ["username", "user_type", "last_activity", "first_seen"]
        if sort_by and sort_by not in VALID_SORT_FIELDS:
            raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of: {VALID_SORT_FIELDS}")

        # Calculate actual offset
        actual_offset = offset + (page - 1) * per_page

        threshold = datetime.now(UTC) - timedelta(days=days)

        # STORY-058: Always compute last_activity (not just for sorting)
        # For testers: MAX(Test.end_at) via Bug.reported_by_user_id -> Test
        # For customers: MAX(Test.end_at) via created_by_user_id OR submitted_by_user_id
        # Note: Bug.created_at was dropped in STORY-054 (always NULL), so use Test.end_at

        # Subquery for tester activity (via bugs)
        tester_activity_subquery = (
            select(func.max(Test.end_at))
            .select_from(Bug)
            .join(Test, Bug.test_id == Test.id)  # type: ignore[arg-type]
            .where(Bug.reported_by_user_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )

        # Subquery for customer activity (created tests)
        customer_created_subquery = (
            select(func.max(Test.end_at))
            .where(Test.created_by_user_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )

        # Subquery for customer activity (submitted tests)
        customer_submitted_subquery = (
            select(func.max(Test.end_at))
            .where(Test.submitted_by_user_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )

        # Combine all activity sources: bugs, created tests, submitted tests
        # Use greatest() to get the maximum across all sources (handles NULL gracefully)
        last_activity_subquery = func.coalesce(
            func.max(
                tester_activity_subquery,
                customer_created_subquery,
                customer_submitted_subquery,
            ),
            User.last_seen,  # Fallback to last_seen if no activity
        ).label("last_activity")

        # Base query: SELECT User, last_activity
        query = select(User, last_activity_subquery).where(
            col(User.last_seen) >= threshold, col(User.customer_id) == self.customer_id
        )

        if user_type:
            query = query.where(col(User.user_type) == user_type)

        # Apply sorting
        if sort_by == "last_activity":
            if sort_order == "desc":
                query = query.order_by(desc(last_activity_subquery))
            else:
                query = query.order_by(last_activity_subquery.asc())
        elif sort_by:
            # Simple field sorting (username, user_type, first_seen)
            sort_column = getattr(User, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(col(sort_column).asc())
        else:
            # Default: sort by username ascending
            query = query.order_by(col(User.username).asc())

        # Apply pagination
        query = query.limit(per_page).offset(actual_offset)

        # Execute query
        result = await self.session.exec(query)
        rows = result.all()

        # Transform rows to dict format
        return [{"user": row[0], "last_activity": row[1]} for row in rows]

    async def count_active_users(self, user_type: str | None = None, days: int = 30) -> int:
        """Count active users (no JOIN needed for count).

        Args:
            user_type: Optional filter ("tester", "customer"). If None, all types.
            days: Number of days to look back

        Returns:
            Total count of active users matching the filters
        """
        from datetime import timedelta

        threshold = datetime.now(UTC) - timedelta(days=days)

        query = (
            select(func.count())
            .select_from(User)
            .where(col(User.last_seen) >= threshold, col(User.customer_id) == self.customer_id)
        )

        if user_type:
            query = query.where(col(User.user_type) == user_type)

        result = await self.session.exec(query)
        return result.one()

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username to look up

        Returns:
            User ORM model or None if not found
        """
        result = await self.session.exec(
            select(User).where(
                col(User.username) == username, col(User.customer_id) == self.customer_id
            )
        )
        return result.first()

    async def get_user_with_activity(self, user_id: int) -> dict[str, Any] | None:
        """Get user with activity counts based on user type.

        STORY-057: Added for get_user_summary tool.

        For customers: tests_created_count, tests_submitted_count
        For testers: bugs_reported_count

        Args:
            user_id: User identifier

        Returns:
            User dictionary with metadata and activity counts, or None if not found

        Example:
            >>> await repo.get_user_with_activity(123)
            {
                "id": 123,
                "username": "john_doe",
                "user_type": "customer",
                "tests_created_count": 15,
                "tests_submitted_count": 12,
                "last_activity": "2025-11-28T10:30:00Z"
            }
        """
        from testio_mcp.models.orm import Bug, Test

        # Get user
        result = await self.session.exec(
            select(User).where(User.id == user_id, User.customer_id == self.customer_id)
        )
        user = result.first()

        if not user:
            return None

        # Base user info
        user_dict: dict[str, Any] = {
            "id": user.id,
            "username": user.username,
            "user_type": user.user_type,
        }

        # Activity counts and last_activity based on user_type
        if user.user_type == "customer":
            # Count tests created
            tests_created_stmt = (
                select(func.count())
                .select_from(Test)
                .where(Test.created_by_user_id == user.id, Test.customer_id == self.customer_id)
            )
            tests_created_result = await self.session.exec(tests_created_stmt)
            tests_created_count = tests_created_result.one()

            # Count tests submitted
            tests_submitted_stmt = (
                select(func.count())
                .select_from(Test)
                .where(Test.submitted_by_user_id == user.id, Test.customer_id == self.customer_id)
            )
            tests_submitted_result = await self.session.exec(tests_submitted_stmt)
            tests_submitted_count = tests_submitted_result.one()

            # Get most recent activity (created or submitted test)
            last_created_stmt = (
                select(Test.synced_at)
                .where(Test.created_by_user_id == user.id, Test.customer_id == self.customer_id)
                .order_by(desc(Test.synced_at))
                .limit(1)
            )
            last_created_result = await self.session.exec(last_created_stmt)
            last_created = last_created_result.first()

            last_submitted_stmt = (
                select(Test.synced_at)
                .where(Test.submitted_by_user_id == user.id, Test.customer_id == self.customer_id)
                .order_by(desc(Test.synced_at))
                .limit(1)
            )
            last_submitted_result = await self.session.exec(last_submitted_stmt)
            last_submitted = last_submitted_result.first()

            # Use the most recent of the two
            last_activity = max(
                filter(None, [last_created, last_submitted]), default=user.last_seen
            )

            user_dict.update(
                {
                    "tests_created_count": tests_created_count,
                    "tests_submitted_count": tests_submitted_count,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                }
            )
        else:  # tester
            # Count bugs reported
            bugs_reported_stmt = (
                select(func.count())
                .select_from(Bug)
                .where(Bug.reported_by_user_id == user.id, Bug.customer_id == self.customer_id)
            )
            bugs_reported_result = await self.session.exec(bugs_reported_stmt)
            bugs_reported_count = bugs_reported_result.one()

            # Get most recent bug reported
            last_bug_stmt = (
                select(Bug.synced_at)
                .where(Bug.reported_by_user_id == user.id, Bug.customer_id == self.customer_id)
                .order_by(desc(Bug.synced_at))
                .limit(1)
            )
            last_bug_result = await self.session.exec(last_bug_stmt)
            last_bug = last_bug_result.first()

            last_activity = last_bug or user.last_seen

            user_dict.update(
                {
                    "bugs_reported_count": bugs_reported_count,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                }
            )

        return user_dict
