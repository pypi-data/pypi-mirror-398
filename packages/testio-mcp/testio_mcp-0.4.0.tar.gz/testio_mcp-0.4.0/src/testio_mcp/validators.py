"""Pydantic field validators for input coercion.

This module provides reusable validators that handle numeric type variations
that pass MCP's JSON schema validation but need coercion for strict type safety.

MCP Protocol Constraints:
- MCP validates JSON schema before reaching these validators
- For `int` parameters: Only integers reach validator (strings/floats blocked by MCP)
- For `list[int]` parameters: Only lists reach validator, but elements may be floats
- These validators handle edge cases MCP allows (e.g., float elements in int lists)

Design Philosophy:
- Accept what MCP's JSON schema allows
- Coerce numeric variations (e.g., 123.0 -> 123)
- Fail early with clear error messages
- Services always receive correctly-typed values
"""

from typing import Any


def coerce_to_int(value: Any) -> int:
    """Coerce numeric value to integer.

    MCP JSON schema validation ensures only integers reach this validator.
    This function handles edge cases like JSON floats with .0 (e.g., 123.0).

    Args:
        value: Input value (int or float with .0 from JSON)

    Returns:
        Integer value

    Raises:
        ValueError: If value has decimal part or is invalid type

    Examples:
        >>> coerce_to_int(123)
        123
        >>> coerce_to_int(123.0)  # JSON number edge case
        123
        >>> coerce_to_int(123.5)
        Traceback (most recent call last):
        ValueError: Invalid integer: 123.5 (decimal values not allowed)
    """
    # Already an int (common case)
    if isinstance(value, int):
        return value

    # Float with no decimal part (JSON edge case: 123.0)
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(f"Invalid integer: {value} (decimal values not allowed)")

    # Should not reach here due to MCP JSON schema validation
    raise ValueError(
        f"Cannot convert {type(value).__name__} to integer. "
        f"MCP should have blocked this type at protocol level."
    )


def coerce_to_int_list(value: Any) -> list[int]:
    """Coerce list elements to integers.

    MCP JSON schema validation ensures only lists reach this validator.
    Elements within the list may be integers or floats (e.g., [1, 2.0, 3]).

    Args:
        value: List with integer or float elements

    Returns:
        List of integers

    Raises:
        ValueError: If any element has decimal part or invalid type

    Examples:
        >>> coerce_to_int_list([1, 2, 3])
        [1, 2, 3]
        >>> coerce_to_int_list([1, 2.0, 3])  # JSON edge case
        [1, 2, 3]
        >>> coerce_to_int_list([1, 2.5, 3])
        Traceback (most recent call last):
        ValueError: Invalid integer in list: Invalid integer: 2.5 (decimal values not allowed)
    """
    # MCP ensures this is a list
    if isinstance(value, list):
        try:
            return [coerce_to_int(item) for item in value]
        except ValueError as e:
            raise ValueError(f"Invalid integer in list: {e}") from e

    # Should not reach here - MCP requires list[int] type
    raise ValueError(
        f"Cannot convert {type(value).__name__} to list of integers. "
        f"MCP should have validated this as a list at protocol level."
    )
