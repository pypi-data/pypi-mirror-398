"""Unit tests for parse_int_list_input utility function.

Tests normalization logic for handling multiple input formats from different MCP clients.
This enables flexible product_id input for tools like sync_data.
"""

import pytest

from testio_mcp.utilities.parsing import parse_int_list_input


@pytest.mark.unit
def test_parses_list_of_ints() -> None:
    """Verify Python list of ints is returned as-is."""
    result = parse_int_list_input([598, 599])
    assert result == [598, 599]


@pytest.mark.unit
def test_parses_single_int() -> None:
    """Verify single int is wrapped in list."""
    result = parse_int_list_input(598)
    assert result == [598]


@pytest.mark.unit
def test_parses_single_string() -> None:
    """Verify single string number is parsed to list."""
    result = parse_int_list_input("598")
    assert result == [598]


@pytest.mark.unit
def test_parses_json_array_of_ints() -> None:
    """Verify JSON array string of ints is parsed correctly."""
    result = parse_int_list_input("[598, 599]")
    assert result == [598, 599]


@pytest.mark.unit
def test_parses_json_array_of_strings() -> None:
    """Verify JSON array of string numbers is parsed correctly."""
    result = parse_int_list_input('["598", "599"]')
    assert result == [598, 599]


@pytest.mark.unit
def test_parses_comma_separated_string() -> None:
    """Verify comma-separated string is parsed correctly."""
    result = parse_int_list_input("598,599")
    assert result == [598, 599]


@pytest.mark.unit
def test_parses_comma_separated_with_spaces() -> None:
    """Verify comma-separated with spaces is parsed correctly."""
    result = parse_int_list_input("598, 599, 600")
    assert result == [598, 599, 600]


@pytest.mark.unit
def test_handles_none() -> None:
    """Verify None input returns None."""
    result = parse_int_list_input(None)
    assert result is None


@pytest.mark.unit
def test_handles_empty_list() -> None:
    """Verify empty list returns None."""
    result = parse_int_list_input([])
    assert result is None


@pytest.mark.unit
def test_handles_empty_string() -> None:
    """Verify empty string returns None."""
    result = parse_int_list_input("")
    assert result is None


@pytest.mark.unit
def test_handles_whitespace_string() -> None:
    """Verify whitespace-only string returns None."""
    result = parse_int_list_input("   ")
    assert result is None


@pytest.mark.unit
def test_handles_empty_json_array() -> None:
    """Verify empty JSON array returns None."""
    result = parse_int_list_input("[]")
    assert result is None


@pytest.mark.unit
def test_parses_list_of_string_numbers() -> None:
    """Verify list of string numbers is converted to ints."""
    result = parse_int_list_input(["598", "599"])
    assert result == [598, 599]


@pytest.mark.unit
def test_rejects_invalid_string() -> None:
    """Verify non-numeric string is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input("not_a_number")

    assert "Cannot parse" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_invalid_in_comma_separated() -> None:
    """Verify non-numeric value in comma-separated is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input("598,abc,599")

    assert "non-integers" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_invalid_in_json_array() -> None:
    """Verify non-numeric value in JSON array is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input('["598", "abc"]')

    assert "non-integer" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_invalid_in_list() -> None:
    """Verify non-numeric value in list is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input(["598", "abc"])

    assert "non-integer" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_malformed_json() -> None:
    """Verify malformed JSON is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input("[598,]")

    assert "Invalid JSON" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_json_object() -> None:
    """Verify JSON object (not array) is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input('{"id": 598}')

    # Falls through to comma-separated parsing, then single value, fails on parse
    assert "Cannot parse" in str(exc_info.value) or "non-integers" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_float_string() -> None:
    """Verify float string is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input("598.5")

    assert "Cannot parse" in str(exc_info.value)


@pytest.mark.unit
def test_rejects_unsupported_type() -> None:
    """Verify unsupported type is rejected."""
    with pytest.raises(ValueError) as exc_info:
        parse_int_list_input({"id": 598})  # type: ignore[arg-type]

    assert "Unsupported input type" in str(exc_info.value)


# Real-world scenarios from the screenshot
@pytest.mark.unit
def test_scenario_string_single_id() -> None:
    """Verify '24734' (string) is parsed - the actual error case from screenshot."""
    result = parse_int_list_input("24734")
    assert result == [24734]


@pytest.mark.unit
def test_scenario_string_array_notation() -> None:
    """Verify '[24734]' (string) is parsed - another error case from screenshot."""
    result = parse_int_list_input("[24734]")
    assert result == [24734]
