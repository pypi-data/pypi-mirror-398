"""Reusable progress reporting utility.

Provides a transport-agnostic ProgressReporter that:
- Wraps any async callback (FastMCP, custom, or None)
- Handles errors gracefully (best-effort, never fails the operation)
- Throttles updates to prevent spam
- Supports indeterminate progress (total=None)

Usage in tools:
    from testio_mcp.utilities.progress import ProgressReporter

    @mcp.tool()
    async def sync_data(ctx: Context, ...) -> dict:
        reporter = ProgressReporter.from_context(ctx)
        await service.execute_sync(..., progress=reporter)

Usage in services:
    async def execute_sync(self, ..., progress: ProgressReporter | None = None):
        progress = progress or ProgressReporter.noop()
        await progress.report(1, 3, "Phase 1/3: products...")
        # ... do work
        await progress.report(2, 3, "Phase 2/3: features...")

AG-UI/CopilotKit Exploration (2025-12-05):
    Decision: ✅ APPROVED - Implement Progress Notifications
    Rationale: Low effort (~2-4 hours), no downside (no-op if unsupported)
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import Context

logger = logging.getLogger(__name__)


# Type alias for raw callback (what FastMCP provides)
ProgressCallback = Callable[[float, float | None, str | None], Awaitable[None]]

# Type alias for batch progress callback (used by repositories)
# Args: (current_completed: int, total_batches: int)
BatchProgressCallback = Callable[[int, int], Awaitable[None]]


async def safe_batch_callback(
    callback: BatchProgressCallback | None,
    current: int,
    total: int,
) -> None:
    """Best-effort callback invocation (never fails, except for cancellation).

    Args:
        callback: Optional progress callback
        current: Current completed count (1-indexed)
        total: Total batch count

    Raises:
        asyncio.CancelledError: Re-raised to preserve cancellation semantics
    """
    import asyncio

    if callback is None:
        return
    try:
        await callback(current, total)
    except asyncio.CancelledError:
        raise  # Must propagate cancellation
    except Exception as e:
        logger.debug(f"Progress callback failed (non-fatal): {e}")


@dataclass
class ProgressReporter:
    """Transport-agnostic progress reporter with throttling and error handling.

    Attributes:
        callback: The underlying async callback (or None for no-op)
        throttle_seconds: Minimum time between updates (default: 0.5s)
        throttle_count: Minimum items between updates (default: 5)
        _last_report_time: Internal tracking for time-based throttling
        _last_report_progress: Internal tracking for count-based throttling
    """

    callback: ProgressCallback | None = None
    throttle_seconds: float = 0.5
    throttle_count: int = 5
    _last_report_time: float = field(default=0.0, repr=False)
    _last_report_progress: float = field(default=-1.0, repr=False)

    @classmethod
    def from_context(cls, ctx: Context, **kwargs: Any) -> ProgressReporter:
        """Create a ProgressReporter from FastMCP Context.

        Args:
            ctx: FastMCP Context (has report_progress method)
            **kwargs: Override throttle_seconds, throttle_count

        Returns:
            ProgressReporter wrapping ctx.report_progress
        """
        return cls(callback=ctx.report_progress, **kwargs)

    @classmethod
    def noop(cls) -> ProgressReporter:
        """Create a no-op reporter (for CLI, background sync, tests)."""
        return cls(callback=None)

    async def report(
        self,
        progress: float,
        total: float | None = None,
        message: str | None = None,
        *,
        force: bool = False,
    ) -> None:
        """Report progress (best-effort, never raises).

        Args:
            progress: Current progress value (must increase)
            total: Total value (None for indeterminate/spinner)
            message: Human-readable status message
            force: Bypass throttling (use for final completion)
        """
        if self.callback is None:
            return

        # Throttling: skip if too soon (unless forced)
        if not force:
            now = time.monotonic()
            time_ok = (now - self._last_report_time) >= self.throttle_seconds
            count_ok = (progress - self._last_report_progress) >= self.throttle_count

            # Must pass at least one threshold
            if not time_ok and not count_ok:
                return

        # Best-effort: never let progress reporting fail the operation
        try:
            await self.callback(progress, total, message)
            self._last_report_time = time.monotonic()
            self._last_report_progress = progress
        except Exception as e:
            logger.debug(f"Progress report failed (non-fatal): {e}")

    async def complete(self, message: str | None = None) -> None:
        """Report 100% completion (always sent, bypasses throttle)."""
        await self.report(100, 100, message, force=True)
