"""Analytics service for dynamic metric queries.

This module provides the AnalyticsService class implementing the "Metric Cube" pattern.
Registry-driven SQL builder that constructs dynamic queries from dimension/metric requests.

STORY-043: Analytics Service (The Engine)
Epic: EPIC-007 (Generic Analytics Framework)

Example:
    >>> service = AnalyticsService(session, customer_id=123)
    >>> result = await service.query_metrics(
    ...     metrics=["bug_count"],
    ...     dimensions=["feature"],
    ...     sort_by="bug_count",
    ...     sort_order="desc"
    ... )
    >>> print(result["data"][0])  # Top feature by bug count
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Float, Integer, Text, case, func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.analytics import QueryMetadata, QueryResponse, VisualizationHint
from testio_mcp.models.orm import Bug, Feature, Product, Test, TestFeature, TestPlatform, User
from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.test_repository import TestRepository
from testio_mcp.repositories.user_repository import UserRepository
from testio_mcp.schemas.constants import EXECUTED_TEST_STATUSES
from testio_mcp.schemas.visualization_constants import (
    BAR_MAX_ROWS,
    CATEGORICAL_DIMS,
    COUNT_METRICS,
    ENTITY_DIMS,
    MULTI_LINE_MAX_SERIES,
    PIE_MAX_CATEGORIES,
    RATE_METRICS,
    TIME_DIMS,
)
from testio_mcp.services.base_service import BaseService
from testio_mcp.services.query_builder import QueryBuilder
from testio_mcp.utilities.progress import ProgressReporter

logger = logging.getLogger(__name__)


@dataclass
class DimensionDef:
    """Definition of a dimension for grouping.

    Attributes:
        key: Unique dimension identifier (e.g., "feature", "month")
        description: Human-readable description
        column: SQLAlchemy column expression for grouping
        id_column: Optional ID column for rich context (enables linking)
        join_path: List of ORM models needed for joins
        filter_condition: Optional WHERE clause expression
        example: Example dimension value
    """

    key: str
    description: str
    column: Any  # SQLAlchemy column expression
    id_column: Any | None  # ID column for rich context
    join_path: list[type]  # ORM models to join
    filter_condition: Any | None = None  # Optional WHERE clause
    example: str = ""


@dataclass
class MetricDef:
    """Definition of a metric for aggregation.

    Attributes:
        key: Unique metric identifier (e.g., "bug_count")
        description: Human-readable description
        expression: SQLAlchemy aggregation expression (e.g., func.count(...))
        join_path: List of ORM models needed for metric calculation
        formula: Human-readable formula string
    """

    key: str
    description: str
    expression: Any  # SQLAlchemy aggregation expression
    join_path: list[type]  # ORM models needed
    formula: str  # Human-readable formula


def build_dimension_registry() -> dict[str, DimensionDef]:
    """Build dimension registry with join paths and columns.

    This is a module-level function for use by prompts and other callers
    that need dimension metadata without instantiating AnalyticsService.

    Returns:
        Dictionary mapping dimension keys to DimensionDef objects.
    """
    return {
        "feature": DimensionDef(
            key="feature",
            description="Group by Feature Title",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
            example="Login, Signup, Dashboard",
        ),
        "product": DimensionDef(
            key="product",
            description="Group by Product",
            column=Product.title,
            id_column=Product.id,
            join_path=[TestFeature, Feature, Product],
            example="Canva, Zoom, Slack",
        ),
        "platform": DimensionDef(
            key="platform",
            description="Group by Platform (OS)",
            column=TestPlatform.operating_system_name,
            id_column=TestPlatform.operating_system_id,
            join_path=[Test, TestPlatform],
            example="iOS, Android, Windows, Mac OS",
        ),
        "tester": DimensionDef(
            key="tester",
            description="Group by Tester Username",
            column=User.username,
            id_column=User.id,
            join_path=[Bug, User],  # Via Bug.reported_by_user_id
            filter_condition=User.user_type == "tester",
            example="alice, bob, charlie",
        ),
        "customer": DimensionDef(
            key="customer",
            description="Group by Customer Username",
            column=Test.created_by,  # Denormalized for performance (no User join needed)
            id_column=Test.created_by_user_id,
            join_path=[Test],  # Direct from Test (created_by is denormalized)
            filter_condition=col(Test.created_by).is_not(None),
            example="acme_corp, beta_user_1",
        ),
        "severity": DimensionDef(
            key="severity",
            description="Group by Bug Severity",
            column=Bug.severity,
            id_column=None,  # No ID for enum
            join_path=[Bug],
            example="critical, major, minor",
        ),
        "status": DimensionDef(
            key="status",
            description="Group by Bug/Test Status",
            column=Bug.status,  # or Test.status depending on context
            id_column=None,
            join_path=[Bug],
            example="open, closed, accepted",
        ),
        "testing_type": DimensionDef(
            key="testing_type",
            description="Group by Testing Type",
            column=Test.testing_type,
            id_column=None,
            join_path=[Test],
            example="coverage, focused, rapid",
        ),
        "month": DimensionDef(
            key="month",
            description="Group by Month (test end date)",
            column=func.strftime("%Y-%m", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-11, 2024-12",
        ),
        "week": DimensionDef(
            key="week",
            description="Group by Week (test end date)",
            column=func.strftime("%Y-W%W", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-W47, 2024-W48",
        ),
        "quarter": DimensionDef(
            key="quarter",
            description="Group by Quarter (test end date)",
            # SQLite logic: strftime('%Y-Q', end_at) || ((strftime('%m', end_at) + 2) / 3)
            column=func.strftime("%Y-Q", Test.end_at)
            + func.cast(
                func.cast(
                    (func.cast(func.strftime("%m", Test.end_at), Integer) + 2) / 3,
                    Integer,
                ),
                Text,
            ),
            id_column=None,
            join_path=[Test],
            example="2024-Q3, 2024-Q4",
        ),
        "rejection_reason": DimensionDef(
            key="rejection_reason",
            description="Group by Rejection Reason",
            column=Bug.rejection_reason,
            id_column=None,
            join_path=[Bug],
            example="ignored_instructions, not_reproducible",
        ),
        "test_environment": DimensionDef(
            key="test_environment",
            description="Group by Test Environment",
            column=func.json_extract(Test.test_environment, "$.title"),
            id_column=func.cast(func.json_extract(Test.test_environment, "$.id"), Integer),
            join_path=[Test],
            filter_condition=(
                col(Test.test_environment).is_not(None)
                & (func.json_extract(Test.test_environment, "$.title") != "null")
            ),
            example="iOS 14, Android 12, Web Chrome",
        ),
        "known_bug": DimensionDef(
            key="known_bug",
            description="Group by Known Bug Status",
            column=case(
                (col(Bug.known).is_(True), "true"),
                (col(Bug.known).is_(False), "false"),
                else_="false",
            ),
            id_column=None,
            join_path=[Bug],
            example="true, false",
        ),
    }


def build_metric_registry() -> dict[str, MetricDef]:
    """Build metric registry with aggregation expressions.

    This is a module-level function for use by prompts and other callers
    that need metric metadata without instantiating AnalyticsService.

    Returns:
        Dictionary mapping metric keys to MetricDef objects.
    """
    return {
        "test_count": MetricDef(
            key="test_count",
            description="Total number of tests",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id)",
        ),
        "bug_count": MetricDef(
            key="bug_count",
            description="Total number of bugs found",
            expression=func.count(func.distinct(Bug.id)),
            join_path=[TestFeature, Bug],  # Via Bug.test_feature_id
            formula="COUNT(DISTINCT bug_id)",
        ),
        "bug_severity_score": MetricDef(
            key="bug_severity_score",
            description="Weighted bug severity score",
            expression=func.sum(
                case(
                    # Type ignored: SQLAlchemy case() tuple signature - mypy limitation
                    (Bug.severity == "critical", 5),  # type: ignore[arg-type]
                    (Bug.severity == "major", 3),  # type: ignore[arg-type]
                    (Bug.severity == "minor", 1),  # type: ignore[arg-type]
                    else_=0,
                )
            ),
            join_path=[TestFeature, Bug],
            formula="SUM(CASE severity WHEN 'critical' THEN 5 ...)",
        ),
        "features_tested": MetricDef(
            key="features_tested",
            description="Number of unique features tested",
            expression=func.count(func.distinct(TestFeature.feature_id)),
            join_path=[TestFeature],
            formula="COUNT(DISTINCT feature_id)",
        ),
        "active_testers": MetricDef(
            key="active_testers",
            description="Number of unique testers",
            expression=func.count(func.distinct(Bug.reported_by_user_id)),
            join_path=[Bug],
            formula="COUNT(DISTINCT reported_by_user_id)",
        ),
        "bugs_per_test": MetricDef(
            key="bugs_per_test",
            description="Ratio of bugs to tests (fragility metric)",
            expression=(
                func.count(func.distinct(Bug.id)).cast(Float)
                / func.nullif(func.count(func.distinct(Test.id)), 0)
            ),
            join_path=[Test, TestFeature, Bug],
            formula="bug_count / NULLIF(test_count, 0)",
        ),
        "tests_created": MetricDef(
            key="tests_created",
            description="Number of tests created by customers",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id WHERE created_by_user_id IS NOT NULL)",
        ),
        "tests_submitted": MetricDef(
            key="tests_submitted",
            description="Number of tests submitted for review",
            expression=func.sum(
                case(
                    (col(Test.submitted_by_user_id).is_not(None), 1),
                    else_=0,
                )
            ),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id WHERE submitted_by_user_id IS NOT NULL)",
        ),
        # Rate metrics (STORY-082)
        # CRITICAL: Use COUNT(DISTINCT CASE WHEN ... THEN bug_id END) pattern
        # to prevent row multiplication when joining to many-to-many dimensions
        # like platform (TestPlatform) or feature (TestFeature).
        # Bug fix: SUM(CASE) counts rows, not distinct bugs, causing rates > 100%
        # when the same bug appears in multiple join rows.
        "overall_acceptance_rate": MetricDef(
            key="overall_acceptance_rate",
            description="Overall acceptance rate (active + auto accepted / total bugs)",
            expression=(
                func.count(
                    func.distinct(
                        case(
                            (Bug.status == "accepted", Bug.id),  # type: ignore[arg-type]
                            (Bug.status == "auto_accepted", Bug.id),  # type: ignore[arg-type]
                            else_=None,
                        )
                    )
                ).cast(Float)
                / func.nullif(func.count(func.distinct(Bug.id)), 0)
            ),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT accepted_bug_id) / NULLIF(COUNT(DISTINCT bug_id), 0)",
        ),
        "rejection_rate": MetricDef(
            key="rejection_rate",
            description="Rejection rate (rejected bugs / total bugs)",
            expression=(
                func.count(
                    func.distinct(
                        case(
                            (Bug.status == "rejected", Bug.id),  # type: ignore[arg-type]
                            else_=None,
                        )
                    )
                ).cast(Float)
                / func.nullif(func.count(func.distinct(Bug.id)), 0)
            ),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT rejected_bug_id) / NULLIF(COUNT(DISTINCT bug_id), 0)",
        ),
        "review_rate": MetricDef(
            key="review_rate",
            description="Review rate (human-reviewed bugs / total bugs)",
            expression=(
                func.count(
                    func.distinct(
                        case(
                            (Bug.status == "accepted", Bug.id),  # type: ignore[arg-type]
                            (Bug.status == "rejected", Bug.id),  # type: ignore[arg-type]
                            else_=None,
                        )
                    )
                ).cast(Float)
                / func.nullif(func.count(func.distinct(Bug.id)), 0)
            ),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT reviewed_bug_id) / NULLIF(COUNT(DISTINCT bug_id), 0)",
        ),
        "active_acceptance_rate": MetricDef(
            key="active_acceptance_rate",
            description="Active acceptance rate (actively accepted bugs / total bugs)",
            expression=(
                func.count(
                    func.distinct(
                        case(
                            (Bug.status == "accepted", Bug.id),  # type: ignore[arg-type]
                            else_=None,
                        )
                    )
                ).cast(Float)
                / func.nullif(func.count(func.distinct(Bug.id)), 0)
            ),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT active_accepted_bug_id) / NULLIF(COUNT(DISTINCT bug_id), 0)",
        ),
        "auto_acceptance_rate": MetricDef(
            key="auto_acceptance_rate",
            description="Auto acceptance rate (auto-accepted / total accepted bugs)",
            expression=(
                func.count(
                    func.distinct(
                        case(
                            (Bug.status == "auto_accepted", Bug.id),  # type: ignore[arg-type]
                            else_=None,
                        )
                    )
                ).cast(Float)
                / func.nullif(
                    func.count(
                        func.distinct(
                            case(
                                (Bug.status == "accepted", Bug.id),  # type: ignore[arg-type]
                                (Bug.status == "auto_accepted", Bug.id),  # type: ignore[arg-type]
                                else_=None,
                            )
                        )
                    ),
                    0,
                )
            ),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT auto_id) / NULLIF(COUNT(DISTINCT accepted_id), 0)",
        ),
    }


class AnalyticsService(BaseService):
    """Registry-driven analytics query engine.

    Constructs dynamic SQL from dimension/metric requests without custom queries.
    Implements the "Metric Cube" pattern for flexible analytics.

    Security:
        All queries filter by customer_id via TestFeature.customer_id for multi-tenant isolation.

    Performance:
        - Max 2 dimensions (V1 limit)
        - Max 1000 rows (hard limit)
        - Query timeout: HTTP_TIMEOUT_SECONDS=90.0 (inherited from client)

    Attributes:
        session: AsyncSession for database queries
        customer_id: Customer ID for data filtering
        client: TestIOClient for repository composition (inherited from BaseService)
    """

    def __init__(
        self,
        session: AsyncSession,
        customer_id: int,
        client: TestIOClient,
        cache: Any | None = None,
    ):
        """Initialize analytics service.

        Args:
            session: AsyncSession for database queries
            customer_id: Customer ID for data filtering
            client: TestIOClient for creating repository instances (composition)
            cache: PersistentCache for per-entity refresh locks (STORY-062 fix)
        """
        super().__init__(client)
        self.session = session
        self.customer_id = customer_id
        self.cache = cache

        # Initialize registries from module-level functions
        self._dimensions = build_dimension_registry()
        self._metrics = build_metric_registry()

    async def query_metrics(
        self,
        metrics: list[str],
        dimensions: list[str],
        filters: dict[str, Any] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
        limit: int | None = None,
        progress: ProgressReporter | None = None,
        tests_limit: int | None = None,
    ) -> QueryResponse:
        """Execute dynamic analytics query.

        STORY-055: Added limit parameter.

        Args:
            metrics: List of metric keys to measure
            dimensions: List of dimension keys to group by
            filters: Optional dimension value filters
            start_date: Optional start date (filters on Test.end_at)
            end_date: Optional end date (filters on Test.end_at)
            sort_by: Optional metric/dimension to sort by
            sort_order: Sort order ('asc' or 'desc')
            limit: Optional result limit (max rows to return), default: None (unlimited up to 1000)
            progress: Optional ProgressReporter for real-time progress updates
            tests_limit: Optional limit on tests to include in metrics. When specified,
                        only the most recent N tests (by end_at DESC) are included.
                        If combined with date filters, applies limit after date filtering.

        Returns:
            QueryResponse with data, metadata, explanation, and warnings

        Raises:
            ValueError: If invalid dimensions/metrics or too many dimensions
        """
        # Validation
        self._validate_request(metrics, dimensions, filters)

        # Initialize progress reporter (noop if None)
        progress = progress or ProgressReporter.noop()

        # Auto-include test_count when bugs_per_test is requested for context
        # This prevents misleading comparisons of single-test vs multi-test features
        metrics_with_context = metrics.copy()
        if "bugs_per_test" in metrics and "test_count" not in metrics:
            metrics_with_context.append("test_count")

        # Validate product_id filter upfront (fail fast with clear error)
        if filters and "product_id" in filters:
            product_id_value = filters["product_id"]
            if isinstance(product_id_value, list):
                await self._validate_products_exist(product_id_value)
            else:
                await self._validate_product_exists(product_id_value)

        # Phase 1: Identify scope (lightweight queries to get test_ids and product_ids)
        await progress.report(0, 4, "Identifying query scope...", force=True)
        test_ids = await self._get_scoped_test_ids(filters, start_date, end_date, tests_limit)

        product_ids = await self._extract_product_ids(test_ids)

        # AC3.3: Repository integration - refresh stale data BEFORE analytics query
        warnings: list[str] = []

        # Create UserRepository first for tester extraction (STORY-036)
        # CRITICAL: Must be created before TestRepository/BugRepository
        # so that user extraction works during bug refresh
        user_repo = UserRepository(
            session=self.session, client=self.client, customer_id=self.customer_id
        )

        # Phase 2: Refresh tests (check for stale test metadata)
        await progress.report(
            1, 4, f"Refreshing test metadata ({len(test_ids)} tests)...", force=True
        )
        test_repo = TestRepository(
            session=self.session,
            client=self.client,
            customer_id=self.customer_id,
            user_repo=user_repo,  # Inject for customer extraction
            cache=self.cache,  # STORY-062 fix: Enable isolated sessions
        )

        async def on_test_batch(current: int, total: int) -> None:
            await progress.report(1, 4, f"Refreshing tests: batch {current}/{total}...")

        try:
            _, test_stats = await test_repo.get_tests_cached_or_refresh(
                test_ids, on_batch_progress=on_test_batch
            )
            # AC3.4: Add warning if cache_hit_rate < 50%
            if test_stats["cache_hit_rate"] < 50:
                warnings.append(
                    f"Warning: {test_stats['api_calls']} tests had stale metadata "
                    "and were refreshed."
                )
        except Exception as e:
            # AC3.5: Error handling for failed refresh (graceful degradation)
            logger.error(f"Failed to refresh test data: {e}")
            warnings.append("Warning: Test refresh failed. Data may be stale. Using cached data.")

        # Phase 3: Refresh bugs (check for stale bug data)
        await progress.report(2, 4, f"Refreshing bug data ({len(test_ids)} tests)...", force=True)
        bug_repo = BugRepository(
            session=self.session,
            client=self.client,
            customer_id=self.customer_id,
            user_repo=user_repo,  # Inject for tester extraction
            cache=self.cache,  # STORY-062 fix: Enable isolated sessions
        )

        async def on_bug_batch(current: int, total: int) -> None:
            await progress.report(2, 4, f"Refreshing bugs: batch {current}/{total}...")

        try:
            _, bug_stats = await bug_repo.get_bugs_cached_or_refresh(
                test_ids, on_batch_progress=on_bug_batch
            )
            # AC3.4: Add warning if cache_hit_rate < 50%
            if bug_stats["cache_hit_rate"] < 50:
                warnings.append(
                    f"Warning: {bug_stats['api_calls']} tests had stale bug data "
                    "and were refreshed."
                )
            # Surface partial failures (Codex review finding)
            if bug_stats.get("api_failed", 0) > 0:
                warnings.append(
                    f"Warning: {bug_stats['api_failed']} tests failed to refresh bug data. "
                    "Results may be incomplete or stale for those tests."
                )
        except Exception as e:
            # AC3.5: Error handling for failed refresh (graceful degradation)
            logger.error(f"Failed to refresh bug data: {e}")
            warnings.append("Warning: Bug refresh failed. Data may be stale. Using cached data.")

        # Phase 4: Refresh features (check for stale feature data)
        await progress.report(3, 4, "Refreshing feature data...", force=True)
        feature_repo = FeatureRepository(
            session=self.session,
            client=self.client,
            customer_id=self.customer_id,
            cache=self.cache,  # STORY-062 fix: Enable isolated sessions
        )
        try:
            _, feature_stats = await feature_repo.get_features_cached_or_refresh(product_ids)
            # AC3.4: Add warning if cache_hit_rate < 50%
            if feature_stats["cache_hit_rate"] < 50:
                warnings.append(
                    f"Warning: {feature_stats['api_calls']} products had stale "
                    "feature data and were refreshed."
                )
            # Surface partial failures (Codex review finding)
            if feature_stats.get("api_failed", 0) > 0:
                warnings.append(
                    f"Warning: {feature_stats['api_failed']} products failed to refresh "
                    "feature data. Results may be incomplete or stale for those products."
                )
        except Exception as e:
            # AC3.5: Error handling for failed refresh (graceful degradation)
            logger.error(f"Failed to refresh feature data: {e}")
            warnings.append(
                "Warning: Feature refresh failed. Data may be stale. Using cached data."
            )

        # Apply default status filter if not explicitly provided
        # This ensures consistency with get_product_quality_report
        effective_filters = filters.copy() if filters else {}
        if "status" not in effective_filters:
            # Default: exclude initialized (not reviewed/executed) and cancelled (never executed)
            # Rationale: Quality metrics should reflect only executed tests
            effective_filters["status"] = EXECUTED_TEST_STATUSES

        # Build query (after all data is fresh)
        builder = QueryBuilder(self.session, self.customer_id)
        builder.set_dimensions(dimensions, self._dimensions)
        builder.set_metrics(metrics_with_context, self._metrics)
        builder.set_filters(effective_filters)
        builder.set_date_range(start_date, end_date)

        # Smart sort defaults: time dimensions sort chronologically (ascending)
        effective_sort_by: str
        effective_sort_order = sort_order
        if sort_by is None:
            primary_dim = dimensions[0] if dimensions else None
            if primary_dim in TIME_DIMS:
                # Time dimension: sort chronologically (ascending by date)
                effective_sort_by = primary_dim
                effective_sort_order = "asc"
            else:
                # Non-time dimension: sort by first metric (descending by value)
                effective_sort_by = metrics[0]
        else:
            effective_sort_by = sort_by

        builder.set_sort(effective_sort_by, effective_sort_order)

        # Execute analytics query with timing
        start_time = time.perf_counter()
        stmt = builder.build()

        # STORY-055: Apply limit if specified (defaults to 1000 row cap)
        if limit is not None:
            stmt = stmt.limit(limit)
        else:
            # Default cap at 1000 rows to prevent memory issues
            stmt = stmt.limit(1000)

        # Known SQLModel/mypy limitation: session.exec() with dynamic SELECT
        # doesn't satisfy strict type checking. See: fastapi/sqlmodel#831
        result = await self.session.exec(stmt)  # type: ignore[call-overload]
        rows = result.all()
        query_time_ms = int((time.perf_counter() - start_time) * 1000)

        # Complete progress
        await progress.complete("Query complete")

        # Format response (include warnings and timing)
        # Use metrics_with_context so test_count appears when bugs_per_test is requested
        return self._format_response(
            rows, metrics_with_context, dimensions, builder, warnings, query_time_ms, limit
        )

    def _validate_request(
        self, metrics: list[str], dimensions: list[str], filters: dict[str, Any] | None
    ) -> None:
        """Validate request against guardrails.

        Raises:
            ValueError: If request violates guardrails
        """
        # Max 2 dimensions (V1 limit)
        if len(dimensions) > 2:
            raise ValueError(
                f"Too many dimensions ({len(dimensions)} provided, max 2). "
                "Try focusing on fewer groupings."
            )

        # Validate dimension keys
        invalid_dims = [d for d in dimensions if d not in self._dimensions]
        if invalid_dims:
            raise ValueError(
                f"Invalid dimensions: {invalid_dims}. "
                f"Valid options: {list(self._dimensions.keys())}"
            )

        # Validate metric keys
        invalid_metrics = [m for m in metrics if m not in self._metrics]
        if invalid_metrics:
            error_msg = (
                f"Invalid metrics: {invalid_metrics}. Valid options: {list(self._metrics.keys())}"
            )
            # Add helpful suggestion for common mistake
            if "acceptance_rate" in invalid_metrics:
                error_msg += (
                    "\n\nDid you mean: overall_acceptance_rate, "
                    "active_acceptance_rate, or auto_acceptance_rate?"
                )
            raise ValueError(error_msg)

        # Validate filter keys
        # product_id and status are special filters that work without corresponding dimensions
        if filters:
            allowed_filter_keys = set(self._dimensions.keys()) | {"product_id", "status"}
            invalid_filters = [f for f in filters if f not in allowed_filter_keys]
            if invalid_filters:
                raise ValueError(
                    f"Invalid filter keys: {invalid_filters}. "
                    f"Valid filters: dimension keys, 'product_id', or 'status'."
                )

    async def _get_scoped_test_ids(
        self,
        filters: dict[str, Any] | None,
        start_date: str | None,
        end_date: str | None,
        tests_limit: int | None = None,
    ) -> list[int]:
        """Identify test IDs in scope for this analytics query (AC3.2).

        Lightweight query (<10ms for typical cases) to get test_ids that match
        filters and date range. This determines which tests need staleness checks.

        Default behavior: Excludes initialized and cancelled tests (unexecuted tests)
        to match get_product_quality_report behavior. Override with filters={'status': [...]}.

        Args:
            filters: Optional dimension value filters
            start_date: Optional start date (filters on Test.end_at)
            end_date: Optional end date (filters on Test.end_at)
            tests_limit: Optional limit on tests. When specified, returns only the
                        most recent N tests (by end_at DESC) after applying filters.

        Returns:
            List of test IDs in scope
        """
        # Build lightweight query to get test IDs
        stmt = select(Test.id).where(col(Test.customer_id) == self.customer_id)

        # Apply product_id filter if provided (special filter)
        if filters and "product_id" in filters:
            product_id_value = filters["product_id"]
            if isinstance(product_id_value, list):
                stmt = stmt.where(col(Test.product_id).in_(product_id_value))
            else:
                stmt = stmt.where(col(Test.product_id) == product_id_value)

        # Apply status filter (default: exclude unexecuted tests)
        # This ensures consistency with get_product_quality_report
        if filters and "status" in filters:
            # User explicitly specified status filter
            status_values = filters["status"]
            if isinstance(status_values, str):
                status_values = [status_values]
            stmt = stmt.where(col(Test.status).in_(status_values))
        else:
            # Default: exclude initialized (not reviewed/executed) and cancelled (never executed)
            # Rationale: Quality metrics should reflect only executed tests
            stmt = stmt.where(col(Test.status).in_(EXECUTED_TEST_STATUSES))

        # Apply date range filters if provided
        if start_date or end_date:
            # Use QueryBuilder's date parsing logic
            from testio_mcp.utilities.date_utils import parse_flexible_date

            if start_date:
                start_dt = parse_flexible_date(start_date)
                stmt = stmt.where(col(Test.end_at) >= start_dt)
            if end_date:
                end_dt = parse_flexible_date(end_date)
                stmt = stmt.where(col(Test.end_at) <= end_dt)

        # Apply tests_limit if specified (get most recent N tests by end_at)
        # Sort by end_at DESC when tests_limit is set for consistent "most recent" semantics
        if tests_limit is not None:
            stmt = stmt.order_by(col(Test.end_at).desc()).limit(tests_limit)

        # Execute query and extract scalar values (Test.id is an integer)
        result = await self.session.exec(stmt)
        # SQLModel's select(Model.column) returns ScalarResult directly
        # Filter out None values (shouldn't happen but satisfies type checker)
        test_ids = [tid for tid in result.all() if tid is not None]
        return test_ids

    async def _extract_product_ids(self, test_ids: list[int]) -> list[int]:
        """Extract product IDs from test IDs (AC3.2).

        Lightweight query to get unique product_ids for the given tests.

        Args:
            test_ids: List of test IDs

        Returns:
            List of unique product IDs
        """
        if not test_ids:
            return []

        # Query unique product_ids for these tests
        stmt = select(Test.product_id).where(col(Test.id).in_(test_ids)).distinct()
        result = await self.session.exec(stmt)
        # SQLModel's select(Model.column) returns ScalarResult directly
        product_ids = list(result.all())
        return product_ids

    async def _validate_product_exists(self, product_id: int) -> None:
        """Validate that a product exists, raise ProductNotFoundException if not.

        Args:
            product_id: Product ID to validate

        Raises:
            ProductNotFoundException: If product doesn't exist for this customer
        """
        from testio_mcp.exceptions import ProductNotFoundException
        from testio_mcp.models.orm import Product

        stmt = select(Product).where(
            Product.id == product_id, Product.customer_id == self.customer_id
        )
        result = await self.session.exec(stmt)
        if result.first() is None:
            raise ProductNotFoundException(product_id)

    async def _validate_products_exist(self, product_ids: list[int]) -> None:
        """Validate that all products exist, raise ProductNotFoundException if any don't.

        Args:
            product_ids: List of Product IDs to validate

        Raises:
            ProductNotFoundException: If any product doesn't exist (reports all missing)
        """
        from testio_mcp.exceptions import ProductNotFoundException
        from testio_mcp.models.orm import Product

        if not product_ids:
            return

        # Query all existing products in one query
        stmt = select(Product.id).where(
            col(Product.id).in_(product_ids),
            col(Product.customer_id) == self.customer_id,
        )
        result = await self.session.exec(stmt)
        existing_ids = set(result.all())

        # Find missing products
        missing_ids = [pid for pid in product_ids if pid not in existing_ids]
        if missing_ids:
            # Report all missing products
            raise ProductNotFoundException(missing_ids)

    def _format_response(
        self,
        rows: list[Any],
        metrics: list[str],
        dimensions: list[str],
        builder: QueryBuilder,
        staleness_warnings: list[str] | None = None,
        query_time_ms: int = 0,
        limit: int | None = None,
    ) -> QueryResponse:
        """Format query results with metadata.

        STORY-055: Added limit parameter for custom limit warnings.

        Args:
            rows: Query result rows
            metrics: List of metric keys
            dimensions: List of dimension keys
            builder: QueryBuilder instance (for metadata extraction)
            staleness_warnings: Optional staleness warnings from repository refreshes
            query_time_ms: Query execution time in milliseconds

        Returns:
            QueryResponse with typed data, metadata, explanation, and warnings
        """
        # Format data rows
        data = []
        for row in rows:
            row_dict = {}
            for dim in dimensions:
                # Include both ID and display name
                dim_def = self._dimensions[dim]
                if dim_def.id_column is not None:
                    row_dict[f"{dim}_id"] = getattr(row, f"{dim}_id", None)
                row_dict[dim] = getattr(row, dim, None)
            for metric in metrics:
                row_dict[metric] = getattr(row, metric, None)
            data.append(row_dict)

        # Generate explanation
        explanation = self._generate_explanation(metrics, dimensions, builder)

        # Collect warnings (include staleness warnings from repositories)
        warnings = list(staleness_warnings) if staleness_warnings else []

        # STORY-055: Update limit warning based on custom limit or default 1000
        effective_limit = limit if limit is not None else 1000
        if len(rows) >= effective_limit:
            if limit is not None:
                warnings.append(f"Results limited to {limit} rows (custom limit)")
            else:
                warnings.append("Results limited to 1000 rows (default)")

        if builder.start_date or builder.end_date:
            date_range = f"{builder.start_date or 'beginning'} to {builder.end_date or 'now'}"
            if not builder.start_date or not builder.end_date:
                warnings.append(f"Date range spans {date_range}, consider narrowing")

        # Generate visualization hint
        visualization_hint = self._determine_visualization_hint(data, dimensions, metrics)

        return QueryResponse(
            data=data,
            metadata=QueryMetadata(
                total_rows=len(rows),
                dimensions_used=dimensions,
                metrics_used=metrics,
                query_time_ms=query_time_ms,
            ),
            query_explanation=explanation,
            warnings=warnings,
            visualization_hint=visualization_hint,
        )

    def _generate_explanation(
        self, metrics: list[str], dimensions: list[str], builder: QueryBuilder
    ) -> str:
        """Generate human-readable query explanation."""
        metric_names = [self._metrics[m].description for m in metrics]
        dim_names = [self._dimensions[d].description for d in dimensions]

        explanation = f"Showing {', '.join(metric_names)}"
        if dimensions:
            explanation += f" grouped by {', '.join(dim_names)}"
        if builder.filters:
            filter_desc = ", ".join([f"{k}={v}" for k, v in builder.filters.items()])
            explanation += f" filtered by {filter_desc}"

        # Fix string formatting bug - properly construct "ascending"/"descending"
        sort_word = "descending" if builder.sort_order == "desc" else "ascending"
        explanation += f", sorted by {builder.sort_column} {sort_word}"

        return explanation

    def _determine_visualization_hint(
        self,
        data: list[dict[str, Any]],
        dimensions: list[str],
        metrics: list[str],
    ) -> VisualizationHint:
        """Determine the best visualization for query results.

        Implements the decision matrix for chart type selection based on:
        - Dimension types (time, categorical, entity)
        - Row count and series cardinality
        - Metric types (counts vs rates)

        Args:
            data: Formatted query result rows
            dimensions: List of dimension keys used
            metrics: List of metric keys used

        Returns:
            VisualizationHint with recommended chart configuration
        """
        row_count = len(data)

        # Handle empty results
        if row_count == 0:
            return VisualizationHint(
                chart_type="table",
                rationale="No data returned",
                confidence="low",
                metric_types=self._classify_metrics(metrics),
            )

        # Classify dimensions
        dim1 = dimensions[0] if dimensions else None
        dim2 = dimensions[1] if len(dimensions) > 1 else None

        dim1_type = self._classify_dimension(dim1) if dim1 else None
        dim2_type = self._classify_dimension(dim2) if dim2 else None

        # Classify metrics
        metric_types = self._classify_metrics(metrics)
        count_metrics = [m for m in metrics if metric_types.get(m) == "count"]
        rate_metrics = [m for m in metrics if metric_types.get(m) == "rate"]
        has_mixed_metrics = bool(count_metrics) and bool(rate_metrics)

        # Calculate series cardinality for two-dimension queries
        series_count = 0
        unique_series: list[str] = []
        if dim2 and data:
            unique_series = list({str(row.get(dim2, "")) for row in data})
            series_count = len(unique_series)

        # Decision logic
        return self._apply_decision_matrix(
            dim1=dim1,
            dim2=dim2,
            dim1_type=dim1_type,
            dim2_type=dim2_type,
            row_count=row_count,
            series_count=series_count,
            unique_series=unique_series,
            metrics=metrics,
            count_metrics=count_metrics,
            rate_metrics=rate_metrics,
            has_mixed_metrics=has_mixed_metrics,
            metric_types=metric_types,
        )

    def _classify_dimension(self, dim: str) -> str:
        """Classify a dimension as time, categorical, or entity."""
        if dim in TIME_DIMS:
            return "time"
        elif dim in CATEGORICAL_DIMS:
            return "categorical"
        elif dim in ENTITY_DIMS:
            return "entity"
        else:
            # Unknown dimension - treat as entity (safest fallback)
            return "entity"

    def _classify_metrics(self, metrics: list[str]) -> dict[str, str]:
        """Classify metrics as count or rate."""
        result = {}
        for m in metrics:
            if m in RATE_METRICS:
                result[m] = "rate"
            elif m in COUNT_METRICS:
                result[m] = "count"
            else:
                # Unknown metric - treat as count (safest)
                result[m] = "count"
        return result

    def _apply_decision_matrix(
        self,
        dim1: str | None,
        dim2: str | None,
        dim1_type: str | None,
        dim2_type: str | None,
        row_count: int,
        series_count: int,
        unique_series: list[str],
        metrics: list[str],
        count_metrics: list[str],
        rate_metrics: list[str],
        has_mixed_metrics: bool,
        metric_types: dict[str, str],
    ) -> VisualizationHint:
        """Apply the decision matrix to determine chart type.

        Decision Matrix:
        | dim1 | dim2 | condition | chart_type |
        |------|------|-----------|------------|
        | time | - | any | line |
        | time | categorical | series ≤8 | multi_line |
        | time | categorical | series >8 | table |
        | time | entity | series ≤8 | multi_line (top N) |
        | time | entity | series >8 | table |
        | categorical | - | ≤7 & 1 metric | pie |
        | categorical | - | ≤7 & 2+ metrics | horizontal_bar |
        | categorical | - | >7 | horizontal_bar |
        | categorical | categorical | dim1 ≤15 | stacked_bar |
        | categorical | categorical | dim1 >15 | table |
        | entity | - | ≤15 | horizontal_bar |
        | entity | - | >15 | table |
        | entity | categorical | ≤15 | stacked_bar |
        | entity | categorical | >15 | table |
        | entity | entity | any | table |
        """
        # Single dimension cases
        if dim2 is None:
            return self._handle_single_dimension(
                dim1=dim1,
                dim1_type=dim1_type,
                row_count=row_count,
                metrics=metrics,
                count_metrics=count_metrics,
                rate_metrics=rate_metrics,
                has_mixed_metrics=has_mixed_metrics,
                metric_types=metric_types,
            )

        # Two dimension cases
        return self._handle_two_dimensions(
            dim1=dim1,
            dim2=dim2,
            dim1_type=dim1_type,
            dim2_type=dim2_type,
            row_count=row_count,
            series_count=series_count,
            unique_series=unique_series,
            metrics=metrics,
            count_metrics=count_metrics,
            rate_metrics=rate_metrics,
            has_mixed_metrics=has_mixed_metrics,
            metric_types=metric_types,
        )

    def _handle_single_dimension(
        self,
        dim1: str | None,
        dim1_type: str | None,
        row_count: int,
        metrics: list[str],
        count_metrics: list[str],
        rate_metrics: list[str],
        has_mixed_metrics: bool,
        metric_types: dict[str, str],
    ) -> VisualizationHint:
        """Handle single dimension visualization selection."""
        # Time dimension → line chart
        if dim1_type == "time":
            return VisualizationHint(
                chart_type="line",
                x_axis=dim1,
                y_axis=count_metrics if has_mixed_metrics else metrics,
                y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                rationale="Time dimension; line chart shows trend over time",
                confidence="high",
                alternatives=["table"],
                metric_types=metric_types,
            )

        # Categorical dimension
        if dim1_type == "categorical":
            # Pie chart for small category count with single metric
            if row_count <= PIE_MAX_CATEGORIES and len(metrics) == 1:
                return VisualizationHint(
                    chart_type="pie",
                    x_axis=dim1,
                    y_axis=[metrics[0]],
                    rationale=(
                        f"Categorical with ≤{PIE_MAX_CATEGORIES} categories, "
                        "single metric; pie for distribution"
                    ),
                    confidence="high",
                    alternatives=["horizontal_bar", "table"],
                    metric_types=metric_types,
                )
            # Horizontal bar for multiple metrics or many categories
            else:
                return VisualizationHint(
                    chart_type="horizontal_bar",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    rationale=(
                        "Categorical with multiple metrics or >7 categories; "
                        "horizontal bar for comparison"
                    ),
                    confidence="high",
                    alternatives=["table"],
                    metric_types=metric_types,
                )

        # Entity dimension
        if dim1_type == "entity":
            if row_count <= BAR_MAX_ROWS:
                return VisualizationHint(
                    chart_type="horizontal_bar",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    rationale=(
                        f"Entity with ≤{BAR_MAX_ROWS} rows; horizontal bar for ranked comparison"
                    ),
                    confidence="high",
                    alternatives=["table"],
                    metric_types=metric_types,
                )
            else:
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    rationale=f"Entity dimension with >{BAR_MAX_ROWS} rows; table for readability",
                    confidence="high",
                    alternatives=["horizontal_bar"],
                    metric_types=metric_types,
                )

        # Fallback
        return VisualizationHint(
            chart_type="table",
            x_axis=dim1,
            y_axis=metrics,
            rationale="Unknown dimension type; defaulting to table",
            confidence="low",
            metric_types=metric_types,
        )

    def _handle_two_dimensions(
        self,
        dim1: str | None,
        dim2: str | None,
        dim1_type: str | None,
        dim2_type: str | None,
        row_count: int,
        series_count: int,
        unique_series: list[str],
        metrics: list[str],
        count_metrics: list[str],
        rate_metrics: list[str],
        has_mixed_metrics: bool,
        metric_types: dict[str, str],
    ) -> VisualizationHint:
        """Handle two dimension visualization selection."""
        # Time as primary dimension
        if dim1_type == "time":
            if series_count <= MULTI_LINE_MAX_SERIES:
                return VisualizationHint(
                    chart_type="multi_line",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    series_by=dim2,
                    included_series=unique_series,
                    rationale=(f"Time with {series_count} series; multi-line by {dim2}"),
                    confidence="high",
                    alternatives=["table"],
                    metric_types=metric_types,
                )
            else:
                # Too many series
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    series_by=dim2,
                    dropped_series_count=series_count - MULTI_LINE_MAX_SERIES,
                    rationale=(f"Time with >{MULTI_LINE_MAX_SERIES} series; table for clarity"),
                    confidence="medium",
                    alternatives=["multi_line"],
                    metric_types=metric_types,
                )

        # Categorical + Categorical
        if dim1_type == "categorical" and dim2_type == "categorical":
            # Get unique dim1 values for row count check
            if row_count <= BAR_MAX_ROWS:
                return VisualizationHint(
                    chart_type="stacked_bar",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    series_by=dim2,
                    included_series=unique_series,
                    rationale=(f"Two categorical dims, ≤{BAR_MAX_ROWS} groups; stacked bar"),
                    confidence="high",
                    alternatives=["grouped_bar", "table"],
                    metric_types=metric_types,
                )
            else:
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    series_by=dim2,
                    rationale=(f"Two categorical dims, >{BAR_MAX_ROWS} groups; table"),
                    confidence="high",
                    alternatives=["stacked_bar"],
                    metric_types=metric_types,
                )

        # Entity + Categorical
        if dim1_type == "entity" and dim2_type == "categorical":
            # Get unique dim1 values
            if row_count <= BAR_MAX_ROWS:
                return VisualizationHint(
                    chart_type="stacked_bar",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    series_by=dim2,
                    included_series=unique_series,
                    rationale=(f"Entity + categorical, ≤{BAR_MAX_ROWS} entities; stacked bar"),
                    confidence="high",
                    alternatives=["grouped_bar", "table"],
                    metric_types=metric_types,
                )
            else:
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    series_by=dim2,
                    rationale=(f"Entity + categorical, >{BAR_MAX_ROWS} entities; table"),
                    confidence="high",
                    alternatives=["stacked_bar"],
                    metric_types=metric_types,
                )

        # Entity + Entity → always table
        if dim1_type == "entity" and dim2_type == "entity":
            return VisualizationHint(
                chart_type="table",
                x_axis=dim1,
                y_axis=metrics,
                series_by=dim2,
                rationale="Two entity dimensions; table for complex cross-tabulation",
                confidence="high",
                alternatives=[],
                metric_types=metric_types,
            )

        # Categorical + Entity (reversed order)
        if dim1_type == "categorical" and dim2_type == "entity":
            if series_count <= MULTI_LINE_MAX_SERIES:
                return VisualizationHint(
                    chart_type="grouped_bar",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    series_by=dim2,
                    included_series=unique_series,
                    rationale=(
                        f"Categorical + entity, ≤{MULTI_LINE_MAX_SERIES} entities; grouped bar"
                    ),
                    confidence="medium",
                    alternatives=["stacked_bar", "table"],
                    metric_types=metric_types,
                )
            else:
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    series_by=dim2,
                    rationale=(f"Categorical + entity, >{MULTI_LINE_MAX_SERIES} entities; table"),
                    confidence="high",
                    alternatives=["grouped_bar"],
                    metric_types=metric_types,
                )

        # Time + Entity (less common, treat like time + categorical)
        if dim1_type == "time" and dim2_type == "entity":
            if series_count <= MULTI_LINE_MAX_SERIES:
                return VisualizationHint(
                    chart_type="multi_line",
                    x_axis=dim1,
                    y_axis=count_metrics if has_mixed_metrics else metrics,
                    y_axis_secondary=rate_metrics if has_mixed_metrics else [],
                    series_by=dim2,
                    included_series=unique_series,
                    rationale=(f"Time + entity, ≤{MULTI_LINE_MAX_SERIES} entities; multi-line"),
                    confidence="medium",
                    alternatives=["table"],
                    metric_types=metric_types,
                )
            else:
                return VisualizationHint(
                    chart_type="table",
                    x_axis=dim1,
                    y_axis=metrics,
                    series_by=dim2,
                    dropped_series_count=series_count - MULTI_LINE_MAX_SERIES,
                    rationale=(f"Time + entity, >{MULTI_LINE_MAX_SERIES} entities; table"),
                    confidence="high",
                    alternatives=["multi_line"],
                    metric_types=metric_types,
                )

        # Default fallback
        return VisualizationHint(
            chart_type="table",
            x_axis=dim1,
            y_axis=metrics,
            series_by=dim2,
            rationale="Complex dimension combination; defaulting to table",
            confidence="low",
            metric_types=metric_types,
        )
