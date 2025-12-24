"""Bug classification and acceptance rate utilities.

This module provides shared utilities for classifying bugs into status buckets
and calculating acceptance rates. These functions are extracted from TestService
to enable reuse across the codebase (STORY-023b).

Business Logic:
- Bug statuses are mutually exclusive (accepted XOR auto_accepted XOR rejected XOR forwarded)
- Reviewed bugs = bugs reviewed by humans (active_accepted + rejected)
- Acceptance rates use total_bugs as denominator (all bugs regardless of status)
- Auto acceptance rate uses accepted bugs as denominator (active + auto)

Status Enrichment (STORY-047):
- The `status` field should contain enriched values from the database
- "auto_accepted" status is stored directly instead of requiring JSON parsing
- Original API response preserved in `raw_data` for reference
"""

from typing import Any


def classify_bugs(bugs: list[dict[str, Any]]) -> dict[str, int]:
    """Classify bugs into status buckets (mutually exclusive).

    This function categorizes bugs into mutually exclusive status buckets based
    on their enriched status field. It's used for bug metrics and acceptance
    rate calculations.

    Expected Status Values (enriched, STORY-047):
    - "accepted": Actively accepted by customer
    - "auto_accepted": Auto-accepted after 10 days (no customer action)
    - "rejected": Bug was rejected
    - "forwarded": Bug is open/pending

    Classification Output:
    - active_accepted: status="accepted" (actively approved by customer)
    - auto_accepted: status="auto_accepted" (auto-approved after 10 days)
    - rejected: status="rejected"
    - open: status="forwarded" (API "forwarded" maps to user-facing "open")
    - total_accepted: active_accepted + auto_accepted (derived field)
    - reviewed: active_accepted + rejected (human-reviewed bugs only)

    Args:
        bugs: List of bug dictionaries with enriched "status" field.
              Expected values: "accepted", "auto_accepted", "rejected", "forwarded"

    Returns:
        Dictionary with status counts:
        {
            "active_accepted": int,
            "auto_accepted": int,
            "rejected": int,
            "open": int,
            "total_accepted": int,  # Derived: active + auto
            "reviewed": int         # Derived: active + rejected (human-reviewed)
        }

    Example:
        >>> bugs = [
        ...     {"status": "accepted"},       # Actively accepted
        ...     {"status": "auto_accepted"},  # Auto-accepted
        ...     {"status": "rejected"},
        ...     {"status": "forwarded"},
        ... ]
        >>> classify_bugs(bugs)
        {
            "active_accepted": 1,
            "auto_accepted": 1,
            "rejected": 1,
            "open": 1,
            "total_accepted": 2,
            "reviewed": 2  # Only active_accepted + rejected (human-reviewed)
        }

    Note:
        STORY-047: Status field should contain enriched values from database.
        The "auto_accepted" status is now stored directly instead of requiring
        JSON parsing of the auto_accepted boolean field.
    """
    # Initialize counters
    counts = {
        "active_accepted": 0,
        "auto_accepted": 0,
        "rejected": 0,
        "open": 0,
    }

    for bug in bugs:
        status = bug.get("status", "unknown")

        if status == "auto_accepted":
            # Auto-accepted after 10 days (enriched status, STORY-047)
            counts["auto_accepted"] += 1
        elif status == "accepted":
            # Actively accepted by customer
            counts["active_accepted"] += 1
        elif status == "rejected":
            counts["rejected"] += 1
        elif status == "forwarded":
            # Map API "forwarded" to user-facing "open"
            counts["open"] += 1

    # Calculate derived fields
    counts["total_accepted"] = counts["active_accepted"] + counts["auto_accepted"]
    counts["reviewed"] = counts["active_accepted"] + counts["rejected"]  # Human-reviewed only

    return counts


