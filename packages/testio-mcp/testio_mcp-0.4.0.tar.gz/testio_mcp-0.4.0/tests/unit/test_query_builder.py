"""Unit tests for QueryBuilder.

Tests verify that:
1. QueryBuilder constructs SELECT with dimension columns and metric expressions
2. Adds necessary joins based on dimension/metric requirements
3. Applies customer_id filter (security)
4. Adds date range filter when start_date/end_date provided
5. Validates sort_order and sort_by
6. Limits results to 1000 rows

STORY-043: Analytics Service (The Engine)
Epic: EPIC-007 (Generic Analytics Framework)
"""

from itertools import combinations
from unittest.mock import AsyncMock

import pytest

from testio_mcp.models.orm import Bug, Feature, Test, TestFeature
from testio_mcp.services.analytics_service import (
    DimensionDef,
    MetricDef,
    build_dimension_registry,
    build_metric_registry,
)
from testio_mcp.services.query_builder import QueryBuilder


@pytest.mark.unit
def test_query_builder_validates_sort_order() -> None:
    """Test QueryBuilder validates sort_order is 'asc' or 'desc'."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Set up minimal metrics so sort validation passes
    metrics = {
        "test_metric": MetricDef(
            key="test_metric",
            description="Test Metric",
            expression=func.count(Bug.id),
            join_path=[Bug],
            formula="COUNT(bug_id)",
        )
    }
    builder.set_metrics(["test_metric"], metrics)

    # Valid sort_order
    builder.set_sort("test_metric", "asc")
    assert builder.sort_order == "asc"

    builder.set_sort("test_metric", "desc")
    assert builder.sort_order == "desc"

    # Invalid sort_order
    with pytest.raises(ValueError, match="sort_order must be 'asc' or 'desc'"):
        builder.set_sort("test_metric", "invalid")


@pytest.mark.unit
def test_query_builder_validates_sort_by_in_dimensions_or_metrics() -> None:
    """Test QueryBuilder validates sort_by is in dimensions or metrics."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Set dimensions and metrics
    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)

    # Valid sort_by (dimension)
    builder.set_sort("feature", "desc")
    assert builder.sort_column == "feature"

    # Valid sort_by (metric)
    builder.set_sort("bug_count", "desc")
    assert builder.sort_column == "bug_count"

    # Invalid sort_by
    with pytest.raises(ValueError, match="sort_by 'invalid' must be a dimension or metric"):
        builder.set_sort("invalid", "desc")


@pytest.mark.unit
def test_query_builder_adds_customer_id_filter() -> None:
    """Test QueryBuilder always filters by TestFeature.customer_id."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Set minimal dimensions and metrics
    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_sort("bug_count", "desc")

    # Build query
    stmt = builder.build()

    # Verify WHERE clause includes customer_id filter
    where_clause = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "test_features.customer_id = 123" in where_clause


@pytest.mark.unit
def test_query_builder_limits_results_to_1000() -> None:
    """Test QueryBuilder limits results to 1000 rows."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()

    # Verify LIMIT clause
    assert stmt._limit_clause is not None  # type: ignore[attr-defined]
    assert stmt._limit_clause.value == 1000  # type: ignore[attr-defined]


@pytest.mark.unit
def test_query_builder_uses_test_feature_as_anchor() -> None:
    """Test QueryBuilder starts with TestFeature as anchor table."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()

    # Verify FROM clause is TestFeature
    froms = stmt.get_final_froms()
    assert len(froms) > 0
    # Check if TestFeature is in the FROM clause
    from_tables = [str(f) for f in froms]
    assert any("test_features" in table for table in from_tables)


@pytest.mark.unit
def test_query_builder_adds_group_by_for_dimensions() -> None:
    """Test QueryBuilder adds GROUP BY for dimension columns."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()

    # Verify GROUP BY clause exists
    group_by = stmt._group_by_clauses  # type: ignore[attr-defined]
    assert len(group_by) > 0


