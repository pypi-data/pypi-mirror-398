"""Unit tests for bug summary aggregation with known bugs support (STORY-072).

Tests the _aggregate_bug_summary method's handling of known_bugs_count
and known field in recent_bugs.
"""

from unittest.mock import MagicMock

import pytest

from testio_mcp.services.test_service import TestService


@pytest.mark.unit
class TestBugSummaryKnownBugs:
    """Tests for known bugs support in bug summary aggregation."""

    def test_counts_known_bugs(self) -> None:
        """Verify known_bugs_count is calculated correctly."""
        # Create service with mocked dependencies
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        bugs = [
            {
                "id": 1,
                "title": "Bug 1",
                "severity": "high",
                "status": "accepted",
                "auto_accepted": False,
                "known": True,
                "created_at": "2025-01-01T00:00:00Z",
                "devices": [],
            },
            {
                "id": 2,
                "title": "Bug 2",
                "severity": "low",
                "status": "open",
                "known": False,
                "created_at": "2025-01-02T00:00:00Z",
                "devices": [],
            },
            {
                "id": 3,
                "title": "Bug 3",
                "severity": "critical",
                "status": "rejected",
                "known": True,
                "created_at": "2025-01-03T00:00:00Z",
                "devices": [],
            },
        ]

        summary = service._aggregate_bug_summary(bugs)

        assert summary["total_count"] == 3
        assert summary["known_bugs_count"] == 2

    def test_known_bugs_count_defaults_to_zero(self) -> None:
        """Verify known_bugs_count is 0 when no bugs are known."""
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        bugs = [
            {
                "id": 1,
                "title": "Bug 1",
                "severity": "high",
                "status": "accepted",
                "auto_accepted": False,
                "known": False,
                "created_at": "2025-01-01T00:00:00Z",
                "devices": [],
            },
            {
                "id": 2,
                "title": "Bug 2",
                "severity": "low",
                "status": "open",
                "created_at": "2025-01-02T00:00:00Z",
                "devices": [],
            },
        ]

        summary = service._aggregate_bug_summary(bugs)

        assert summary["total_count"] == 2
        assert summary["known_bugs_count"] == 0

    def test_handles_missing_known_field(self) -> None:
        """Verify known field defaults to False when missing."""
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        bugs = [
            {
                "id": 1,
                "title": "Bug without known field",
                "severity": "high",
                "status": "accepted",
                "auto_accepted": False,
                "created_at": "2025-01-01T00:00:00Z",
                "devices": [],
            }
        ]

        summary = service._aggregate_bug_summary(bugs)

        assert summary["known_bugs_count"] == 0

    def test_recent_bugs_include_known_field(self) -> None:
        """Verify recent_bugs include known field."""
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        bugs = [
            {
                "id": 1,
                "title": "Known bug",
                "severity": "high",
                "status": "accepted",
                "auto_accepted": False,
                "known": True,
                "created_at": "2025-01-03T00:00:00Z",
                "devices": [],
            },
            {
                "id": 2,
                "title": "New bug",
                "severity": "low",
                "status": "open",
                "known": False,
                "created_at": "2025-01-02T00:00:00Z",
                "devices": [],
            },
            {
                "id": 3,
                "title": "Another bug",
                "severity": "critical",
                "status": "rejected",
                "created_at": "2025-01-01T00:00:00Z",
                "devices": [],
            },
        ]

        summary = service._aggregate_bug_summary(bugs)

        assert len(summary["recent_bugs"]) == 3
        # Most recent first (sorted by created_at descending)
        assert summary["recent_bugs"][0]["id"] == "1"
        assert summary["recent_bugs"][0]["known"] is True
        assert summary["recent_bugs"][1]["id"] == "2"
        assert summary["recent_bugs"][1]["known"] is False
        assert summary["recent_bugs"][2]["id"] == "3"
        assert summary["recent_bugs"][2]["known"] is False  # Missing field defaults to False

    def test_empty_bugs_list(self) -> None:
        """Verify known_bugs_count is 0 for empty bug list."""
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        summary = service._aggregate_bug_summary([])

        assert summary["total_count"] == 0
        assert summary["known_bugs_count"] == 0
        assert summary["recent_bugs"] == []

    def test_all_bugs_known(self) -> None:
        """Verify known_bugs_count equals total_count when all bugs are known."""
        service = TestService(
            client=MagicMock(),
            test_repo=MagicMock(),
            bug_repo=MagicMock(),
            product_repo=MagicMock(),
        )

        bugs = [
            {
                "id": i,
                "title": f"Known bug {i}",
                "severity": "high",
                "status": "accepted",
                "auto_accepted": False,
                "known": True,
                "created_at": f"2025-01-0{i}T00:00:00Z",
                "devices": [],
            }
            for i in range(1, 6)
        ]

        summary = service._aggregate_bug_summary(bugs)

        assert summary["total_count"] == 5
        assert summary["known_bugs_count"] == 5
        assert all(bug["known"] is True for bug in summary["recent_bugs"])
