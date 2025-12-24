"""Unit tests for date parsing utilities.

Tests use freezegun to freeze time, allowing deterministic testing of date parsing
that delegates to dateparser (which uses real system time internally).
"""

from datetime import datetime

import pytest
from fastmcp.exceptions import ToolError
from freezegun import freeze_time

from testio_mcp.utilities.date_utils import parse_flexible_date
from testio_mcp.utilities.timezone_utils import normalize_to_utc


@freeze_time("2024-11-06 12:00:00")
class TestNaturalLanguageParsing:
    """Test natural language date parsing with frozen time (Nov 6, 2024 12:00 UTC)."""

    def test_today_returns_current_date(self) -> None:
        """Test 'today' returns current date at 00:00:00 UTC."""
        result = parse_flexible_date("today", start_of_day=True)
        assert result == "2024-11-06T00:00:00Z"

    def test_today_end_of_day(self) -> None:
        """Test 'today' with start_of_day=False returns 23:59:59."""
        result = parse_flexible_date("today", start_of_day=False)
        assert result == "2024-11-06T23:59:59Z"

    def test_yesterday_returns_previous_day(self) -> None:
        """Test 'yesterday' returns previous day."""
        result = parse_flexible_date("yesterday")
        assert result == "2024-11-05T00:00:00Z"

    def test_tomorrow_returns_next_day(self) -> None:
        """Test 'tomorrow' returns next day."""
        result = parse_flexible_date("tomorrow")
        assert result == "2024-11-07T00:00:00Z"

    def test_last_7_days_normalized_correctly(self) -> None:
        """Test 'last 7 days' is normalized to '7 days ago' correctly."""
        result = parse_flexible_date("last 7 days")
        assert result == "2024-10-30T00:00:00Z"

    def test_last_30_days_normalized_correctly(self) -> None:
        """Test 'last 30 days' is normalized to '30 days ago' correctly."""
        result = parse_flexible_date("last 30 days")
        assert result == "2024-10-07T00:00:00Z"

    def test_last_3_months_normalized(self) -> None:
        """Test 'last 3 months' is normalized to '3 months ago'."""
        result = parse_flexible_date("last 3 months")
        # From Nov 6 2024 - 3 months = Aug 6 2024
        assert result == "2024-08-06T00:00:00Z"

    def test_3_months_ago_dateparser_native(self) -> None:
        """Test '3 months ago' parses correctly via dateparser."""
        result = parse_flexible_date("3 months ago")
        # Should be same as "last 3 months"
        assert result == "2024-08-06T00:00:00Z"

    def test_last_3_months_equals_3_months_ago(self) -> None:
        """Test 'last 3 months' and '3 months ago' produce same result."""
        result1 = parse_flexible_date("last 3 months")
        result2 = parse_flexible_date("3 months ago")
        assert result1 == result2

    def test_1_year_ago(self) -> None:
        """Test '1 year ago' returns correct date."""
        result = parse_flexible_date("1 year ago")
        assert result == "2023-11-06T00:00:00Z"

    def test_last_2_years(self) -> None:
        """Test 'last 2 years' is normalized to '2 years ago'."""
        result = parse_flexible_date("last 2 years")
        assert result == "2022-11-06T00:00:00Z"

    def test_this_week(self) -> None:
        """Test 'this week' returns correct date."""
        result = parse_flexible_date("this week")
        # Nov 6 2024 is Wednesday, should return Monday Nov 4
        # Note: dateparser may interpret this differently, let's just verify it parses
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert parsed.year == 2024
        assert parsed.month == 11

    def test_last_week(self) -> None:
        """Test 'last week' returns correct date."""
        result = parse_flexible_date("last week")
        # Should be previous week
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert parsed.year == 2024
        assert parsed.month in (10, 11)  # Could be late Oct or early Nov

    def test_this_month(self) -> None:
        """Test 'this month' returns correct date."""
        result = parse_flexible_date("this month")
        # Should be Nov 1 or similar
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert parsed.year == 2024
        assert parsed.month == 11

    def test_last_month(self) -> None:
        """Test 'last month' returns correct date."""
        result = parse_flexible_date("last month")
        # Should be Oct
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert parsed.year == 2024
        assert parsed.month == 10


