"""Utility functions for TestIO MCP server.

Commonly used utilities exposed at package level for convenience.
"""

# Existing utilities
from testio_mcp.utilities.bug_classifiers import calculate_acceptance_rates, classify_bugs
from testio_mcp.utilities.date_utils import parse_flexible_date
from testio_mcp.utilities.file_export import (
    get_file_format,
    resolve_output_path,
    write_report_to_file,
)
from testio_mcp.utilities.parsing import (
    parse_int_list_input,
    parse_list_input,
    parse_rejection_reason_input,
    parse_severity_input,
    parse_status_input,
)

# NEW: Moved from root (STORY-028)
from testio_mcp.utilities.progress import (
    BatchProgressCallback,
    ProgressReporter,
    safe_batch_callback,
)
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.utilities.service_helpers import (
    get_service_context,
    get_service_context_from_server_context,
)
from testio_mcp.utilities.timezone_utils import normalize_to_utc

__all__ = [
    # Existing
    "BatchProgressCallback",
    "calculate_acceptance_rates",
    "classify_bugs",
    "get_file_format",
    "get_service_context",
    "get_service_context_from_server_context",
    "parse_flexible_date",
    "parse_int_list_input",
    "parse_list_input",
    "parse_rejection_reason_input",
    "parse_severity_input",
    "parse_status_input",
    "ProgressReporter",
    "resolve_output_path",
    "safe_batch_callback",
    "write_report_to_file",
    # NEW: Moved from root
    "inline_schema_refs",
    "normalize_to_utc",
]
