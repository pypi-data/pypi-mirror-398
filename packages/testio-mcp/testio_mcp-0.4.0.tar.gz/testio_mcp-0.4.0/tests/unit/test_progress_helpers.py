"""Unit tests for progress reporting helpers.

Tests for BatchProgressCallback type alias and safe_batch_callback helper function.

Progress Reporting Extension Plan - Phase 4
"""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

from testio_mcp.utilities.progress import BatchProgressCallback, safe_batch_callback


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_batch_callback_swallows_generic_exception() -> None:
    """Verify generic exceptions are swallowed and logged (not propagated)."""

    async def failing_callback(current: int, total: int) -> None:
        raise ValueError("Something went wrong in callback")

    # Should not raise - exception is swallowed
    await safe_batch_callback(failing_callback, 1, 10)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_batch_callback_propagates_cancelled_error() -> None:
    """Verify CancelledError is NOT swallowed (must propagate for cancellation)."""

    async def cancelling_callback(current: int, total: int) -> None:
        raise asyncio.CancelledError()

    # CancelledError should propagate (not swallowed)
    with pytest.raises(asyncio.CancelledError):
        await safe_batch_callback(cancelling_callback, 1, 10)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_batch_callback_handles_none_gracefully() -> None:
    """Verify None callback is handled gracefully (no-op)."""
    # Should not raise when callback is None
    await safe_batch_callback(None, 1, 10)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_batch_callback_invokes_callback() -> None:
    """Verify callback is actually invoked with correct parameters."""
    mock_callback = AsyncMock()

    await safe_batch_callback(mock_callback, 5, 20)

    mock_callback.assert_called_once_with(5, 20)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_safe_batch_callback_logs_exception_at_debug_level(caplog: Any) -> None:
    """Verify exceptions are logged at DEBUG level (non-fatal)."""

    async def failing_callback(current: int, total: int) -> None:
        raise RuntimeError("Test error for logging")

    # Set DEBUG level for the specific logger
    with caplog.at_level(logging.DEBUG, logger="testio_mcp.utilities.progress"):
        await safe_batch_callback(failing_callback, 1, 10)

    # Should have logged at debug level
    assert any(
        "Progress callback failed (non-fatal)" in record.message and record.levelno == logging.DEBUG
        for record in caplog.records
    )


@pytest.mark.unit
def test_batch_progress_callback_type_alias() -> None:
    """Verify BatchProgressCallback type alias is usable and correct."""
    # Type should be Callable[[int, int], Awaitable[None]]
    # We just verify it's importable and usable as a type hint

    async def sample_callback(current: int, total: int) -> None:
        pass

    # This should type-check correctly
    callback: BatchProgressCallback = sample_callback
    assert callable(callback)