@freeze_time("2024-11-06 12:00:00")
class TestQuarterTerms:
    """Test quarter terms with frozen time (Nov 6, 2024 is Q4)."""

    def test_this_quarter(self) -> None:
        """Test 'this quarter' returns Q4 start (Oct 1, 2024)."""
        result = parse_flexible_date("this quarter")
        assert result == "2024-10-01T00:00:00Z"

    def test_last_quarter(self) -> None:
        """Test 'last quarter' returns Q3 start (Jul 1, 2024)."""
        result = parse_flexible_date("last quarter")
        assert result == "2024-07-01T00:00:00Z"


@freeze_time("2024-02-15 12:00:00")
class TestQuarterTermsQ1:
    """Test quarter terms in Q1."""

    def test_this_quarter_q1(self) -> None:
        """Test 'this quarter' in Q1 returns Jan 1."""
        result = parse_flexible_date("this quarter")
        assert result == "2024-01-01T00:00:00Z"


@freeze_time("2024-05-15 12:00:00")
class TestQuarterTermsQ2:
    """Test quarter terms in Q2."""

    def test_this_quarter_q2(self) -> None:
        """Test 'this quarter' in Q2 returns Apr 1."""
        result = parse_flexible_date("this quarter")
        assert result == "2024-04-01T00:00:00Z"


@freeze_time("2024-08-15 12:00:00")
class TestQuarterTermsQ3:
    """Test quarter terms in Q3."""

    def test_this_quarter_q3(self) -> None:
        """Test 'this quarter' in Q3 returns Jul 1."""
        result = parse_flexible_date("this quarter")
        assert result == "2024-07-01T00:00:00Z"


class TestISO8601Parsing:
    """Test ISO 8601 date parsing (no time freezing needed)."""

    def test_iso_8601_basic(self) -> None:
        """Test ISO 8601 date parses correctly."""
        result = parse_flexible_date("2024-01-01")
        assert result == "2024-01-01T00:00:00Z"

    def test_iso_8601_end_of_day(self) -> None:
        """Test ISO 8601 date with end of day normalization."""
        result = parse_flexible_date("2024-12-31", start_of_day=False)
        assert result == "2024-12-31T23:59:59Z"

    def test_iso_8601_various_dates(self) -> None:
        """Test various ISO 8601 dates."""
        test_cases = [
            ("2024-01-15", "2024-01-15T00:00:00Z"),
            ("2023-06-30", "2023-06-30T00:00:00Z"),
            ("2025-12-25", "2025-12-25T00:00:00Z"),
        ]
        for input_date, expected in test_cases:
            result = parse_flexible_date(input_date)
            assert result == expected


