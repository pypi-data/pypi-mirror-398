"""Unit tests for file export utilities (STORY-025).

Tests verify path resolution, file writing, and security constraints.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from testio_mcp.utilities.file_export import (
    get_file_format,
    resolve_output_path,
    write_report_to_file,
)


@pytest.mark.unit
def test_resolve_output_path_absolute_path(tmp_path: Path) -> None:
    """Verify absolute paths are used as-is (after expanding ~)."""
    absolute_path = str(tmp_path / "report.json")

    resolved = resolve_output_path(absolute_path)

    assert resolved == Path(absolute_path).resolve()
    assert resolved.is_absolute()


@pytest.mark.unit
def test_resolve_output_path_relative_path(tmp_path: Path) -> None:
    """Verify relative paths resolve to ~/.testio-mcp/reports/."""
    relative_path = "report.json"

    with patch("testio_mcp.utilities.file_export.Path.home", return_value=tmp_path):
        resolved = resolve_output_path(relative_path)

        expected = tmp_path / ".testio-mcp" / "reports" / relative_path
        assert resolved == expected.resolve()
        assert resolved.is_absolute()


@pytest.mark.unit
def test_resolve_output_path_nested_relative_path(tmp_path: Path) -> None:
    """Verify nested relative paths create subdirectories."""
    relative_path = "q3-2025/report.json"

    with patch("testio_mcp.utilities.file_export.Path.home", return_value=tmp_path):
        resolved = resolve_output_path(relative_path)

        expected = tmp_path / ".testio-mcp" / "reports" / "q3-2025" / "report.json"
        assert resolved == expected.resolve()

        # Verify parent directory was created
        assert resolved.parent.exists()


@pytest.mark.unit
def test_resolve_output_path_expands_tilde(tmp_path: Path) -> None:
    """Verify ~ is expanded to home directory."""
    # Mock os.path.expanduser which Path.expanduser() uses internally

    tilde_path = "~/custom_reports/report.json"

    def mock_expanduser(path: str) -> str:
        if path.startswith("~"):
            return str(tmp_path / path[2:])  # Remove ~/
        return path

    with patch("os.path.expanduser", side_effect=mock_expanduser):
        resolved = resolve_output_path(tilde_path)

        expected = tmp_path / "custom_reports" / "report.json"
        assert resolved == expected.resolve()


@pytest.mark.unit
def test_resolve_output_path_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify path traversal attempts are rejected."""
    traversal_path = "../../../etc/passwd"

    with patch("testio_mcp.utilities.file_export.Path.home", return_value=tmp_path):
        with pytest.raises(ValueError, match="Path traversal"):
            resolve_output_path(traversal_path)


@pytest.mark.unit
def test_resolve_output_path_rejects_unsupported_extension(tmp_path: Path) -> None:
    """Verify unsupported file extensions are rejected."""
    invalid_path = str(tmp_path / "report.csv")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        resolve_output_path(invalid_path)


@pytest.mark.unit
def test_resolve_output_path_accepts_json_extension(tmp_path: Path) -> None:
    """Verify .json extension is accepted."""
    json_path = str(tmp_path / "report.json")

    resolved = resolve_output_path(json_path)

    assert resolved.suffix.lower() == ".json"


@pytest.mark.unit
def test_resolve_output_path_creates_parent_directories(tmp_path: Path) -> None:
    """Verify parent directories are created automatically."""
    nested_path = str(tmp_path / "reports" / "q3-2025" / "report.json")

    # Parent directories don't exist
    assert not Path(tmp_path / "reports").exists()

    resolved = resolve_output_path(nested_path)

    # Parent directories were created
    assert resolved.parent.exists()
    assert resolved.parent.is_dir()


@pytest.mark.unit
def test_write_report_to_file_writes_json(tmp_path: Path) -> None:
    """Verify report data is written as formatted JSON."""
    output_path = tmp_path / "report.json"
    report_data = {
        "summary": {"total_tests": 2, "total_bugs": 5},
        "by_test": [{"test_id": 1}, {"test_id": 2}],
        "cache_stats": {"cache_hits": 2},
    }

    bytes_written = write_report_to_file(report_data, output_path)

    # Verify file exists
    assert output_path.exists()

    # Verify file contents
    file_content = output_path.read_text(encoding="utf-8")
    file_data = json.loads(file_content)

    assert file_data == report_data

    # Verify bytes written
    assert bytes_written > 0
    assert bytes_written == len(file_content.encode("utf-8"))


@pytest.mark.unit
def test_write_report_to_file_formats_json_with_indent(tmp_path: Path) -> None:
    """Verify JSON is formatted with indentation for readability."""
    output_path = tmp_path / "report.json"
    report_data = {"summary": {"total_tests": 1}}

    write_report_to_file(report_data, output_path)

    file_content = output_path.read_text(encoding="utf-8")

    # Verify JSON is formatted (contains newlines from indentation)
    assert "\n" in file_content

    # Verify JSON is valid
    parsed = json.loads(file_content)
    assert parsed == report_data


@pytest.mark.unit
def test_write_report_to_file_rejects_non_json_extension(tmp_path: Path) -> None:
    """Verify non-JSON extensions are rejected."""
    output_path = tmp_path / "report.csv"

    with pytest.raises(ValueError, match="must have .json extension"):
        write_report_to_file({"data": "test"}, output_path)


@pytest.mark.unit
def test_write_report_to_file_handles_unicode(tmp_path: Path) -> None:
    """Verify Unicode characters are handled correctly."""
    output_path = tmp_path / "report.json"
    report_data = {"title": "Test with émojis 🐛 and 中文"}

    write_report_to_file(report_data, output_path)

    # Verify file can be read back
    file_content = output_path.read_text(encoding="utf-8")
    file_data = json.loads(file_content)

    assert file_data["title"] == "Test with émojis 🐛 and 中文"


@pytest.mark.unit
def test_get_file_format_returns_json_for_json_extension() -> None:
    """Verify get_file_format returns 'json' for .json extension."""
    path = Path("report.json")

    format_type = get_file_format(path)

    assert format_type == "json"


@pytest.mark.unit
def test_get_file_format_case_insensitive() -> None:
    """Verify file format detection is case-insensitive."""
    path_upper = Path("REPORT.JSON")
    path_lower = Path("report.json")

    assert get_file_format(path_upper) == "json"
    assert get_file_format(path_lower) == "json"


@pytest.mark.unit
def test_get_file_format_rejects_unsupported_extension() -> None:
    """Verify unsupported extensions are rejected."""
    path = Path("report.csv")

    with pytest.raises(ValueError, match="Unsupported file format"):
        get_file_format(path)
