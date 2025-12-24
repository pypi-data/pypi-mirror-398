"""Unit tests for Data Transfer Objects (DTOs).

Tests validation and type safety for service layer DTOs.
"""

import pytest
from pydantic import ValidationError

from testio_mcp.schemas.dtos import ServiceBugDTO, ServiceTestDTO


@pytest.mark.unit
class TestServiceTestDTO:
    """Tests for ServiceTestDTO validation."""

    def test_validates_with_all_fields(self) -> None:
        """Verify DTO accepts all fields including test_environment."""
        dto = ServiceTestDTO(
            id=123,
            title="Login test",
            goal="Verify login flow",
            status="running",
            review_status="review_successful",
            testing_type="rapid",
            duration=30,
            starts_at="2025-01-01T00:00:00+00:00",
            ends_at="2025-01-01T00:30:00+00:00",
            test_environment={"os": "Windows 11", "browser": "Chrome"},
        )

        assert dto.id == 123
        assert dto.title == "Login test"
        assert dto.test_environment == {"os": "Windows 11", "browser": "Chrome"}

    def test_validates_with_minimal_fields(self) -> None:
        """Verify DTO accepts minimal required fields."""
        dto = ServiceTestDTO(
            id=456,
            title="Minimal test",
            status="locked",
            testing_type="focused",
        )

        assert dto.id == 456
        assert dto.title == "Minimal test"
        assert dto.goal is None
        assert dto.test_environment is None

    def test_test_environment_defaults_to_none(self) -> None:
        """Verify test_environment is optional and defaults to None."""
        dto = ServiceTestDTO(
            id=789,
            title="Test without environment",
            status="running",
            testing_type="coverage",
        )

        assert dto.test_environment is None

    def test_test_environment_accepts_dict(self) -> None:
        """Verify test_environment accepts arbitrary dict structure."""
        env = {
            "platforms": ["iOS", "Android"],
            "browsers": ["Safari", "Chrome"],
            "versions": {"min": "14.0", "max": "17.0"},
        }
        dto = ServiceTestDTO(
            id=999,
            title="Multi-platform test",
            status="running",
            testing_type="usability",
            test_environment=env,
        )

        assert dto.test_environment == env
        assert dto.test_environment["platforms"] == ["iOS", "Android"]

    def test_rejects_invalid_id_type(self) -> None:
        """Verify DTO rejects non-integer id."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceTestDTO(
                id="not-an-integer",  # type: ignore[arg-type]
                title="Test",
                status="running",
                testing_type="rapid",
            )

        assert "id" in str(exc_info.value).lower()

    def test_requires_mandatory_fields(self) -> None:
        """Verify DTO enforces required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceTestDTO(id=123)  # type: ignore[call-arg]

        error_msg = str(exc_info.value).lower()
        assert "title" in error_msg or "field required" in error_msg


@pytest.mark.unit
class TestServiceBugDTO:
    """Tests for ServiceBugDTO validation."""

    def test_validates_with_all_fields(self) -> None:
        """Verify DTO accepts all fields including known."""
        dto = ServiceBugDTO(
            id=1,
            title="Login fails on Chrome",
            severity="high",
            status="accepted",
            known=True,
        )

        assert dto.id == 1
        assert dto.title == "Login fails on Chrome"
        assert dto.severity == "high"
        assert dto.status == "accepted"
        assert dto.known is True

    def test_known_defaults_to_false(self) -> None:
        """Verify known field defaults to False."""
        dto = ServiceBugDTO(
            id=2,
            title="Bug without known flag",
            severity="low",
            status="open",
        )

        assert dto.known is False

    def test_known_accepts_boolean(self) -> None:
        """Verify known field accepts boolean values."""
        dto_true = ServiceBugDTO(
            id=3,
            title="Known issue",
            severity="critical",
            status="accepted",
            known=True,
        )
        dto_false = ServiceBugDTO(
            id=4,
            title="New issue",
            severity="high",
            status="open",
            known=False,
        )

        assert dto_true.known is True
        assert dto_false.known is False

    def test_rejects_invalid_id_type(self) -> None:
        """Verify DTO rejects non-integer id."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceBugDTO(
                id="not-an-integer",  # type: ignore[arg-type]
                title="Bug",
                severity="high",
                status="open",
            )

        assert "id" in str(exc_info.value).lower()

    def test_requires_mandatory_fields(self) -> None:
        """Verify DTO enforces required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceBugDTO(id=1)  # type: ignore[call-arg]

        error_msg = str(exc_info.value).lower()
        assert "title" in error_msg or "field required" in error_msg
