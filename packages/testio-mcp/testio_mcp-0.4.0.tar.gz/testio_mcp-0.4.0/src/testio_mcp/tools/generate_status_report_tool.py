"""MCP tool for generating status reports from multiple tests.

STORY-023d: TEMPORARILY DISABLED - ReportService deleted.
STORY-023e: Will be reimplemented with MultiTestReportService.

This module will implement the generate_status_report tool following the service
layer pattern (ADR-006). The tool will be a thin wrapper that:
1. Validates input with Pydantic/Literal types
2. Extracts dependencies from server context (ADR-007)
3. Delegates to MultiTestReportService (STORY-023e)
4. Converts exceptions to user-friendly error format
"""

# TODO(STORY-023e): Reimplement with MultiTestReportService
# This tool has been temporarily disabled because ReportService was deleted in STORY-023d.
# It will be reimplemented in STORY-023e using the new MultiTestReportService.
