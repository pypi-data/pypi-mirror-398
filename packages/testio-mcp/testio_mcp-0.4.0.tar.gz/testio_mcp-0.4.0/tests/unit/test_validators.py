"""Unit tests for input coercion validators.

Tests validators that handle numeric type variations within MCP's JSON schema
constraints (e.g., float elements in lists that should be integers).
"""

import pytest

from testio_mcp.validators import coerce_to_int, coerce_to_int_list


class TestCoerceToInt:
    """Test coerce_to_int function.

    Note: MCP JSON schema blocks strings/non-numeric types at protocol level.
    These tests focus on cases that can actually reach the validator.
    """

    def test_int_passthrough(self):
        """Integer values pass through unchanged (common case)."""
        assert coerce_to_int(123) == 123
        assert coerce_to_int(0) == 0
        assert coerce_to_int(-5) == -5

    def test_float_with_zero_decimal(self):
        """Floats with .0 convert to int (JSON edge case)."""
        assert coerce_to_int(123.0) == 123
        assert coerce_to_int(0.0) == 0

    def test_float_with_decimal_raises(self):
        """Float with decimal part raises ValueError."""
        with pytest.raises(ValueError, match="decimal values not allowed"):
            coerce_to_int(123.5)
        with pytest.raises(ValueError, match="decimal values not allowed"):
            coerce_to_int(0.1)

    def test_unsupported_type_raises(self):
        """Unsupported types raise ValueError (should not reach due to MCP)."""
        with pytest.raises(ValueError, match="MCP should have blocked"):
            coerce_to_int("123")  # MCP blocks strings
        with pytest.raises(ValueError, match="MCP should have blocked"):
            coerce_to_int([123])  # MCP blocks lists
        with pytest.raises(ValueError, match="MCP should have blocked"):
            coerce_to_int(None)  # MCP blocks null


class TestCoerceToIntList:
    """Test coerce_to_int_list function.

    Note: MCP JSON schema requires list[int] type, so only lists reach validator.
    These tests focus on element coercion within lists (e.g., float to int).
    """

    def test_int_list_passthrough(self):
        """List of integers passes through unchanged (common case)."""
        assert coerce_to_int_list([1, 2, 3]) == [1, 2, 3]
        assert coerce_to_int_list([0]) == [0]
        assert coerce_to_int_list([]) == []

    def test_float_elements_convert(self):
        """List with float elements (JSON edge case) converts to ints."""
        assert coerce_to_int_list([1, 2.0, 3]) == [1, 2, 3]
        assert coerce_to_int_list([123.0]) == [123]

    def test_list_with_decimal_element_raises(self):
        """List with decimal float raises ValueError."""
        with pytest.raises(ValueError, match="Invalid integer in list"):
            coerce_to_int_list([1, 2.5, 3])
        with pytest.raises(ValueError, match="Invalid integer in list"):
            coerce_to_int_list([0.1])

    def test_unsupported_type_raises(self):
        """Non-list types raise ValueError (should not reach due to MCP)."""
        with pytest.raises(ValueError, match="MCP should have validated"):
            coerce_to_int_list(123)  # MCP requires list
        with pytest.raises(ValueError, match="MCP should have validated"):
            coerce_to_int_list("123")  # MCP requires list
        with pytest.raises(ValueError, match="MCP should have validated"):
            coerce_to_int_list(None)  # MCP requires list


class TestValidatorRealWorldCases:
    """Test realistic cases that can actually reach validators through MCP."""

    def test_json_integer_passthrough(self):
        """JSON integers pass through (most common case)."""
        assert coerce_to_int(1216) == 1216
        assert coerce_to_int_list([54, 22, 48]) == [54, 22, 48]

    def test_json_float_edge_case(self):
        """JSON floats with .0 are coerced (edge case from some parsers)."""
        assert coerce_to_int(1216.0) == 1216
        assert coerce_to_int_list([54.0, 22, 48]) == [54, 22, 48]

    def test_mixed_numeric_list(self):
        """Lists with mixed numeric types are coerced."""
        assert coerce_to_int_list([1216, 1742.0, 1619]) == [1216, 1742, 1619]
