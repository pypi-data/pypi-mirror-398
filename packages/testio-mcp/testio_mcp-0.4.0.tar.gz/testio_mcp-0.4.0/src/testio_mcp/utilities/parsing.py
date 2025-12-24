"""Parsing utilities for transforming input formats.

This module provides centralized parsing functions used by both MCP tools
and REST endpoints to ensure consistent input handling.
"""

import json

from testio_mcp.schemas.constants import VALID_TEST_STATUSES


def parse_int_list_input(value: str | int | list[int] | list[str] | None) -> list[int] | None:
    """Parse integer list input from multiple formats into normalized list.

    Handles various input formats from different MCP clients:
    1. Python list of ints: [598, 599]
    2. Python list of strings: ["598", "599"]
    3. Single int: 598
    4. Single string: "598"
    5. JSON array string: "[598, 599]" or '["598","599"]'
    6. Comma-separated string: "598,599" or "598, 599"

    Args:
        value: Integer list input in any supported format

    Returns:
        Normalized list of integers, or None if input is None/empty

    Raises:
        ValueError: If input format is invalid or values can't be parsed as integers

    Examples:
        >>> parse_int_list_input([598, 599])
        [598, 599]
        >>> parse_int_list_input(598)
        [598]
        >>> parse_int_list_input("598")
        [598]
        >>> parse_int_list_input("[598, 599]")
        [598, 599]
        >>> parse_int_list_input("598,599")
        [598, 599]
        >>> parse_int_list_input(None)
        None
    """
    if value is None:
        return None

    # Single integer - wrap in list
    if isinstance(value, int):
        return [value]

    # Already a list - convert elements to int
    if isinstance(value, list):
        if not value:
            return None
        try:
            return [int(v) for v in value]
        except (ValueError, TypeError) as e:
            raise ValueError(f"List contains non-integer values: {e}") from e

    # String input - try JSON first, then comma-separated, then single value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Try JSON array format (handles both [598] and ["598"])
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
                if not parsed:
                    return None
                return [int(v) for v in parsed]
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array format: {e}") from e
            except (ValueError, TypeError) as e:
                raise ValueError(f"JSON array contains non-integer values: {e}") from e

        # Try comma-separated format
        if "," in value:
            try:
                return [int(v.strip()) for v in value.split(",") if v.strip()]
            except ValueError as e:
                raise ValueError(f"Comma-separated values contain non-integers: {e}") from e

        # Single string value
        try:
            return [int(value)]
        except ValueError as e:
            raise ValueError(f"Cannot parse '{value}' as integer: {e}") from e

    raise ValueError(f"Unsupported input type: {type(value).__name__}")


def parse_list_input(value: str | list[str] | None) -> list[str] | None:
    """Parse generic list input from multiple formats into normalized list.

    Handles three input formats from different MCP clients:
    1. JSON array string: "[\\\"value1\\\",\\\"value2\\\"]"
    2. Comma-separated string: "value1,value2"
    3. Python list: ["value1", "value2"]

    No validation of values - accepts any strings.

    Args:
        value: List input in any supported format

    Returns:
        Normalized list of strings, or None if input is None

    Raises:
        ValueError: If input format is invalid

    Examples:
        >>> parse_list_input('["rejected","forwarded"]')
        ['rejected', 'forwarded']
        >>> parse_list_input("critical,high")
        ['critical', 'high']
        >>> parse_list_input(["critical", "high"])
        ['critical', 'high']
        >>> parse_list_input(None)
        None
    """
    if value is None:
        return None

    # Already a list - return as-is
    if isinstance(value, list):
        return value if value else None

    # String input - try JSON first, then comma-separated
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Try JSON array format
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
                if not all(isinstance(s, str) for s in parsed):
                    raise ValueError("JSON array must contain only strings")
                return parsed if parsed else None
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array format: {e}") from e

        # Comma-separated format
        values = [s.strip() for s in value.split(",") if s.strip()]
        return values if values else None

    raise ValueError(f"Unsupported input type: {type(value).__name__}")


