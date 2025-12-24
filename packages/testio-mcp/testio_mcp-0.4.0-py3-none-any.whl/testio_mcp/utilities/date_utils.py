"""Date parsing utilities for flexible date input handling.

This module provides utilities for parsing various date formats including:
- ISO 8601 dates (YYYY-MM-DD)
- Natural language dates via dateparser (today, yesterday, 3 months ago, last week, etc.)
- Custom patterns not supported by dateparser ("last N days", quarter terms)

Performance characteristics:
- ISO 8601: strptime parsing (~1μs, fast path)
- Custom patterns: regex + date math (~10μs)
- Natural language: dateparser (~100μs, comprehensive fallback)
"""

import re
from datetime import UTC, datetime

import dateparser
from dateutil.relativedelta import relativedelta
from fastmcp.exceptions import ToolError


def parse_flexible_date(date_input: str, start_of_day: bool = True) -> str:
    """Parse flexible date input and return ISO 8601 datetime string with UTC timezone.

    Uses a simplified two-step approach:
    1. Try ISO 8601 format (fast path, ~1μs)
    2. Fall back to dateparser for natural language (~100μs)

    Time-of-day handling:
    - start_of_day=True: Normalizes to 00:00:00 UTC (for start dates)
    - start_of_day=False: Normalizes to 23:59:59 UTC (for end dates)

    Supported formats (via dateparser):
    - ISO 8601: "2024-01-01"
    - Single day: "today", "yesterday", "tomorrow"
    - Day ranges: "last 7 days", "last 30 days", "3 days ago"
    - Week terms: "this week", "last week", "next Friday"
    - Month terms: "this month", "last month", "3 months ago"
    - Quarter terms: "this quarter", "last quarter"
    - Year terms: "this year", "last year", "2 years ago"
    - Complex: "in 2 weeks", "next Tuesday", etc.

    Args:
        date_input: Date string in any supported format
        start_of_day: If True, normalize to 00:00:00 UTC; if False, normalize to 23:59:59 UTC

    Returns:
        ISO 8601 datetime string with UTC timezone (format: YYYY-MM-DDTHH:MM:SSZ)

    Raises:
        ToolError: If date_input cannot be parsed

    Examples:
        >>> parse_flexible_date("2024-01-01")
        '2024-01-01T00:00:00Z'

        >>> parse_flexible_date("today")
        '2024-11-20T00:00:00Z'

        >>> parse_flexible_date("3 months ago")
        '2024-08-20T00:00:00Z'

        >>> parse_flexible_date("last week")
        '2024-11-13T00:00:00Z'
    """
    date_input_stripped = date_input.strip()

    # Reject year-only inputs (e.g., "2025") - ambiguous
    if re.match(r"^\d{4}$", date_input_stripped):
        raise ToolError(
            f"❌ Ambiguous year-only input: '{date_input}'\n"
            f"ℹ️ Year-only dates are not supported (unclear if you mean Jan 1 or entire year)\n"
            f"💡 Use ISO format ('2025-01-01') for specific dates, "
            f"or natural language ('this year', 'last year') for year ranges"
        )

    # Method 1: Try ISO 8601 format first (fast path, ~1μs)
    parsed_date: datetime
    try:
        parsed_date = datetime.strptime(date_input_stripped, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        # Method 2: Normalize "last X {unit}" to "X {unit} ago" (dateparser format)
        date_input_normalized = date_input_stripped
        last_x_match = re.match(
            r"^last\s+(\d+)\s+(days?|weeks?|months?|years?)$", date_input_stripped, re.IGNORECASE
        )
        if last_x_match:
            number = last_x_match.group(1)
            unit = last_x_match.group(2)
            date_input_normalized = f"{number} {unit} ago"

        # Method 3: Handle quarter terms (dateparser doesn't support these)
        date_input_lower = date_input_stripped.lower()

        if date_input_lower in ("this quarter", "last quarter"):
            today = datetime.now(UTC)
            quarter_month = ((today.month - 1) // 3) * 3 + 1  # Q1=1, Q2=4, Q3=7, Q4=10
            quarter_start = today.replace(
                month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )

            if date_input_lower == "this quarter":
                parsed_date = quarter_start
            else:  # last quarter
                parsed_date = quarter_start - relativedelta(months=3)
        else:
            # Method 4: Use dateparser for everything else (comprehensive, ~100μs)
            parsed_date_temp = dateparser.parse(
                date_input_normalized,
                settings={
                    "PREFER_DATES_FROM": "past",  # Prefer past interpretations
                    "TIMEZONE": "UTC",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )

            if parsed_date_temp is None:
                raise ToolError(
                    f"❌ Could not parse date: '{date_input}'\n"
                    f"ℹ️ Supported formats:\n"
                    f"   - ISO 8601: 'YYYY-MM-DD' (e.g., '2024-01-01')\n"
                    f"   - Natural language: 'today', '3 months ago', 'last week', etc.\n"
                    f"   - Day ranges: 'last 7 days', 'last 30 days'\n"
                    f"   - Quarter terms: 'this quarter', 'last quarter'\n"
                    f"💡 Try using a more specific date format or ISO 8601"
                ) from None

            # Ensure UTC timezone
            if parsed_date_temp.tzinfo is None:
                parsed_date = parsed_date_temp.replace(tzinfo=UTC)
            else:
                parsed_date = parsed_date_temp.astimezone(UTC)

    # Validate year is reasonable (1900-2100)
    if parsed_date.year < 1900 or parsed_date.year > 2100:
        raise ToolError(
            f"❌ Invalid date year: {parsed_date.year}\n"
            f"ℹ️ Year must be between 1900 and 2100\n"
            f"💡 Check your date input: '{date_input}'"
        )

    # Normalize time-of-day based on start_of_day parameter
    if start_of_day:
        # Start of day: 00:00:00 UTC
        normalized_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # End of day: 23:59:59 UTC
        normalized_date = parsed_date.replace(hour=23, minute=59, second=59, microsecond=0)

    # Return ISO 8601 datetime string with UTC timezone
    # Format: YYYY-MM-DDTHH:MM:SSZ
    return normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
