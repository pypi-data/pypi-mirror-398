"""Unit tests for bug transformers."""

from datetime import UTC, datetime

from testio_mcp.transformers.bug_transformers import transform_api_bug_to_orm


class TestBugTransformers:
    """Tests for bug transformation logic."""

    def test_transform_rejected_bug_with_reason(self):
        """Test parsing rejection reason from comments."""
        api_bug = {
            "id": 1,
            "title": "Bug 1",
            "status": "rejected",
            "comments": [
                {"body": "Some random comment"},
                {"body": "The behaviour/design described here is intentional."},
            ],
        }

        result = transform_api_bug_to_orm(api_bug)
        assert result["rejection_reason"] == "intended_behavior"
        assert result["status"] == "rejected"

    def test_transform_rejected_bug_request_timeout(self):
        """Test parsing request_timeout rejection reason."""
        api_bug = {
            "id": 2,
            "title": "Bug 2",
            "status": "rejected",
            "comments": [
                {
                    "body": (
                        "Your bug was rejected automatically, because you "
                        "didn't respond to the request within 24 hours"
                    )
                }
            ],
        }

        result = transform_api_bug_to_orm(api_bug)
        assert result["rejection_reason"] == "request_timeout"

    def test_transform_rejected_bug_no_match(self):
        """Test rejected bug with comments but no known reason."""
        api_bug = {
            "id": 3,
            "title": "Bug 3",
            "status": "rejected",
            "comments": [{"body": "Just a random comment"}],
        }

        result = transform_api_bug_to_orm(api_bug)
        assert result["rejection_reason"] is None

    def test_transform_accepted_bug(self):
        """Test accepted bug (should not parse rejection reason)."""
        api_bug = {
            "id": 4,
            "title": "Bug 4",
            "status": "accepted",
            "comments": [{"body": "The behaviour/design described here is intentional."}],
        }

        result = transform_api_bug_to_orm(api_bug)
        assert result["rejection_reason"] is None

    def test_transform_result_fields_cleaning(self):
        """Test cleaning of actual/expected result fields."""
        api_bug = {
            "id": 5,
            "actual_result": "  Bad result  ",
            "expected_result": "",  # Should become None
            "steps": ["Step 1", "Step 2"],
        }

        result = transform_api_bug_to_orm(api_bug)
        assert result["actual_result"] == "Bad result"
        assert result["expected_result"] is None
        assert result["steps"] == "Step 1\nStep 2"

    def test_transform_reported_at(self):
        """Test parsing of reported_at timestamp."""
        api_bug = {"id": 6, "reported_at": "2023-01-01T12:00:00+00:00"}

        result = transform_api_bug_to_orm(api_bug)
        assert result["reported_at"] == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
