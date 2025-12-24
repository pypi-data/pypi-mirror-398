"""Bug transformers.

This module provides transformation logic for converting API bug data
to ORM models, including parsing rejection reasons from comments.
"""

import json
from datetime import datetime
from typing import Any, TypedDict

from testio_mcp.schemas.constants import REJECTION_REASONS


class BugOrmData(TypedDict, total=False):
    """Type-safe dictionary for Bug ORM model creation.

    This TypedDict documents the structure for Bug(**data) creation.
    Fields are populated in two phases:

    Phase 1 - transform_api_bug_to_orm():
        id, title, severity, status, actual_result, expected_result,
        rejection_reason, steps, reported_at, raw_data

    Phase 2 - Repository enrichment (bug_repository.py):
        customer_id, test_id, test_feature_id, reported_by_user_id, synced_at

    All fields use total=False since they're added incrementally.
    """

    # Phase 1: From transformer
    id: int | None
    title: str
    severity: str | None
    status: str | None
    actual_result: str | None
    expected_result: str | None
    rejection_reason: str | None
    steps: str | None
    reported_at: datetime | None
    raw_data: str
    known: bool | None

    # Phase 2: Added by repository
    customer_id: int
    test_id: int
    test_feature_id: int | None
    reported_by_user_id: int | None
    synced_at: datetime


def _parse_rejection_reason(comments: list[dict[str, Any]] | None) -> str | None:
    """Parse rejection reason from bug comments.

    Iterates through comments to find a match against known rejection reasons.
    Returns the key of the first matching reason, or None if no match found.

    Args:
        comments: List of comment dictionaries from API

    Returns:
        Rejection reason key (e.g., "request_timeout", "intended_behavior") or None
    """
    if not comments:
        return None

    for comment in comments:
        body = comment.get("body", "")
        if not body:
            continue

        for reason in REJECTION_REASONS:
            if reason["default_comment"] in body:
                return reason["key"]

    return None


def transform_api_bug_to_orm(api_bug: dict[str, Any]) -> BugOrmData:
    """Transform API bug dictionary to ORM-compatible dictionary.

    Handles:
    - Field extraction and normalization
    - Rejection reason parsing from comments (STORY-067)
    - Rich text field cleaning (STORY-063)

    Args:
        api_bug: Raw bug dictionary from TestIO API

    Returns:
        BugOrmData TypedDict compatible with Bug ORM model
    """
    # Extract basic fields
    bug_id = api_bug.get("id")
    title = api_bug.get("title", "Untitled")
    severity = api_bug.get("severity")
    status = api_bug.get("status")

    # Extract result fields (STORY-063)
    actual_result = api_bug.get("actual_result")
    expected_result = api_bug.get("expected_result")

    # Trim whitespace and convert empty strings to None
    if actual_result is not None:
        actual_result = actual_result.strip() or None
    if expected_result is not None:
        expected_result = expected_result.strip() or None

    # Extract steps (array -> newline-separated string)
    steps_array = api_bug.get("steps")
    steps = "\n".join(steps_array) if steps_array and isinstance(steps_array, list) else None

    # Parse rejection reason (STORY-067)
    rejection_reason = None
    if status == "rejected":
        comments = api_bug.get("comments", [])
        rejection_reason = _parse_rejection_reason(comments)

    # Parse reported_at
    reported_at_str = api_bug.get("reported_at")
    reported_at = None
    if reported_at_str:
        try:
            from dateutil import parser

            reported_at = parser.isoparse(reported_at_str)
        except (ValueError, TypeError):
            pass  # Invalid datetime, leave as None

    # Extract known flag (STORY-070)
    known_val = api_bug.get("known", False)
    known = bool(known_val) if isinstance(known_val, bool) else False

    return {
        "id": bug_id,
        "title": title,
        "severity": severity,
        "status": status,
        "actual_result": actual_result,
        "expected_result": expected_result,
        "rejection_reason": rejection_reason,
        "steps": steps,
        "reported_at": reported_at,
        "raw_data": json.dumps(api_bug),
        "known": known,
    }
