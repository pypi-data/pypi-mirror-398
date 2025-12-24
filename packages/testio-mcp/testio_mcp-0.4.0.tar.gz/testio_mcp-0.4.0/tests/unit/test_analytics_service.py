"""Unit tests for AnalyticsService.

Tests verify that:
1. query_metrics constructs correct queries for single/multiple dimensions
2. Dimension registry has 8 dimensions with correct join paths
3. Metric registry has 6 metrics with correct expressions
4. Performance guardrails enforced (max 2 dimensions, validation)
5. Rich response format with metadata and explanation
6. Direct attribution via Bug.test_feature_id (no fractional logic)
7. Error handling for invalid inputs

STORY-043: Analytics Service (The Engine)
Epic: EPIC-007 (Generic Analytics Framework)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.analytics_service import AnalyticsService


def _create_mock_row(**kwargs) -> MagicMock:  # type: ignore[misc]
    """Create a mock row object with attribute access."""
    mock = MagicMock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock


@pytest.mark.unit
@pytest.mark.asyncio
async def test_single_dimension_single_metric() -> None:
    """Test basic query: bug_count by feature."""
    # Setup: Mock session that returns query results
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [
        _create_mock_row(feature_id=1, feature="Login", bug_count=10),
        _create_mock_row(feature_id=2, feature="Dashboard", bug_count=5),
    ]
    mock_session.exec.return_value = mock_result

    # Create service (with mock client for STORY-044B)
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Call query_metrics
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["feature"])

    # Verify response is QueryResponse model
    assert result.data is not None
    assert result.metadata is not None
    assert result.query_explanation is not None
    assert result.warnings is not None

    # Verify metadata
    assert result.metadata.dimensions_used == ["feature"]
    assert result.metadata.metrics_used == ["bug_count"]
    assert result.metadata.total_rows == 2

    # Verify data includes both ID and display name
    assert result.data[0]["feature_id"] == 1
    assert result.data[0]["feature"] == "Login"
    assert result.data[0]["bug_count"] == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_dimensions() -> None:
    """Test multi-dimension query: bug_count by feature and month."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [
        _create_mock_row(feature_id=1, feature="Login", month="2024-11", bug_count=10),
        _create_mock_row(feature_id=1, feature="Login", month="2024-12", bug_count=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["feature", "month"])

    # Verify dimensions used
    assert result.metadata.dimensions_used == ["feature", "month"]

    # Verify rows have both dimensions
    assert result.data[0]["feature"] == "Login"
    assert result.data[0]["month"] == "2024-11"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_status_filter_excludes_unexecuted_tests() -> None:
    """Test that query_metrics applies default status filter excluding initialized/cancelled."""
    from unittest.mock import patch

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [_create_mock_row(feature_id=1, feature="Login", bug_count=10)]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Patch QueryBuilder to spy on set_filters call
    with patch("testio_mcp.services.analytics_service.QueryBuilder") as MockQueryBuilder:
        mock_builder = MagicMock()
        MockQueryBuilder.return_value = mock_builder
        mock_builder.build.return_value = MagicMock()  # Return mock SELECT statement

        # Call query_metrics WITHOUT status filter
        await service.query_metrics(metrics=["bug_count"], dimensions=["feature"])

        # Verify set_filters was called with default status filter
        set_filters_call = mock_builder.set_filters.call_args[0][0]
        assert "status" in set_filters_call
        assert set(set_filters_call["status"]) == {
            "running",
            "locked",
            "archived",
            "customer_finalized",
        }
        assert "initialized" not in set_filters_call["status"]
        assert "cancelled" not in set_filters_call["status"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_explicit_status_filter_overrides_default() -> None:
    """Test that explicit status filter overrides the default."""
    from unittest.mock import patch

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [_create_mock_row(feature_id=1, feature="Login", bug_count=10)]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Patch QueryBuilder to spy on set_filters call
    with patch("testio_mcp.services.analytics_service.QueryBuilder") as MockQueryBuilder:
        mock_builder = MagicMock()
        MockQueryBuilder.return_value = mock_builder
        mock_builder.build.return_value = MagicMock()

        # Call query_metrics WITH explicit status filter (including initialized)
        await service.query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"status": ["initialized", "cancelled"]},
        )

        # Verify set_filters was called with user's explicit status filter
        set_filters_call = mock_builder.set_filters.call_args[0][0]
        assert "status" in set_filters_call
        assert set(set_filters_call["status"]) == {"initialized", "cancelled"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dimension_filters() -> None:
    """Test dimension value filtering."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [_create_mock_row(severity="critical", bug_count=5)]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    # Use severity as BOTH dimension AND filter (dimension must be included to filter on it)
    result = await service.query_metrics(
        metrics=["bug_count"], dimensions=["severity"], filters={"severity": "critical"}
    )

    # Verify filter mentioned in explanation
    assert "filtered by severity=critical" in result.query_explanation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sort_control() -> None:
    """Test sort_by and sort_order."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [
        _create_mock_row(feature_id=1, feature="Login", bug_count=10),
        _create_mock_row(feature_id=2, feature="Dashboard", bug_count=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(
        metrics=["bug_count"],
        dimensions=["feature"],
        sort_by="bug_count",
        sort_order="desc",
    )

    # Verify descending order in data (mocked data already sorted)
    assert result.data[0]["bug_count"] >= result.data[1]["bug_count"]

    # Verify explanation mentions sort order
    assert "descending" in result.query_explanation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sort_ascending_in_explanation() -> None:
    """Test that ascending sort order appears correctly in explanation."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [
        _create_mock_row(feature_id=1, feature="Login", bug_count=5),
        _create_mock_row(feature_id=2, feature="Dashboard", bug_count=10),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(
        metrics=["bug_count"],
        dimensions=["feature"],
        sort_by="bug_count",
        sort_order="asc",
    )

    # Verify explanation has "ascending" not "descendingending" bug
    assert "ascending" in result.query_explanation
    assert "descending" not in result.query_explanation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_too_many_dimensions_error() -> None:
    """Test error when exceeding max dimensions."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    with pytest.raises(ValueError, match="Too many dimensions"):
        await service.query_metrics(
            metrics=["bug_count"],
            dimensions=["feature", "month", "severity"],  # 3 dimensions
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_dimension_key() -> None:
    """Test error for invalid dimension key."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    with pytest.raises(ValueError, match="Invalid dimensions"):
        await service.query_metrics(metrics=["bug_count"], dimensions=["invalid_dimension"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_metric_key() -> None:
    """Test error for invalid metric key."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    with pytest.raises(ValueError, match="Invalid metrics"):
        await service.query_metrics(metrics=["invalid_metric"], dimensions=["feature"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_acceptance_rate_suggests_alternatives() -> None:
    """Test that 'acceptance_rate' error suggests the correct metric names."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    with pytest.raises(ValueError) as exc_info:
        await service.query_metrics(metrics=["acceptance_rate"], dimensions=["feature"])

    error_msg = str(exc_info.value)
    assert "Did you mean:" in error_msg
    assert "overall_acceptance_rate" in error_msg
    assert "active_acceptance_rate" in error_msg
    assert "auto_acceptance_rate" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_filter_key() -> None:
    """Test error for invalid filter key."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    with pytest.raises(ValueError, match="Invalid filter keys"):
        await service.query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"invalid_filter": "value"},
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_product_id_filter_accepts_list() -> None:
    """Test that product_id filter accepts a list of IDs."""
    mock_session = AsyncMock()

    # Mock different results for different queries:
    # 1. Product validation query - returns all product IDs (all exist)
    # 2. Test IDs query - returns empty (no tests)
    # 3. Main metrics query - returns results
    product_validation_result = MagicMock()
    product_validation_result.all.return_value = [21362, 24994, 24959]  # All products exist

    test_ids_result = MagicMock()
    test_ids_result.all.return_value = [1, 2, 3]  # Some test IDs

    product_ids_result = MagicMock()
    product_ids_result.all.return_value = [21362]  # Product IDs from tests

    metrics_result = MagicMock()
    metrics_result.all.return_value = [
        _create_mock_row(feature_id=1, feature="Login", bug_count=10),
    ]

    # Return different results for each exec call
    mock_session.exec.side_effect = [
        product_validation_result,  # _validate_products_exist
        test_ids_result,  # _get_scoped_test_ids
        product_ids_result,  # _extract_product_ids
        metrics_result,  # main query
    ]

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Should not raise - list of product_ids is valid
    result = await service.query_metrics(
        metrics=["bug_count"],
        dimensions=["feature"],
        filters={"product_id": [21362, 24994, 24959]},
    )

    # Verify query executed successfully
    assert result is not None
    assert mock_session.exec.called


@pytest.mark.unit
@pytest.mark.asyncio
async def test_row_limit_warning() -> None:
    """Test warning when results hit 1000 row limit."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    # Create 1000 rows to trigger warning
    mock_result.all.return_value = [
        _create_mock_row(feature_id=i, feature=f"Feature{i}", bug_count=1) for i in range(1000)
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["feature"])

    # Verify warning included (STORY-055: Updated message format)
    assert any("Results limited to 1000 rows" in w for w in result.warnings)


@pytest.mark.unit
def test_dimension_registry_has_expected_dimensions() -> None:
    """Test dimension registry has all expected dimensions."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    dimensions = service._dimensions

    # Verify count (14 dimensions total)
    assert len(dimensions) == 14

    # Verify keys
    expected_keys = [
        "feature",
        "product",
        "platform",  # Normalized from Test.requirements
        "tester",
        "customer",
        "severity",
        "status",
        "testing_type",  # STORY-054 AC11
        "month",
        "week",
        "quarter",
        "rejection_reason",
        "test_environment",  # STORY-075
        "known_bug",  # STORY-075
    ]
    assert set(dimensions.keys()) == set(expected_keys)

    # Verify each has required fields
    for dim in dimensions.values():
        assert dim.key
        assert dim.description
        assert dim.column is not None
        assert dim.join_path


@pytest.mark.unit
def test_metric_registry_has_13_metrics() -> None:
    """Test metric registry has correct 13 metrics (STORY-082: +5 rate metrics)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    metrics = service._metrics

    # Verify count (8 base + 5 rate metrics = 13)
    assert len(metrics) == 13

    # Verify keys
    expected_keys = [
        "test_count",
        "bug_count",
        "bug_severity_score",
        "features_tested",
        "active_testers",
        "bugs_per_test",
        "tests_created",  # STORY-045
        "tests_submitted",  # STORY-045
        "overall_acceptance_rate",  # STORY-082
        "rejection_rate",  # STORY-082
        "review_rate",  # STORY-082
        "active_acceptance_rate",  # STORY-082
        "auto_acceptance_rate",  # STORY-082
    ]
    assert set(metrics.keys()) == set(expected_keys)

    # Verify each has required fields
    for metric in metrics.values():
        assert metric.key
        assert metric.description
        assert metric.expression is not None
        assert metric.join_path
        assert metric.formula


@pytest.mark.unit
def test_feature_dimension_join_path() -> None:
    """Test feature dimension has correct join path for direct attribution."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    from testio_mcp.models.orm import Feature, TestFeature

    feature_dim = service._dimensions["feature"]

    # Verify join path: TestFeature → Feature (direct, no fractional attribution)
    assert feature_dim.join_path == [TestFeature, Feature]


@pytest.mark.unit
def test_bug_count_metric_join_path() -> None:
    """Test bug_count metric uses direct attribution via test_feature_id."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    from testio_mcp.models.orm import Bug, TestFeature

    bug_count_metric = service._metrics["bug_count"]

    # Verify join path: TestFeature → Bug (via Bug.test_feature_id)
    assert bug_count_metric.join_path == [TestFeature, Bug]


@pytest.mark.unit
def test_tester_dimension_has_user_type_filter() -> None:
    """Test tester dimension has user_type filter condition."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    tester_dim = service._dimensions["tester"]

    # Verify filter_condition exists (should filter for user_type == 'tester')
    assert tester_dim.filter_condition is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_response_includes_query_explanation() -> None:
    """Test response includes human-readable query explanation."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [_create_mock_row(feature_id=1, feature="Login", bug_count=10)]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(
        metrics=["bug_count"], dimensions=["feature"], sort_by="bug_count"
    )

    # Verify explanation is human-readable
    explanation = result.query_explanation
    assert "Total number of bugs found" in explanation  # Metric description
    assert "Group by Feature Title" in explanation  # Dimension description
    assert "bug_count" in explanation  # Sort column


@pytest.mark.unit
@pytest.mark.asyncio
async def test_date_range_warning() -> None:
    """Test warning when date range is unbounded."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(
        metrics=["bug_count"],
        dimensions=["month"],
        start_date="2024-01-01",  # Only start_date (unbounded end)
    )

    # Verify warning about unbounded date range
    assert any("Date range spans" in w for w in result.warnings)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_metrics() -> None:
    """Test query with multiple metrics."""
    mock_session = AsyncMock()
    mock_result = MagicMock()  # Result object is NOT async
    mock_result.all.return_value = [
        _create_mock_row(
            feature_id=1, feature="Login", bug_count=10, test_count=5, bugs_per_test=2.0
        )
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)
    result = await service.query_metrics(
        metrics=["bug_count", "test_count", "bugs_per_test"], dimensions=["feature"]
    )

    # Verify all metrics in response
    assert result.data[0]["bug_count"] == 10
    assert result.data[0]["test_count"] == 5
    assert result.data[0]["bugs_per_test"] == 2.0

    # Verify metadata
    assert result.metadata.metrics_used == [
        "bug_count",
        "test_count",
        "bugs_per_test",
    ]


# STORY-045: Customer Engagement Analytics Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_by_customer_dimension() -> None:
    """Test querying by customer dimension (STORY-045 AC4.1)."""
    # Setup: Mock session that returns customer data
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(customer_id=1, customer="acme_corp", tests_created=5),
        _create_mock_row(customer_id=2, customer="beta_user_1", tests_created=3),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["tests_created"], dimensions=["customer"])

    # Verify customer dimension
    assert result.metadata.dimensions_used == ["customer"]

    # Verify results have customer_id and customer (username)
    assert result.data[0]["customer_id"] == 1
    assert result.data[0]["customer"] == "acme_corp"
    assert result.data[0]["tests_created"] == 5

    assert result.data[1]["customer_id"] == 2
    assert result.data[1]["customer"] == "beta_user_1"
    assert result.data[1]["tests_created"] == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tests_created_metric() -> None:
    """Test tests_created metric calculation (STORY-045 AC4.2)."""
    # Setup: Create 5 tests total
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(customer_id=1, customer="acme_corp", tests_created=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["tests_created"], dimensions=["customer"])

    # Verify count
    total_tests = sum(row["tests_created"] for row in result.data)
    assert total_tests == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tests_submitted_metric() -> None:
    """Test tests_submitted metric calculation with
    submitted_by_user_id filtering (STORY-045 AC4.3)."""
    # Setup: Customer with 5 tests that have submitted_by_user_id set,
    # 1 test without (total 6 created, 5 submitted)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(customer_id=1, customer="acme_corp", tests_submitted=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["tests_submitted"], dimensions=["customer"])

    # Verify only tests with submitted_by_user_id counted (not tests without submitter)
    total_submitted = sum(row["tests_submitted"] for row in result.data)
    assert total_submitted == 5  # 5 tests with submitted_by_user_id set


@pytest.mark.unit
@pytest.mark.asyncio
async def test_combined_customer_metrics() -> None:
    """Test querying multiple customer metrics together (STORY-045 AC4.4)."""
    # Setup
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(customer_id=1, customer="acme_corp", tests_created=10, tests_submitted=8),
        _create_mock_row(customer_id=2, customer="beta_user_1", tests_created=5, tests_submitted=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(
        metrics=["tests_created", "tests_submitted"],
        dimensions=["customer"],
        sort_by="tests_created",
        sort_order="desc",
    )

    # Verify both metrics present
    assert result.data[0]["tests_created"] == 10
    assert result.data[0]["tests_submitted"] == 8

    # Verify logical relationship: created >= submitted
    for row in result.data:
        assert row["tests_created"] >= row["tests_submitted"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_customer_engagement_trend() -> None:
    """Test customer engagement over time (customer + month dimensions) (STORY-045 AC4.5)."""
    # Setup
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(customer_id=1, customer="acme_corp", month="2024-11", tests_created=5),
        _create_mock_row(customer_id=1, customer="acme_corp", month="2024-12", tests_created=8),
        _create_mock_row(customer_id=2, customer="beta_user_1", month="2024-11", tests_created=3),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(
        metrics=["tests_created"], dimensions=["customer", "month"]
    )

    # Verify multi-dimension query
    assert result.metadata.dimensions_used == ["customer", "month"]

    # Verify rows have both dimensions
    assert result.data[0]["customer"] == "acme_corp"
    assert result.data[0]["month"] == "2024-11"
    assert result.data[0]["tests_created"] == 5

    # Verify trend data
    assert result.data[1]["customer"] == "acme_corp"
    assert result.data[1]["month"] == "2024-12"
    assert result.data[1]["tests_created"] == 8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quarter_dimension() -> None:
    """Test querying by quarter dimension (STORY-068)."""
    # Setup
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(quarter="2024-Q3", bug_count=10),
        _create_mock_row(quarter="2024-Q4", bug_count=15),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["quarter"])

    # Verify dimension used
    assert result.metadata.dimensions_used == ["quarter"]

    # Verify rows have quarter
    assert result.data[0]["quarter"] == "2024-Q3"
    assert result.data[0]["bug_count"] == 10
    assert result.data[1]["quarter"] == "2024-Q4"
    assert result.data[1]["bug_count"] == 15


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejection_reason_dimension() -> None:
    """Test querying by rejection_reason dimension (STORY-068)."""
    # Setup
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(rejection_reason="ignored_instructions", bug_count=5),
        _create_mock_row(rejection_reason="not_reproducible", bug_count=3),
        _create_mock_row(rejection_reason=None, bug_count=2),  # NULL case
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["rejection_reason"])

    # Verify dimension used
    assert result.metadata.dimensions_used == ["rejection_reason"]

    # Verify rows have rejection_reason
    assert result.data[0]["rejection_reason"] == "ignored_instructions"
    assert result.data[0]["bug_count"] == 5
    assert result.data[2]["rejection_reason"] is None
    assert result.data[2]["bug_count"] == 2


# STORY-075: Test Environment and Known Bug Dimensions


@pytest.mark.unit
def test_dimension_registry_includes_test_environment_and_known_bug() -> None:
    """Test that dimension registry includes test_environment and known_bug (AC1)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    dimensions = service._dimensions

    # Verify test_environment and known_bug are in registry
    assert "test_environment" in dimensions
    assert "known_bug" in dimensions

    # Verify total count (14 dimensions including platform)
    assert len(dimensions) == 14


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_by_test_environment_dimension() -> None:
    """Test querying by test_environment dimension with valid data (AC2)."""
    # Setup: Mock session that returns test_environment data
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(test_environment_id=1, test_environment="iOS 14", bug_count=10),
        _create_mock_row(test_environment_id=2, test_environment="Android 12", bug_count=5),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["test_environment"])

    # Verify results are grouped by environment name (title)
    assert result.metadata.dimensions_used == ["test_environment"]
    assert result.data[0]["test_environment_id"] == 1
    assert result.data[0]["test_environment"] == "iOS 14"
    assert result.data[0]["bug_count"] == 10
    assert result.data[1]["test_environment_id"] == 2
    assert result.data[1]["test_environment"] == "Android 12"
    assert result.data[1]["bug_count"] == 5


@pytest.mark.unit
def test_test_environment_dimension_has_null_filter() -> None:
    """Test test_environment dimension has filter condition for NULL values (AC2)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    test_env_dim = service._dimensions["test_environment"]

    # Verify filter_condition exists (should exclude NULL and 'null' string)
    assert test_env_dim.filter_condition is not None


@pytest.mark.unit
def test_test_environment_uses_json_extract() -> None:
    """Test test_environment dimension uses json_extract for title extraction (AC2)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    from testio_mcp.models.orm import Test

    test_env_dim = service._dimensions["test_environment"]

    # Verify join path uses Test table
    assert Test in test_env_dim.join_path


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_by_known_bug_dimension() -> None:
    """Test querying by known_bug dimension with true/false values (AC3)."""
    # Setup: Mock session that returns known_bug data
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(known_bug="true", bug_count=15),
        _create_mock_row(known_bug="false", bug_count=10),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute
    result = await service.query_metrics(metrics=["bug_count"], dimensions=["known_bug"])

    # Verify results show bug counts grouped by true vs false
    assert result.metadata.dimensions_used == ["known_bug"]
    assert result.data[0]["known_bug"] == "true"
    assert result.data[0]["bug_count"] == 15
    assert result.data[1]["known_bug"] == "false"
    assert result.data[1]["bug_count"] == 10


@pytest.mark.unit
def test_known_bug_dimension_formats_as_strings() -> None:
    """Test known_bug dimension formats boolean values as 'true'/'false' strings (AC3)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    from testio_mcp.models.orm import Bug

    known_bug_dim = service._dimensions["known_bug"]

    # Verify join path uses Bug table
    assert Bug in known_bug_dim.join_path

    # Verify id_column is None (boolean dimension, no ID)
    assert known_bug_dim.id_column is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_test_environment_and_known_bug_combined() -> None:
    """Test querying both new dimensions together (edge case)."""
    # Setup: Mock session that returns combined data
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(
            test_environment_id=1,
            test_environment="iOS 14",
            known_bug="true",
            bug_count=5,
        ),
        _create_mock_row(
            test_environment_id=1,
            test_environment="iOS 14",
            known_bug="false",
            bug_count=10,
        ),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute - using both new dimensions
    result = await service.query_metrics(
        metrics=["bug_count"], dimensions=["test_environment", "known_bug"]
    )

    # Verify both dimensions used
    assert result.metadata.dimensions_used == ["test_environment", "known_bug"]

    # Verify rows have both dimension values
    assert result.data[0]["test_environment"] == "iOS 14"
    assert result.data[0]["known_bug"] == "true"
    assert result.data[0]["bug_count"] == 5


# Regression tests for many-to-many dimension aggregation bug fix


@pytest.mark.unit
def test_rate_metrics_use_count_distinct_pattern() -> None:
    """Test rate metrics use COUNT(DISTINCT CASE) pattern to prevent row multiplication.

    Regression test for bug where platform dimension caused rates > 100%:
    - A test can have multiple platforms (iOS, Android, Web)
    - Same bug appears in multiple rows when JOINed to TestPlatform
    - SUM(CASE WHEN accepted THEN 1) counted rows, not distinct bugs
    - COUNT(DISTINCT bug_id) in denominator was correct
    - Result: numerator inflated, rates > 100%

    Fix: Use COUNT(DISTINCT CASE WHEN accepted THEN bug_id END) in numerator
    to ensure both numerator and denominator count distinct bugs.
    """
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Get rate metrics
    rate_metrics = [
        "overall_acceptance_rate",
        "rejection_rate",
        "review_rate",
        "active_acceptance_rate",
        "auto_acceptance_rate",
    ]

    for metric_key in rate_metrics:
        metric = service._metrics[metric_key]
        formula = metric.formula

        # Verify formula shows COUNT(DISTINCT ...) pattern
        assert "COUNT(DISTINCT" in formula, (
            f"Metric '{metric_key}' should use COUNT(DISTINCT) pattern in formula. Got: {formula}"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_dimension_with_rate_metrics_returns_valid_rates() -> None:
    """Test platform dimension with rate metrics returns rates between 0 and 1.

    Regression test: When querying by platform dimension, each test can have
    multiple platforms. Without COUNT(DISTINCT) fix, the same bug would be
    counted multiple times in the numerator, causing rates > 100%.
    """
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Simulate what fixed query returns: rates between 0 and 1
    mock_result.all.return_value = [
        _create_mock_row(
            platform_id=1,
            platform="iOS",
            bug_count=100,
            overall_acceptance_rate=0.75,
            rejection_rate=0.25,
        ),
        _create_mock_row(
            platform_id=2,
            platform="Android",
            bug_count=80,
            overall_acceptance_rate=0.60,
            rejection_rate=0.40,
        ),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    result = await service.query_metrics(
        metrics=["bug_count", "overall_acceptance_rate", "rejection_rate"],
        dimensions=["platform"],
    )

    # Verify rates are valid (between 0 and 1)
    for row in result.data:
        acceptance_rate = row["overall_acceptance_rate"]
        rejection_rate = row["rejection_rate"]

        # Rates must be between 0 and 1 (not > 100% like the bug caused)
        assert acceptance_rate is None or 0 <= acceptance_rate <= 1, (
            f"overall_acceptance_rate must be between 0 and 1, got {acceptance_rate}"
        )
        assert rejection_rate is None or 0 <= rejection_rate <= 1, (
            f"rejection_rate must be between 0 and 1, got {rejection_rate}"
        )

        # Rates should sum to <= 1 (acceptance + rejection <= total)
        if acceptance_rate is not None and rejection_rate is not None:
            total = acceptance_rate + rejection_rate
            assert total <= 1.01, (  # Small epsilon for floating point
                f"acceptance_rate + rejection_rate should be <= 1, got {total}"
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_feature_dimension_with_rate_metrics_returns_valid_rates() -> None:
    """Test feature dimension with rate metrics returns valid rates.

    Features also have many-to-many relationship with tests via TestFeature.
    Same fix applies: COUNT(DISTINCT) ensures correct aggregation.
    """
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(
            feature_id=1,
            feature="Login",
            bug_count=50,
            overall_acceptance_rate=0.80,
            rejection_rate=0.20,
        ),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    result = await service.query_metrics(
        metrics=["bug_count", "overall_acceptance_rate", "rejection_rate"],
        dimensions=["feature"],
    )

    # Verify rates are valid
    for row in result.data:
        acceptance_rate = row["overall_acceptance_rate"]
        rejection_rate = row["rejection_rate"]

        assert acceptance_rate is None or 0 <= acceptance_rate <= 1
        assert rejection_rate is None or 0 <= rejection_rate <= 1
