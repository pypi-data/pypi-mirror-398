"""Unit tests for bug classification utilities.

Tests classify_bugs() and calculate_acceptance_rates() functions.

STORY-047: Tests updated to use enriched status values.
- "auto_accepted" status is now stored directly in the status field
- classify_bugs() reads from enriched status, not auto_accepted boolean
"""

import pytest

from testio_mcp.utilities.bug_classifiers import (
    calculate_acceptance_rates,
    classify_bugs,
)


@pytest.mark.unit
def test_classify_bugs_mixed_statuses():
    """Verify classify_bugs handles mixed bug statuses correctly.

    STORY-047: Uses enriched status values (auto_accepted as status).
    """
    bugs = [
        {"status": "accepted"},  # Actively accepted
        {"status": "auto_accepted"},  # Auto-accepted (enriched status)
        {"status": "rejected"},
        {"status": "forwarded"},
    ]

    result = classify_bugs(bugs)

    assert result["active_accepted"] == 1
    assert result["auto_accepted"] == 1
    assert result["rejected"] == 1
    assert result["open"] == 1
    assert result["total_accepted"] == 2
    assert result["reviewed"] == 2  # Only active_accepted + rejected (human-reviewed)


@pytest.mark.unit
def test_classify_bugs_auto_accepted_status():
    """Verify auto_accepted status is counted correctly (STORY-047 enriched format)."""
    bugs = [
        {"status": "auto_accepted"},
        {"status": "auto_accepted"},
    ]

    result = classify_bugs(bugs)

    assert result["active_accepted"] == 0
    assert result["auto_accepted"] == 2
    assert result["total_accepted"] == 2


@pytest.mark.unit
def test_classify_bugs_active_accepted_status():
    """Verify accepted status (active acceptance) is counted correctly."""
    bugs = [
        {"status": "accepted"},
        {"status": "accepted"},
    ]

    result = classify_bugs(bugs)

    assert result["active_accepted"] == 2
    assert result["auto_accepted"] == 0
    assert result["total_accepted"] == 2


@pytest.mark.unit
def test_classify_bugs_empty_list():
    """Verify classify_bugs handles empty bug list."""
    result = classify_bugs([])

    assert result["active_accepted"] == 0
    assert result["auto_accepted"] == 0
    assert result["rejected"] == 0
    assert result["open"] == 0
    assert result["total_accepted"] == 0
    assert result["reviewed"] == 0


@pytest.mark.unit
def test_classify_bugs_unknown_status_ignored():
    """Verify bugs with unknown status are ignored in classification."""
    bugs = [
        {"status": "unknown"},
        {"status": "pending"},
        {"status": "in_review"},
    ]

    result = classify_bugs(bugs)

    # All counts should be zero (unknown statuses ignored)
    assert result["active_accepted"] == 0
    assert result["auto_accepted"] == 0
    assert result["rejected"] == 0
    assert result["open"] == 0
    assert result["total_accepted"] == 0
    assert result["reviewed"] == 0


@pytest.mark.unit
def test_classify_bugs_missing_status_field():
    """Verify bugs with missing status field are handled gracefully."""
    bugs = [
        {},  # No status field
        {"title": "Bug without status"},
    ]

    result = classify_bugs(bugs)

    # Should not crash, all counts zero
    assert result["active_accepted"] == 0
    assert result["auto_accepted"] == 0
    assert result["rejected"] == 0
    assert result["open"] == 0


@pytest.mark.unit
def test_classify_bugs_forwarded_maps_to_open():
    """Verify 'forwarded' status maps to 'open' bucket."""
    bugs = [
        {"status": "forwarded"},
        {"status": "forwarded"},
        {"status": "forwarded"},
    ]

    result = classify_bugs(bugs)

    assert result["open"] == 3
    assert result["reviewed"] == 0  # Forwarded bugs not reviewed


@pytest.mark.unit
def test_classify_bugs_reviewed_excludes_auto_and_open():
    """Verify reviewed count is human-reviewed only (active + rejected).

    STORY-047: Uses enriched status values.
    """
    bugs = [
        {"status": "accepted"},  # reviewed (human-reviewed)
        {"status": "auto_accepted"},  # NOT reviewed (auto-accepted)
        {"status": "rejected"},  # reviewed (human-reviewed)
        {"status": "forwarded"},  # NOT reviewed (open)
        {"status": "forwarded"},  # NOT reviewed (open)
    ]

    result = classify_bugs(bugs)

    assert result["reviewed"] == 2  # Only active_accepted + rejected (human-reviewed)
    assert result["open"] == 2


@pytest.mark.unit
def test_classify_bugs_realistic_distribution():
    """Test with realistic bug distribution matching production data.

    STORY-047: Simulates enriched status from backfilled data.
    Production distribution: ~72% active accepted, ~28% auto_accepted
    """
    bugs = [
        {"status": "accepted"},
        {"status": "accepted"},
        {"status": "accepted"},
        {"status": "accepted"},  # 4 active accepted (~72%)
        {"status": "auto_accepted"},
        {"status": "auto_accepted"},  # 2 auto_accepted (~28%)
        {"status": "rejected"},
        {"status": "rejected"},  # 2 rejected
        {"status": "forwarded"},  # 1 open
    ]

    result = classify_bugs(bugs)

    assert result["active_accepted"] == 4
    assert result["auto_accepted"] == 2
    assert result["rejected"] == 2
    assert result["open"] == 1
    assert result["total_accepted"] == 6
    assert result["reviewed"] == 6  # 4 active + 2 rejected (human-reviewed)


