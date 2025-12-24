"""Unit tests for GenerateQualityReportInput Pydantic model validation.

PQR Refactor: Updated for multi-product support.
Tests validate date range logic (start_date <= end_date) after parsing flexible formats.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from testio_mcp.tools.product_quality_report_tool import GenerateQualityReportInput


@pytest.mark.unit
class TestGenerateQualityReportInputValidation:
    """Test Pydantic model validation for generate_quality_report input."""

    def test_valid_iso_date_range(self) -> None:
        """Test that valid ISO date range (start < end) passes validation."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            start_date="2025-07-01",
            end_date="2025-10-31",
        )
        assert validated.product_ids == [598]
        assert validated.start_date == "2025-07-01"
        assert validated.end_date == "2025-10-31"

    def test_same_start_and_end_date_allowed(self) -> None:
        """Test that start_date == end_date is allowed (single day report)."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            start_date="2025-07-01",
            end_date="2025-07-01",
        )
        assert validated.start_date == "2025-07-01"
        assert validated.end_date == "2025-07-01"

    def test_start_date_after_end_date_raises_error(self) -> None:
        """Test that start_date > end_date raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                start_date="2025-10-01",  # October
                end_date="2025-07-01",  # July (before start!)
            )

        error_msg = str(exc_info.value)
        assert "start_date is after end_date" in error_msg
        assert "2025-10-01" in error_msg
        assert "2025-07-01" in error_msg

    @patch("testio_mcp.utilities.date_utils.datetime")
    def test_business_terms_validated_after_parsing(self, mock_datetime: object) -> None:
        """Test that business terms are validated after parsing to dates."""
        mock_datetime.now.return_value = datetime(2025, 11, 19, tzinfo=UTC)
        mock_datetime.strptime = datetime.strptime
        mock_datetime.fromisoformat = datetime.fromisoformat

        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                start_date="tomorrow",  # Nov 20
                end_date="yesterday",  # Nov 18 (before start!)
            )

        error_msg = str(exc_info.value)
        assert "start_date is after end_date" in error_msg

    def test_only_start_date_allowed(self) -> None:
        """Test that providing only start_date (no end_date) is allowed."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            start_date="2025-07-01",
            end_date=None,
        )
        assert validated.start_date == "2025-07-01"
        assert validated.end_date is None

    def test_only_end_date_allowed(self) -> None:
        """Test that providing only end_date (no start_date) is allowed."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            start_date=None,
            end_date="2025-10-31",
        )
        assert validated.start_date is None
        assert validated.end_date == "2025-10-31"

    def test_no_dates_allowed(self) -> None:
        """Test that omitting both dates is allowed (all-time report)."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            start_date=None,
            end_date=None,
        )
        assert validated.start_date is None
        assert validated.end_date is None

    def test_invalid_date_format_raises_error(self) -> None:
        """Test that invalid date format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                start_date="not-a-date",
                end_date="2025-10-31",
            )

        error_msg = str(exc_info.value)
        assert "Could not parse date" in error_msg or "not-a-date" in error_msg

    def test_year_only_input_raises_error(self) -> None:
        """Test that year-only input (e.g., '2025') is rejected with clear error."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                start_date="2025",  # Year-only (ambiguous)
                end_date="2025-10-31",
            )

        error_msg = str(exc_info.value)
        assert "ambiguous" in error_msg.lower() or "year-only" in error_msg.lower()
        assert "2025" in error_msg

    def test_year_only_end_date_raises_error(self) -> None:
        """Test that year-only input in end_date is also rejected."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                start_date="2025-07-01",
                end_date="2025",  # Year-only (ambiguous)
            )

        error_msg = str(exc_info.value)
        assert "ambiguous" in error_msg.lower() or "year-only" in error_msg.lower()
        assert "2025" in error_msg

    def test_product_ids_accepts_single_int(self) -> None:
        """Test that product_ids accepts single int and normalizes to list."""
        validated = GenerateQualityReportInput(product_ids=598)
        assert validated.product_ids == [598]

    def test_product_ids_accepts_list(self) -> None:
        """Test that product_ids accepts list of ints."""
        validated = GenerateQualityReportInput(product_ids=[598, 599])
        assert validated.product_ids == [598, 599]

    def test_product_ids_dedupes(self) -> None:
        """Test that duplicate product_ids are removed while preserving order."""
        validated = GenerateQualityReportInput(product_ids=[598, 599, 598])
        assert validated.product_ids == [598, 599]

    def test_product_ids_empty_list_raises_error(self) -> None:
        """Test that empty product_ids list raises ValidationError."""
        with pytest.raises(ValidationError):
            GenerateQualityReportInput(product_ids=[])

    def test_test_ids_accepts_list(self) -> None:
        """Test that test_ids accepts list of ints."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            test_ids=[123, 456],
        )
        assert validated.test_ids == [123, 456]

    def test_test_ids_dedupes(self) -> None:
        """Test that duplicate test_ids are removed while preserving order."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            test_ids=[123, 456, 123],
        )
        assert validated.test_ids == [123, 456]

    def test_test_ids_empty_list_raises_error(self) -> None:
        """Test that empty test_ids list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateQualityReportInput(
                product_ids=[598],
                test_ids=[],
            )

        error_msg = str(exc_info.value)
        assert "Empty test_ids" in error_msg

    def test_test_ids_none_allowed(self) -> None:
        """Test that test_ids=None is allowed (all tests)."""
        validated = GenerateQualityReportInput(
            product_ids=[598],
            test_ids=None,
        )
        assert validated.test_ids is None

    def test_all_parameters_optional_except_product_ids(self) -> None:
        """Test that only product_ids is required."""
        validated = GenerateQualityReportInput(product_ids=[598])
        assert validated.product_ids == [598]
        assert validated.test_ids is None
        assert validated.start_date is None
        assert validated.end_date is None
        assert validated.statuses is None
        assert validated.output_file is None
