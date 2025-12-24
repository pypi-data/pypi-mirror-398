"""Unit tests for test_transformers module.

Tests the Anti-Corruption Layer (ACL) pattern for transforming service layer
data (using 'id') to API models (using 'test_id').
"""

import pytest
from pydantic import ValidationError

from testio_mcp.schemas.api import TestSummary
from testio_mcp.transformers.test_transformers import to_test_summary, to_test_summary_list


@pytest.mark.unit
def test_to_test_summary_transforms_id_to_test_id() -> None:
    """Verify id → test_id transformation at ACL boundary."""
    service_test = {
        "id": 123,
        "title": "Login test",
        "goal": "Verify login flow",
        "status": "running",
        "review_status": None,
        "testing_type": "rapid",
        "duration": 30,
        "starts_at": "2025-01-01T00:00:00+00:00",
        "ends_at": "2025-01-01T00:30:00+00:00",
    }

    result = to_test_summary(service_test)

    assert isinstance(result, TestSummary)
    assert result.test_id == 123  # Transformed from 'id'
    assert result.title == "Login test"
    assert result.goal == "Verify login flow"
    assert result.status == "running"
    assert result.testing_type == "rapid"
    assert result.duration == 30


@pytest.mark.unit
def test_to_test_summary_handles_optional_fields() -> None:
    """Verify optional fields are handled correctly."""
    minimal_test = {
        "id": 456,
        "title": "Minimal test",
        "status": "locked",
        "testing_type": "focused",
    }

    result = to_test_summary(minimal_test)

    assert result.test_id == 456
    assert result.title == "Minimal test"
    assert result.goal is None
    assert result.review_status is None
    assert result.duration is None
    assert result.starts_at is None
    assert result.ends_at is None


@pytest.mark.unit
def test_to_test_summary_validates_with_dto() -> None:
    """Verify DTO validation catches schema mismatches."""
    invalid_test = {
        "id": "not-an-integer",  # Invalid type
        "title": "Test",
        "status": "running",
        "testing_type": "rapid",
    }

    with pytest.raises(ValidationError) as exc_info:
        to_test_summary(invalid_test)

    assert "id" in str(exc_info.value).lower()


@pytest.mark.unit
def test_to_test_summary_requires_mandatory_fields() -> None:
    """Verify mandatory fields are enforced by DTO."""
    incomplete_test = {
        "id": 789,
        # Missing: title, status, testing_type
    }

    with pytest.raises(ValidationError) as exc_info:
        to_test_summary(incomplete_test)

    error_msg = str(exc_info.value).lower()
    assert "title" in error_msg or "field required" in error_msg


@pytest.mark.unit
def test_to_test_summary_list_transforms_multiple_tests() -> None:
    """Verify batch transformation for list endpoints."""
    service_tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "running",
            "testing_type": "rapid",
        },
        {
            "id": 2,
            "title": "Test 2",
            "status": "locked",
            "testing_type": "focused",
        },
        {
            "id": 3,
            "title": "Test 3",
            "status": "archived",
            "testing_type": "coverage",
        },
    ]

    result = to_test_summary_list(service_tests)

    assert len(result) == 3
    assert all(isinstance(item, TestSummary) for item in result)
    assert result[0].test_id == 1
    assert result[1].test_id == 2
    assert result[2].test_id == 3
    assert result[0].title == "Test 1"
    assert result[1].title == "Test 2"
    assert result[2].title == "Test 3"


@pytest.mark.unit
def test_to_test_summary_list_handles_empty_list() -> None:
    """Verify empty list handling."""
    result = to_test_summary_list([])

    assert result == []
    assert isinstance(result, list)


@pytest.mark.unit
def test_to_test_summary_list_propagates_validation_errors() -> None:
    """Verify validation errors from individual items propagate."""
    service_tests = [
        {"id": 1, "title": "Valid", "status": "running", "testing_type": "rapid"},
        {"id": "invalid", "title": "Invalid", "status": "locked", "testing_type": "focused"},
    ]

    with pytest.raises(ValidationError):
        to_test_summary_list(service_tests)


@pytest.mark.unit
def test_to_test_summary_preserves_all_test_types() -> None:
    """Verify all testing_type values are preserved."""
    test_types = ["rapid", "focused", "coverage", "usability"]

    for i, test_type in enumerate(test_types):
        service_test = {
            "id": i,
            "title": f"Test {test_type}",
            "status": "running",
            "testing_type": test_type,
        }
        result = to_test_summary(service_test)
        assert result.testing_type == test_type


@pytest.mark.unit
def test_to_test_summary_preserves_timestamps() -> None:
    """Verify timestamp fields are preserved as-is."""
    service_test = {
        "id": 999,
        "title": "Timestamp test",
        "status": "archived",
        "testing_type": "rapid",
        "starts_at": "2025-01-15T10:00:00+00:00",
        "ends_at": "2025-01-15T11:00:00+00:00",
    }

    result = to_test_summary(service_test)

    assert result.starts_at == "2025-01-15T10:00:00+00:00"
    assert result.ends_at == "2025-01-15T11:00:00+00:00"


@pytest.mark.unit
def test_to_test_summary_maps_test_environment() -> None:
    """Verify test_environment field is mapped correctly (STORY-072)."""
    service_test = {
        "id": 1000,
        "title": "Environment test",
        "status": "running",
        "testing_type": "rapid",
        "test_environment": {
            "os": "Windows 11",
            "browser": "Chrome",
            "version": "120.0",
        },
    }

    result = to_test_summary(service_test)

    assert result.test_environment == {
        "os": "Windows 11",
        "browser": "Chrome",
        "version": "120.0",
    }


@pytest.mark.unit
def test_to_test_summary_handles_null_test_environment() -> None:
    """Verify test_environment defaults to None when not provided (STORY-072)."""
    service_test = {
        "id": 1001,
        "title": "Test without environment",
        "status": "locked",
        "testing_type": "focused",
    }

    result = to_test_summary(service_test)

    assert result.test_environment is None


@pytest.mark.unit
def test_to_test_summary_list_preserves_test_environment() -> None:
    """Verify test_environment is preserved in batch transformation (STORY-072)."""
    service_tests = [
        {
            "id": 1,
            "title": "Test 1",
            "status": "running",
            "testing_type": "rapid",
            "test_environment": {"os": "iOS"},
        },
        {
            "id": 2,
            "title": "Test 2",
            "status": "locked",
            "testing_type": "focused",
            "test_environment": None,
        },
    ]

    result = to_test_summary_list(service_tests)

    assert len(result) == 2
    assert result[0].test_environment == {"os": "iOS"}
    assert result[1].test_environment is None
