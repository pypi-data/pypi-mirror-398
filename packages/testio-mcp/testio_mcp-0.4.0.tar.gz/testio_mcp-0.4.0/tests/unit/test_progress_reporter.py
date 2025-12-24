"""Unit tests for ProgressReporter utility.

Tests cover:
- Factory methods (noop, from_context)
- Throttling logic (time-based, count-based, combined)
- Error handling (callback errors logged, no re-raise)
- Indeterminate progress (total=None)
- Completion semantics (force=True bypasses throttle)

AG-UI/CopilotKit Exploration (2025-12-05):
    Target: 95% coverage for progress.py
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.utilities.progress import ProgressReporter

# =============================================================================
# Factory Methods
# =============================================================================


@pytest.mark.unit
def test_noop_returns_reporter_with_no_callback():
    """Verify noop() returns a reporter that does nothing."""
    reporter = ProgressReporter.noop()

    assert reporter.callback is None
    assert reporter.throttle_seconds == 0.5
    assert reporter.throttle_count == 5


@pytest.mark.unit
def test_from_context_extracts_report_progress():
    """Verify from_context() extracts ctx.report_progress callback."""
    mock_ctx = MagicMock()
    mock_ctx.report_progress = AsyncMock()

    reporter = ProgressReporter.from_context(mock_ctx)

    assert reporter.callback is mock_ctx.report_progress


@pytest.mark.unit
def test_from_context_accepts_throttle_overrides():
    """Verify from_context() allows overriding throttle settings."""
    mock_ctx = MagicMock()
    mock_ctx.report_progress = AsyncMock()

    reporter = ProgressReporter.from_context(mock_ctx, throttle_seconds=2.0, throttle_count=10)

    assert reporter.throttle_seconds == 2.0
    assert reporter.throttle_count == 10


# =============================================================================
# Basic Reporting
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_report_invokes_callback_with_args():
    """Verify report() calls callback with progress, total, message."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    await reporter.report(5, 10, "Halfway there")

    mock_callback.assert_called_once_with(5, 10, "Halfway there")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_report_noop_does_nothing():
    """Verify noop reporter doesn't crash when report() is called."""
    reporter = ProgressReporter.noop()

    # Should not raise
    await reporter.report(5, 10, "Test message")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_report_supports_none_total():
    """Verify report() works with total=None (indeterminate progress)."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    await reporter.report(42, None, "Processing...")

    mock_callback.assert_called_once_with(42, None, "Processing...")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_report_supports_none_message():
    """Verify report() works with message=None."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    await reporter.report(5, 10, None)

    mock_callback.assert_called_once_with(5, 10, None)


# =============================================================================
# Throttling: Time-based
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_throttling_respects_time_threshold():
    """Verify rapid calls within throttle_seconds are skipped."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1.0,
        throttle_count=1000,  # High so time is the limiting factor
    )

    # First call fires
    await reporter.report(1, 10, "First")

    # Second call immediately after - should be throttled
    await reporter.report(2, 10, "Second")

    assert mock_callback.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_throttling_allows_after_time_passes():
    """Verify calls after throttle_seconds have passed are allowed."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=0.05,  # 50ms for fast test
        throttle_count=1000,
    )

    await reporter.report(1, 10, "First")

    # Wait for throttle window to pass
    await asyncio.sleep(0.06)

    await reporter.report(2, 10, "Second")

    assert mock_callback.call_count == 2


# =============================================================================
# Throttling: Count-based
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_throttling_respects_count_threshold():
    """Verify calls within throttle_count are skipped."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1000.0,  # High so count is the limiting factor
        throttle_count=5,
    )

    # First call fires (progress=0)
    await reporter.report(0, 100, "Start")

    # Second call (progress=1) - delta only 1, throttled
    await reporter.report(1, 100, "One")

    # Third call (progress=2) - delta only 2, throttled
    await reporter.report(2, 100, "Two")

    assert mock_callback.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_throttling_allows_after_count_delta():
    """Verify calls after progress increases by throttle_count are allowed."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1000.0,  # High so count is the limiting factor
        throttle_count=5,
    )

    # First call at 0
    await reporter.report(0, 100, "Start")

    # Jump by 5 - should be allowed
    await reporter.report(5, 100, "Five")

    assert mock_callback.call_count == 2


# =============================================================================
# Throttling: Combined (OR logic)
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_throttling_either_threshold_allows_report():
    """Verify that passing EITHER time OR count threshold allows the call."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1000.0,  # High
        throttle_count=3,
    )

    # First call
    await reporter.report(0, 100, "Start")

    # Small time delta, but count delta = 3 (passes count threshold)
    await reporter.report(3, 100, "Three")

    assert mock_callback.call_count == 2


# =============================================================================
# Force flag
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_force_bypasses_throttling():
    """Verify force=True bypasses all throttling."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1000.0,
        throttle_count=1000,
    )

    await reporter.report(0, 100, "Start")
    await reporter.report(1, 100, "Forced", force=True)

    assert mock_callback.call_count == 2


# =============================================================================
# Complete method
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_sends_100_percent():
    """Verify complete() sends progress=100, total=100."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    await reporter.complete("Done!")

    mock_callback.assert_called_once_with(100, 100, "Done!")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_bypasses_throttle():
    """Verify complete() always fires (uses force=True internally)."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(
        callback=mock_callback,
        throttle_seconds=1000.0,
        throttle_count=1000,
    )

    await reporter.report(0, 100, "Start")
    await reporter.complete("Finished")

    assert mock_callback.call_count == 2


# =============================================================================
# Error Handling
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_callback_error_is_caught_and_logged():
    """Verify callback errors are caught, logged, and don't propagate."""
    mock_callback = AsyncMock(side_effect=Exception("Network error"))
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    # Should NOT raise
    await reporter.report(5, 10, "Test")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_callback_error_allows_subsequent_calls():
    """Verify that after a callback error, subsequent calls still work."""
    call_count = 0

    async def flaky_callback(progress: float, total: float | None, msg: str | None) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("First call fails")
        # Second call succeeds

    reporter = ProgressReporter(callback=flaky_callback, throttle_seconds=0)

    # First call fails (but is caught)
    await reporter.report(1, 10, "First")

    # Second call should still attempt
    await reporter.report(2, 10, "Second")

    assert call_count == 2


# =============================================================================
# Internal State Tracking
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_last_report_progress_updated_on_success():
    """Verify _last_report_progress is updated after successful report."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    assert reporter._last_report_progress == -1.0

    await reporter.report(42, 100, "Test")

    assert reporter._last_report_progress == 42


@pytest.mark.unit
@pytest.mark.asyncio
async def test_last_report_time_updated_on_success():
    """Verify _last_report_time is updated after successful report."""
    mock_callback = AsyncMock()
    reporter = ProgressReporter(callback=mock_callback, throttle_seconds=0)

    before = time.monotonic()
    await reporter.report(1, 10, "Test")
    after = time.monotonic()

    assert before <= reporter._last_report_time <= after
