"""Unit tests for MultiTestReportService file export functionality (STORY-025).

Tests verify that:
1. File export writes report data to JSON file
2. File metadata response structure is correct
3. Parent directories are created automatically
4. Relative vs absolute paths work correctly
5. File overwrite succeeds
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_file_export_writes_json_file(tmp_path: Path) -> None:
    """Verify file export writes report data to JSON file with proper formatting."""
    tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "locked",
            "start_at": "2024-01-01T00:00:00+00:00",
            "end_at": "2024-01-02T00:00:00+00:00",
        }
    ]
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=tests,
        bugs_by_test={1: []},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Create output file path
    output_file = str(tmp_path / "test_report.json")

    # Call with output_file specified
    result = await service.get_product_quality_report(
        product_ids=[123],
        output_file=output_file,
    )

    # Verify file was written
    assert Path(output_file).exists()

    # Verify file contents match expected structure
    file_content = Path(output_file).read_text(encoding="utf-8")
    file_data = json.loads(file_content)

    assert "summary" in file_data
    assert "test_data" in file_data
    # Note: cache_stats was removed in PQR refactor for token efficiency

    # Verify file metadata response structure
    assert "file_path" in result
    assert "summary" in result
    assert "record_count" in result
    assert "file_size_bytes" in result
    assert "format" in result

    # Verify metadata values
    assert result["file_path"] == output_file
    assert result["record_count"] == 1
    assert result["format"] == "json"
    assert result["file_size_bytes"] > 0

    # Verify summary in metadata matches file summary
    assert result["summary"]["total_tests"] == file_data["summary"]["total_tests"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_creates_parent_directories(tmp_path: Path) -> None:
    """Verify parent directories are created automatically for nested paths."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Create nested path (parent doesn't exist)
    output_file = str(tmp_path / "reports" / "q3-2025" / "test_report.json")

    # Call with output_file specified
    result = await service.get_product_quality_report(
        product_ids=[123],
        output_file=output_file,
    )

    # Verify parent directories were created
    assert Path(output_file).parent.exists()
    assert Path(output_file).exists()

    # Verify file was written
    assert result["file_path"] == output_file


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_relative_path_resolves_to_reports_dir(tmp_path: Path) -> None:
    """Verify relative paths resolve to ~/.testio-mcp/reports/ directory."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Use relative path
    relative_path = "test_report.json"

    # Mock Path.home() to return tmp_path for testing
    with patch("testio_mcp.utilities.file_export.Path.home", return_value=tmp_path):
        result = await service.get_product_quality_report(
            product_ids=[123],
            output_file=relative_path,
        )

        # Verify path resolved to reports directory
        expected_path = tmp_path / ".testio-mcp" / "reports" / relative_path
        assert result["file_path"] == str(expected_path)
        assert Path(result["file_path"]).exists()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_absolute_path_used_as_is(tmp_path: Path) -> None:
    """Verify absolute paths are used as-is (after expanding ~)."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Use absolute path
    absolute_path = str(tmp_path / "absolute_report.json")

    # Call with absolute path
    result = await service.get_product_quality_report(
        product_ids=[123],
        output_file=absolute_path,
    )

    # Verify absolute path used as-is
    assert result["file_path"] == absolute_path
    assert Path(absolute_path).exists()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_overwrites_existing_file(tmp_path: Path) -> None:
    """Verify file overwrite succeeds (existing file is replaced)."""
    tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "locked",
            "start_at": "2024-01-01T00:00:00+00:00",
            "end_at": "2024-01-02T00:00:00+00:00",
        }
    ]
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=tests,
        bugs_by_test={1: []},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    output_file = str(tmp_path / "test_report.json")

    # Create existing file with different content
    Path(output_file).write_text('{"old": "data"}', encoding="utf-8")
    original_size = Path(output_file).stat().st_size

    # Call with output_file (should overwrite)
    await service.get_product_quality_report(
        product_ids=[123],
        output_file=output_file,
    )

    # Verify file was overwritten
    assert Path(output_file).exists()
    new_size = Path(output_file).stat().st_size
    assert new_size != original_size  # Size changed

    # Verify new content is correct
    file_data = json.loads(Path(output_file).read_text(encoding="utf-8"))
    assert "summary" in file_data
    assert "test_data" in file_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_metadata_structure() -> None:
    """Verify file export metadata response has correct structure."""
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

    # Call with output_file (using MagicMock to avoid actual file I/O)
    with (
        patch("testio_mcp.services.multi_test_report_service.resolve_output_path") as mock_resolve,
        patch("testio_mcp.services.multi_test_report_service.write_report_to_file") as mock_write,
        patch("testio_mcp.services.multi_test_report_service.get_file_format") as mock_format,
    ):
        mock_path = MagicMock(spec=Path)
        mock_path.__str__ = lambda self: "/tmp/test_report.json"
        mock_resolve.return_value = mock_path
        mock_write.return_value = 1024  # File size in bytes
        mock_format.return_value = "json"

        result = await service.get_product_quality_report(
            product_ids=[123],
            output_file="test_report.json",
        )

        # Verify metadata structure
        assert "file_path" in result
        assert "summary" in result
        assert "record_count" in result
        assert "file_size_bytes" in result
        assert "format" in result

        # Verify metadata values
        assert result["file_path"] == "/tmp/test_report.json"
        assert result["record_count"] == 2
        assert result["file_size_bytes"] == 1024
        assert result["format"] == "json"

        # Verify summary is included (without test_data array)
        assert "total_tests" in result["summary"]
        assert "tests_by_status" in result["summary"]
        assert "total_bugs" in result["summary"]
        assert result["summary"]["total_tests"] == 2

        # Verify test_data is NOT in metadata (only in file)
        assert "test_data" not in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_returns_full_data_when_output_file_none() -> None:
    """Verify service returns full report data when output_file is None."""
    tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "locked",
            "start_at": "2024-01-01T00:00:00+00:00",
            "end_at": "2024-01-02T00:00:00+00:00",
        }
    ]
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=tests,
        bugs_by_test={1: []},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Call without output_file (should return full data)
    result = await service.get_product_quality_report(
        product_ids=[123],
        output_file=None,
    )

    # Verify full report structure returned
    assert "summary" in result
    assert "test_data" in result
    # Note: cache_stats was removed in PQR refactor for token efficiency

    # Verify NOT file metadata structure
    assert "file_path" not in result
    assert "record_count" not in result
    assert "file_size_bytes" not in result
    assert "format" not in result