@pytest.mark.unit
def test_calculate_acceptance_rates_normal_case():
    """Verify calculate_acceptance_rates with typical bug counts."""
    # 12 active, 3 auto, 3 rejected, 2 open = 20 total
    result = calculate_acceptance_rates(
        active_accepted=12, auto_accepted=3, rejected=3, open_bugs=2
    )

    assert result is not None
    assert result["active_acceptance_rate"] == pytest.approx(12 / 20)  # 0.6
    assert result["auto_acceptance_rate"] == pytest.approx(3 / 15)  # 0.2 (3 / (12+3))
    assert result["overall_acceptance_rate"] == pytest.approx(15 / 20)  # 0.75
    assert result["rejection_rate"] == pytest.approx(3 / 20)  # 0.15


@pytest.mark.unit
def test_calculate_acceptance_rates_zero_bugs_returns_dict_with_none_values():
    """Verify calculate_acceptance_rates returns dict with None values when no bugs (STORY-081).

    When total_bugs == 0, all rate fields should be None (not 0.0) to distinguish
    "no data" from "perfect quality" (0% rejection = all bugs accepted).
    """
    result = calculate_acceptance_rates(active_accepted=0, auto_accepted=0, rejected=0, open_bugs=0)

    # After STORY-081: Returns dict with None values, not None itself
    assert result is not None
    assert isinstance(result, dict)
    assert result["active_acceptance_rate"] is None
    assert result["auto_acceptance_rate"] is None
    assert result["overall_acceptance_rate"] is None
    assert result["rejection_rate"] is None
    assert result["review_rate"] is None


@pytest.mark.unit
def test_calculate_acceptance_rates_only_accepted():
    """Verify rates when only accepted bugs exist."""
    result = calculate_acceptance_rates(
        active_accepted=10, auto_accepted=0, rejected=0, open_bugs=0
    )

    assert result is not None
    assert result["active_acceptance_rate"] == 1.0  # 10/10
    assert result["auto_acceptance_rate"] == 0.0  # 0/10 accepted bugs
    assert result["overall_acceptance_rate"] == 1.0  # 10/10
    assert result["rejection_rate"] == 0.0  # 0/10


@pytest.mark.unit
def test_calculate_acceptance_rates_only_rejected():
    """Verify rates when only rejected bugs exist."""
    result = calculate_acceptance_rates(
        active_accepted=0, auto_accepted=0, rejected=10, open_bugs=0
    )

    assert result is not None
    assert result["active_acceptance_rate"] == 0.0  # 0/10
    assert result["auto_acceptance_rate"] is None  # No accepted bugs
    assert result["overall_acceptance_rate"] == 0.0  # 0/10
    assert result["rejection_rate"] == 1.0  # 10/10


@pytest.mark.unit
def test_calculate_acceptance_rates_only_auto_accepted():
    """Verify rates when only auto-accepted bugs exist."""
    result = calculate_acceptance_rates(
        active_accepted=0, auto_accepted=10, rejected=0, open_bugs=0
    )

    assert result is not None
    assert result["active_acceptance_rate"] == 0.0  # 0/10
    assert result["auto_acceptance_rate"] == 1.0  # 10/10 accepted
    assert result["overall_acceptance_rate"] == 1.0  # 10/10
    assert result["rejection_rate"] == 0.0  # 0/10


@pytest.mark.unit
def test_calculate_acceptance_rates_mixed_proportions():
    """Verify rates with realistic mixed proportions."""
    # 20 active, 5 auto, 5 rejected, 0 open = 30 total
    result = calculate_acceptance_rates(
        active_accepted=20, auto_accepted=5, rejected=5, open_bugs=0
    )

    assert result is not None
    assert result["active_acceptance_rate"] == pytest.approx(20 / 30)  # 0.6667
    assert result["auto_acceptance_rate"] == pytest.approx(5 / 25)  # 0.2 (5/(20+5))
    assert result["overall_acceptance_rate"] == pytest.approx(25 / 30)  # 0.8333
    assert result["rejection_rate"] == pytest.approx(5 / 30)  # 0.1667


@pytest.mark.unit
def test_calculate_acceptance_rates_rates_sum_to_one():
    """Verify acceptance rate and rejection rate sum to 1.0."""
    # 7 active, 3 auto, 10 rejected, 0 open = 20 total
    result = calculate_acceptance_rates(
        active_accepted=7, auto_accepted=3, rejected=10, open_bugs=0
    )

    assert result is not None
    # overall (10/20) + rejection (10/20) = 1.0
    total_rate = result["overall_acceptance_rate"] + result["rejection_rate"]
    assert total_rate == pytest.approx(1.0)