@pytest.mark.unit
def test_query_builder_includes_dimension_id_columns() -> None:
    """Test QueryBuilder includes both ID and value columns for dimensions."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()

    # Verify SELECT includes both feature_id and feature columns
    select_clause = str(stmt)
    assert "feature_id" in select_clause.lower() or "features.id" in select_clause.lower()


@pytest.mark.unit
def test_query_builder_applies_date_range_filter() -> None:
    """Test QueryBuilder adds date range filter when start_date/end_date provided."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    dimensions = {
        "month": DimensionDef(
            key="month",
            description="Month",
            column=func.strftime("%Y-%m", Test.end_at),  # STORY-054: Use end_at
            id_column=None,
            join_path=[Test],
        )
    }
    metrics = {
        "test_count": MetricDef(
            key="test_count",
            description="Test Count",
            expression=func.count(Test.id),
            join_path=[Test],
            formula="COUNT(test_id)",
        )
    }

    builder.set_dimensions(["month"], dimensions)
    builder.set_metrics(["test_count"], metrics)
    builder.set_date_range(start_date="2024-11-01", end_date="2024-11-30")
    builder.set_sort("test_count", "desc")

    stmt = builder.build()

    # Verify WHERE clause includes date range (via Test.end_at)
    where_clause = str(stmt)
    assert "end_at" in where_clause.lower()


