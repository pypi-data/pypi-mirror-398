"""Test service for exploratory test status operations.

This service handles business logic for test status queries, following
the service layer pattern (ADR-006). It is framework-agnostic and can
be used from MCP tools, REST APIs, CLI, or webhooks.

STORY-023c: Refactored to use repositories instead of cache.
STORY-023d: Added list_tests and bug operations.

Responsibilities:
- Test listing and filtering (from SQLite)
- API refresh orchestration (always fresh data)
- Data aggregation (test + bugs)
- Bug operations
- Domain exception raising

Does NOT handle:
- MCP protocol formatting
- User-facing error messages
- HTTP transport concerns
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

from testio_mcp.client import TestIOClient
from testio_mcp.exceptions import ProductNotFoundException, TestNotFoundException
from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.repositories.test_repository import TestRepository
from testio_mcp.schemas.constants import VALID_TEST_STATUSES
from testio_mcp.services.base_service import BaseService
from testio_mcp.utilities import calculate_acceptance_rates, classify_bugs

if TYPE_CHECKING:
    from testio_mcp.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


def _extract_enum_value(value: str | Enum) -> str:
    """Extract string value from enum or return string as-is.

    Helper for accepting both enum instances (from MCP tools) and raw strings
    (from tests, future REST API, etc.) without requiring conversion at call sites.

    Args:
        value: String or enum instance

    Returns:
        String value

    Example:
        >>> _extract_enum_value(TestStatus.RUNNING)
        'running'
        >>> _extract_enum_value("running")
        'running'
    """
    return value.value if isinstance(value, Enum) else value


class TestService(BaseService):
    """Business logic for exploratory test operations.

    Uses repositories for data access (STORY-023c).
    Background sync keeps SQLite fresh for list operations.
    Get operations refresh from API for always-fresh data.

    Example:
        ```python
        service = TestService(
            client=client,
            test_repo=test_repo,
            bug_repo=bug_repo
        )
        status = await service.get_test_status(test_id=109363)
        ```
    """

    __test__ = False

    def __init__(
        self,
        client: TestIOClient,
        test_repo: TestRepository,
        bug_repo: BugRepository,
        product_repo: "ProductRepository",
    ) -> None:
        """Initialize service with API client and repositories.

        Args:
            client: TestIO API client for making HTTP requests
            test_repo: Repository for test data access
            bug_repo: Repository for bug data access
            product_repo: Repository for product data access
        """
        super().__init__(client)
        self.test_repo = test_repo
        self.bug_repo = bug_repo
        self.product_repo = product_repo

    async def get_test_summary(self, test_id: int) -> dict[str, Any]:
        """Get comprehensive status of a single exploratory test.

        This method (STORY-024 intelligent caching pattern):
        1. Refreshes test metadata from API (always fresh)
        2. Uses intelligent bug caching (immutable tests cached, mutable refreshed if stale)
        3. Queries data from SQLite repositories
        4. Aggregates bug summary statistics
        5. Returns structured data

        Args:
            test_id: Exploratory test ID (integer from API, e.g., 109363)

        Returns:
            Dictionary with complete test details and bug summary

        Raises:
            TestNotFoundException: If test ID not found (404)
            TestIOAPIError: If API returns error response

        Example:
            >>> status = await service.get_test_summary(109363)
            >>> print(status["test"]["title"])
            'Evgeniya Testing'
            >>> print(status["bugs"]["total_count"])
            1
        """
        # Step 1: Refresh test metadata from API (always fresh)
        try:
            await self.test_repo.refresh_test(test_id)
        except Exception as e:
            # Transform 404 to domain exception
            if hasattr(e, "status_code") and e.status_code == 404:
                raise TestNotFoundException(test_id) from e
            raise

        # Commit metadata update before bug refresh to avoid SQLite write lock contention.
        # Without this, the long-lived service session can hold a write transaction open
        # while the bug refresh uses an isolated session, leading to "database is locked"
        # when both attempt to update the tests table concurrently.
        await self.test_repo.commit()

        # Step 2: Intelligent bug caching (same logic as EBR)
        # Immutable tests (archived/cancelled): SQLite cache
        # Mutable tests (running/locked): Refresh if stale (>1h)
        bugs_by_test, _cache_stats = await self.bug_repo.get_bugs_cached_or_refresh(
            test_ids=[test_id],
            force_refresh=False,
        )

        # Step 3: Query test metadata from SQLite
        test_with_bugs = await self.test_repo.get_test_with_bugs(test_id)

        if not test_with_bugs:
            raise TestNotFoundException(test_id)

        test = test_with_bugs["test"]
        # Use bugs from intelligent cache (not from test_with_bugs)
        bugs = bugs_by_test.get(test_id, [])

        # Step 4: Aggregate bug summary (with platform breakdown)
        bug_summary = self._aggregate_bug_summary(bugs)

        # Step 4: Build response (keep IDs as integers from API)
        # Summarize requirements for quick diagnostic use
        requirements_summary = self._summarize_requirements(test.get("requirements", []))

        return {
            "test": {
                "id": test["id"],
                "title": test["title"],
                "goal": test.get("goal"),
                "instructions": test.get("instructions_text")
                or test.get("instructions"),  # STORY-057: Added from AC4
                "out_of_scope": test.get("out_of_scope"),  # STORY-057: Added from AC4
                "testing_type": test["testing_type"],
                "duration": test.get("duration"),
                "status": test["status"],
                "review_status": test.get("review_status"),
                "requirements_summary": requirements_summary,
                "enable_low": test.get("enable_low", False),  # STORY-057: Config flag from AC4
                "enable_high": test.get("enable_high", False),  # STORY-057: Config flag from AC4
                "enable_critical": test.get(
                    "enable_critical", False
                ),  # STORY-057: Config flag from AC4
                "starts_at": test.get("starts_at"),
                "ends_at": test.get("ends_at"),
                "product": {
                    "id": test["product"]["id"],
                    "name": test["product"]["name"],
                },
                "feature": (
                    {
                        "id": test["feature"]["id"],
                        "name": test["feature"]["name"],
                    }
                    if test.get("feature")
                    else None
                ),
                "test_environment": (
                    {
                        "id": test["test_environment"]["id"],
                        "title": test["test_environment"]["title"],
                    }
                    if test.get("test_environment")
                    else None
                ),  # STORY-073: AC1
            },
            "bugs": bug_summary,
        }

    def _aggregate_bug_summary(self, bugs: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate bug data into summary statistics.

        This is a private helper method that processes raw bug data from
        the API into a structured summary with:
        - Total count
        - Counts by severity
        - Counts by status (active_accepted, auto_accepted, rejected, open)
        - Acceptance rates (if auto_accepted field available)
        - Recent bugs (last 3)

        Bug Status Taxonomy (STORY-005c):
        - active_accepted: status="accepted" AND auto_accepted=false
        - auto_accepted: status="accepted" AND auto_accepted=true
        - total_accepted: active_accepted + auto_accepted (derived)
        - rejected: status="rejected"
        - open: status="forwarded" (awaiting customer triage)

        Args:
            bugs: List of bug dictionaries from API

        Returns:
            Dictionary with aggregated bug statistics

        Example:
            >>> bugs = [
            ...     {"id": 1, "severity": "high", "status": "accepted", "auto_accepted": false},
            ...     {"id": 2, "severity": "low", "status": "forwarded"}
            ... ]
            >>> summary = service._aggregate_bug_summary(bugs)
            >>> summary["total_count"]
            2
            >>> summary["by_severity"]["high"]
            1
            >>> summary["by_status"]["active_accepted"]
            1
            >>> summary["by_status"]["open"]
            1
        """
        summary: dict[str, Any] = {
            "total_count": len(bugs),
            "known_bugs_count": 0,  # STORY-072: Count of bugs marked as known issues
            "by_severity": {
                "critical": 0,
                "high": 0,
                "low": 0,
                "visual": 0,
                "content": 0,
                "custom": 0,
            },
            "by_status": {
                "active_accepted": 0,
                "auto_accepted": 0,
                "total_accepted": 0,
                "rejected": 0,
                "open": 0,
            },
            "by_platform": {
                "operating_systems": {},
                "browsers": {},
                "device_categories": {},
            },
            "acceptance_rates": None,
            "recent_bugs": [],
        }

        for bug in bugs:
            # Count by severity
            severity = bug.get("severity", "unknown")
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1

            # Count known bugs (STORY-072)
            if bug.get("known", False):
                summary["known_bugs_count"] += 1

            # Aggregate platform data for diagnostic insights
            devices = bug.get("devices", [])
            for device in devices:
                # Operating system
                os_info = device.get("operating_system")
                if os_info:
                    os_name = os_info.get("name", "Unknown")
                    summary["by_platform"]["operating_systems"][os_name] = (
                        summary["by_platform"]["operating_systems"].get(os_name, 0) + 1
                    )

                # Browser
                browsers = device.get("browsers", [])
                for browser in browsers:
                    browser_name = browser.get("name", "Unknown")
                    summary["by_platform"]["browsers"][browser_name] = (
                        summary["by_platform"]["browsers"].get(browser_name, 0) + 1
                    )

                # Device category
                category = device.get("category")
                if category:
                    category_name = category.get("name", "Unknown")
                    summary["by_platform"]["device_categories"][category_name] = (
                        summary["by_platform"]["device_categories"].get(category_name, 0) + 1
                    )

        # Classify bugs into status buckets using shared utility (STORY-023b)
        bug_counts = classify_bugs(bugs)
        summary["by_status"]["active_accepted"] = bug_counts["active_accepted"]
        summary["by_status"]["auto_accepted"] = bug_counts["auto_accepted"]
        summary["by_status"]["total_accepted"] = bug_counts["total_accepted"]
        summary["by_status"]["rejected"] = bug_counts["rejected"]
        summary["by_status"]["open"] = bug_counts["open"]

        # Always calculate acceptance rates (individual rates may be None if no bugs)
        # STORY-047: classify_bugs() uses enriched status from database
        # STORY-081: rates dict always returned (never None), but individual rates may be None
        summary["acceptance_rates"] = self._calculate_acceptance_rates(
            summary["by_status"], summary["total_count"]
        )

        # Get 3 most recent bugs (sorted by created_at descending)
        sorted_bugs = sorted(
            bugs,
            key=lambda b: b.get("created_at", ""),
            reverse=True,
        )
        summary["recent_bugs"] = [
            {
                "id": str(bug["id"]),
                "title": bug["title"],
                "severity": bug["severity"],
                "status": bug["status"],
                "created_at": bug.get("created_at"),
                "known": bug.get("known", False),  # STORY-072
            }
            for bug in sorted_bugs[:3]
        ]

        return summary

    def _summarize_requirements(self, requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Summarize test requirements into concise format.

        Extracts key requirement info (OS, browsers, device types) from
        verbose requirements array for quick diagnostic reference.

        Preserves OS-browser relationships and device category context.

        Version Range Handling:
        - Exact version (min == max): "Windows 11"
        - Minimum only: "Windows 10+"
        - Maximum only: "Windows ≤11"
        - Range (min != max): "Windows 10-11"
        - No version: "Windows"

        Args:
            requirements: List of requirement objects from test data

        Returns:
            List of requirement summaries with OS-browser relationships:
                [
                    {
                        "platform": "Windows 11 (Computers)",
                        "browsers": ["Chrome", "Firefox", "Edge Chromium"]
                    },
                    {
                        "platform": "iOS 17.0+ (Smartphones)",
                        "browsers": ["Chrome", "Safari"]
                    }
                ]
        """
        summaries = []

        for req in requirements:
            # Extract OS with version range
            os_info = req.get("operating_system")
            category = req.get("category")
            browsers = req.get("browsers", [])

            if os_info:
                os_name = os_info.get("name", "Unknown")
                min_version = req.get("min_operating_system_version")
                max_version = req.get("max_operating_system_version")

                # Build platform string with version range
                if min_version and max_version:
                    min_name = min_version.get("name", "")
                    max_name = max_version.get("name", "")
                    # If min and max are the same, show exact version
                    if min_name == max_name:
                        platform_str = f"{os_name} {min_name}"
                    else:
                        # Show range: "Windows 10-11"
                        platform_str = f"{os_name} {min_name}-{max_name}"
                elif min_version:
                    # Only minimum: "Windows 10+"
                    version_name = min_version.get("name", "")
                    platform_str = f"{os_name} {version_name}+"
                elif max_version:
                    # Only maximum: "Windows ≤11"
                    version_name = max_version.get("name", "")
                    platform_str = f"{os_name} ≤{version_name}"
                else:
                    # No version constraints
                    platform_str = os_name

                # Add device category context to disambiguate
                # (e.g., "iOS 17.0+ (Smartphones)" vs "iOS 17.0+ (Tablets)")
                if category:
                    category_name = category.get("name", "Unknown")
                    platform_str = f"{platform_str} ({category_name})"

                # Extract browser names
                browser_names = [b.get("name", "Unknown") for b in browsers]

                summaries.append(
                    {
                        "platform": platform_str,
                        "browsers": browser_names,
                    }
                )

        return summaries

    async def list_tests(
        self,
        product_id: int,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        statuses: list[str | Enum] | None = None,
        testing_type: str | None = None,
        sort_by: str = "end_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """List tests for a specific product with pagination, filtering, and sorting.

        This method queries local SQLite only (fast, no API calls).
        For detailed test information with bug summaries, use get_test_status.

        This method (STORY-054 AC10 added sorting and testing_type):
        1. Extracts enum values if enums provided
        2. Validates statuses and sorting parameters
        3. Queries tests from SQLite using TestRepository with filtering and sorting
        4. Determines has_more flag (heuristic: true if results == per_page)
        5. Returns structured data with pagination metadata

        Args:
            product_id: The product ID (integer from API, e.g., 25073)
            page: Page number (1-indexed, default: 1)
            per_page: Number of results per page (default: 100)
            offset: Additional offset on top of page calculation (default: 0)
                   Final offset = offset + (page - 1) * per_page
                   Use case: Fetch small sample (page=1, per_page=10), then continue
                   with larger pages (page=1, per_page=100, offset=10)
            statuses: Filter by test statuses (enums or strings).
                     Default: None (returns ALL tests)
                     Available: running, locked, archived, cancelled,
                                customer_finalized, initialized
                     None or [] means return all tests (no filtering)
            testing_type: Filter by testing type (coverage, focused, rapid).
                         Default: None (all types)
            sort_by: Field to sort by (start_at, end_at, status, title).
                    Default: end_at
            sort_order: Sort order (asc, desc). Default: desc

        Returns:
            Dictionary with product info, filtered tests, and pagination metadata:
            - product: Product details
            - tests: Filtered test list for current page
            - statuses_filter: Effective statuses used (all 6 if None/[], exact list otherwise)
            - has_more: Whether more results may be available (heuristic)

        Raises:
            ValueError: If any status/sort value is invalid
            ProductNotFoundException: If product ID doesn't exist (404)

        Example:
            >>> result = await service.list_tests(
            ...     product_id=25073,
            ...     testing_type="coverage",
            ...     sort_by="title",
            ...     sort_order="asc"
            ... )
            >>> print(result["tests"][0]["title"])
            'A/B Test Feature'
        """
        # Extract enum values if needed (supports both enums and strings)
        statuses_str: list[str] | None = (
            [_extract_enum_value(s) for s in statuses] if statuses is not None else None
        )

        # Validate statuses if provided (runtime validation)
        if statuses_str is not None and len(statuses_str) > 0:
            self._validate_statuses(statuses_str)

        # Determine effective statuses for response (output contract)
        effective_statuses = statuses_str if statuses_str else VALID_TEST_STATUSES

        # Query product info from ProductRepository (STORY-032A)
        product_info = await self.product_repo.get_product_info(product_id)
        if not product_info:
            raise ProductNotFoundException(product_id)

        # Staleness check: Refresh mutable test metadata if stale (STORY-046, AC10)
        # Get all test IDs for this product first (fast query)
        test_ids_result = await self.test_repo.get_test_ids_for_product(product_id)
        if test_ids_result:
            # Check staleness and refresh if needed (read-through caching)
            _, cache_stats = await self.test_repo.get_tests_cached_or_refresh(test_ids_result)

            # Log warning if cache hit rate < 50%
            cache_hit_rate = cache_stats.get("cache_hit_rate", 100.0)
            if cache_hit_rate < 50.0:
                logger.warning(
                    f"Low cache hit rate for product {product_id}: {cache_hit_rate:.1f}% "
                    f"({cache_stats.get('cache_hits')}/{cache_stats.get('total_tests')} cached)"
                )

        # Query tests from TestRepository with pagination (AC3)
        # SQL handles filtering, sorting, and pagination (fast, ~10ms)
        tests = await self.test_repo.query_tests(
            product_id=product_id,
            statuses=statuses_str,  # SQL-level filtering (None = all statuses)
            testing_type=testing_type,  # STORY-054 AC10
            sort_by=sort_by,  # STORY-054 AC10
            sort_order=sort_order,  # STORY-054 AC10
            page=page,
            per_page=per_page,
            offset=offset,
        )

        # Get total count of matching tests (for pagination metadata)
        # SQL COUNT query with same filters (fast, ~5ms)
        total_count = await self.test_repo.count_filtered_tests(
            product_id=product_id,
            statuses=statuses_str,  # Same filters as query
            testing_type=testing_type,  # STORY-054 AC10
        )

        # Determine has_more flag (heuristic: true if results == per_page)
        # This indicates likely more results available (not guaranteed)
        has_more = len(tests) == per_page

        # Calculate actual offset used (for pagination metadata)
        actual_offset = offset + (page - 1) * per_page

        # Build response with pagination metadata (output contract clarity)
        return {
            "product": product_info,
            "tests": tests,
            "statuses_filter": effective_statuses,  # Shows what filter was applied
            "total_count": total_count,  # Total matching results across all pages
            "offset": actual_offset,  # Actual offset used in query
            "has_more": has_more,  # Pagination heuristic
        }

    def _validate_statuses(self, statuses: list[str]) -> None:
        """Validate that all provided statuses are valid.

        Args:
            statuses: List of status strings to validate

        Raises:
            ValueError: If any status is invalid with descriptive message
                       listing all valid statuses

        Example:
            >>> service._validate_statuses(["running", "locked"])  # No error
            >>> service._validate_statuses(["invalid"])  # Raises ValueError
        """
        invalid = [s for s in statuses if s not in VALID_TEST_STATUSES]
        if invalid:
            raise ValueError(
                f"Invalid status values: {', '.join(invalid)}. "
                f"Valid statuses: {', '.join(VALID_TEST_STATUSES)}"
            )

    def _aggregate_bug_counts(self, bugs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Aggregate bugs by test_cycle_id.

        Groups bugs by test ID and counts them by severity.

        Args:
            bugs: List of bug dictionaries from API

        Returns:
            Dictionary mapping test_id -> {total: int, by_severity: {severity: count}}

        Example:
            >>> bugs = [
            ...     {"test": {"id": "1"}, "severity": "high"},
            ...     {"test": {"id": "1"}, "severity": "low"}
            ... ]
            >>> counts = service._aggregate_bug_counts(bugs)
            >>> counts["1"]["total"]
            2
            >>> counts["1"]["by_severity"]["high"]
            1
        """
        bug_counts: dict[str, dict[str, Any]] = {}
        for bug in bugs:
            test_id = str(bug.get("test", {}).get("id", ""))
            if not test_id:
                continue

            if test_id not in bug_counts:
                bug_counts[test_id] = {"total": 0, "by_severity": {}}

            bug_counts[test_id]["total"] += 1
            severity = bug.get("severity", "unknown")
            bug_counts[test_id]["by_severity"][severity] = (
                bug_counts[test_id]["by_severity"].get(severity, 0) + 1
            )

        return bug_counts

    async def get_test_bugs(self, test_id: int) -> dict[str, Any]:
        """Get all bugs for a specific test (always fresh).

        This method (added in STORY-023d):
        1. Refreshes bugs from API (always fresh)
        2. Queries bugs from SQLite using BugRepository
        3. Classifies bugs by status
        4. Returns structured data

        Args:
            test_id: Exploratory test ID (integer from API, e.g., 109363)

        Returns:
            Dictionary with bug list and classification counts

        Raises:
            TestNotFoundException: If test ID not found (404)
            TestIOAPIError: If API returns error response

        Example:
            >>> result = await service.get_test_bugs(test_id=109363)
            >>> print(result["total_count"])
            5
            >>> print(result["by_status"]["active_accepted"])
            3
        """
        # Step 1: Refresh bugs from API (always fresh)
        try:
            await self.bug_repo.refresh_bugs(test_id)
        except Exception as e:
            # Transform 404 to domain exception
            if hasattr(e, "status_code") and e.status_code == 404:
                raise TestNotFoundException(test_id) from e
            raise

        # Step 2: Query from SQLite
        bugs = await self.bug_repo.get_bugs(test_id)

        # Step 3: Classify bugs using shared utility
        bug_counts = classify_bugs(bugs)

        # Step 4: Build response
        return {
            "test_id": test_id,
            "bugs": bugs,
            "total_count": len(bugs),
            "by_status": {
                "active_accepted": bug_counts["active_accepted"],
                "auto_accepted": bug_counts["auto_accepted"],
                "total_accepted": bug_counts["total_accepted"],
                "rejected": bug_counts["rejected"],
                "open": bug_counts["open"],
            },
        }

    def _calculate_acceptance_rates(
        self, bugs_by_status: dict[str, int], total_bugs: int
    ) -> dict[str, Any]:
        """Calculate acceptance rates from bug counts.

        Acceptance rates use total bugs as denominator (all bugs regardless of status).
        Human-reviewed bugs (reviewed) = active_accepted + rejected (excludes auto_accepted).

        This method wraps the shared utility function and adds service-specific
        fields (open_count, has_alert) that depend on TestService settings.

        After STORY-081, calculate_acceptance_rates() always returns a dict
        (never None). Individual rate values may be None when total_bugs == 0.

        Args:
            bugs_by_status: Dictionary with bug counts by status
            total_bugs: Total bug count (pre-calculated, not derived)

        Returns:
            Dictionary with acceptance rates (individual rates may be None if no bugs)

        Example:
            >>> bugs_by_status = {
            ...     "active_accepted": 12,
            ...     "auto_accepted": 3,
            ...     "rejected": 3,
            ...     "open": 2
            ... }
            >>> rates = service._calculate_acceptance_rates(bugs_by_status, 20)
            >>> rates["active_acceptance_rate"]
            0.6  # 12/20
            >>> rates["overall_acceptance_rate"]
            0.75  # (12+3)/20
        """
        # Use shared utility for core acceptance rate calculation (STORY-023b)
        # Pass explicit total_bugs for future-proofing (handles new bug statuses)
        rates = calculate_acceptance_rates(
            active_accepted=bugs_by_status["active_accepted"],
            auto_accepted=bugs_by_status["auto_accepted"],
            rejected=bugs_by_status["rejected"],
            open_bugs=bugs_by_status["open"],
            total_bugs=total_bugs,  # Use pre-calculated total (not derived)
        )

        # Add service-specific fields
        from testio_mcp.config import settings

        rates["open_count"] = bugs_by_status["open"]

        # auto_acceptance_rate may be None (no accepted bugs) or float (0.0 to 1.0)
        auto_rate = rates["auto_acceptance_rate"]
        rates["has_alert"] = (
            auto_rate is not None and auto_rate > settings.AUTO_ACCEPTANCE_ALERT_THRESHOLD
        )

        # review_rate is now calculated in the shared utility (no duplication!)
        return rates