def calculate_acceptance_rates(
    active_accepted: int,
    auto_accepted: int,
    rejected: int,
    open_bugs: int,
    total_bugs: int | None = None,
) -> dict[str, float | None]:
    """Calculate acceptance rates using explicit or derived total_bugs.

    Rate calculations:
    - active_acceptance_rate: active_accepted / total_bugs (None if total_bugs == 0)
    - auto_acceptance_rate: auto_accepted / (active_accepted + auto_accepted)
      (None if no accepted bugs)
    - overall_acceptance_rate: (active_accepted + auto_accepted) / total_bugs
      (None if total_bugs == 0)
    - rejection_rate: rejected / total_bugs (None if total_bugs == 0)
    - review_rate: (active_accepted + rejected) / total_bugs (None if total_bugs == 0)

    Args:
        active_accepted: Count of actively accepted bugs (customer approved)
        auto_accepted: Count of auto-accepted bugs (auto-approved after 10 days)
        rejected: Count of rejected bugs
        open_bugs: Count of open (forwarded) bugs
        total_bugs: Explicit total bug count (e.g., len(bugs)). If None, derived from status counts.
                   Pass explicit count for future-proofing against new bug statuses.

    Returns:
        Dictionary with acceptance rates (individual rates are None if no bugs):
        {
            "active_acceptance_rate": float | None,  # 0.0 to 1.0, None if no bugs
            "auto_acceptance_rate": float | None,    # 0.0 to 1.0, None if no accepted bugs
            "overall_acceptance_rate": float | None, # 0.0 to 1.0, None if no bugs
            "rejection_rate": float | None,          # 0.0 to 1.0, None if no bugs
            "review_rate": float | None,             # 0.0 to 1.0, None if no bugs
        }

        When total_bugs == 0, all rate fields are None (not 0.0) to distinguish
        "no data" from "perfect quality" (STORY-081).

    Example:
        >>> # Explicit total (recommended - future-proof)
        >>> calculate_acceptance_rates(
        ...     active_accepted=12,
        ...     auto_accepted=3,
        ...     rejected=3,
        ...     open_bugs=2,
        ...     total_bugs=20
        ... )
        {
            "active_acceptance_rate": 0.6,        # 12/20
            "auto_acceptance_rate": 0.2,          # 3/15
            "overall_acceptance_rate": 0.75,      # 15/20
            "rejection_rate": 0.15,               # 3/20
            "review_rate": 0.75,                  # (12+3)/20 = 15/20
        }

        >>> # Derived total (backward compatible)
        >>> calculate_acceptance_rates(12, 3, 3, 2)
        {...}  # Same result

        >>> # No bugs - rates are None (not 0.0)
        >>> calculate_acceptance_rates(0, 0, 0, 0, 0)
        {
            "active_acceptance_rate": None,
            "auto_acceptance_rate": None,
            "overall_acceptance_rate": None,
            "rejection_rate": None,
            "review_rate": None,
        }
    """
    # Use explicit total_bugs if provided, otherwise derive from status counts
    if total_bugs is None:
        total_bugs = active_accepted + auto_accepted + rejected + open_bugs

    total_accepted = active_accepted + auto_accepted

    # When no bugs exist, return None for all rates to distinguish "no data" from "0%"
    if total_bugs == 0:
        return {
            "active_acceptance_rate": None,
            "auto_acceptance_rate": None,
            "overall_acceptance_rate": None,
            "rejection_rate": None,
            "review_rate": None,
        }

    active_rate = active_accepted / total_bugs
    overall_rate = total_accepted / total_bugs
    rejection_rate_val = rejected / total_bugs

    # Auto acceptance rate uses accepted bugs as denominator
    auto_rate: float | None = None
    if total_accepted > 0:
        auto_rate = auto_accepted / total_accepted

    # Review rate = bugs reviewed by humans (active_accepted + rejected) / total_bugs
    # Excludes auto_accepted (system-reviewed) and open (not reviewed)
    user_reviewed = active_accepted + rejected
    review_rate_val = user_reviewed / total_bugs

    return {
        "active_acceptance_rate": active_rate,
        "auto_acceptance_rate": auto_rate,
        "overall_acceptance_rate": overall_rate,
        "rejection_rate": rejection_rate_val,
        "review_rate": review_rate_val,
    }