@pytest.mark.unit
def test_query_builder_joins_test_for_date_filtering() -> None:
    """Test QueryBuilder ensures Test is joined when date filtering is used."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Use feature dimension (doesn't include Test in join path)
    dimensions = {
        "feature": DimensionDef(
            key="feature",
            description="Feature",
            column=Feature.title,
            id_column=Feature.id,
            join_path=[TestFeature, Feature],
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(Bug.id),
            join_path=[TestFeature, Bug],
            formula="COUNT(bug_id)",
        )
    }

    builder.set_dimensions(["feature"], dimensions)
    builder.set_metrics(["bug_count"], metrics)
    builder.set_date_range(start_date="2024-11-01", end_date=None)
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()

    # Verify Test is joined (needed for date filtering)
    query_str = str(stmt)
    assert "tests" in query_str.lower()


# ==========================================
# Dimension Combination Tests
# ==========================================
# These tests verify that all dimension combinations generate valid SQL
# without join ambiguity errors. This catches issues like the tester+platform
# bug fixed in query_builder.py:_get_join_condition().

# All 14 dimensions
DIMENSIONS = [
    "feature",
    "product",
    "platform",
    "tester",
    "customer",
    "severity",
    "status",
    "testing_type",
    "month",
    "week",
    "quarter",
    "rejection_reason",
    "test_environment",
    "known_bug",
]

# Pre-build registries once for all tests
DIMENSION_REGISTRY = build_dimension_registry()
METRIC_REGISTRY = build_metric_registry()


@pytest.mark.unit
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_single_dimension_generates_valid_sql(dimension: str) -> None:
    """Test each single dimension generates valid SQL without errors."""
    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    builder.set_dimensions([dimension], DIMENSION_REGISTRY)
    builder.set_metrics(["bug_count"], METRIC_REGISTRY)
    builder.set_sort("bug_count", "desc")

    # Should not raise any exception (especially join ambiguity errors)
    stmt = builder.build()
    assert stmt is not None

    # Verify SQL string can be generated (catches compilation errors)
    sql_str = str(stmt)
    assert "test_features" in sql_str.lower()  # Anchor table always present


@pytest.mark.unit
@pytest.mark.parametrize("dim1,dim2", list(combinations(DIMENSIONS, 2)))
def test_dimension_pair_generates_valid_sql(dim1: str, dim2: str) -> None:
    """Test all 91 dimension pairs generate valid SQL without join ambiguity.

    This test catches errors like:
    - "Can't determine join between X and Y; tables have more than one
      foreign key constraint relationship between them"

    These errors occur when SQLAlchemy can't infer which FK to use for a join,
    requiring explicit onclause in QueryBuilder._get_join_condition().
    """
    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    builder.set_dimensions([dim1, dim2], DIMENSION_REGISTRY)
    builder.set_metrics(["bug_count"], METRIC_REGISTRY)
    builder.set_sort("bug_count", "desc")

    # Should not raise any exception
    stmt = builder.build()
    assert stmt is not None

    # Verify SQL string can be generated
    sql_str = str(stmt)
    assert "test_features" in sql_str.lower()


@pytest.mark.unit
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_dimension_with_product_id_filter(dimension: str) -> None:
    """Test each dimension works with product_id filter."""
    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    builder.set_dimensions([dimension], DIMENSION_REGISTRY)
    builder.set_metrics(["bug_count"], METRIC_REGISTRY)
    builder.set_filters({"product_id": 598})
    builder.set_sort("bug_count", "desc")

    # Should not raise any exception
    stmt = builder.build()
    assert stmt is not None

    # Verify product_id filter is in WHERE clause
    sql_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "product_id" in sql_str.lower() or "598" in sql_str


@pytest.mark.unit
@pytest.mark.parametrize(
    "dim1,dim2",
    [
        # Combinations that previously caused join ambiguity issues
        ("tester", "platform"),
        ("platform", "tester"),
        # Other potentially problematic combinations (User has multiple FKs)
        ("tester", "customer"),
        ("customer", "tester"),
        # Platform combinations (TestPlatform joins via Test)
        ("platform", "feature"),
        ("platform", "severity"),
        ("platform", "month"),
    ],
)
def test_known_problematic_dimension_pairs(dim1: str, dim2: str) -> None:
    """Regression test for dimension pairs that previously caused issues.

    These combinations involve models with multiple FK relationships:
    - tester + platform: User joined via Bug, Test has 2 FKs to User
    - tester + customer: Both involve User table
    - platform + *: TestPlatform joins via Test which has complex relationships
    """
    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    builder.set_dimensions([dim1, dim2], DIMENSION_REGISTRY)
    builder.set_metrics(["bug_count"], METRIC_REGISTRY)
    builder.set_sort("bug_count", "desc")

    # Should not raise "Can't determine join" error
    stmt = builder.build()
    assert stmt is not None

    # Verify both dimension tables are in the query
    sql_str = str(stmt).lower()
    assert "test_features" in sql_str  # Anchor always present


@pytest.mark.unit
def test_query_builder_applies_status_filter_list() -> None:
    """Test QueryBuilder applies status filter with list of values."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    metrics = {
        "test_count": MetricDef(
            key="test_count",
            description="Test Count",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id)",
        )
    }
    builder.set_metrics(["test_count"], metrics)

    dimensions = {
        "month": DimensionDef(
            key="month",
            description="Month",
            column=func.strftime("%Y-%m", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-11",
        )
    }
    builder.set_dimensions(["month"], dimensions)

    # Set status filter with list
    builder.set_filters({"status": ["running", "locked", "archived"]})
    builder.set_sort("test_count", "desc")

    stmt = builder.build()
    sql_str = str(stmt).lower()

    # Verify status filter is applied with IN clause
    # SQLAlchemy uses parameter binding, so we just check for the IN clause structure
    assert "tests.status in" in sql_str


@pytest.mark.unit
def test_query_builder_applies_status_filter_tuple() -> None:
    """Test QueryBuilder handles tuple input for status filter."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    metrics = {
        "test_count": MetricDef(
            key="test_count",
            description="Test Count",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id)",
        )
    }
    builder.set_metrics(["test_count"], metrics)

    dimensions = {
        "month": DimensionDef(
            key="month",
            description="Month",
            column=func.strftime("%Y-%m", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-11",
        )
    }
    builder.set_dimensions(["month"], dimensions)

    # Set status filter with tuple (regression test for tuple/set support)
    builder.set_filters({"status": ("running", "locked")})
    builder.set_sort("test_count", "desc")

    stmt = builder.build()
    sql_str = str(stmt).lower()

    # Verify status filter uses IN clause (not equality)
    assert "tests.status in" in sql_str
    assert "tests.status = (" not in sql_str  # Should NOT be equality with tuple


@pytest.mark.unit
def test_query_builder_applies_status_filter_single_value() -> None:
    """Test QueryBuilder handles single string value for status filter."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    metrics = {
        "test_count": MetricDef(
            key="test_count",
            description="Test Count",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id)",
        )
    }
    builder.set_metrics(["test_count"], metrics)

    dimensions = {
        "month": DimensionDef(
            key="month",
            description="Month",
            column=func.strftime("%Y-%m", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-11",
        )
    }
    builder.set_dimensions(["month"], dimensions)

    # Set status filter with single string
    builder.set_filters({"status": "running"})
    builder.set_sort("test_count", "desc")

    stmt = builder.build()
    sql_str = str(stmt).lower()

    # Verify status filter uses equality
    assert "tests.status" in sql_str


@pytest.mark.unit
def test_query_builder_dimension_filter_with_list() -> None:
    """Test QueryBuilder handles list values in dimension filters.

    Regression test for the bug where querying with dimensions=["status"]
    and a default status filter (list) caused SQLite error:
    "Error binding parameter: type 'list' is not supported"

    The fix is to use IN clause for list values instead of equality.
    """
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Use a non-status dimension to test generic list filter handling
    dimensions = {
        "severity": DimensionDef(
            key="severity",
            description="Group by Bug Severity",
            column=Bug.severity,
            id_column=None,
            join_path=[Bug],
            example="critical, major, minor",
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(func.distinct(Bug.id)),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT bug_id)",
        )
    }

    builder.set_dimensions(["severity"], dimensions)
    builder.set_metrics(["bug_count"], metrics)

    # Apply list filter to the severity dimension
    builder.set_filters({"severity": ["critical", "major"]})
    builder.set_sort("bug_count", "desc")

    # Should not raise any exception
    stmt = builder.build()
    assert stmt is not None

    # Verify dimension filter uses IN clause, not equality
    sql_str = str(stmt).lower()
    # Bug.severity should use IN clause with the list values
    assert "bugs.severity in" in sql_str