def parse_status_input(value: str | list[str] | None) -> list[str] | None:
    """Parse status input from multiple formats into normalized list.

    Handles three input formats from different MCP clients:
    1. JSON array string: "[\\\"locked\\\",\\\"archived\\\"]"
    2. Comma-separated string: "locked,archived"
    3. Python list: ["locked", "archived"]

    Args:
        value: Status input in any supported format

    Returns:
        Normalized list of status strings, or None if input is None

    Raises:
        ValueError: If input format is invalid or contains invalid statuses

    Examples:
        >>> parse_status_input('["locked","archived"]')
        ['locked', 'archived']
        >>> parse_status_input("locked,archived")
        ['locked', 'archived']
        >>> parse_status_input(["locked", "archived"])
        ['locked', 'archived']
        >>> parse_status_input(None)
        None
    """
    if value is None:
        return None

    # Already a list - validate and return
    if isinstance(value, list):
        invalid = [s for s in value if s not in VALID_TEST_STATUSES]
        if invalid:
            valid_str = ", ".join(VALID_TEST_STATUSES)
            raise ValueError(f"Invalid status values: {invalid}. Valid statuses: {valid_str}")
        return value

    # String input - try JSON first, then comma-separated
    if isinstance(value, str):
        value = value.strip()

        # Try JSON array format
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
                if not all(isinstance(s, str) for s in parsed):
                    raise ValueError("JSON array must contain only strings")

                invalid = [s for s in parsed if s not in VALID_TEST_STATUSES]
                if invalid:
                    raise ValueError(
                        f"Invalid status values: {invalid}. "
                        f"Valid statuses: {', '.join(VALID_TEST_STATUSES)}"
                    )
                return parsed
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array format: {e}") from e

        # Comma-separated format
        statuses = [s.strip() for s in value.split(",")]
        invalid = [s for s in statuses if s not in VALID_TEST_STATUSES]
        if invalid:
            valid_str = ", ".join(VALID_TEST_STATUSES)
            raise ValueError(f"Invalid status values: {invalid}. Valid statuses: {valid_str}")
        return statuses

    raise ValueError(f"Unsupported status input type: {type(value).__name__}")


def parse_severity_input(value: str | list[str] | None) -> list[str] | None:
    """Parse severity input from multiple formats into normalized list.

    Handles three input formats from different MCP clients:
    1. JSON array string: "[\\\"critical\\\",\\\"high\\\"]"
    2. Comma-separated string: "critical,high"
    3. Python list: ["critical", "high"]

    Args:
        value: Severity input in any supported format

    Returns:
        Normalized list of severity strings, or None if input is None

    Raises:
        ValueError: If input format is invalid

    Examples:
        >>> parse_severity_input('["critical","high"]')
        ['critical', 'high']
        >>> parse_severity_input("critical,high")
        ['critical', 'high']
        >>> parse_severity_input(["critical", "high"])
        ['critical', 'high']
        >>> parse_severity_input(None)
        None
    """
    if value is None:
        return None

    # Already a list - return as-is
    if isinstance(value, list):
        return value if value else None

    # String input - try JSON first, then comma-separated
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Try JSON array format
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
                if not all(isinstance(s, str) for s in parsed):
                    raise ValueError("JSON array must contain only strings")
                return parsed if parsed else None
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array format: {e}") from e

        # Comma-separated format
        severities = [s.strip() for s in value.split(",") if s.strip()]
        return severities if severities else None

    raise ValueError(f"Unsupported severity input type: {type(value).__name__}")


def parse_rejection_reason_input(value: str | list[str] | None) -> list[str] | None:
    """Parse rejection reason input from multiple formats into normalized list.

    Handles three input formats from different MCP clients:
    1. JSON array string: "[\\\"test_is_invalid\\\",\\\"no_reproduction\\\"]"
    2. Comma-separated string: "test_is_invalid,no_reproduction"
    3. Python list: ["test_is_invalid", "no_reproduction"]

    Args:
        value: Rejection reason input in any supported format

    Returns:
        Normalized list of rejection reason strings, or None if input is None

    Raises:
        ValueError: If input format is invalid

    Examples:
        >>> parse_rejection_reason_input('["test_is_invalid","no_reproduction"]')
        ['test_is_invalid', 'no_reproduction']
        >>> parse_rejection_reason_input("test_is_invalid,no_reproduction")
        ['test_is_invalid', 'no_reproduction']
        >>> parse_rejection_reason_input(["test_is_invalid", "no_reproduction"])
        ['test_is_invalid', 'no_reproduction']
        >>> parse_rejection_reason_input(None)
        None
    """
    if value is None:
        return None

    # Already a list - return as-is
    if isinstance(value, list):
        return value if value else None

    # String input - try JSON first, then comma-separated
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Try JSON array format
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
                if not all(isinstance(s, str) for s in parsed):
                    raise ValueError("JSON array must contain only strings")
                return parsed if parsed else None
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array format: {e}") from e

        # Comma-separated format
        reasons = [s.strip() for s in value.split(",") if s.strip()]
        return reasons if reasons else None

    raise ValueError(f"Unsupported rejection reason input type: {type(value).__name__}")
