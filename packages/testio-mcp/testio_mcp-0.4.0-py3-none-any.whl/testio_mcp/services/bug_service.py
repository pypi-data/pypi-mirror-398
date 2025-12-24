"""Bug service for bug listing and filtering operations.

This service handles business logic for bug queries, following
the service layer pattern (ADR-006). It is framework-agnostic and can
be used from MCP tools, REST APIs, CLI, or webhooks.

STORY-084: Created for list_bugs tool implementation.

Responsibilities:
- Bug listing and filtering (from SQLite)
- Pagination and sorting
- Filter combination (AND logic)
- Domain exception raising

Does NOT handle:
- MCP protocol formatting
- User-facing error messages
- HTTP transport concerns
"""

import logging
from typing import TYPE_CHECKING, Any

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.services.base_service import BaseService

if TYPE_CHECKING:
    from testio_mcp.repositories.test_repository import TestRepository

logger = logging.getLogger(__name__)


class BugService(BaseService):
    """Business logic for bug operations.

    Uses repositories for data access.
    Handles filtering, pagination, and sorting.

    Example:
        ```python
        service = BugService(
            client=client,
            bug_repo=bug_repo,
            test_repo=test_repo
        )
        result = await service.list_bugs(
            test_ids=[123, 456],
            status=["rejected"],
            page=1,
            per_page=50
        )
        ```
    """

    __test__ = False

    def __init__(
        self,
        client: TestIOClient,
        bug_repo: BugRepository,
        test_repo: "TestRepository",
    ) -> None:
        """Initialize service with API client and repositories.

        Args:
            client: TestIO API client for making HTTP requests
            bug_repo: Repository for bug data access
            test_repo: Repository for test data access (to validate test_ids)
        """
        super().__init__(client)
        self.bug_repo = bug_repo
        self.test_repo = test_repo

    async def list_bugs(
        self,
        test_ids: list[int],
        status: list[str] | None = None,
        severity: list[str] | None = None,
        rejection_reason: list[str] | None = None,
        reported_by_user_id: int | None = None,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        sort_by: str = "reported_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """List bugs for specified tests with filters, pagination, and sorting.

        Returns bugs only for the specified test IDs (scoped query prevents
        mass data fetch). Combines multiple filters with AND logic.

        Staleness check: Refreshes test metadata (and cascades to bugs) if stale,
        using same pattern as query_metrics and get_product_quality_report.

        Args:
            test_ids: Required list of test identifiers to scope query
            status: Optional filter by bug status (single value or list)
            severity: Optional filter by bug severity (single value or list)
            rejection_reason: Optional filter by rejection reason (single value or list)
            reported_by_user_id: Optional filter by reporting user ID
            page: Page number (1-indexed) for pagination
            per_page: Number of items per page (default: 100)
            offset: Starting offset for pagination (0-indexed)
            sort_by: Field to sort by (reported_at, severity, status, title)
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with:
                - bugs: List of bug dictionaries with minimal fields
                - pagination: PaginationInfo with page metadata
                - filters_applied: Dictionary of applied filters for transparency
                - warnings: List of warning messages (if tests not found or stale)
        """
        warnings: list[str] = []

        # Check staleness and refresh test metadata (cascades to bugs)
        # Same pattern as query_metrics and get_product_quality_report
        tests_dict, test_stats = await self.test_repo.get_tests_cached_or_refresh(test_ids)

        # Warn if tests not found (404 or never synced)
        found_test_ids = set(tests_dict.keys())
        missing_test_ids = set(test_ids) - found_test_ids
        if missing_test_ids:
            warnings.append(
                f"Warning: {len(missing_test_ids)} test(s) not found "
                f"(IDs: {sorted(missing_test_ids)}). "
                "These tests may not exist, may have been deleted, or haven't been synced yet. "
                "Use list_tests to see available tests."
            )

        # Warn if many tests needed refresh (stale metadata)
        if test_stats.get("cache_hit_rate", 100.0) < 50.0:
            api_calls = test_stats.get("api_calls", 0)
            warnings.append(
                f"Warning: {api_calls} test(s) had stale metadata and were refreshed from API."
            )

        # Delegate to repository for query (now safe - tests refreshed if needed)
        bugs, total_count = await self.bug_repo.list_bugs(
            test_ids=test_ids,
            status=status,
            severity=severity,
            rejection_reason=rejection_reason,
            reported_by_user_id=reported_by_user_id,
            page=page,
            per_page=per_page,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Calculate pagination metadata
        actual_offset = offset + (page - 1) * per_page
        start_index = actual_offset
        end_index = actual_offset + len(bugs) - 1 if bugs else -1
        has_more = actual_offset + len(bugs) < total_count

        # Build filters_applied for transparency
        filters_applied: dict[str, object] = {"test_ids": test_ids}
        if status:
            filters_applied["status"] = status
        if severity:
            filters_applied["severity"] = severity
        if rejection_reason:
            filters_applied["rejection_reason"] = rejection_reason
        if reported_by_user_id:
            filters_applied["reported_by_user_id"] = reported_by_user_id

        # Warn if no bugs found for valid tests (could be legitimately empty)
        if total_count == 0 and found_test_ids:
            warnings.append(
                f"Info: No bugs found for {len(found_test_ids)} test(s). "
                "This could mean the tests have no bugs, or bugs haven't been synced yet."
            )

        result: dict[str, Any] = {
            "bugs": bugs,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "offset": actual_offset,
                "start_index": start_index,
                "end_index": end_index,
                "total_count": total_count,
                "has_more": has_more,
            },
            "filters_applied": filters_applied,
        }

        # Add warnings if any
        if warnings:
            result["warnings"] = warnings

        return result

    async def get_bug_summary(self, bug_id: int) -> dict[str, Any]:
        """Get bug summary with full details, related entities, and metadata.

        STORY-085: Added for get_bug_summary tool.

        SQLite-only (no API calls). Returns comprehensive bug information with:
        - Core fields (id, title, severity, status, known)
        - Detail fields (actual_result, expected_result, steps)
        - Rejection field (rejection_reason if rejected)
        - Related entities (reported_by_user, test, feature)
        - Metadata (reported_at, data_as_of)

        Args:
            bug_id: Bug identifier

        Returns:
            Bug summary dictionary with all fields per AC1-3

        Raises:
            BugNotFoundException: If bug not found

        Example:
            >>> summary = await service.get_bug_summary(12345)
            >>> print(summary["rejection_reason"])
            test_is_invalid
        """
        from datetime import UTC, datetime

        from testio_mcp.exceptions import BugNotFoundException

        # Delegate to repository
        bug_dict = await self.bug_repo.get_bug_by_id(bug_id)

        if not bug_dict:
            raise BugNotFoundException(bug_id)

        # Add data_as_of timestamp for staleness visibility (AC3)
        return {
            **bug_dict,
            "data_as_of": datetime.now(UTC).isoformat(),
        }
