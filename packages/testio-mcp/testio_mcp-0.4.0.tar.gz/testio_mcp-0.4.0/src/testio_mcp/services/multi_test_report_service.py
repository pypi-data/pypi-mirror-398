"""Multi-test reporting service for Product Quality Report (PQR) generation.

This service aggregates bug metrics across multiple tests for products,
providing comprehensive quality reporting capabilities.

STORY-023e: Implements PQR functionality on SQLite-first architecture
PQR Refactor: Multi-product support, test_ids filtering, include_test_data flag

Responsibilities:
- Multi-product bug aggregation (portfolio analysis)
- Flexible date filtering (ISO 8601, business terms, natural language)
- Acceptance rate calculations
- Test status filtering
- Period summarization
- Per-product breakdown for multi-product queries

Does NOT handle:
- MCP protocol formatting
- User-facing error messages
- HTTP transport concerns
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from testio_mcp.client import TestIOClient
from testio_mcp.config import settings
from testio_mcp.exceptions import (
    ProductNotFoundException,
    ValidationError,
)
from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.repositories.test_repository import TestRepository
from testio_mcp.schemas.constants import EXECUTED_TEST_STATUSES
from testio_mcp.schemas.playbook_thresholds import PlaybookThresholds
from testio_mcp.services.base_service import BaseService
from testio_mcp.utilities.bug_classifiers import (
    calculate_acceptance_rates,
    classify_bugs,
)
from testio_mcp.utilities.date_utils import parse_flexible_date
from testio_mcp.utilities.file_export import (
    get_file_format,
    resolve_output_path,
    write_report_to_file,
)
from testio_mcp.utilities.health_status import compute_health_indicators_dict
from testio_mcp.utilities.progress import ProgressReporter

if TYPE_CHECKING:
    from testio_mcp.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class MultiTestReportService(BaseService):
    """Service for multi-test reporting and aggregation.

    Generates Product Quality Reports (PQR) that aggregate metrics across
    multiple tests for one or more products (portfolio analysis).

    Example:
        ```python
        service = MultiTestReportService(
            client=client,
            test_repo=test_repo,
            bug_repo=bug_repo,
            product_repo=product_repo,
        )
        # Single product
        report = await service.get_product_quality_report(
            product_ids=[598],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        # Multi-product (portfolio)
        report = await service.get_product_quality_report(
            product_ids=[598, 599, 600],
        )
        # Specific tests only
        report = await service.get_product_quality_report(
            product_ids=[598],
            test_ids=[141290, 141285],
        )
        ```
    """

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

    async def get_product_quality_report(
        self,
        product_ids: list[int],
        test_ids: list[int] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: list[str] | None = None,
        output_file: str | None = None,
        progress: ProgressReporter | None = None,
        include_test_data: bool = True,
    ) -> dict[str, Any]:
        """Generate Product Quality Report for one or more products.

        Aggregates bug metrics across tests with flexible filtering.
        Supports multi-product queries for portfolio analysis.

        Args:
            product_ids: List of product IDs to report on (required, non-empty)
            test_ids: Optional filter to specific test IDs. If provided, only
                     these tests are included. Must belong to product_ids.
            start_date: Start date (ISO 8601, relative, or natural language)
                       Examples: "2024-01-01", "last 30 days", "this quarter"
                       Filters on test end_at (when test completed).
            end_date: End date (ISO 8601, relative, or natural language)
                     Examples: "2024-12-31", "today", "yesterday"
                     Filters on test end_at (when test completed).
            statuses: Filter tests by status. If None, excludes ["initialized", "cancelled"]
                     by default (only executed tests). Pass explicit list to override.
            output_file: Optional path to export full report as file.
                        If specified, includes full test_data in export.
            progress: Optional ProgressReporter for real-time progress updates.
            include_test_data: If True, include per-test details in response.
                              Set to False for MCP (token efficiency).
                              Set to True for REST API / file export.

        Returns:
            Dictionary with structure:
                {
                    "summary": {...},
                    "product_ids": [598, 599],
                    "products": [{"id": 598, "title": "Android"}, ...],
                    "test_ids": [141290, 141285, ...],
                    "by_product": [...] | None,  # Only for multi-product
                    "test_data": [...] | None,   # Only when include_test_data=True
                    "thresholds": {...},
                }

            When output_file is specified, also includes:
                {
                    "file_path": str,
                    "record_count": int,
                    "file_size_bytes": int,
                    "format": "json",
                }

        Raises:
            ValidationError: If product_ids is empty or test_ids is empty list
            ProductNotFoundException: If any product doesn't exist
            TestNotFoundException: If any test_id doesn't exist
            TestProductMismatchError: If test_ids don't belong to product_ids
        """
        # Initialize progress reporter (noop if None)
        progress = progress or ProgressReporter.noop()

        # Validate product_ids is not empty
        if not product_ids:
            raise ValidationError("product_ids", "At least one product_id required")

        # Validate test_ids (if provided) is not empty
        if test_ids is not None and len(test_ids) == 0:
            raise ValidationError("test_ids", "Empty test_ids invalid. Use None for all tests")

        # Dedupe product_ids while preserving order
        product_ids = list(dict.fromkeys(product_ids))

        # Dedupe test_ids while preserving order
        if test_ids is not None:
            test_ids = list(dict.fromkeys(test_ids))

        # Mutual exclusivity: test_ids cannot combine with date/status filters
        # test_ids means "report on exactly these tests" - additional filters are confusing
        if test_ids:
            if start_date or end_date:
                raise ValidationError(
                    field="test_ids",
                    message="Cannot use test_ids with date filters. "
                    "test_ids specifies exact tests; date filters are for discovery.",
                )
            if statuses:
                raise ValidationError(
                    field="test_ids",
                    message="Cannot use test_ids with status filters. "
                    "test_ids specifies exact tests; status filters are for discovery.",
                )

        # Verify all products exist and collect their info
        products_info: list[dict[str, Any]] = []
        for product_id in product_ids:
            product_info = await self.product_repo.get_product_info(product_id)
            if not product_info:
                raise ProductNotFoundException(product_id)
            products_info.append(
                {
                    "id": product_id,
                    "title": product_info.get("name", f"Product {product_id}"),
                }
            )

        # Validate test_ids belong to product_ids (if provided)
        if test_ids:
            await self.test_repo.validate_tests_belong_to_products(test_ids, product_ids)

        # Apply default filter if statuses not specified
        # Default: exclude unexecuted tests (initialized, cancelled)
        effective_statuses = statuses
        if statuses is None:
            effective_statuses = EXECUTED_TEST_STATUSES

        # Parse date filters (flexible formats)
        parsed_start_date: datetime | None = None
        parsed_end_date: datetime | None = None

        if start_date:
            start_iso = parse_flexible_date(start_date, start_of_day=True)
            parsed_start_date = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))

        if end_date:
            end_iso = parse_flexible_date(end_date, start_of_day=False)
            parsed_end_date = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))

        # Phase 1: Get summary aggregates via SQL (fast, no data transfer)
        await progress.report(0, 3, "Loading summary aggregates...", force=True)

        # Get test aggregates across all products
        test_aggregates = await self.test_repo.get_test_aggregates_for_products(
            product_ids=product_ids,
            statuses=effective_statuses,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            date_field="end_at",
            test_ids=test_ids,
        )

        total_tests_matched = test_aggregates["total_tests"]
        tests_by_status = test_aggregates["tests_by_status"]
        tests_by_type = test_aggregates["tests_by_type"]

        # Get all test IDs matching filters (for bug aggregate query)
        # Always sorted by end_at descending (most recent first)
        if test_ids:
            # Sort user-provided test_ids by end_at
            all_test_ids = await self.test_repo.sort_test_ids_by_end_at(test_ids)
        else:
            all_test_ids = await self.test_repo.get_test_ids_for_products(
                product_ids=product_ids,
                statuses=effective_statuses,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                date_field="end_at",
            )

        # Get bug aggregates (total_bugs, bugs_by_status, bugs_by_severity)
        bug_aggregates = await self.bug_repo.get_bug_aggregates_for_tests(test_ids=all_test_ids)

        total_bugs = bug_aggregates["total_bugs"]
        bugs_by_status_raw = bug_aggregates["bugs_by_status"]
        bugs_by_severity = bug_aggregates["bugs_by_severity"]

        logger.debug(
            f"Generating PQR for products {product_ids}: "
            f"{total_tests_matched} tests, {total_bugs} bugs with filters: "
            f"start_date={start_date}, end_date={end_date}, statuses={statuses}"
        )

        # Phase 2: Build per-product breakdown if multi-product
        await progress.report(1, 3, "Building product breakdown...", force=True)

        # Load playbook thresholds once (used for health indicators in breakdown)
        playbook_thresholds = PlaybookThresholds.from_settings(settings)

        by_product: list[dict[str, Any]] | None = None
        if len(product_ids) > 1:
            # PERF: Use grouped aggregate queries to avoid N+1 (3 queries vs 3*N)
            # Fetch all test and bug aggregates grouped by product in single queries
            test_agg_by_product = await self.test_repo.get_test_aggregates_grouped_by_product(
                product_ids=product_ids,
                statuses=effective_statuses,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                date_field="end_at",
                test_ids=test_ids,
            )
            bug_agg_by_product = await self.bug_repo.get_bug_aggregates_grouped_by_product(
                product_ids=product_ids,
            )

            by_product = []
            for product_info in products_info:
                product_id = product_info["id"]

                # Get pre-fetched aggregates for this product
                prod_test_agg = test_agg_by_product.get(
                    product_id,
                    {"total_tests": 0, "tests_by_status": {}, "tests_by_type": {}},
                )
                prod_bug_agg = bug_agg_by_product.get(
                    product_id,
                    {"total_bugs": 0, "bugs_by_status": {}, "bugs_by_severity": {}},
                )

                # Calculate rates for this product
                prod_summary_counts = {
                    "active_accepted": prod_bug_agg["bugs_by_status"].get("accepted", 0),
                    "auto_accepted": prod_bug_agg["bugs_by_status"].get("auto_accepted", 0),
                    "rejected": prod_bug_agg["bugs_by_status"].get("rejected", 0),
                    "open": prod_bug_agg["bugs_by_status"].get("open", 0),
                }
                prod_total_bugs = prod_bug_agg["total_bugs"]

                prod_rates = calculate_acceptance_rates(
                    active_accepted=prod_summary_counts["active_accepted"],
                    auto_accepted=prod_summary_counts["auto_accepted"],
                    rejected=prod_summary_counts["rejected"],
                    open_bugs=prod_summary_counts["open"],
                    total_bugs=prod_total_bugs,
                )

                # Compute health indicators for this product
                prod_health = compute_health_indicators_dict(
                    rejection_rate=prod_rates.get("rejection_rate"),
                    auto_acceptance_rate=prod_rates.get("auto_acceptance_rate"),
                    review_rate=prod_rates.get("review_rate"),
                    thresholds=playbook_thresholds,
                )

                by_product.append(
                    {
                        "product_id": product_id,
                        "product_title": product_info["title"],
                        "total_tests": prod_test_agg["total_tests"],
                        "total_bugs": prod_total_bugs,
                        "bugs_by_severity": prod_bug_agg["bugs_by_severity"],
                        "tests_by_status": prod_test_agg["tests_by_status"],
                        "tests_by_type": prod_test_agg["tests_by_type"],
                        "health_indicators": prod_health,
                        **prod_rates,
                    }
                )

        # Phase 3: Build test data if requested
        await progress.report(2, 3, "Generating report...", force=True)

        test_data_results: list[dict[str, Any]] | None = None
        warnings: list[str] = []

        if include_test_data or output_file is not None:
            # Query tests for all products
            all_tests = await self.test_repo.query_tests_for_products(
                product_ids=product_ids,
                statuses=effective_statuses,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                date_field="end_at",
                sort_by="end_at",
                sort_order="desc",
                test_ids=test_ids,
            )

            # Extract test IDs for bug fetching
            test_ids_for_bugs = [t["id"] for t in all_tests if t.get("id") is not None]

            async def on_bug_batch(current: int, total: int) -> None:
                await progress.report(2, 3, f"Loading bugs: batch {current}/{total}...")

            # Get bugs for all tests
            bugs_by_test, cache_stats = await self.bug_repo.get_bugs_cached_or_refresh(
                test_ids=test_ids_for_bugs,
                force_refresh=False,
                on_batch_progress=on_bug_batch,
            )

            # Surface partial failures as warnings
            if cache_stats.get("api_failed", 0) > 0:
                warnings.append(
                    f"Warning: {cache_stats['api_failed']} tests failed to refresh bug data. "
                    "Results may be incomplete or stale for those tests."
                )

            test_data_results = []
            for test in all_tests:
                test_id = test.get("id")
                if test_id is None:
                    continue

                bugs = bugs_by_test.get(test_id, [])
                bug_counts = classify_bugs(bugs)
                bugs_count = len(bugs)

                rates = calculate_acceptance_rates(
                    active_accepted=bug_counts["active_accepted"],
                    auto_accepted=bug_counts["auto_accepted"],
                    rejected=bug_counts["rejected"],
                    open_bugs=bug_counts["open"],
                    total_bugs=bugs_count,
                )

                test_result: dict[str, Any] = {
                    "test_id": test_id,
                    "product_id": test.get("product", {}).get("id"),
                    "title": test.get("title", "Untitled"),
                    "status": test.get("status", "unknown"),
                    "testing_type": test.get("testing_type"),
                    "start_at": test.get("start_at"),
                    "end_at": test.get("end_at"),
                    "bugs_count": bugs_count,
                    "bugs": {
                        "active_accepted": bug_counts["active_accepted"],
                        "auto_accepted": bug_counts["auto_accepted"],
                        "rejected": bug_counts["rejected"],
                        "open": bug_counts["open"],
                        "total_accepted": bug_counts["total_accepted"],
                        "reviewed": bug_counts["reviewed"],
                    },
                    "test_environment": test.get("test_environment"),
                }

                self._apply_acceptance_rates(test_result, rates)
                test_data_results.append(test_result)

        # Map raw bug status counts to our status names
        summary_counts = {
            "active_accepted": bugs_by_status_raw.get("accepted", 0),
            "auto_accepted": bugs_by_status_raw.get("auto_accepted", 0),
            "rejected": bugs_by_status_raw.get("rejected", 0),
            "open": bugs_by_status_raw.get("open", 0),
        }

        # Calculate summary acceptance rates from aggregates
        summary_rates = calculate_acceptance_rates(
            active_accepted=summary_counts["active_accepted"],
            auto_accepted=summary_counts["auto_accepted"],
            rejected=summary_counts["rejected"],
            open_bugs=summary_counts["open"],
            total_bugs=total_bugs,
        )

        # Build period string for display
        period_str = self._format_period_string(start_date, end_date)

        # Build summary section
        total_accepted = summary_counts["active_accepted"] + summary_counts["auto_accepted"]
        reviewed = summary_counts["active_accepted"] + summary_counts["rejected"]

        bugs_by_status = {
            "active_accepted": summary_counts["active_accepted"],
            "auto_accepted": summary_counts["auto_accepted"],
            "rejected": summary_counts["rejected"],
            "open": summary_counts["open"],
        }

        # Calculate average bugs per test
        avg_bugs_per_test = 0.0
        if total_tests_matched > 0:
            avg_bugs_per_test = round(total_bugs / total_tests_matched, 2)

        summary: dict[str, Any] = {
            "product_ids": product_ids,
            "products": products_info,
            "total_tests": total_tests_matched,
            "tests_by_status": tests_by_status,
            "statuses_applied": effective_statuses or "all",
            "total_bugs": total_bugs,
            "bugs_by_status": bugs_by_status,
            "bugs_by_severity": bugs_by_severity,
            "tests_by_type": tests_by_type,
            "total_accepted": total_accepted,
            "reviewed": reviewed,
            "avg_bugs_per_test": avg_bugs_per_test,
            "period": period_str,
        }

        # Add summary acceptance rates
        self._apply_acceptance_rates(summary, summary_rates)

        # Compute health indicators based on playbook thresholds
        # (playbook_thresholds already loaded above for by_product breakdown)
        health_indicators = compute_health_indicators_dict(
            rejection_rate=summary.get("rejection_rate"),
            auto_acceptance_rate=summary.get("auto_acceptance_rate"),
            review_rate=summary.get("review_rate"),
            thresholds=playbook_thresholds,
        )
        summary["health_indicators"] = health_indicators

        logger.info(
            f"PQR generated for products {product_ids}: "
            f"{total_tests_matched} tests, {total_bugs} bugs, "
            f"acceptance_rate={summary.get('overall_acceptance_rate')}"
        )

        # Complete progress
        await progress.complete(
            f"Report complete: {total_tests_matched} tests, {total_bugs:,} bugs"
        )

        # Build thresholds dict for response (transparency for consumers)
        thresholds_dict = {
            "rejection_rate": {
                "warning": playbook_thresholds.rejection_rate.warning,
                "critical": playbook_thresholds.rejection_rate.critical,
                "direction": playbook_thresholds.rejection_rate.direction,
            },
            "auto_acceptance_rate": {
                "warning": playbook_thresholds.auto_acceptance_rate.warning,
                "critical": playbook_thresholds.auto_acceptance_rate.critical,
                "direction": playbook_thresholds.auto_acceptance_rate.direction,
            },
            "review_rate": {
                "warning": playbook_thresholds.review_rate.warning,
                "critical": playbook_thresholds.review_rate.critical,
                "direction": playbook_thresholds.review_rate.direction,
            },
        }

        # If output_file is specified, write to file and return metadata
        if output_file is not None:
            output_path = resolve_output_path(output_file)

            # Build full report dict for file export
            full_report: dict[str, Any] = {
                "summary": summary,
                "product_ids": product_ids,
                "products": products_info,
                "test_ids": all_test_ids,
                "by_product": by_product,
                "test_data": test_data_results,
                "thresholds": thresholds_dict,
            }
            if warnings:
                full_report["warnings"] = warnings

            # Write report to file
            file_size_bytes = write_report_to_file(full_report, output_path)
            file_format = get_file_format(output_path)

            # Return file metadata
            result: dict[str, Any] = {
                "file_path": str(output_path),
                "summary": summary,
                "product_ids": product_ids,
                "products": products_info,
                "test_ids": all_test_ids,
                "by_product": by_product,
                "record_count": len(test_data_results) if test_data_results else 0,
                "file_size_bytes": file_size_bytes,
                "format": file_format,
                "thresholds": thresholds_dict,
            }
            if warnings:
                result["warnings"] = warnings
            return result

        # Build and return result
        result = {
            "summary": summary,
            "product_ids": product_ids,
            "products": products_info,
            "test_ids": all_test_ids,
            "by_product": by_product,
            "thresholds": thresholds_dict,
        }

        # Only include test_data when explicitly requested
        if include_test_data:
            result["test_data"] = test_data_results

        if warnings:
            result["warnings"] = warnings

        return result

    def _apply_acceptance_rates(
        self, target: dict[str, Any], rates: dict[str, float | None]
    ) -> None:
        """Apply acceptance rates to target dict.

        Args:
            target: Dictionary to update with rate fields
            rates: Rate dictionary from calculate_acceptance_rates()
        """
        target["active_acceptance_rate"] = rates["active_acceptance_rate"]
        target["auto_acceptance_rate"] = rates["auto_acceptance_rate"]
        target["overall_acceptance_rate"] = rates["overall_acceptance_rate"]
        target["rejection_rate"] = rates["rejection_rate"]
        target["review_rate"] = rates["review_rate"]

    def _format_period_string(self, start_date: str | None, end_date: str | None) -> str:
        """Format period string for display in PQR summary.

        Args:
            start_date: Start date string (original input)
            end_date: End date string (original input)

        Returns:
            Human-readable period string
        """
        if not start_date and not end_date:
            return "all time"
        elif start_date and not end_date:
            return f"{start_date} to present"
        elif not start_date and end_date:
            return f"through {end_date}"
        else:
            return f"{start_date} to {end_date}"
