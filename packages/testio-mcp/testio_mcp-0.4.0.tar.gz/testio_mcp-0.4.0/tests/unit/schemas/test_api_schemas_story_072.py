"""Unit tests for API schema changes in STORY-072.

Tests validation and serialization for test_environment and known fields.
"""

import pytest
from pydantic import ValidationError

from testio_mcp.schemas.api.bugs import BugSummary, RecentBug
from testio_mcp.schemas.api.tests import TestDetails, TestSummary


@pytest.mark.unit
class TestTestSummarySchema:
    """Tests for TestSummary schema with test_environment field."""

    def test_serializes_with_test_environment(self) -> None:
        """Verify TestSummary serializes test_environment field."""
        summary = TestSummary(
            test_id=123,
            title="Login test",
            status="running",
            testing_type="rapid",
            test_environment={"os": "Windows 11", "browser": "Chrome"},
        )

        assert summary.test_id == 123
        assert summary.test_environment == {"os": "Windows 11", "browser": "Chrome"}

    def test_test_environment_defaults_to_none(self) -> None:
        """Verify test_environment is optional."""
        summary = TestSummary(
            test_id=456,
            title="Test without environment",
            status="locked",
            testing_type="focused",
        )

        assert summary.test_environment is None

    def test_serializes_to_dict_with_test_environment(self) -> None:
        """Verify model_dump includes test_environment."""
        summary = TestSummary(
            test_id=789,
            title="Test",
            status="running",
            testing_type="rapid",
            test_environment={"platform": "iOS"},
        )

        data = summary.model_dump()

        assert "test_environment" in data
        assert data["test_environment"] == {"platform": "iOS"}


@pytest.mark.unit
class TestTestDetailsSchema:
    """Tests for TestDetails schema with test_environment field."""

    def test_serializes_with_test_environment(self) -> None:
        """Verify TestDetails serializes test_environment field."""
        from testio_mcp.schemas.api.products import ProductInfo

        details = TestDetails(
            id=123,
            title="Login test",
            status="running",
            testing_type="rapid",
            test_environment={"os": "macOS", "browser": "Safari"},
            product=ProductInfo(id=1, name="Test Product", type="web"),
        )

        assert details.test_environment == {"os": "macOS", "browser": "Safari"}

    def test_test_environment_defaults_to_none(self) -> None:
        """Verify test_environment is optional in TestDetails."""
        from testio_mcp.schemas.api.products import ProductInfo

        details = TestDetails(
            id=456,
            title="Test",
            status="locked",
            testing_type="focused",
            product=ProductInfo(id=1, name="Product", type="web"),
        )

        assert details.test_environment is None


@pytest.mark.unit
class TestBugSummarySchema:
    """Tests for BugSummary schema with known_bugs_count field."""

    def test_serializes_with_known_bugs_count(self) -> None:
        """Verify BugSummary serializes known_bugs_count field."""
        summary = BugSummary(
            total_count=10,
            known_bugs_count=3,
            by_severity={"high": 5, "low": 5},
            by_status={"active_accepted": 8, "rejected": 2, "open": 0},
            by_platform={
                "operating_systems": {},
                "browsers": {},
                "device_categories": {},
            },
            acceptance_rates={
                "active_acceptance_rate": 0.8,
                "auto_acceptance_rate": None,
                "overall_acceptance_rate": 0.8,
                "rejection_rate": 0.2,
                "review_rate": 1.0,
                "open_count": 0,
                "has_alert": False,
            },
        )

        assert summary.total_count == 10
        assert summary.known_bugs_count == 3

    def test_known_bugs_count_defaults_to_zero(self) -> None:
        """Verify known_bugs_count defaults to 0."""
        summary = BugSummary(
            total_count=5,
            by_severity={"high": 3, "low": 2},
            by_status={"active_accepted": 5, "rejected": 0, "open": 0},
            by_platform={
                "operating_systems": {},
                "browsers": {},
                "device_categories": {},
            },
            acceptance_rates={
                "active_acceptance_rate": 1.0,
                "auto_acceptance_rate": None,
                "overall_acceptance_rate": 1.0,
                "rejection_rate": 0.0,
                "review_rate": 1.0,
                "open_count": 0,
                "has_alert": False,
            },
        )

        assert summary.known_bugs_count == 0

    def test_rejects_negative_known_bugs_count(self) -> None:
        """Verify known_bugs_count must be non-negative."""
        with pytest.raises(ValidationError) as exc_info:
            BugSummary(
                total_count=10,
                known_bugs_count=-1,
                by_severity={},
                by_status={},
                by_platform={},
                acceptance_rates={
                    "active_acceptance_rate": None,
                    "auto_acceptance_rate": None,
                    "overall_acceptance_rate": None,
                    "rejection_rate": None,
                    "review_rate": None,
                    "open_count": 0,
                    "has_alert": False,
                },
            )

        assert "known_bugs_count" in str(exc_info.value).lower()

    def test_serializes_to_dict_with_known_bugs_count(self) -> None:
        """Verify model_dump includes known_bugs_count."""
        summary = BugSummary(
            total_count=10,
            known_bugs_count=2,
            by_severity={},
            by_status={},
            by_platform={},
            acceptance_rates={
                "active_acceptance_rate": None,
                "auto_acceptance_rate": None,
                "overall_acceptance_rate": None,
                "rejection_rate": None,
                "review_rate": None,
                "open_count": 0,
                "has_alert": False,
            },
        )

        data = summary.model_dump()

        assert "known_bugs_count" in data
        assert data["known_bugs_count"] == 2


@pytest.mark.unit
class TestRecentBugSchema:
    """Tests for RecentBug schema with known field."""

    def test_serializes_with_known_field(self) -> None:
        """Verify RecentBug serializes known field."""
        bug = RecentBug(
            id="123",
            title="Known issue",
            severity="high",
            status="accepted",
            known=True,
        )

        assert bug.known is True

    def test_known_defaults_to_false(self) -> None:
        """Verify known field defaults to False."""
        bug = RecentBug(
            id="456",
            title="New bug",
            severity="low",
            status="open",
        )

        assert bug.known is False

    def test_serializes_to_dict_with_known(self) -> None:
        """Verify model_dump includes known field."""
        bug = RecentBug(
            id="789",
            title="Bug",
            severity="critical",
            status="rejected",
            known=True,
        )

        data = bug.model_dump()

        assert "known" in data
        assert data["known"] is True

    def test_accepts_both_boolean_values(self) -> None:
        """Verify known field accepts True and False."""
        bug_true = RecentBug(
            id="1",
            title="Known",
            severity="high",
            status="accepted",
            known=True,
        )
        bug_false = RecentBug(
            id="2",
            title="New",
            severity="low",
            status="open",
            known=False,
        )

        assert bug_true.known is True
        assert bug_false.known is False
