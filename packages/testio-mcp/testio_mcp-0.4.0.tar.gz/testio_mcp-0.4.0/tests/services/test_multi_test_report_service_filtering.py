"""Unit tests for MultiTestReportService default filtering behavior (STORY-026).

Tests verify that:
1. statuses=None excludes initialized and cancelled by default
2. Explicit statuses list overrides default filtering
3. statuses_applied field is correctly included in response
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from testio_mcp.services.multi_test_report_service import MultiTestReportService


def setup_repo_mocks(
    tests: list[dict[str, Any]] | None = None,
    bugs_by_test: dict[int, list[dict[str, Any]]] | None = None,
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    """Create mock repositories with standard responses for PQR tests."""
    tests = tests or []
    bugs_by_test = bugs_by_test or {}

    test_ids = [t["id"] for t in tests if t.get("id")]

    # Count tests by status/type
    tests_by_status: dict[str, int] = {}
    tests_by_type: dict[str, int] = {}
    for t in tests:
        status = t.get("status", "unknown")
        tests_by_status[status] = tests_by_status.get(status, 0) + 1
        ttype = t.get("testing_type", "unknown")
        tests_by_type[ttype] = tests_by_type.get(ttype, 0) + 1

    # Count bugs by status/severity
    total_bugs = sum(len(bugs) for bugs in bugs_by_test.values())
    bugs_by_status: dict[str, int] = {}
    bugs_by_severity: dict[str, int] = {}
    for bugs in bugs_by_test.values():
        for bug in bugs:
            status = bug.get("status", "unknown")
            bugs_by_status[status] = bugs_by_status.get(status, 0) + 1
            severity = bug.get("severity", "unknown")
            bugs_by_severity[severity] = bugs_by_severity.get(severity, 0) + 1

    mock_test_repo = AsyncMock()
    mock_test_repo.get_test_aggregates_for_products.return_value = {
        "total_tests": len(tests),
        "tests_by_status": tests_by_status,
        "tests_by_type": tests_by_type,
    }
    mock_test_repo.get_test_ids_for_products.return_value = test_ids
    mock_test_repo.query_tests_for_products.return_value = tests

    mock_bug_repo = AsyncMock()
    mock_bug_repo.get_bug_aggregates_for_tests.return_value = {
        "total_bugs": total_bugs,
        "bugs_by_status": bugs_by_status,
        "bugs_by_severity": bugs_by_severity,
    }
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = (
        bugs_by_test,
        {
            "total_tests": len(test_ids),
            "cache_hits": len(test_ids),
            "api_calls": 0,
            "cache_hit_rate": 100.0 if test_ids else 0.0,
            "breakdown": {"immutable_cached": len(test_ids)},
        },
    )

    mock_product_repo = AsyncMock()
    mock_product_repo.get_product_info.return_value = {
        "id": 123,
        "name": "Test Product",
        "type": "web",
    }

    return mock_test_repo, mock_bug_repo, mock_product_repo


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_excludes_initialized_and_cancelled() -> None:
    """Verify statuses=None excludes initialized and cancelled by default."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Call with statuses=None
    result = await service.get_product_quality_report(
        product_ids=[123],
        statuses=None,  # Default filter
    )

    # Verify query_tests_for_products called with correct filter
    mock_test_repo.query_tests_for_products.assert_called_once()
    call_args = mock_test_repo.query_tests_for_products.call_args
    assert call_args.kwargs["product_ids"] == [123]
    assert call_args.kwargs["statuses"] == [
        "running",
        "locked",
        "archived",
        "customer_finalized",
    ]

    # Verify summary includes effective statuses
    assert result["summary"]["statuses_applied"] == [
        "running",
        "locked",
        "archived",
        "customer_finalized",
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_explicit_statuses_override_default() -> None:
    """Verify explicit statuses list overrides default filtering."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Call with explicit statuses
    result = await service.get_product_quality_report(
        product_ids=[123],
        statuses=["initialized", "cancelled"],  # Explicit override
    )

    # Verify explicit statuses used (no default filter applied)
    call_args = mock_test_repo.query_tests_for_products.call_args
    assert call_args.kwargs["statuses"] == ["initialized", "cancelled"]

    # Verify statuses_applied reflects explicit choice
    assert result["summary"]["statuses_applied"] == ["initialized", "cancelled"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_mock_data_excludes_unexecuted() -> None:
    """Test with mock data: verify initialized/cancelled tests excluded from results."""
    tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "locked",
            "start_at": "2024-01-01T00:00:00+00:00",
            "end_at": "2024-01-02T00:00:00+00:00",
        },
        {
            "id": 2,
            "title": "Test 2",
            "status": "archived",
            "start_at": "2024-01-03T00:00:00+00:00",
            "end_at": "2024-01-04T00:00:00+00:00",
        },
    ]
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=tests,
        bugs_by_test={1: [], 2: []},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Call with statuses=None (default filter)
    result = await service.get_product_quality_report(product_ids=[123], statuses=None)

    # Verify no initialized/cancelled tests in results
    statuses_in_results = result["summary"]["tests_by_status"].keys()
    assert "initialized" not in statuses_in_results
    assert "cancelled" not in statuses_in_results

    # Verify only executed tests counted
    assert result["summary"]["total_tests"] == 2
    assert result["summary"]["tests_by_status"] == {"locked": 1, "archived": 1}

    # Verify statuses_applied field
    assert result["summary"]["statuses_applied"] == [
        "running",
        "locked",
        "archived",
        "customer_finalized",
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_all_statuses_when_explicit_empty_list() -> None:
    """Verify that passing an explicit empty list uses 'all' statuses."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Call with explicit empty list (edge case: should be treated as "no filter")
    result = await service.get_product_quality_report(
        product_ids=[123],
        statuses=[],  # Explicit empty list
    )

    # Verify empty list passed to repository (no filter, but explicit choice)
    call_args = mock_test_repo.query_tests_for_products.call_args
    assert call_args.kwargs["statuses"] == []

    # Verify statuses_applied shows "all" for empty list
    # Empty list is falsy, so effective_statuses or "all" returns "all"
    assert result["summary"]["statuses_applied"] == "all"