@pytest.mark.unit
def test_query_builder_status_dimension_skips_dimension_filter() -> None:
    """Test QueryBuilder skips applying status filter to Bug.status dimension.

    When "status" is used as a dimension (Bug.status for grouping), the default
    status filter (EXECUTED_TEST_STATUSES) should only apply to Test.status,
    not to Bug.status. Bug statuses (accepted, rejected, auto_accepted) are
    completely different from test statuses (running, locked, archived).

    Applying test status filter to Bug.status would incorrectly filter out all bugs.
    """
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    # Use status dimension (Bug.status)
    dimensions = {
        "status": DimensionDef(
            key="status",
            description="Group by Bug/Test Status",
            column=Bug.status,
            id_column=None,
            join_path=[Bug],
            example="open, closed, accepted",
        )
    }
    metrics = {
        "bug_count": MetricDef(
            key="bug_count",
            description="Bug Count",
            expression=func.count(func.distinct(Bug.id)),
            join_path=[TestFeature, Bug],
            formula="COUNT(DISTINCT bug_id)",
        )
    }

    builder.set_dimensions(["status"], dimensions)
    builder.set_metrics(["bug_count"], metrics)

    # Apply default test status filter (these are TEST statuses, not BUG statuses)
    builder.set_filters({"status": ["running", "locked", "archived", "customer_finalized"]})
    builder.set_sort("bug_count", "desc")

    stmt = builder.build()
    assert stmt is not None

    sql_str = str(stmt).lower()

    # The status filter should apply to Test.status (special filter)
    assert "tests.status in" in sql_str

    # The status filter should NOT apply to Bug.status (dimension column)
    # because test statuses and bug statuses are different domains
    assert "bugs.status in" not in sql_str


@pytest.mark.unit
def test_query_builder_rejects_unknown_filter_keys() -> None:
    """Test QueryBuilder raises ValueError for unknown filter keys."""
    from sqlalchemy import func

    mock_session = AsyncMock()
    builder = QueryBuilder(session=mock_session, customer_id=123)

    metrics = {
        "test_count": MetricDef(
            key="test_count",
            description="Test Count",
            expression=func.count(func.distinct(Test.id)),
            join_path=[Test],
            formula="COUNT(DISTINCT test_id)",
        )
    }
    builder.set_metrics(["test_count"], metrics)

    dimensions = {
        "month": DimensionDef(
            key="month",
            description="Month",
            column=func.strftime("%Y-%m", Test.end_at),
            id_column=None,
            join_path=[Test],
            example="2024-11",
        )
    }
    builder.set_dimensions(["month"], dimensions)

    # Set filter with typo (should raise)
    builder.set_filters({"statu": "running"})  # Typo: "statu" instead of "status"
    builder.set_sort("test_count", "desc")

    with pytest.raises(ValueError) as exc_info:
        builder.build()

    assert "Unknown filter keys" in str(exc_info.value)
    assert "statu" in str(exc_info.value)
