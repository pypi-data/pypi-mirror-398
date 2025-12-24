"""Timezone normalization utilities.

This module contains timezone-related utilities with minimal dependencies
to avoid circular imports when used in repository layer.

IMPORTANT: Keep this module dependency-free (only stdlib + dateutil).
Do not import from other testio_mcp modules to prevent circular imports.
"""

from datetime import UTC

from dateutil.parser import isoparse


def normalize_to_utc(timestamp_str: str | None) -> str | None:
    """Convert timestamp to UTC ISO 8601 format.

    Normalizes timestamps from various timezones to UTC for consistent database storage
    and reliable date comparisons. This prevents issues with mixed timezone formats
    (e.g., "2025-11-09T22:00:00+01:00" vs "2025-11-09T23:00:00+00:00" representing
    the same moment in time).

    Args:
        timestamp_str: ISO 8601 timestamp string with timezone info (e.g.,
            "2025-11-09T22:00:00+01:00", "2025-11-09T21:00:00+00:00",
            "2025-11-09T16:00:00-05:00"). Returns None if input is None.

    Returns:
        UTC timestamp string in format: YYYY-MM-DDTHH:MM:SS+00:00
        Returns None if input is None (handles optional timestamps like start_at/end_at).

    Raises:
        ValueError: If timestamp is naive (no timezone info). All timestamps MUST
            have timezone information to ensure correct normalization.

    Examples:
        >>> normalize_to_utc("2025-11-09T22:00:00+01:00")
        '2025-11-09T21:00:00+00:00'

        >>> normalize_to_utc("2025-11-09T21:00:00+00:00")
        '2025-11-09T21:00:00+00:00'

        >>> normalize_to_utc("2025-11-09T16:00:00-05:00")
        '2025-11-09T21:00:00+00:00'

        >>> normalize_to_utc(None)
        None

        >>> normalize_to_utc("2025-11-09T22:00:00")  # No timezone!
        Traceback (most recent call last):
            ...
        ValueError: Naive datetime not allowed: 2025-11-09T22:00:00

    Note:
        This function is used by TestRepository to normalize all timestamps
        before database insert. All timestamps in the database are stored in UTC
        for consistent querying and comparison.
    """
    if timestamp_str is None:
        return None

    # Parse ISO 8601 timestamp (handles various formats including +HH:MM, Z suffix)
    dt = isoparse(timestamp_str)

    # Validate that timestamp is timezone-aware
    if dt.tzinfo is None:
        raise ValueError(f"Naive datetime not allowed: {timestamp_str}")

    # Convert to UTC and return ISO 8601 format with +00:00 offset
    return dt.astimezone(UTC).isoformat()
