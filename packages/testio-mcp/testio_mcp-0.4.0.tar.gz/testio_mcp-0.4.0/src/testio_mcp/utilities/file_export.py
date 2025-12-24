"""File export utilities for EBR report generation.

This module provides path resolution and file writing utilities for exporting
large EBR reports to files instead of JSON responses (STORY-025).
"""

import json
import logging
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Supported file formats (MVP: JSON only)
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".json",)
SUPPORTED_FORMATS: tuple[Literal["json"], ...] = ("json",)


def resolve_output_path(output_file: str) -> Path:
    """Resolve output file path with safety checks.

    Path resolution rules:
    - Absolute paths: Used as-is (after expanding ~)
    - Relative paths: Relative to ~/.testio-mcp/reports/
    - Creates parent directories if needed
    - Validates extension (.json for MVP)

    Args:
        output_file: File path (absolute or relative)

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path is invalid, extension unsupported, or path traversal detected

    Examples:
        >>> # Absolute path - used as-is
        >>> resolve_output_path("/tmp/reports/canva-q3-2025.json")
        Path("/tmp/reports/canva-q3-2025.json")

        >>> # Relative path - relative to ~/.testio-mcp/reports/
        >>> resolve_output_path("canva-q3-2025.json")
        Path("/Users/username/.testio-mcp/reports/canva-q3-2025.json")

        >>> # Subdirectory (created if needed)
        >>> resolve_output_path("q3-2025/canva.json")
        Path("/Users/username/.testio-mcp/reports/q3-2025/canva.json")

        >>> # Path traversal (rejected)
        >>> resolve_output_path("../../../etc/passwd")
        ValueError: Path traversal not allowed
    """
    # Expand user home directory (~)
    expanded_path = Path(output_file).expanduser()

    # Determine if path is absolute or relative
    if expanded_path.is_absolute():
        # Absolute path: use as-is
        resolved_path = expanded_path
    else:
        # Relative path: resolve relative to ~/.testio-mcp/reports/
        reports_dir = Path.home() / ".testio-mcp" / "reports"
        resolved_path = reports_dir / expanded_path

    # Resolve any remaining relative components (e.g., ./file.json -> file.json)
    resolved_path = resolved_path.resolve()

    # Security: Prevent path traversal for relative paths
    # Check if resolved path is still within reports directory
    if not expanded_path.is_absolute():
        reports_dir_resolved = Path.home() / ".testio-mcp" / "reports"
        reports_dir_resolved = reports_dir_resolved.resolve()

        try:
            # This raises ValueError if path is outside reports directory
            resolved_path.relative_to(reports_dir_resolved)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: '{output_file}' resolves to '{resolved_path}' "
                f"which is outside allowed directory '{reports_dir_resolved}'"
            ) from None

    # Validate file extension
    file_extension = resolved_path.suffix.lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension: '{file_extension}'. "
            f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Create parent directories if needed
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    return resolved_path


def write_report_to_file(report_data: dict[str, Any], output_path: Path) -> int:
    """Write EBR report data to JSON file.

    Args:
        report_data: Full report dictionary (summary, by_test, cache_stats)
        output_path: Path to output file (must have .json extension)

    Returns:
        Number of bytes written

    Raises:
        PermissionError: If file cannot be written (permissions)
        OSError: If disk is full or other I/O error occurs
        ValueError: If output_path doesn't have .json extension

    Example:
        >>> report = {"summary": {...}, "by_test": [...], "cache_stats": {...}}
        >>> path = Path("/tmp/report.json")
        >>> bytes_written = write_report_to_file(report, path)
        >>> print(f"Wrote {bytes_written} bytes")
    """
    # Validate extension
    if output_path.suffix.lower() != ".json":
        raise ValueError(f"File must have .json extension, got: {output_path.suffix}")

    # Write formatted JSON (indent=2 for readability, ensure_ascii=False for Unicode)
    json_content = json.dumps(report_data, indent=2, ensure_ascii=False)
    bytes_written = output_path.write_text(json_content, encoding="utf-8")

    logger.info(f"Wrote EBR report to {output_path} ({bytes_written} bytes)")

    return bytes_written


def get_file_format(output_path: Path) -> Literal["json"]:
    """Get file format from path extension.

    Args:
        output_path: Path to file

    Returns:
        File format string ("json" for MVP)

    Raises:
        ValueError: If extension is not supported
    """
    extension = output_path.suffix.lower()
    if extension == ".json":
        return "json"
    raise ValueError(f"Unsupported file format: {extension}")
