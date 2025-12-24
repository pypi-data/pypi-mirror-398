"""Unit tests for TestService.

Verifies business logic for test listing, status retrieval, and bug aggregation.
Mocks repositories to ensure isolation from database.
"""

from unittest.mock import AsyncMock

import pytest

from testio_mcp.exceptions import ProductNotFoundException, TestNotFoundException
from testio_mcp.services.test_service import TestService


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def mock_test_repo():
    return AsyncMock()


@pytest.fixture
def mock_bug_repo():
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_client, mock_test_repo, mock_bug_repo, mock_product_repo):
    return TestService(
        client=mock_client,
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_summary_success(service, mock_test_repo, mock_bug_repo):
    """Verify get_test_summary returns complete test details with bugs."""
    test_id = 123

    # Mock bug repo response (intelligent caching)
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = (
        {123: [{"id": 1, "status": "accepted", "severity": "high", "title": "Bug Title"}]},
        {"cache_hits": 1},
    )

    # Mock test repo response
    mock_test_repo.get_test_with_bugs.return_value = {
        "test": {
            "id": 123,
            "title": "Test Title",
            "status": "running",
            "testing_type": "exploratory",
            "product": {"id": 1, "name": "Product"},
            "requirements": [],
        }
    }

    result = await service.get_test_summary(test_id)

    # Verify interactions
    mock_test_repo.refresh_test.assert_called_once_with(test_id)
    mock_bug_repo.get_bugs_cached_or_refresh.assert_called_once_with(
        test_ids=[test_id], force_refresh=False
    )
    mock_test_repo.get_test_with_bugs.assert_called_once_with(test_id)

    # Verify result structure
    assert result["test"]["id"] == 123
    assert result["test"]["title"] == "Test Title"
    assert result["bugs"]["total_count"] == 1
    assert result["bugs"]["by_severity"]["high"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_summary_not_found(service, mock_test_repo):
    """Verify get_test_summary raises TestNotFoundException if test missing."""
    test_id = 999

    # Mock refresh failure (404)
    error = Exception("Not Found")
    error.status_code = 404
    mock_test_repo.refresh_test.side_effect = error

    with pytest.raises(TestNotFoundException):
        await service.get_test_summary(test_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tests_success(service, mock_test_repo, mock_product_repo):
    """Verify list_tests returns paginated results."""
    product_id = 1

    # Mock product exists
    mock_product_repo.get_product_info.return_value = {"id": 1, "name": "Product"}

    # Mock staleness check (STORY-046, AC10)
    mock_test_repo.get_test_ids_for_product.return_value = [1, 2]
    mock_test_repo.get_tests_cached_or_refresh.return_value = (
        {1: {"id": 1}, 2: {"id": 2}},  # test_data dict
        {"cache_hits": 2, "total_tests": 2, "cache_hit_rate": 100.0},  # cache_stats
    )

    # Mock tests query
    mock_test_repo.query_tests.return_value = [
        {"id": 1, "title": "Test 1"},
        {"id": 2, "title": "Test 2"},
    ]
    mock_test_repo.count_filtered_tests.return_value = 10

    result = await service.list_tests(product_id=product_id, page=1, per_page=50)

    # Verify interactions
    mock_product_repo.get_product_info.assert_called_once_with(product_id)
    mock_test_repo.query_tests.assert_called_once()

    # Verify result
    assert len(result["tests"]) == 2
    assert result["total_count"] == 10
    assert result["has_more"] is False  # 2 < 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tests_product_not_found(service, mock_product_repo):
    """Verify list_tests raises ProductNotFoundException."""
    product_id = 999
    mock_product_repo.get_product_info.return_value = None

    with pytest.raises(ProductNotFoundException):
        await service.list_tests(product_id=product_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_bugs_success(service, mock_bug_repo):
    """Verify get_test_bugs refreshes and returns bugs."""
    test_id = 123

    # STORY-047: Use enriched status values
    mock_bug_repo.get_bugs.return_value = [
        {"id": 1, "status": "accepted"},  # Active accepted (enriched)
        {"id": 2, "status": "rejected"},
    ]

    result = await service.get_test_bugs(test_id)

    # Verify interactions
    mock_bug_repo.refresh_bugs.assert_called_once_with(test_id)
    mock_bug_repo.get_bugs.assert_called_once_with(test_id)

    # Verify classification
    assert result["total_count"] == 2
    assert result["by_status"]["active_accepted"] == 1
    assert result["by_status"]["rejected"] == 1


# STORY-073: Test Environment and Known Bugs Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_summary_includes_test_environment_when_present(
    service, mock_test_repo, mock_bug_repo
):
    """Verify get_test_summary includes test_environment in response when present.

    AC1: Given a test with test_environment data, when get_test_summary() is called,
    then the response includes test_environment: {id, title}.
    """
    test_id = 123

    # Mock bug repo response
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = ({123: []}, {"cache_hits": 1})

    # Mock test repo response with test_environment
    mock_test_repo.get_test_with_bugs.return_value = {
        "test": {
            "id": 123,
            "title": "Test Title",
            "status": "running",
            "testing_type": "exploratory",
            "product": {"id": 1, "name": "Product"},
            "requirements": [],
            "test_environment": {"id": 456, "title": "Production Environment"},
        }
    }

    result = await service.get_test_summary(test_id)

    # Verify test_environment is included in response
    assert result["test"]["test_environment"] is not None
    assert result["test"]["test_environment"]["id"] == 456
    assert result["test"]["test_environment"]["title"] == "Production Environment"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_summary_handles_none_test_environment(
    service, mock_test_repo, mock_bug_repo
):
    """Verify get_test_summary handles None test_environment gracefully.

    AC1: Test that when test_environment is None, the response includes
    test_environment: None (not missing).
    """
    test_id = 123

    # Mock bug repo response
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = ({123: []}, {"cache_hits": 1})

    # Mock test repo response without test_environment
    mock_test_repo.get_test_with_bugs.return_value = {
        "test": {
            "id": 123,
            "title": "Test Title",
            "status": "running",
            "testing_type": "exploratory",
            "product": {"id": 1, "name": "Product"},
            "requirements": [],
            "test_environment": None,
        }
    }

    result = await service.get_test_summary(test_id)

    # Verify test_environment is None (not missing)
    assert "test_environment" in result["test"]
    assert result["test"]["test_environment"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregate_bug_summary_calculates_known_bugs_count_mixed(service):
    """Verify _aggregate_bug_summary counts bugs where known==True.

    AC2: Given bugs with mixed known values (3 known, 2 unknown),
    when _aggregate_bug_summary is called,
    then summary["known_bugs_count"] == 3.
    """
    bugs = [
        {
            "id": 1,
            "title": "Bug 1",
            "severity": "high",
            "status": "accepted",
            "known": True,
            "created_at": "2024-01-01",
        },
        {
            "id": 2,
            "title": "Bug 2",
            "severity": "low",
            "status": "accepted",
            "known": False,
            "created_at": "2024-01-02",
        },
        {
            "id": 3,
            "title": "Bug 3",
            "severity": "critical",
            "status": "accepted",
            "known": True,
            "created_at": "2024-01-03",
        },
        {
            "id": 4,
            "title": "Bug 4",
            "severity": "high",
            "status": "rejected",
            "known": False,
            "created_at": "2024-01-04",
        },
        {
            "id": 5,
            "title": "Bug 5",
            "severity": "low",
            "status": "forwarded",
            "known": True,
            "created_at": "2024-01-05",
        },
    ]

    summary = service._aggregate_bug_summary(bugs)

    # Verify known_bugs_count calculation
    assert summary["known_bugs_count"] == 3
    assert summary["total_count"] == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregate_bug_summary_known_bugs_count_zero_when_none_known(service):
    """Verify known_bugs_count is 0 when no bugs are known.

    AC2: Given bugs with all known=False,
    when _aggregate_bug_summary is called,
    then summary["known_bugs_count"] == 0.
    """
    bugs = [
        {
            "id": 1,
            "title": "Bug 1",
            "severity": "high",
            "status": "accepted",
            "known": False,
            "created_at": "2024-01-01",
        },
        {
            "id": 2,
            "title": "Bug 2",
            "severity": "low",
            "status": "rejected",
            "known": False,
            "created_at": "2024-01-02",
        },
    ]

    summary = service._aggregate_bug_summary(bugs)

    # Verify known_bugs_count is 0
    assert summary["known_bugs_count"] == 0
    assert summary["total_count"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregate_bug_summary_known_bugs_count_defaults_to_false(service):
    """Verify known_bugs_count handles missing 'known' field (defaults to False).

    AC2: Given bugs without 'known' field,
    when _aggregate_bug_summary is called,
    then summary["known_bugs_count"] == 0 (defaults to False).
    """
    bugs = [
        {
            "id": 1,
            "title": "Bug 1",
            "severity": "high",
            "status": "accepted",
            "created_at": "2024-01-01",
        },
        {
            "id": 2,
            "title": "Bug 2",
            "severity": "low",
            "status": "rejected",
            "created_at": "2024-01-02",
        },
    ]

    summary = service._aggregate_bug_summary(bugs)

    # Verify known_bugs_count is 0 when field is missing
    assert summary["known_bugs_count"] == 0
    assert summary["total_count"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tests_includes_test_environment_in_each_test(
    service, mock_test_repo, mock_product_repo
):
    """Verify list_tests includes test_environment in each test.

    AC3: Given tests with test_environment data,
    when list_tests() is called,
    then each test in response["tests"] includes test_environment field.
    """
    product_id = 1

    # Mock product exists
    mock_product_repo.get_product_info.return_value = {"id": 1, "name": "Product"}

    # Mock staleness check
    mock_test_repo.get_test_ids_for_product.return_value = [1, 2]
    mock_test_repo.get_tests_cached_or_refresh.return_value = (
        {1: {"id": 1}, 2: {"id": 2}},
        {"cache_hits": 2, "total_tests": 2, "cache_hit_rate": 100.0},
    )

    # Mock tests query with test_environment
    mock_test_repo.query_tests.return_value = [
        {
            "id": 1,
            "title": "Test 1",
            "test_environment": {"id": 100, "title": "Staging"},
        },
        {
            "id": 2,
            "title": "Test 2",
            "test_environment": {"id": 200, "title": "Production"},
        },
    ]
    mock_test_repo.count_filtered_tests.return_value = 2

    result = await service.list_tests(product_id=product_id, page=1, per_page=50)

    # Verify all tests include test_environment
    assert len(result["tests"]) == 2
    assert result["tests"][0]["test_environment"]["id"] == 100
    assert result["tests"][0]["test_environment"]["title"] == "Staging"
    assert result["tests"][1]["test_environment"]["id"] == 200
    assert result["tests"][1]["test_environment"]["title"] == "Production"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tests_handles_none_test_environment_gracefully(
    service, mock_test_repo, mock_product_repo
):
    """Verify list_tests handles None test_environment gracefully.

    AC3: Given tests with test_environment=None,
    when list_tests() is called,
    then tests with None are included in results.
    """
    product_id = 1

    # Mock product exists
    mock_product_repo.get_product_info.return_value = {"id": 1, "name": "Product"}

    # Mock staleness check
    mock_test_repo.get_test_ids_for_product.return_value = [1, 2]
    mock_test_repo.get_tests_cached_or_refresh.return_value = (
        {1: {"id": 1}, 2: {"id": 2}},
        {"cache_hits": 2, "total_tests": 2, "cache_hit_rate": 100.0},
    )

    # Mock tests query with None test_environment
    mock_test_repo.query_tests.return_value = [
        {"id": 1, "title": "Test 1", "test_environment": None},
        {"id": 2, "title": "Test 2", "test_environment": None},
    ]
    mock_test_repo.count_filtered_tests.return_value = 2

    result = await service.list_tests(product_id=product_id, page=1, per_page=50)

    # Verify tests with None test_environment are included
    assert len(result["tests"]) == 2
    assert result["tests"][0]["test_environment"] is None
    assert result["tests"][1]["test_environment"] is None
