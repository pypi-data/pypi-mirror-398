"""Query builder for dynamic SQL construction.

This module provides the QueryBuilder class for constructing SQLAlchemy SELECT statements
from dimension and metric definitions.

STORY-043: Analytics Service (The Engine)
Epic: EPIC-007 (Generic Analytics Framework)

Example:
    >>> builder = QueryBuilder(session, customer_id=123)
    >>> builder.set_dimensions(["feature"], dimension_registry)
    >>> builder.set_metrics(["bug_count"], metric_registry)
    >>> builder.set_sort("bug_count", "desc")
    >>> stmt = builder.build()
    >>> result = await session.exec(stmt)
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Select, and_, asc, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm import Bug, Test, TestFeature, TestPlatform

if TYPE_CHECKING:
    from testio_mcp.services.analytics_service import DimensionDef, MetricDef


class QueryBuilder:
    """Constructs dynamic SQL queries from dimensions and metrics.

    Implements the query building logic for the Metric Cube.

    Security:
        Always filters by TestFeature.customer_id for multi-tenant isolation.

    Attributes:
        session: AsyncSession for query execution
        customer_id: Customer ID for filtering
        dimensions: List of dimension definitions
        metrics: List of metric definitions
        filters: Dimension value filters
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        sort_column: Column/metric to sort by
        sort_order: Sort direction ('asc' or 'desc')
    """

    def __init__(self, session: AsyncSession, customer_id: int):
        """Initialize query builder.

        Args:
            session: AsyncSession for query execution
            customer_id: Customer ID for filtering
        """
        self.session = session
        self.customer_id = customer_id
        self.dimensions: list[DimensionDef] = []
        self.metrics: list[MetricDef] = []
        self.filters: dict[str, Any] = {}
        self.start_date: str | None = None
        self.end_date: str | None = None
        self.sort_column: Any = None
        self.sort_order: str = "desc"

    def set_dimensions(
        self, dimension_keys: list[str], registry: dict[str, "DimensionDef"]
    ) -> None:
        """Set dimensions from registry."""
        self.dimensions = [registry[key] for key in dimension_keys]

    def set_metrics(self, metric_keys: list[str], registry: dict[str, "MetricDef"]) -> None:
        """Set metrics from registry."""
        self.metrics = [registry[key] for key in metric_keys]

    def set_filters(self, filters: dict[str, Any]) -> None:
        """Set dimension value filters."""
        self.filters = filters

    def set_date_range(self, start_date: str | None, end_date: str | None) -> None:
        """Set date range filter."""
        self.start_date = start_date
        self.end_date = end_date

    def set_sort(self, sort_by: str, sort_order: str) -> None:
        """Set sort column and order.

        Args:
            sort_by: Column to sort by (must be in dimensions or metrics)
            sort_order: Sort direction ('asc' or 'desc')

        Raises:
            ValueError: If sort_by is not in dimensions/metrics or sort_order invalid
        """
        # Validate sort_order
        if sort_order not in ("asc", "desc"):
            raise ValueError(f"sort_order must be 'asc' or 'desc', got '{sort_order}'")

        # Validate sort_by is in dimensions or metrics
        valid_columns = [d.key for d in self.dimensions] + [m.key for m in self.metrics]
        if sort_by not in valid_columns:
            raise ValueError(
                f"sort_by '{sort_by}' must be a dimension or metric. Valid options: {valid_columns}"
            )

        self.sort_column = sort_by
        self.sort_order = sort_order

    # fmt: off
    def _ensure_test_joined(
        self, stmt: Select, joined_models: set[type]  # type: ignore[type-arg]
    ) -> Select:  # type: ignore[type-arg]
        # fmt: on
        """Ensure Test table is joined to the statement.

        Helper to avoid duplicating join logic for product_id, status, and date filters.

        Args:
            stmt: Current SELECT statement
            joined_models: Set tracking which models are already joined

        Returns:
            Updated SELECT statement with Test joined (if not already)
        """
        if Test not in joined_models:
            # Type ignored: SQLAlchemy join condition mypy limitation
            stmt = stmt.join(Test, TestFeature.test_id == Test.id)  # type: ignore[arg-type]
            joined_models.add(Test)
        return stmt

    def build(self) -> Select:  # type: ignore[type-arg]
        """Build SQLAlchemy select statement.

        Returns:
            Select statement ready for execution

        Raises:
            ValueError: If filters contain unknown keys
        """
        # Validate filter keys (prevent silent failures from typos)
        known_filters = {"product_id", "status"} | {d.key for d in self.dimensions}
        unknown_filters = set(self.filters.keys()) - known_filters
        if unknown_filters:
            raise ValueError(
                f"Unknown filter keys: {unknown_filters}. Valid filters: {sorted(known_filters)}"
            )

        # Build SELECT columns
        select_columns = []
        group_by_columns = []

        # Add dimension columns and IDs
        for dim in self.dimensions:
            if dim.id_column is not None:
                select_columns.append(dim.id_column.label(f"{dim.key}_id"))
                group_by_columns.append(dim.id_column)  # Must group by ID too
            select_columns.append(dim.column.label(dim.key))
            group_by_columns.append(dim.column)

        # Add metric expressions
        for metric in self.metrics:
            select_columns.append(metric.expression.label(metric.key))

        # Start with TestFeature as anchor table (CRITICAL for customer_id filtering)
        stmt = select(*select_columns).select_from(TestFeature)

        # Add joins
        # CRITICAL: Dimensions use INNER JOIN (define grouping grain)
        #           Metrics use LEFT JOIN (preserve zero counts)
        joined_models: set[type] = set()
        for dim in self.dimensions:
            stmt = self._add_joins(stmt, dim.join_path, joined_models, join_type="inner")
        for metric in self.metrics:
            stmt = self._add_joins(stmt, metric.join_path, joined_models, join_type="left")

        # Add filters
        where_clauses = []

        # Customer filter (security - filter by customer_id)
        where_clauses.append(TestFeature.customer_id == self.customer_id)

        # product_id filter (special filter - works without product dimension)
        if "product_id" in self.filters:
            stmt = self._ensure_test_joined(stmt, joined_models)
            # product_id can be a single value or collection (list, tuple, set)
            product_id_values = self.filters["product_id"]
            if isinstance(product_id_values, (list, tuple, set)):
                where_clauses.append(Test.product_id.in_(product_id_values))  # type: ignore[attr-defined]
            else:
                where_clauses.append(Test.product_id == product_id_values)

        # status filter (special filter - works without status dimension)
        if "status" in self.filters:
            stmt = self._ensure_test_joined(stmt, joined_models)
            # Status can be a single value or collection (list, tuple, set)
            status_values = self.filters["status"]
            if isinstance(status_values, (list, tuple, set)):
                where_clauses.append(Test.status.in_(status_values))  # type: ignore[attr-defined]
            else:
                where_clauses.append(Test.status == status_values)

        # Dimension filters
        for dim in self.dimensions:
            if dim.key in self.filters:
                # Skip if this is the "status" dimension - the special status filter
                # above already applies to Test.status, and applying it to Bug.status
                # (the status dimension column) would incorrectly filter out all bugs
                # since bug statuses (accepted, rejected) differ from test statuses
                # (running, locked, archived, customer_finalized).
                if dim.key == "status":
                    continue

                filter_value = self.filters[dim.key]
                # Handle list values with IN clause
                if isinstance(filter_value, (list, tuple, set)):
                    where_clauses.append(dim.column.in_(filter_value))
                else:
                    where_clauses.append(dim.column == filter_value)
            if dim.filter_condition is not None:
                where_clauses.append(dim.filter_condition)

        # Date range filter (ensure Test is joined)
        if self.start_date or self.end_date:
            from testio_mcp.utilities.date_utils import parse_flexible_date

            stmt = self._ensure_test_joined(stmt, joined_models)

            if self.start_date:
                start = parse_flexible_date(self.start_date)
                # Type ignored: SQLAlchemy column comparison with datetime
                where_clauses.append(Test.end_at >= start)  # type: ignore[operator]
            if self.end_date:
                end = parse_flexible_date(self.end_date)
                # Type ignored: SQLAlchemy column comparison with datetime
                where_clauses.append(Test.end_at <= end)  # type: ignore[operator]

        if where_clauses:
            # Type ignored: SQLAlchemy and_() accepts column expressions
            stmt = stmt.where(and_(*where_clauses))  # type: ignore[arg-type]

        # Group by dimensions (includes both column and id_column)
        if group_by_columns:
            stmt = stmt.group_by(*group_by_columns)

        # Order by - resolve sort_by to actual column/metric expression
        # Find the labeled column from our select list
        sort_column_expr = None
        for col in select_columns:
            if hasattr(col, "name") and col.name == self.sort_column:
                sort_column_expr = col
                break

        if sort_column_expr is None:
            # Fallback: use first metric
            sort_column_expr = select_columns[-1] if select_columns else select_columns[0]

        if self.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column_expr))
        else:
            stmt = stmt.order_by(asc(sort_column_expr))

        # Limit (safety)
        stmt = stmt.limit(1000)

        return stmt

    def _add_joins(
        self,
        stmt: Select,  # type: ignore[type-arg]
        join_path: list[type],
        joined_models: set[type],
        join_type: str = "inner",
    ) -> Select:  # type: ignore[type-arg]
        """Add necessary joins to statement.

        Args:
            stmt: Current SELECT statement
            join_path: List of ORM models to join
            joined_models: Set of already-joined models (for deduplication)
            join_type: Type of join - "inner" (default) or "left"
                - "inner": Used for dimensions (defines grouping grain)
                - "left": Used for metrics (preserves zero counts)

        Returns:
            Updated SELECT statement with joins added

        Note:
            Skips TestFeature since it's the anchor table (already in select_from).
            Uses explicit join conditions for models with ambiguous relationships.

        Bug Fix (STORY-044):
            Metrics need LEFT JOIN to include zero counts (e.g., tests without bugs).
            Dimensions need INNER JOIN to filter to entities with that dimension.
        """
        for model in join_path:
            # Skip TestFeature - it's the anchor table (already in select_from)
            if model is TestFeature:
                continue
            if model not in joined_models:
                # Get explicit join condition for models with ambiguous relationships
                onclause = self._get_join_condition(model, joined_models)

                if join_type == "left":
                    if onclause is not None:
                        stmt = stmt.outerjoin(model, onclause)
                    else:
                        stmt = stmt.outerjoin(model)
                else:
                    if onclause is not None:
                        stmt = stmt.join(model, onclause)
                    else:
                        stmt = stmt.join(model)
                joined_models.add(model)
        return stmt

    def _get_join_condition(self, model: type, joined_models: set[type]) -> Any | None:
        """Get explicit join condition for models with ambiguous relationships.

        Some models have multiple foreign key paths (e.g., Bug can join via test_id
        or via test_feature). This method returns explicit join conditions to
        avoid SQLAlchemy's "Can't determine join" error.

        Args:
            model: The ORM model being joined
            joined_models: Set of already-joined models

        Returns:
            Explicit onclause for the join, or None to use SQLAlchemy's inference
        """
        # Import User here to avoid circular imports at module level
        from testio_mcp.models.orm import User

        # Bug joins to TestFeature via test_feature_id (primary path for analytics)
        if model is Bug:
            return Bug.test_feature_id == TestFeature.id

        # User joins to Bug via reported_by_user_id (tester dimension)
        if model is User and Bug in joined_models:
            return User.id == Bug.reported_by_user_id

        # TestPlatform joins to Test via test_id
        if model is TestPlatform and Test in joined_models:
            return TestPlatform.test_id == Test.id

        # Test joins to TestFeature via test_id (primary analytics path)
        # This explicit condition prevents ambiguity when User is already joined
        # (Test has 2 FKs to User: created_by_user_id, submitted_by_user_id)
        if model is Test:
            return Test.id == TestFeature.test_id

        # Default: let SQLAlchemy infer the join condition
        return None
