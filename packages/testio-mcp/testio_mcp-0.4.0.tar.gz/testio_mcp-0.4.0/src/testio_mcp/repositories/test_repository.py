"""
Test Repository - Data access layer for test-related database operations.

This repository handles all ORM queries for tests using SQLModel.
It maintains clean separation between business logic (services) and data access.

MVP: Uses instance-level customer_id (single customer)
STORY-010: Will change to method-level customer_id (multi-customer)
STORY-023c: Extended with API refresh methods and bug joins
STORY-032B: Refactored to use SQLModel with AsyncSession
STORY-044C: Referential integrity pattern with proactive FK checks
"""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Test, TestPlatform
from testio_mcp.repositories.base_repository import BaseRepository

# Import from top-level timezone_utils (minimal dependencies) to avoid circular imports
from testio_mcp.utilities.progress import BatchProgressCallback, safe_batch_callback
from testio_mcp.utilities.timezone_utils import normalize_to_utc

if TYPE_CHECKING:
    from testio_mcp.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class TestRepository(BaseRepository):
    """Repository for test-related database operations.

    Handles pure ORM queries with no business logic.
    All queries are scoped to a specific customer for data isolation.

    Note: __test__ = False prevents pytest from collecting this as a test class.

    Attributes:
        session: AsyncSession for ORM operations (inherited from BaseRepository)
        client: TestIO API client for refresh operations (inherited)
        customer_id: Stable customer identifier (inherited)
    """

    __test__ = False  # Prevent pytest collection

    # Override type hint to indicate session is always present in this repository
    session: AsyncSession

    def __init__(
        self,
        session: AsyncSession,
        client: TestIOClient,
        customer_id: int,
        user_repo: "UserRepository | None" = None,
        cache: Any | None = None,
    ) -> None:
        """Initialize repository with async session and API client.

        Args:
            session: Active AsyncSession for ORM operations
            client: TestIO API client for refresh operations
            customer_id: Stable customer identifier from TestIO system
            user_repo: Optional UserRepository for customer user extraction (STORY-036)
            cache: Optional PersistentCache for per-entity refresh locks (STORY-046, AC6)
        """
        super().__init__(session, client, customer_id, cache)
        self.user_repo = user_repo

        # STORY-044C: Per-key locks for feature integrity fills
        # Keyed by product_id to prevent thundering herd when multiple test_features
        # reference the same missing feature
        self._feature_fetch_locks: dict[int, asyncio.Lock] = {}

    def _extract_test_environment(self, test_data: dict[str, Any]) -> dict[str, Any] | None:
        """Extract and filter test_environment from test data.

        STORY-070: Only store id and title for security.
        """
        env = test_data.get("test_environment")
        if not env or not isinstance(env, dict):
            return None

        env_id = env.get("id")
        env_title = env.get("title")

        # Validate types (STORY-070: Security hardening)
        # Ensure id is int and title is str to prevent storing nested objects/PII
        if not isinstance(env_id, int) or not isinstance(env_title, str):
            return None

        return {
            "id": env_id,
            "title": env_title,
        }

    async def _upsert_test_platforms(self, test_id: int, test_data: dict[str, Any]) -> None:
        """Extract and upsert platform requirements from test data.

        Extracts platform info from test_data["requirements"] and creates/updates
        TestPlatform records. Handles the case where a test has multiple platform
        requirements (e.g., iOS + Android, Windows + Mac OS).

        Args:
            test_id: Test identifier
            test_data: Full test payload from API containing "requirements" array
        """
        requirements = test_data.get("requirements", [])
        if not requirements:
            return

        # Track seen OS IDs to avoid duplicates within same test
        seen_os_ids: set[int | None] = set()

        for req in requirements:
            if not isinstance(req, dict):
                continue

            os_data = req.get("operating_system")
            if not os_data or not isinstance(os_data, dict):
                continue

            os_id = os_data.get("id")
            os_name = os_data.get("name")

            if not os_name:
                continue

            # Skip duplicates (same OS can appear for smartphone + tablet)
            if os_id in seen_os_ids:
                continue
            seen_os_ids.add(os_id)

            category_data = req.get("category", {})
            category = category_data.get("key") if isinstance(category_data, dict) else None

            # Check if exists
            stmt = select(TestPlatform).where(
                TestPlatform.test_id == test_id,
                TestPlatform.operating_system_id == os_id,
            )
            result = await self.session.exec(stmt)
            existing = result.first()

            if existing:
                # Update existing
                existing.operating_system_name = os_name
                existing.category = category
            else:
                # Insert new
                platform = TestPlatform(
                    test_id=test_id,
                    operating_system_id=os_id,
                    operating_system_name=os_name,
                    category=category,
                )
                self.session.add(platform)

    # ============================================================================
    # Test Operations
    # ============================================================================

    async def test_exists(self, test_id: int, product_id: int) -> bool:
        """Check if test exists in database.

        Args:
            test_id: Test identifier
            product_id: Product identifier

        Returns:
            True if test exists, False otherwise
        """
        statement = select(Test).where(
            Test.id == test_id,
            Test.customer_id == self.customer_id,
            Test.product_id == product_id,
        )
        result = await self.session.exec(statement)
        test = result.first()
        return test is not None

    async def get_test_status(self, test_id: int) -> str | None:
        """Get current status of a test.

        Args:
            test_id: Test identifier

        Returns:
            Status string or None if not found
        """
        statement = select(Test.status).where(
            Test.id == test_id,
            Test.customer_id == self.customer_id,
        )
        result = await self.session.exec(statement)
        return result.first()

    async def insert_test(
        self,
        test_data: dict[str, Any],
        product_id: int,
        user_id_map: dict[str, int] | None = None,
    ) -> None:
        """Insert or replace a single test in database.

        Note: This method stages changes but does NOT commit.
        Caller must explicitly commit the session to persist changes.
        This allows efficient batching of multiple inserts in a single transaction.

        Args:
            test_data: Full test payload from API
            product_id: Product identifier
            user_id_map: Optional pre-computed username->user_id map for batch operations.
                         If provided, skips individual upsert_user calls (avoids nested flushes).
                         If None, falls back to calling upsert_user for each user.
        """
        test_id = test_data.get("id")
        status = test_data.get("status", "unknown")

        # Normalize all timestamps to UTC before storing (STORY-021c)
        # This ensures consistent date comparisons regardless of API timezone variations
        # normalize_to_utc returns ISO strings, parse them to datetime objects for ORM
        start_at_str = normalize_to_utc(test_data.get("start_at"))
        end_at_str = normalize_to_utc(test_data.get("end_at"))

        # Parse ISO strings to datetime objects (SQLModel expects datetime, not strings)
        start_at = datetime.fromisoformat(start_at_str) if start_at_str else None
        end_at = datetime.fromisoformat(end_at_str) if end_at_str else None

        # Extract customer user metadata (STORY-036)
        created_by = test_data.get("created_by")
        submitted_by = test_data.get("submitted_by")

        # STORY-054: Extract denormalized fields for filtering/sorting/display
        title = test_data.get("title")
        testing_type = test_data.get("testing_type")
        goal = test_data.get("goal_text")
        instructions = test_data.get("instructions_text")
        out_of_scope = test_data.get("out_of_scope_text")
        enable_low = test_data.get("enable_low")
        enable_high = test_data.get("enable_high")
        enable_critical = test_data.get("enable_critical")

        # STORY-070: Extract test environment
        test_environment = self._extract_test_environment(test_data)

        # Get customer user IDs (STORY-036)
        # If user_id_map provided (batch mode), use it directly to avoid nested flushes
        # Otherwise, fall back to individual upsert_user calls
        created_by_user_id: int | None = None
        submitted_by_user_id: int | None = None

        if user_id_map is not None:
            # Batch mode: use pre-computed map (no DB queries needed)
            if created_by:
                created_by_user_id = user_id_map.get(created_by)
            if submitted_by:
                submitted_by_user_id = user_id_map.get(submitted_by)
        elif self.user_repo:
            # Single-test mode: fall back to individual upsert calls
            if created_by:
                user = await self.user_repo.upsert_user(username=created_by, user_type="customer")
                if user:
                    created_by_user_id = user.id

            if submitted_by:
                user = await self.user_repo.upsert_user(username=submitted_by, user_type="customer")
                if user:
                    submitted_by_user_id = user.id

        # NEW (STORY-041): Extract and upsert test_features
        features_data = test_data.get("features", [])
        for feature_data in features_data:
            await self._upsert_test_feature(test_id, feature_data, product_id)  # type: ignore[arg-type]

        # Extract and upsert platform requirements
        await self._upsert_test_platforms(test_id, test_data)  # type: ignore[arg-type]

        # Check if test exists (for upsert pattern)
        statement = select(Test).where(Test.id == test_id, Test.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        existing_test = result.first()

        if existing_test:
            # Update existing test
            # Note: No need to call session.add() for tracked objects
            existing_test.product_id = product_id
            existing_test.data = json.dumps(test_data)
            existing_test.status = status
            existing_test.start_at = start_at
            existing_test.end_at = end_at
            existing_test.synced_at = datetime.now(UTC)
            # Update customer user fields (STORY-036)
            existing_test.created_by = created_by
            existing_test.submitted_by = submitted_by
            existing_test.created_by_user_id = created_by_user_id
            existing_test.submitted_by_user_id = submitted_by_user_id
            # STORY-054: Update denormalized fields
            existing_test.title = title
            existing_test.testing_type = testing_type
            existing_test.goal = goal
            existing_test.instructions = instructions
            existing_test.out_of_scope = out_of_scope
            existing_test.enable_low = enable_low
            existing_test.enable_high = enable_high
            existing_test.enable_critical = enable_critical
            existing_test.test_environment = test_environment
        else:
            # Insert new test
            new_test = Test(
                id=test_id,
                customer_id=self.customer_id,
                product_id=product_id,
                data=json.dumps(test_data),
                status=status,
                start_at=start_at,
                end_at=end_at,
                synced_at=datetime.now(UTC),
                bugs_synced_at=None,
                # Customer user fields (STORY-036)
                created_by=created_by,
                submitted_by=submitted_by,
                created_by_user_id=created_by_user_id,
                submitted_by_user_id=submitted_by_user_id,
                # STORY-054: Denormalized fields
                title=title,
                testing_type=testing_type,
                goal=goal,
                instructions=instructions,
                out_of_scope=out_of_scope,
                enable_low=enable_low,
                enable_high=enable_high,
                enable_critical=enable_critical,
                test_environment=test_environment,
            )
            self.session.add(new_test)

    async def update_test(self, test_data: dict[str, Any], product_id: int) -> None:
        """Update existing test with fresh data from API.

        Used by AC4 refresh logic to update test status and data.
        Preserves bugs_synced_at timestamp (STORY-024 fix).

        STORY-054: Also updates denormalized fields.

        Note: This method stages changes but does NOT commit.
        Caller must explicitly commit the session to persist changes.

        Args:
            test_data: Full test payload from API
            product_id: Product identifier
        """
        test_id = test_data.get("id")
        status = test_data.get("status", "unknown")

        # Normalize all timestamps to UTC before storing (STORY-021c)
        # This ensures consistent date comparisons regardless of API timezone variations
        # normalize_to_utc returns ISO strings, parse them to datetime objects for ORM
        start_at_str = normalize_to_utc(test_data.get("start_at"))
        end_at_str = normalize_to_utc(test_data.get("end_at"))

        # Parse ISO strings to datetime objects (SQLModel expects datetime, not strings)
        start_at = datetime.fromisoformat(start_at_str) if start_at_str else None
        end_at = datetime.fromisoformat(end_at_str) if end_at_str else None

        # STORY-054: Extract denormalized fields (same as insert_test)
        title = test_data.get("title")
        testing_type = test_data.get("testing_type")
        goal = test_data.get("goal_text")
        instructions = test_data.get("instructions_text")
        out_of_scope = test_data.get("out_of_scope_text")
        enable_low = test_data.get("enable_low")
        enable_high = test_data.get("enable_high")
        enable_critical = test_data.get("enable_critical")

        # STORY-070: Extract test environment
        test_environment = self._extract_test_environment(test_data)

        # Fetch existing test
        statement = select(Test).where(
            Test.id == test_id,
            Test.customer_id == self.customer_id,
            Test.product_id == product_id,
        )
        result = await self.session.exec(statement)
        test = result.first()

        if test:
            # Update test fields (preserving bugs_synced_at)
            # Note: No need to call session.add() for tracked objects
            test.data = json.dumps(test_data)
            test.status = status
            test.start_at = start_at
            test.end_at = end_at
            test.synced_at = datetime.now(UTC)
            # STORY-054: Update denormalized fields
            test.title = title
            test.testing_type = testing_type
            test.goal = goal
            test.instructions = instructions
            test.out_of_scope = out_of_scope
            test.enable_low = enable_low
            test.enable_high = enable_high
            test.enable_critical = enable_critical
            test.test_environment = test_environment

            # STORY-041: Extract and upsert test_features (same as insert_test)
            features_data = test_data.get("features", [])
            for feature_data in features_data:
                await self._upsert_test_feature(test_id, feature_data, product_id)  # type: ignore[arg-type]

            # Extract and upsert platform requirements
            await self._upsert_test_platforms(test_id, test_data)  # type: ignore[arg-type]

    async def count_tests(self) -> int:
        """Count total tests for current customer.

        Returns:
            Total number of tests
        """
        statement = (
            select(func.count()).select_from(Test).where(Test.customer_id == self.customer_id)
        )
        result = await self.session.exec(statement)
        count = result.one()
        return count

    async def count_product_tests(self, product_id: int) -> int:
        """Count tests for a specific product.

        Args:
            product_id: Product identifier

        Returns:
            Number of tests for this product
        """
        statement = (
            select(func.count())
            .select_from(Test)
            .where(Test.customer_id == self.customer_id, Test.product_id == product_id)
        )
        result = await self.session.exec(statement)
        count = result.one()
        return count

    async def get_product_last_synced(self, product_id: int) -> str | None:
        """Get last sync timestamp for a specific product.

        Note: This method queries the Product table. It should ideally be in ProductRepository,
        but is kept here for backward compatibility with existing code.

        Args:
            product_id: Product identifier

        Returns:
            ISO 8601 timestamp of last sync, or None if never synced
        """
        from testio_mcp.models.orm import Product

        statement = select(Product.last_synced).where(
            Product.id == product_id, Product.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)
        last_synced = result.first()
        return last_synced.isoformat() if last_synced else None

    async def get_oldest_test_date(self) -> str | None:
        """Get oldest test end date for current customer.

        Returns:
            ISO 8601 timestamp of oldest test end date, or None if no tests
        """
        statement = select(func.min(Test.end_at)).where(Test.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        oldest_date = result.one()
        return oldest_date.isoformat() if oldest_date else None

    async def get_newest_test_date(self) -> str | None:
        """Get newest test end date for current customer.

        Returns:
            ISO 8601 timestamp of newest test end date, or None if no tests
        """
        statement = select(func.max(Test.end_at)).where(Test.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        newest_date = result.one()
        return newest_date.isoformat() if newest_date else None

    async def delete_all_tests(self) -> None:
        """Delete all tests for current customer.

        Used by clear_database operation.
        """
        statement = select(Test).where(Test.customer_id == self.customer_id)
        result = await self.session.exec(statement)
        tests = result.all()

        for test in tests:
            await self.session.delete(test)

        await self.session.commit()

    async def delete_product_tests(self, product_id: int) -> None:
        """Delete all tests for a specific product.

        Args:
            product_id: Product identifier
        """
        statement = select(Test).where(
            Test.customer_id == self.customer_id, Test.product_id == product_id
        )
        result = await self.session.exec(statement)
        tests = result.all()

        for test in tests:
            await self.session.delete(test)

        await self.session.commit()

    async def get_mutable_tests(self, product_id: int) -> list[dict[str, Any]]:
        """Get tests that can change (mutable statuses only) (STORY-021g).

        Mutable test statuses (need frequent sync):
        - customer_finalized: Customer marked as final but can change
        - waiting: Waiting to start
        - running: Currently active, bugs being reported
        - locked: Finalized but not archived yet (still mutable!)
        - initialized: Created but not started

        Immutable test statuses (never change):
        - archived: Test completed and archived (final state)
        - cancelled: Test cancelled (final state)

        Args:
            product_id: Product identifier

        Returns:
            List of dicts with id, status, end_at (sorted by end_at DESC)
        """
        mutable_statuses = ["customer_finalized", "waiting", "running", "locked", "initialized"]

        statement = (
            select(Test.id, Test.status, Test.end_at)
            .where(
                Test.customer_id == self.customer_id,
                Test.product_id == product_id,
                Test.status.in_(mutable_statuses),  # type: ignore[attr-defined]
            )
            .order_by(Test.end_at.desc())  # type: ignore[union-attr]
        )

        result = await self.session.exec(statement)
        rows = result.all()
        return [{"id": row[0], "status": row[1], "end_at": row[2]} for row in rows]

    async def query_tests(
        self,
        product_id: int,
        statuses: list[str] | None = None,
        testing_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "start_at",
        sort_by: str = "end_at",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query tests from database with filtering, sorting, and pagination.

        Implements AC3 query interface with ORM-based filtering for performance.

        STORY-054 AC10: Added title sorting and testing_type filtering.

        Args:
            product_id: Product identifier
            statuses: Optional list of status values to filter by
            testing_type: Optional testing type filter (coverage, focused, rapid)
            start_date: Optional start date for date range filter
            end_date: Optional end date for date range filter
            date_field: Field to use for date filtering (start_at, end_at)
            sort_by: Field to sort by (start_at, end_at, status, title). Default: end_at
            sort_order: Sort order (asc, desc). Default: desc
            page: Page number (1-indexed, default: 1)
            per_page: Number of results per page (default: 100)
            offset: Additional offset on top of page calculation (default: 0)
                   Final offset = offset + (page - 1) * per_page
                   Use case: Fetch small sample (page=1, per_page=10), then continue
                   with larger pages (page=1, per_page=100, offset=10)

        Returns:
            List of test dictionaries (deserialized from JSON data column)

        Raises:
            ValueError: If date_field, sort_by, or sort_order are invalid
        """
        # SECURITY: Validate all field parameters to prevent invalid field access
        ALLOWED_DATE_FIELDS = {"start_at", "end_at"}
        ALLOWED_SORT_FIELDS = {"start_at", "end_at", "status", "title"}
        ALLOWED_SORT_ORDERS = {"asc", "desc"}

        if date_field not in ALLOWED_DATE_FIELDS:
            raise ValueError(
                f"Unsupported date_field: {date_field!r}. "
                f"Must be one of: {', '.join(sorted(ALLOWED_DATE_FIELDS))}"
            )

        if sort_by not in ALLOWED_SORT_FIELDS:
            raise ValueError(
                f"Unsupported sort_by: {sort_by!r}. "
                f"Must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}"
            )

        if sort_order.lower() not in ALLOWED_SORT_ORDERS:
            raise ValueError(f"Unsupported sort_order: {sort_order!r}. Must be 'asc' or 'desc'")

        # STORY-071: Build query selecting both data and test_environment columns
        statement = select(Test.data, Test.test_environment).where(
            Test.customer_id == self.customer_id, Test.product_id == product_id
        )

        # Status filter
        if statuses:
            statement = statement.where(Test.status.in_(statuses))  # type: ignore[attr-defined]

        # STORY-054 AC10: Testing type filter using denormalized column
        if testing_type:
            statement = statement.where(Test.testing_type == testing_type)

        # Date range filter
        if start_date or end_date:
            # Get the appropriate date field attribute
            date_column = getattr(Test, date_field)

            if start_date:
                statement = statement.where(date_column >= start_date)
            if end_date:
                statement = statement.where(date_column <= end_date)

        # Calculate pagination offset (combines page-based + additional offset)
        # Examples:
        # - Page-based only: page=2, per_page=50, offset=0 → items 50-99
        # - With offset: page=1, per_page=100, offset=10 → items 10-109
        actual_offset = offset + (page - 1) * per_page

        # STORY-054 AC10: Dynamic sorting by denormalized fields
        sort_column = getattr(Test, sort_by)
        if sort_order.lower() == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        statement = statement.limit(per_page).offset(actual_offset)

        # Execute query
        result = await self.session.exec(statement)
        rows = result.all()

        # STORY-071: Deserialize JSON data and override test_environment from column
        # Column is authoritative source, not JSON blob
        tests: list[dict[str, Any]] = []
        for data_json, test_environment_column in rows:
            test_dict = json.loads(data_json)
            # Override test_environment with column value (authoritative source)
            if test_environment_column is not None:
                test_dict["test_environment"] = test_environment_column
            tests.append(test_dict)

        return tests

    async def count_filtered_tests(
        self,
        product_id: int,
        statuses: list[str] | None = None,
        testing_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "start_at",
    ) -> int:
        """Count tests matching query criteria (for pagination total_count).

        Uses same WHERE clause logic as query_tests() but returns count instead.

        STORY-054 AC10: Added testing_type filtering.

        Args:
            product_id: Product ID to filter by
            statuses: Optional list of status values to filter by
            testing_type: Optional testing type filter (coverage, focused, rapid)
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            date_field: Date field to filter on ("start_at", "end_at", or "any")

        Returns:
            Total number of tests matching the criteria
        """
        # Build query with filters
        statement = (
            select(func.count())
            .select_from(Test)
            .where(Test.customer_id == self.customer_id, Test.product_id == product_id)
        )

        # Status filter
        if statuses:
            statement = statement.where(Test.status.in_(statuses))  # type: ignore[attr-defined]

        # STORY-054 AC10: Testing type filter using denormalized column
        if testing_type:
            statement = statement.where(Test.testing_type == testing_type)

        # Date filters
        if start_date:
            if date_field == "any":
                # Match if ANY date field is >= start_date
                from sqlmodel import or_

                # STORY-054: Removed created_at (always NULL), use start_at/end_at only
                statement = statement.where(
                    or_(
                        Test.start_at >= start_date,  # type: ignore[operator]
                        Test.end_at >= start_date,  # type: ignore[operator]
                    )
                )
            else:
                date_column = getattr(Test, date_field)
                statement = statement.where(date_column >= start_date)

        if end_date:
            if date_field == "any":
                # Match if ANY date field is <= end_date
                from sqlmodel import or_

                # STORY-054: Removed created_at (always NULL), use start_at/end_at only
                statement = statement.where(
                    or_(
                        Test.start_at <= end_date,  # type: ignore[operator]
                        Test.end_at <= end_date,  # type: ignore[operator]
                    )
                )
            else:
                date_column = getattr(Test, date_field)
                statement = statement.where(date_column <= end_date)

        # Execute query
        result = await self.session.exec(statement)
        count = result.one()
        return count

    async def get_test_aggregates(
        self,
        product_id: int,
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
    ) -> dict[str, Any]:
        """Get aggregate test metrics for summary computation.

        Returns counts grouped by status and testing_type without fetching
        individual test records. Used for token-efficient PQR summaries.

        Args:
            product_id: Product ID to filter by
            statuses: Optional list of status values to filter by
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            date_field: Date field to filter on ("start_at" or "end_at")

        Returns:
            Dictionary with:
                - total_tests: Total count of matching tests
                - tests_by_status: {status: count} mapping
                - tests_by_type: {testing_type: count} mapping
        """
        # Base WHERE clause
        base_where = [Test.customer_id == self.customer_id, Test.product_id == product_id]

        if statuses:
            base_where.append(Test.status.in_(statuses))  # type: ignore[attr-defined]

        if start_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column >= start_date)

        if end_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column <= end_date)

        # Total count
        count_stmt = select(func.count()).select_from(Test).where(*base_where)
        count_result = await self.session.exec(count_stmt)
        total_tests = count_result.one()

        # Group by status
        status_stmt = select(Test.status, func.count()).where(*base_where).group_by(Test.status)
        status_result = await self.session.exec(status_stmt)
        tests_by_status = {row[0]: row[1] for row in status_result.all()}

        # Group by testing_type
        type_stmt = (
            select(Test.testing_type, func.count()).where(*base_where).group_by(Test.testing_type)
        )
        type_result = await self.session.exec(type_stmt)
        tests_by_type = {(row[0] or "unknown"): row[1] for row in type_result.all()}

        return {
            "total_tests": total_tests,
            "tests_by_status": tests_by_status,
            "tests_by_type": tests_by_type,
        }

    async def get_test_aggregates_for_products(
        self,
        product_ids: list[int],
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
        test_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Get aggregate test metrics for multiple products (multi-product PQR).

        Multi-product version of get_test_aggregates(). When test_ids is provided,
        filters to only those specific tests.

        Args:
            product_ids: List of product IDs to filter by
            statuses: Optional list of status values to filter by
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            date_field: Date field to filter on ("start_at" or "end_at")
            test_ids: Optional list of specific test IDs to include

        Returns:
            Dictionary with:
                - total_tests: Total count of matching tests
                - tests_by_status: {status: count} mapping
                - tests_by_type: {testing_type: count} mapping
        """
        from sqlmodel import col

        # Base WHERE clause
        base_where: list[Any] = [
            Test.customer_id == self.customer_id,
            col(Test.product_id).in_(product_ids),
        ]

        # If test_ids provided, filter to only those tests
        if test_ids:
            base_where.append(col(Test.id).in_(test_ids))

        if statuses:
            base_where.append(Test.status.in_(statuses))  # type: ignore[attr-defined]

        if start_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column >= start_date)

        if end_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column <= end_date)

        # Total count
        count_stmt = select(func.count()).select_from(Test).where(*base_where)
        count_result = await self.session.exec(count_stmt)
        total_tests = count_result.one()

        # Group by status
        status_stmt = select(Test.status, func.count()).where(*base_where).group_by(Test.status)
        status_result = await self.session.exec(status_stmt)
        tests_by_status = {row[0]: row[1] for row in status_result.all()}

        # Group by testing_type
        type_stmt = (
            select(Test.testing_type, func.count()).where(*base_where).group_by(Test.testing_type)
        )
        type_result = await self.session.exec(type_stmt)
        tests_by_type = {(row[0] or "unknown"): row[1] for row in type_result.all()}

        return {
            "total_tests": total_tests,
            "tests_by_status": tests_by_status,
            "tests_by_type": tests_by_type,
        }

    async def get_test_aggregates_grouped_by_product(
        self,
        product_ids: list[int],
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
        test_ids: list[int] | None = None,
    ) -> dict[int, dict[str, Any]]:
        """Get test aggregates grouped by product_id in a single query.

        Optimized version that avoids N+1 queries when building per-product
        breakdown for multi-product reports.

        Args:
            product_ids: List of product IDs to aggregate
            statuses: Optional list of status values to filter by
            start_date: Optional start date for date range filter
            end_date: Optional end date for date range filter
            date_field: Field to use for date filtering (start_at, end_at)
            test_ids: Optional list of specific test IDs to include

        Returns:
            Dictionary mapping product_id to aggregates:
            {
                598: {"total_tests": 10, "tests_by_status": {...}, "tests_by_type": {...}},
                599: {"total_tests": 5, "tests_by_status": {...}, "tests_by_type": {...}},
            }
        """
        from sqlmodel import col

        # Initialize result with empty aggregates for all products
        result: dict[int, dict[str, Any]] = {
            pid: {"total_tests": 0, "tests_by_status": {}, "tests_by_type": {}}
            for pid in product_ids
        }

        if not product_ids:
            return result

        # Base WHERE clause
        base_where: list[Any] = [
            Test.customer_id == self.customer_id,
            col(Test.product_id).in_(product_ids),
        ]

        if test_ids:
            base_where.append(col(Test.id).in_(test_ids))

        if statuses:
            base_where.append(Test.status.in_(statuses))  # type: ignore[attr-defined]

        if start_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column >= start_date)

        if end_date:
            date_column = getattr(Test, date_field)
            base_where.append(date_column <= end_date)

        # Count grouped by product_id
        count_stmt = (
            select(Test.product_id, func.count()).where(*base_where).group_by(Test.product_id)  # type: ignore[arg-type]
        )
        count_result = await self.session.exec(count_stmt)
        for row in count_result.all():
            pid, cnt = row[0], row[1]
            if pid in result:
                result[pid]["total_tests"] = cnt

        # Status counts grouped by product_id
        status_stmt = (
            select(Test.product_id, Test.status, func.count())
            .where(*base_where)
            .group_by(Test.product_id, Test.status)  # type: ignore[arg-type]
        )
        status_result = await self.session.exec(status_stmt)
        for row in status_result.all():  # type: ignore[assignment]
            pid, status, cnt = row[0], row[1], row[2]  # type: ignore[misc]
            if pid in result and status:
                result[pid]["tests_by_status"][status] = cnt

        # Type counts grouped by product_id
        type_stmt = (
            select(Test.product_id, Test.testing_type, func.count())
            .where(*base_where)
            .group_by(Test.product_id, Test.testing_type)  # type: ignore[arg-type]
        )
        type_result = await self.session.exec(type_stmt)
        for row in type_result.all():  # type: ignore[assignment]
            pid, testing_type, cnt = row[0], row[1], row[2]  # type: ignore[misc]
            if pid in result:
                result[pid]["tests_by_type"][testing_type or "unknown"] = cnt

        return result

    async def query_tests_for_products(
        self,
        product_ids: list[int],
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
        sort_by: str = "end_at",
        sort_order: str = "desc",
        page: int = 1,
        # Default 1000 is sufficient for most products. For larger products,
        # use output_file to export to JSON (no limit) or pagination.
        per_page: int = 1000,
        test_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Query tests from database for multiple products.

        Multi-product version of query_tests(). Used by generate_quality_report
        for multi-product portfolio analysis.

        Args:
            product_ids: List of product IDs to filter by
            statuses: Optional list of status values to filter by
            start_date: Optional start date for date range filter
            end_date: Optional end date for date range filter
            date_field: Field to use for date filtering (start_at, end_at)
            sort_by: Field to sort by (start_at, end_at, status, title). Default: end_at
            sort_order: Sort order (asc, desc). Default: desc
            page: Page number (1-indexed, default: 1)
            per_page: Number of results per page (default: 1000)
            test_ids: Optional list of specific test IDs to include

        Returns:
            List of test dictionaries (deserialized from JSON data column)
        """
        from sqlmodel import col

        # Build query selecting both data and test_environment columns
        statement = select(Test.data, Test.test_environment).where(
            Test.customer_id == self.customer_id,
            col(Test.product_id).in_(product_ids),
        )

        # If test_ids provided, filter to only those tests
        if test_ids:
            statement = statement.where(col(Test.id).in_(test_ids))

        # Status filter
        if statuses:
            statement = statement.where(Test.status.in_(statuses))  # type: ignore[attr-defined]

        # Date range filter
        if start_date or end_date:
            date_column = getattr(Test, date_field)
            if start_date:
                statement = statement.where(date_column >= start_date)
            if end_date:
                statement = statement.where(date_column <= end_date)

        # Calculate pagination offset
        actual_offset = (page - 1) * per_page

        # Sorting
        sort_column = getattr(Test, sort_by)
        if sort_order.lower() == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        statement = statement.limit(per_page).offset(actual_offset)

        # Execute query
        result = await self.session.exec(statement)
        rows = result.all()

        # Deserialize JSON data and override test_environment from column
        tests: list[dict[str, Any]] = []
        for data_json, test_environment_column in rows:
            test_dict = json.loads(data_json)
            if test_environment_column is not None:
                test_dict["test_environment"] = test_environment_column
            tests.append(test_dict)

        return tests

    async def get_test_ids_for_product(
        self,
        product_id: int,
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
    ) -> list[int]:
        """Get all test IDs matching filters (for bug aggregate queries).

        Args:
            product_id: Product ID to filter by
            statuses: Optional list of status values to filter by
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            date_field: Date field to filter on

        Returns:
            List of test IDs matching the criteria
        """
        statement = select(Test.id).where(
            Test.customer_id == self.customer_id, Test.product_id == product_id
        )

        if statuses:
            statement = statement.where(Test.status.in_(statuses))  # type: ignore[attr-defined]

        if start_date:
            date_column = getattr(Test, date_field)
            statement = statement.where(date_column >= start_date)

        if end_date:
            date_column = getattr(Test, date_field)
            statement = statement.where(date_column <= end_date)

        result = await self.session.exec(statement)
        # Filter out None values for type safety (Test.id is nullable in SQL)
        return [id for id in result.all() if id is not None]

    async def get_test_ids_for_products(
        self,
        product_ids: list[int],
        statuses: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_field: str = "end_at",
    ) -> list[int]:
        """Get all test IDs matching filters for multiple products.

        Multi-product version of get_test_ids_for_product().

        Args:
            product_ids: List of product IDs to filter by
            statuses: Optional list of status values to filter by
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            date_field: Date field to filter on

        Returns:
            List of test IDs matching the criteria across all products
        """
        from sqlmodel import col

        statement = select(Test.id).where(
            Test.customer_id == self.customer_id,
            col(Test.product_id).in_(product_ids),
        )

        if statuses:
            statement = statement.where(Test.status.in_(statuses))  # type: ignore[attr-defined]

        if start_date:
            date_column = getattr(Test, date_field)
            statement = statement.where(date_column >= start_date)

        if end_date:
            date_column = getattr(Test, date_field)
            statement = statement.where(date_column <= end_date)

        # Sort by end_at descending (most recent first)
        statement = statement.order_by(Test.end_at.desc())  # type: ignore[union-attr]

        result = await self.session.exec(statement)
        return [id for id in result.all() if id is not None]

    async def sort_test_ids_by_end_at(
        self,
        test_ids: list[int],
    ) -> list[int]:
        """Sort test IDs by end_at date descending (most recent first).

        Used when user provides explicit test_ids to ensure consistent ordering.

        Args:
            test_ids: List of test IDs to sort

        Returns:
            Same test IDs sorted by end_at descending
        """
        if not test_ids:
            return []

        from sqlmodel import col

        statement = (
            select(Test.id)
            .where(
                col(Test.id).in_(test_ids),
                Test.customer_id == self.customer_id,
            )
            .order_by(Test.end_at.desc())  # type: ignore[union-attr]
        )

        result = await self.session.exec(statement)
        return [id for id in result.all() if id is not None]

    async def get_test_product_mapping(
        self,
        test_ids: list[int],
    ) -> dict[int, int]:
        """Get test_id -> product_id mapping for batch operations.

        Single SQL query to get product associations for multiple tests.
        Used to avoid N+1 queries when filtering test_ids by product.

        Args:
            test_ids: List of test IDs to lookup

        Returns:
            Dictionary mapping test_id to product_id.
            Missing test IDs are not included in the result.
        """
        if not test_ids:
            return {}

        from sqlmodel import col

        statement = select(Test.id, Test.product_id).where(
            col(Test.id).in_(test_ids),
            Test.customer_id == self.customer_id,
        )
        result = await self.session.exec(statement)
        rows = result.all()

        return {row[0]: row[1] for row in rows if row[0] is not None and row[1] is not None}

    async def validate_tests_belong_to_products(
        self,
        test_ids: list[int],
        product_ids: list[int],
    ) -> None:
        """Validate that all test IDs belong to the specified products.

        Single SQL query to validate all test-product associations.
        Used by generate_quality_report when test_ids filter is provided.

        Args:
            test_ids: List of test IDs to validate
            product_ids: List of allowed product IDs

        Raises:
            TestNotFoundException: If any test_id doesn't exist
            TestProductMismatchError: If any test belongs to a product not in product_ids
        """
        from sqlmodel import col

        from testio_mcp.exceptions import TestNotFoundException, TestProductMismatchError

        if not test_ids:
            return

        # Single query: get id and product_id for all requested tests
        statement = select(Test.id, Test.product_id).where(
            col(Test.id).in_(test_ids),
            Test.customer_id == self.customer_id,
        )
        result = await self.session.exec(statement)
        rows = result.all()

        # Build map of found tests
        found_tests: dict[int, int] = {
            row[0]: row[1] for row in rows if row[0] is not None and row[1] is not None
        }

        # Check for missing tests
        for test_id in test_ids:
            if test_id not in found_tests:
                raise TestNotFoundException(test_id)

        # Check for product mismatches
        product_ids_set = set(product_ids)
        for test_id, actual_product_id in found_tests.items():
            if actual_product_id not in product_ids_set:
                raise TestProductMismatchError(
                    test_id=test_id,
                    actual_product_id=actual_product_id,
                    allowed_product_ids=product_ids,
                )

    async def get_tests_cached_or_refresh(
        self,
        test_ids: list[int],
        force_refresh: bool = False,
        on_batch_progress: BatchProgressCallback | None = None,
    ) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
        """Get tests with intelligent caching based on mutability.

        Batch-aware method: Pass single test ID or multiple for efficient batch processing.

        Decision Logic (per test, priority order):
        1. Check synced_at and test status from tests table
        2. If force_refresh=True → mark for refresh (user override)
        3. If synced_at IS NULL → mark for refresh (never synced!)
        4. If test is immutable (archived/cancelled) → use cache (test won't change)
        5. If test is mutable (locked/running/etc.) → check staleness
           - If stale (>TTL seconds) → mark for refresh
           - If fresh → use cache
        6. Batch refresh all tests marked for refresh (single API call per batch)
        7. Return tests for all test IDs from SQLite

        Args:
            test_ids: List of test identifiers (single or multiple)
            force_refresh: Bypass cache and fetch from API for all tests (default: False)
            on_batch_progress: Optional callback invoked after each batch completes.
                Args: (current_completed: int, total_batches: int). Best-effort (errors swallowed).

        Returns:
            Tuple of (tests_dict, cache_stats):
                - tests_dict: Dictionary mapping test_id -> test dict (deserialized JSON)
                  Example: {123: {test1_data}, 124: {test2_data}}
                - cache_stats: Cache efficiency metrics dict with:
                  - total_tests: int
                  - cache_hits: int
                  - api_calls: int
                  - cache_hit_rate: float (0-100)
                  - breakdown: dict with decision category counts

        Performance:
            - Single test cache hit: ~10ms (SQLite query)
            - Batch processing: Efficient batch API calls (15 tests per batch)
            - Immutable tests: Always cache hit (no API calls)

        Logging:
            - DEBUG: Per-test decisions (SQLite vs API, with reason)
            - INFO: Summary stats (cache hit rate, breakdown by category)
            Example logs:
                Test 123: SQLite (immutable (archived))
                Test 124: SQLite (mutable (running), fresh (0.5h))
                Test 125: API (mutable (running), stale (2.3h))
                Test cache: 236/295 from SQLite (80.0% hit rate), 59 from API
                Breakdown: 236 immutable, 40 mutable fresh, 19 mutable stale
        """
        import asyncio

        from testio_mcp.config import settings

        if not test_ids:
            return {}, {
                "total_tests": 0,
                "cache_hits": 0,
                "api_calls": 0,
                "cache_hit_rate": 0.0,
                "breakdown": {},
            }

        # 1. Bulk query: Get test statuses and synced_at for all test IDs
        # Import col for querying (avoid circular import at module level)
        from sqlmodel import col

        statement = select(Test.id, Test.status, Test.synced_at).where(
            col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
        )
        test_result = await self.session.exec(statement)
        rows = test_result.all()
        test_metadata: dict[int, dict[str, Any]] = {
            row[0]: {"status": row[1], "synced_at": row[2]} for row in rows if row[0] is not None
        }

        # 2. Determine which tests need refreshing
        tests_to_refresh: list[int] = []
        now = datetime.now(UTC)

        # Track decision stats for logging
        cache_decisions = {
            "immutable_cached": 0,
            "mutable_fresh": 0,
            "mutable_stale": 0,
            "never_synced": 0,
            "force_refresh": 0,
            "not_in_db": 0,
        }

        for test_id in test_ids:
            metadata = test_metadata.get(test_id)

            if not metadata:
                # Test not in DB - need to refresh (will likely 404 from API)
                tests_to_refresh.append(test_id)
                cache_decisions["not_in_db"] += 1
                logger.debug(f"Test {test_id}: API (not in database)")
                continue

            test_status = metadata["status"]
            synced_at_value = metadata["synced_at"]

            # Parse synced_at timestamp (ISO format with timezone)
            synced_at: datetime | None = None
            if synced_at_value:
                try:
                    # synced_at_value can be str, datetime, or None from DB
                    if isinstance(synced_at_value, str):
                        synced_at = datetime.fromisoformat(synced_at_value)
                    elif isinstance(synced_at_value, datetime):
                        synced_at = synced_at_value

                    # Ensure timezone awareness (assume UTC if naive)
                    if synced_at and synced_at.tzinfo is None:
                        synced_at = synced_at.replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid synced_at for test {test_id}, will refresh")

            # Apply decision logic (same priority order as BugRepository)
            should_refresh = False
            decision_reason = ""

            if force_refresh:
                should_refresh = True
                decision_reason = "force_refresh=True"
                cache_decisions["force_refresh"] += 1
            elif synced_at is None:
                # Never synced - MUST fetch
                should_refresh = True
                decision_reason = "never synced"
                cache_decisions["never_synced"] += 1
            elif test_status in settings.IMMUTABLE_TEST_STATUSES:
                # Immutable (archived/cancelled) - use cache
                should_refresh = False
                decision_reason = f"immutable ({test_status})"
                cache_decisions["immutable_cached"] += 1
            elif test_status in settings.MUTABLE_TEST_STATUSES:
                # Mutable - check staleness
                seconds_since_sync = (now - synced_at).total_seconds()
                hours_since_sync = seconds_since_sync / 3600

                # Use unified CACHE_TTL_SECONDS (STORY-046 AC7)
                if seconds_since_sync > settings.CACHE_TTL_SECONDS:
                    should_refresh = True
                    decision_reason = f"mutable ({test_status}), stale ({hours_since_sync:.1f}h)"
                    cache_decisions["mutable_stale"] += 1
                else:
                    should_refresh = False
                    decision_reason = f"mutable ({test_status}), fresh ({hours_since_sync:.1f}h)"
                    cache_decisions["mutable_fresh"] += 1
            else:
                # Unknown status - default to refresh (defensive)
                should_refresh = True
                decision_reason = f"unknown status '{test_status}'"
                logger.warning(f"Test {test_id} has unknown status '{test_status}'")

            # Log decision
            source = "API" if should_refresh else "SQLite"
            logger.debug(f"Test {test_id}: {source} ({decision_reason})")

            if should_refresh:
                tests_to_refresh.append(test_id)

        # 3. Log cache efficiency summary
        cache_hits = len(test_ids) - len(tests_to_refresh)
        cache_hit_rate = (cache_hits / len(test_ids) * 100) if test_ids else 0

        logger.info(
            f"Test cache decisions: {cache_hits}/{len(test_ids)} from SQLite "
            f"({cache_hit_rate:.1f}% hit rate), {len(tests_to_refresh)} from API"
        )

        # Log breakdown by category (non-zero only)
        breakdown_parts = []
        if cache_decisions["immutable_cached"]:
            breakdown_parts.append(f"{cache_decisions['immutable_cached']} immutable (cached)")
        if cache_decisions["mutable_fresh"]:
            breakdown_parts.append(f"{cache_decisions['mutable_fresh']} mutable fresh (cached)")
        if cache_decisions["mutable_stale"]:
            breakdown_parts.append(f"{cache_decisions['mutable_stale']} mutable stale (API)")
        if cache_decisions["never_synced"]:
            breakdown_parts.append(f"{cache_decisions['never_synced']} never synced (API)")
        if cache_decisions["force_refresh"]:
            breakdown_parts.append(f"{cache_decisions['force_refresh']} force refresh (API)")
        if cache_decisions["not_in_db"]:
            breakdown_parts.append(f"{cache_decisions['not_in_db']} not in DB (API)")

        if breakdown_parts:
            logger.info(f"Breakdown: {', '.join(breakdown_parts)}")

        # 4. Batch refresh tests that need it (with per-entity locks, STORY-046 AC8)
        if tests_to_refresh:
            # Disable autoflush for entire batch operation to prevent nested flush errors
            with self.session.no_autoflush:
                # Batch API calls with multi-lock protection (AC6 fix)
                # Strategy: Acquire all locks for a batch, then make batch API calls
                BATCH_SIZE = 15
                batches = [
                    tests_to_refresh[i : i + BATCH_SIZE]
                    for i in range(0, len(tests_to_refresh), BATCH_SIZE)
                ]

                async def refresh_batch_with_locks(batch: list[int]) -> None:
                    """Refresh a batch of tests with multi-lock protection."""
                    if self.cache:
                        # Get all locks for this batch
                        locks = [self.cache.get_refresh_lock("test", test_id) for test_id in batch]

                        # Acquire all locks concurrently
                        async def acquire_lock(lock: asyncio.Lock) -> asyncio.Lock:
                            await lock.acquire()
                            return lock

                        acquired_locks = await asyncio.gather(
                            *[acquire_lock(lock) for lock in locks]
                        )
                        try:
                            logger.debug(
                                f"Acquired {len(acquired_locks)} test refresh locks for batch"
                            )
                            await self._refresh_tests_batch(batch)
                        finally:
                            # Release all locks
                            for lock in acquired_locks:
                                lock.release()
                    else:
                        # No cache - refresh without locks
                        await self._refresh_tests_batch(batch)

                # Process all batches with progress reporting
                for batch_idx, batch in enumerate(batches, start=1):
                    try:
                        await refresh_batch_with_locks(batch)
                    except Exception as e:
                        # Log but continue - partial success is better than total failure
                        logger.error(f"Batch {batch_idx} refresh failed: {e}")
                    # Always report progress, even on failure (Codex review finding)
                    await safe_batch_callback(on_batch_progress, batch_idx, len(batches))

                # Bulk update synced_at timestamps
                await self._update_tests_synced_at_batch(tests_to_refresh)

            # Commit all changes (tests + sync timestamps) in single transaction
            await self.session.commit()

        # 5. Return tests for ALL requested test IDs from SQLite
        result: dict[int, dict[str, Any]] = {}
        for test_id in test_ids:
            # Query test data from DB
            statement_data = select(Test.data).where(
                Test.id == test_id, Test.customer_id == self.customer_id
            )
            result_data = await self.session.exec(statement_data)
            test_data_json = result_data.first()

            if test_data_json:
                result[test_id] = json.loads(test_data_json)
            else:
                # Test not found (shouldn't happen if refresh succeeded)
                logger.warning(f"Test {test_id} not found in DB after refresh attempt")

        # 6. Build cache stats for transparency
        cache_stats = {
            "total_tests": len(test_ids),
            "cache_hits": cache_hits,
            "api_calls": len(tests_to_refresh),
            "cache_hit_rate": cache_hit_rate,
            "breakdown": {k: v for k, v in cache_decisions.items() if v > 0},  # Only non-zero
        }

        return result, cache_stats

    async def _refresh_tests_batch(self, test_ids: list[int]) -> None:
        """Refresh multiple tests from API (batch operation).

        Pattern: Pre-fetch users to avoid nested flush issues (Codex review feedback).
        Same API calls as before, but reordered to batch user upserts:
        1. Fetch each requested test from API (same calls as before)
        2. Extract unique customer usernames from fetched tests
        3. Bulk upsert users (single IN query + single flush)
        4. Process each test with pre-known user IDs (no nested flushes)

        Note: Caller must commit the transaction after this method.

        Args:
            test_ids: List of test identifiers to refresh
        """
        if not test_ids:
            return

        # Step 1: Fetch each test from API and collect data (same API calls as before)
        tests_data: list[tuple[int, dict[str, Any]]] = []  # (test_id, test_data)
        for test_id in test_ids:
            try:
                response = await self.client.get(f"exploratory_tests/{test_id}")
                test_data = response.get("exploratory_test", {})
                if test_data:
                    tests_data.append((test_id, test_data))
                else:
                    logger.warning(f"Test {test_id} returned empty data from API")
            except Exception as e:
                logger.warning(f"Failed to fetch test {test_id} from API: {e}")

        if not tests_data:
            return

        # Step 2: Extract all unique customer usernames
        usernames: set[str] = set()
        for _, test_data in tests_data:
            if created_by := test_data.get("created_by"):
                usernames.add(created_by)
            if submitted_by := test_data.get("submitted_by"):
                usernames.add(submitted_by)

        # Step 3: Bulk upsert customer users (single IN query + single flush)
        user_id_map: dict[str, int] = {}
        if self.user_repo and usernames:
            user_id_map = await self.user_repo.bulk_upsert_users(
                usernames=usernames,
                user_type="customer",
            )

        # Step 4: Process each test with pre-known user IDs
        for test_id, test_data in tests_data:
            try:
                product_id = test_data.get("product", {}).get("id")
                if not product_id:
                    logger.warning(f"Test {test_id} missing product_id, skipping upsert")
                    continue

                # STORY-024 fix: Preserve bugs_synced_at for existing tests
                if await self.test_exists(test_id, product_id):
                    await self.update_test(test_data, product_id)
                else:
                    await self.insert_test(test_data, product_id, user_id_map=user_id_map)

            except Exception as e:
                logger.warning(f"Failed to process test {test_id}: {e}")
                # Continue with other tests even if one fails

    async def _update_tests_synced_at_batch(self, test_ids: list[int]) -> None:
        """Update synced_at timestamp for multiple tests (bulk update).

        Note: Caller must commit the transaction after this method.

        Args:
            test_ids: List of test identifiers to update
        """
        if not test_ids:
            return

        # Import col for updating
        from sqlmodel import col

        # Bulk update using SQLModel
        now_utc = datetime.now(UTC)  # Keep as datetime object, not ISO string
        statement = select(Test).where(
            col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
        )
        update_result = await self.session.exec(statement)
        tests = update_result.all()

        for test in tests:
            test.synced_at = now_utc
            self.session.add(test)

        # Caller commits (transaction management delegated)

    async def get_test_with_bugs(self, test_id: int) -> dict[str, Any] | None:
        """Get test data with associated bugs (LEFT JOIN).

        Fetches test data from database and includes all associated bugs.
        Returns None if test doesn't exist.

        Args:
            test_id: Test identifier

        Returns:
            Dictionary with test data and bugs list, or None if not found:
                {
                    "test": {...},  # Deserialized test data
                    "bugs": [...]   # List of bug dicts
                }

        Note:
            This query assumes bugs have been refreshed via BugRepository.refresh_bugs().
            Background sync does NOT refresh bugs - they are always fetched on-demand.

            STORY-071: test_environment is read from column (authoritative source), not JSON.
        """
        # Get test data and test_environment column
        statement = select(Test.data, Test.test_environment).where(
            Test.id == test_id, Test.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)
        row = result.first()

        if not row:
            return None

        test_data_json, test_environment_column = row
        test_data = json.loads(test_data_json)

        # STORY-071: Override test_environment with column value (authoritative source)
        # Column takes precedence over JSON blob
        if test_environment_column is not None:
            test_data["test_environment"] = test_environment_column

        # Get bugs for this test
        from sqlmodel import col

        from testio_mcp.models.orm import Bug

        bug_statement = (
            select(Bug.raw_data)
            .where(Bug.test_id == test_id, Bug.customer_id == self.customer_id)
            .order_by(col(Bug.id).desc())  # Order by ID descending (newer bugs have higher IDs)
        )
        bug_result = await self.session.exec(bug_statement)
        bug_data_rows = bug_result.all()
        bugs = [json.loads(raw_data) for raw_data in bug_data_rows]

        return {"test": test_data, "bugs": bugs}

    async def refresh_test(self, test_id: int, user_id_map: dict[str, int] | None = None) -> None:
        """Fetch fresh test data from API and upsert to SQLite.

        Used by get operations to ensure data is always fresh.
        This supplements the background sync which discovers new tests.

        Args:
            test_id: Test identifier
            user_id_map: Optional pre-computed username->user_id map for batch operations.
                         If provided, passes to insert_test to avoid nested flushes.

        Raises:
            httpx.HTTPStatusError: If API request fails (including 404)

        Note:
            Background sync populates tests for list operations (~10ms).
            Refresh operations ensure get operations have fresh data (~70ms).
            Preserves bugs_synced_at for existing tests (STORY-024 fix).
        """
        # Fetch test from API
        # API endpoint: GET /exploratory_tests/{test_id}
        response = await self.client.get(f"exploratory_tests/{test_id}")
        test_data = response.get("exploratory_test", {})

        if not test_data:
            logger.warning(f"Test {test_id} returned empty data from API")
            return

        # Extract product_id from test data
        product_id = test_data.get("product", {}).get("id")
        if not product_id:
            logger.warning(f"Test {test_id} missing product_id, skipping upsert")
            return

        # STORY-024 fix: Preserve bugs_synced_at for existing tests
        # Use update_test (which preserves bugs_synced_at) for existing tests
        # Use insert_test for new tests (bugs_synced_at will be NULL until first bug fetch)
        if await self.test_exists(test_id, product_id):
            await self.update_test(test_data, product_id)
        else:
            await self.insert_test(test_data, product_id, user_id_map=user_id_map)

        # Flush to make changes visible to subsequent queries in same transaction
        await self.session.flush()

    async def _upsert_test_feature(
        self, test_id: int, feature_data: dict[str, Any], product_id: int
    ) -> None:
        """Upsert a single TestFeature from test JSON with proactive integrity checks.

        STORY-044C: Proactive referential integrity pattern
        - Checks if feature exists BEFORE attempting insert/update
        - If feature missing, triggers product-level feature fetch (integrity fill)
        - Prevents FK violations instead of catching IntegrityError reactively

        Args:
            test_id: Test ID
            feature_data: Feature data from test JSON
            product_id: Product ID (needed for feature fetch if missing)

        Example feature_data:
            {
                "id": 1042409,  # TestFeature ID
                "feature_id": 196992,  # Global Feature ID
                "title": "[Presentations] Recording",
                "description": "...",
                "user_stories": ["Story 1", "Story 2"],
                "enable_default": true,
                "enable_content": null,
                "enable_visual": null
            }

        Integrity Fill Triggers:
            - Background sync Phase 3 (discover new tests)
            - Manual test refresh (on-demand via MCP tool)
            - Initial sync (first run)
        """
        from testio_mcp.models.orm import TestFeature

        test_feature_id = feature_data.get("id")
        if not test_feature_id:
            return  # Skip if no ID

        feature_id = feature_data.get("feature_id")
        if not feature_id:
            logger.warning(f"TestFeature {test_feature_id} has no feature_id, skipping")
            return

        # STORY-044C AC1: Proactive feature check BEFORE insert/update
        if not await self._feature_exists(feature_id):
            # Feature missing - trigger integrity fill
            try:
                await self._fetch_and_store_features_for_product(product_id)
            except Exception as e:
                # STORY-044C AC8: Graceful degradation on integrity fill failure
                logger.error(
                    f"Referential integrity fill failed: could not fetch features for "
                    f"product {product_id}: {e}"
                )
                # Emit failure metric
                logger.error(
                    "repository.integrity_fill_failures",
                    extra={
                        "entity_type": "feature",
                        "operation": "sync",
                        "product_id": product_id,
                        "error": str(e),
                    },
                )
                # SKIP test_feature upsert - don't create dangling FK
                return

        # Check if exists (using SQLModel pattern)
        stmt = select(TestFeature).where(TestFeature.id == test_feature_id)
        result = await self.session.exec(stmt)
        existing = result.first()

        # Prepare data - handle None case for user_stories
        user_stories = feature_data.get("user_stories") or []  # Coerce None to []
        user_stories_json = json.dumps(user_stories)

        if existing:
            # Update existing
            existing.customer_id = self.customer_id
            existing.test_id = test_id
            existing.feature_id = feature_id
            existing.title = feature_data.get("title", "")
            existing.description = feature_data.get("description")
            existing.howtofind = feature_data.get("howtofind")
            existing.user_stories = user_stories_json
            existing.enable_default = feature_data.get("enable_default") or False
            existing.enable_content = feature_data.get("enable_content") or False
            existing.enable_visual = feature_data.get("enable_visual") or False
        else:
            # Insert new
            test_feature = TestFeature(
                id=test_feature_id,
                customer_id=self.customer_id,
                test_id=test_id,
                feature_id=feature_id,
                title=feature_data.get("title", ""),
                description=feature_data.get("description"),
                howtofind=feature_data.get("howtofind"),
                user_stories=user_stories_json,
                enable_default=feature_data.get("enable_default") or False,
                enable_content=feature_data.get("enable_content") or False,
                enable_visual=feature_data.get("enable_visual") or False,
            )
            self.session.add(test_feature)

        # STORY-044C AC10: Remove deprecated reactive error handling
        # Proactive check above prevents IntegrityError from ever happening
        # No try/except IntegrityError needed

        # Note: Caller must commit the session
        # This allows batching multiple refreshes in a single transaction

        logger.debug(f"Upserted test_feature {test_feature_id} for test {test_id}")

    # STORY-044C: Referential Integrity Helpers
    # ===========================================================================

    async def _feature_exists(self, feature_id: int) -> bool:
        """Check if feature exists locally (proactive integrity check).

        Used by _upsert_test_feature to prevent FK violations BEFORE attempting insert.

        Args:
            feature_id: Global feature ID to check

        Returns:
            True if feature exists in database, False otherwise

        Example:
            if not await self._feature_exists(feature_id):
                await self._fetch_and_store_features_for_product(product_id)
        """
        from testio_mcp.models.orm import Feature

        stmt = select(Feature.id).where(Feature.id == feature_id)
        result = await self.session.exec(stmt)
        return result.first() is not None

    async def _fetch_and_store_features_for_product(self, product_id: int) -> None:
        """Fetch all features for product from API and store locally (integrity fill).

        Called when test_feature references a feature that doesn't exist.
        Uses FeatureRepository.sync_features() via composition pattern.

        Implements double-check locking pattern to prevent thundering herd:
        1. Acquire per-product lock
        2. Double-check feature still missing (another coroutine may have fetched)
        3. Fetch & store if still missing

        Args:
            product_id: Product ID to fetch features for

        Raises:
            Exception: If API fetch fails (caller handles graceful degradation)

        Logging:
            - WARNING: Integrity fill triggered (indicates data sync gap)
            - INFO: Structured metric for monitoring

        Example:
            try:
                await self._fetch_and_store_features_for_product(product_id)
            except Exception as e:
                logger.error(f"Integrity fill failed: {e}")
                return  # Skip test_feature upsert, don't create dangling FK
        """
        # Get or create lock for this product_id
        if product_id not in self._feature_fetch_locks:
            self._feature_fetch_locks[product_id] = asyncio.Lock()

        lock = self._feature_fetch_locks[product_id]

        async with lock:
            # Double-check pattern: Another coroutine may have fetched while we waited
            # Note: We check if ANY features exist for product, not just the specific feature_id
            # This is simpler and FeatureRepository.sync_features() is idempotent
            from testio_mcp.models.orm import Feature

            check_stmt = (
                select(func.count()).select_from(Feature).where(Feature.product_id == product_id)
            )
            result = await self.session.exec(check_stmt)
            feature_count = result.one()

            if feature_count > 0:
                # Another coroutine already fetched features, we're done
                return

            # Log WARNING (integrity fill indicates data sync gap)
            logger.warning(
                f"Referential integrity fill: features missing for product {product_id}, "
                f"fetching from API (operation: sync)"
            )

            # Fetch & store via composition pattern
            from testio_mcp.repositories.feature_repository import FeatureRepository

            feature_repo = FeatureRepository(self.session, self.client, self.customer_id)
            stats = await feature_repo.sync_features(product_id)

            # Emit structured metric for monitoring
            logger.info(
                "repository.integrity_fills",
                extra={
                    "entity_type": "feature",
                    "operation": "sync",
                    "product_id": product_id,
                    "features_synced": stats.get("total", 0),
                },
            )

    # ===========================================================================
    # End of STORY-044C Integrity Helpers
    # ===========================================================================

    async def get_oldest_mutable_test_synced_at(self) -> str | None:
        """Get the oldest synced_at timestamp for mutable tests only.

        Mutable test statuses (need frequent sync):
        - customer_finalized: Customer marked as final but can change
        - waiting: Waiting to start
        - running: Currently active, bugs being reported
        - locked: Finalized but not archived yet
        - initialized: Created but not started

        Immutable statuses (archived, cancelled) are excluded as they never change.

        Returns:
            Timestamp string (YYYY-MM-DD HH:MM:SS) or None if no mutable tests
        """
        mutable_statuses = ["customer_finalized", "waiting", "running", "locked", "initialized"]

        statement = select(func.min(Test.synced_at)).where(
            Test.customer_id == self.customer_id,
            Test.status.in_(mutable_statuses),  # type: ignore[attr-defined]
        )

        result = await self.session.exec(statement)
        oldest_sync = result.one()

        return oldest_sync.isoformat() if oldest_sync else None

    # ============================================================================
    # Sync Metadata Operations
    # ============================================================================

    async def get_problematic_tests(self, product_id: int | None = None) -> list[dict[str, Any]]:
        """Get tests that failed to sync due to API 500 errors.

        Args:
            product_id: Optional filter for specific product

        Returns:
            List of problematic test records with boundary information
        """
        from testio_mcp.models.orm import SyncMetadata

        statement = select(SyncMetadata.value).where(SyncMetadata.key == "problematic_tests")
        result = await self.session.exec(statement)
        value = result.first()

        if not value:
            return []

        problematic_tests: list[dict[str, Any]] = json.loads(value)

        # Filter by product_id if provided
        if product_id is not None:
            problematic_tests = [t for t in problematic_tests if t.get("product_id") == product_id]

        return problematic_tests

    async def log_problematic_test(self, test_info: dict[str, Any]) -> None:
        """Append problematic test info to sync_metadata.

        Args:
            test_info: Test information dict with boundary data
        """
        from testio_mcp.models.orm import SyncMetadata

        # Get existing problematic tests
        statement = select(SyncMetadata).where(SyncMetadata.key == "problematic_tests")
        result = await self.session.exec(statement)
        metadata = result.first()

        problematic_tests = []
        if metadata and metadata.value:
            problematic_tests = json.loads(metadata.value)

        # Generate unique event_id if not provided
        if "event_id" not in test_info:
            test_info["event_id"] = str(uuid.uuid4())

        # Append new test
        problematic_tests.append(test_info)

        # Update metadata (upsert)
        if metadata:
            metadata.value = json.dumps(problematic_tests)
            self.session.add(metadata)
        else:
            new_metadata = SyncMetadata(
                key="problematic_tests", value=json.dumps(problematic_tests)
            )
            self.session.add(new_metadata)

        await self.session.commit()

        logger.warning(
            f"Logged problematic test: event_id={test_info.get('event_id')}, "
            f"product_id={test_info.get('product_id')}, "
            f"position_range={test_info.get('position_range')}, "
            f"recovery_attempts={test_info.get('recovery_attempts')}"
        )