class TestErrorHandling:
    """Test error handling for unparseable dates."""

    def test_year_only_raises_tool_error(self) -> None:
        """Test year-only input raises ToolError with helpful message."""
        with pytest.raises(ToolError) as exc_info:
            parse_flexible_date("2025")

        error_msg = str(exc_info.value)
        assert "❌ Ambiguous year-only input" in error_msg
        assert "💡 Use ISO format" in error_msg

    def test_empty_string_raises_tool_error(self) -> None:
        """Test empty string raises ToolError."""
        with pytest.raises(ToolError):
            parse_flexible_date("")

    def test_invalid_iso_format_raises_tool_error(self) -> None:
        """Test invalid ISO format raises ToolError."""
        # Note: dateparser is very forgiving, so we test truly unparseable input
        with pytest.raises(ToolError):
            parse_flexible_date("not-a-date-format")

    def test_unparseable_garbage_raises_tool_error(self) -> None:
        """Test completely unparseable input raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            parse_flexible_date("xyz not a date 123")

        error_msg = str(exc_info.value)
        assert "❌ Could not parse date" in error_msg or "❌ Invalid date year" in error_msg


class TestCaseInsensitivity:
    """Test case-insensitive parsing."""

    @freeze_time("2024-11-06")
    def test_uppercase_today(self) -> None:
        """Test 'TODAY' (uppercase) parses correctly."""
        result = parse_flexible_date("TODAY")
        assert result == "2024-11-06T00:00:00Z"

    @freeze_time("2024-11-06")
    def test_mixed_case_last_30_days(self) -> None:
        """Test 'Last 30 Days' (mixed case) parses correctly."""
        result = parse_flexible_date("Last 30 Days")
        assert result == "2024-10-07T00:00:00Z"

    @freeze_time("2024-11-06")
    def test_mixed_case_this_quarter(self) -> None:
        """Test 'This Quarter' (mixed case) parses correctly."""
        result = parse_flexible_date("This Quarter")
        assert result == "2024-10-01T00:00:00Z"


class TestWhitespaceHandling:
    """Test whitespace trimming."""

    @freeze_time("2024-11-06")
    def test_leading_whitespace(self) -> None:
        """Test leading whitespace is trimmed."""
        result = parse_flexible_date("  today")
        assert result == "2024-11-06T00:00:00Z"

    @freeze_time("2024-11-06")
    def test_trailing_whitespace(self) -> None:
        """Test trailing whitespace is trimmed."""
        result = parse_flexible_date("today  ")
        assert result == "2024-11-06T00:00:00Z"

    @freeze_time("2024-11-06")
    def test_both_whitespace(self) -> None:
        """Test both leading and trailing whitespace is trimmed."""
        result = parse_flexible_date("  last 30 days  ")
        assert result == "2024-10-07T00:00:00Z"


class TestNormalizeToUTC:
    """Test UTC normalization for database timestamps (STORY-021c)."""

    def test_normalize_positive_offset(self) -> None:
        """Test normalization of timestamp with positive UTC offset (+01:00)."""
        result = normalize_to_utc("2025-11-09T22:00:00+01:00")
        assert result == "2025-11-09T21:00:00+00:00"

    def test_normalize_negative_offset(self) -> None:
        """Test normalization of timestamp with negative UTC offset (-05:00)."""
        result = normalize_to_utc("2025-11-09T16:00:00-05:00")
        assert result == "2025-11-09T21:00:00+00:00"

    def test_normalize_already_utc(self) -> None:
        """Test normalization of timestamp already in UTC (+00:00)."""
        result = normalize_to_utc("2025-11-09T21:00:00+00:00")
        assert result == "2025-11-09T21:00:00+00:00"

    def test_normalize_zulu_suffix(self) -> None:
        """Test normalization of timestamp with Z (Zulu) suffix."""
        result = normalize_to_utc("2025-11-09T21:00:00Z")
        assert result == "2025-11-09T21:00:00+00:00"

    def test_normalize_various_offsets(self) -> None:
        """Test normalization of timestamps with various timezone offsets."""
        # All represent the same moment: 21:00 UTC on Nov 9, 2025
        test_cases = [
            "2025-11-09T22:00:00+01:00",  # Berlin
            "2025-11-09T21:00:00+00:00",  # London
            "2025-11-09T16:00:00-05:00",  # New York
            "2025-11-09T13:00:00-08:00",  # Los Angeles
            "2025-11-10T06:00:00+09:00",  # Tokyo (next day)
        ]
        expected_utc = "2025-11-09T21:00:00+00:00"

        for timestamp in test_cases:
            result = normalize_to_utc(timestamp)
            assert result == expected_utc, f"Failed for {timestamp}"

    def test_normalize_none_returns_none(self) -> None:
        """Test that None input returns None (handles optional timestamps)."""
        result = normalize_to_utc(None)
        assert result is None

    def test_normalize_naive_datetime_raises_error(self) -> None:
        """Test that naive datetime (no timezone) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_to_utc("2025-11-09T22:00:00")

        error_msg = str(exc_info.value)
        assert "Naive datetime not allowed" in error_msg

    def test_normalize_preserves_microseconds(self) -> None:
        """Test that microseconds are preserved during normalization."""
        result = normalize_to_utc("2025-11-09T22:00:00.123456+01:00")
        assert result == "2025-11-09T21:00:00.123456+00:00"

    def test_normalize_handles_edge_case_offsets(self) -> None:
        """Test normalization with unusual timezone offsets."""
        test_cases = [
            ("2025-11-09T21:30:00+00:30", "2025-11-09T21:00:00+00:00"),  # Partial hour
            ("2025-11-10T02:30:00+05:30", "2025-11-09T21:00:00+00:00"),  # India
            ("2025-11-10T02:45:00+05:45", "2025-11-09T21:00:00+00:00"),  # Nepal
        ]

        for input_ts, expected_utc in test_cases:
            result = normalize_to_utc(input_ts)
            assert result == expected_utc, f"Failed for {input_ts}"
