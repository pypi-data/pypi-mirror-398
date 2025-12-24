"""Unit tests for parse_status_input validator function.

Tests validation logic for handling multiple input formats from different MCP clients.
"""

import pytest

from testio_mcp.tools.list_tests_tool import parse_status_input


@pytest.mark.unit
def test_parses_json_array_string() -> None:
    """Verify JSON array string format is parsed correctly."""
    result = parse_status_input('["locked","archived"]')
    assert result == ["locked", "archived"]


@pytest.mark.unit
def test_parses_comma_separated_string() -> None:
    """Verify comma-separated string format is parsed correctly."""
    result = parse_status_input("locked,archived")
    assert result == ["locked", "archived"]


@pytest.mark.unit
def test_parses_single_status_string() -> None:
    """Verify single status string is parsed correctly."""
    result = parse_status_input("running")
    assert result == ["running"]


@pytest.mark.unit
def test_handles_python_list() -> None:
    """Verify Python list is validated and returned as-is."""
    result = parse_status_input(["locked", "archived"])
    assert result == ["locked", "archived"]


@pytest.mark.unit
def test_handles_none() -> None:
    """Verify None input returns None."""
    result = parse_status_input(None)
    assert result is None


@pytest.mark.unit
def test_strips_whitespace_in_comma_separated() -> None:
    """Verify whitespace is stripped from comma-separated values."""
    result = parse_status_input("running, locked , archived")
    assert result == ["running", "locked", "archived"]


@pytest.mark.unit
def test_rejects_invalid_status_in_json_array() -> None:
    """Verify invalid statuses in JSON array are rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_status_input('["invalid","locked"]')

    assert "Invalid status values" in str(exc_info.value)
    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.unit
def test_rejects_invalid_status_in_comma_separated() -> None:
    """Verify invalid statuses in comma-separated string are rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_status_input("invalid,locked")

    assert "Invalid status values" in str(exc_info.value)
    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.unit
def test_rejects_invalid_status_in_list() -> None:
    """Verify invalid statuses in Python list are rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_status_input(["invalid", "locked"])

    assert "Invalid status values" in str(exc_info.value)
    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.unit
def test_rejects_malformed_json() -> None:
    """Verify malformed JSON array is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_status_input('["locked",]')

    assert "Invalid JSON" in str(exc_info.value) or "decode" in str(exc_info.value).lower()


@pytest.mark.unit
def test_rejects_non_array_json() -> None:
    """Verify JSON object (not array) is rejected.

    Note: JSON objects don't start with '[', so they're treated as
    comma-separated strings and fail status validation.
    """
    with pytest.raises(ValueError) as exc_info:
        parse_status_input('{"status": "locked"}')

    # Falls through to comma-separated parsing, fails on invalid status
    assert "Invalid status values" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_json_array_with_non_strings() -> None:
    """Verify JSON array containing non-strings is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_status_input("[1, 2, 3]")

    assert "must contain only strings" in str(exc_info.value)


@pytest.mark.unit
def test_all_valid_statuses() -> None:
    """Verify all valid statuses are accepted."""
    valid_statuses = [
        "running",
        "locked",
        "archived",
        "cancelled",
        "customer_finalized",
        "initialized",
    ]

    # Test as comma-separated
    result = parse_status_input(",".join(valid_statuses))
    assert result == valid_statuses

    # Test as JSON array
    import json

    result = parse_status_input(json.dumps(valid_statuses))
    assert result == valid_statuses

    # Test as Python list
    result = parse_status_input(valid_statuses)
    assert result == valid_statuses
