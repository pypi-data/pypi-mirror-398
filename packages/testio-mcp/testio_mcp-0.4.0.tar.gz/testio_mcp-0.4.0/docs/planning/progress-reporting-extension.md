# Progress Reporting Extension Plan

**Date:** 2025-12-06
**Status:** Implemented
**Related:** [AG-UI / CopilotKit Exploration](./agui-copilotkit-exploration.md)

---

## Overview

Extend the MCP progress notifications pattern (implemented for `sync_data`) to all tools that perform potentially slow operations via read-through caching.

### Goal

Provide real-time progress feedback for any tool that may trigger API refreshes, using a consistent 3-layer pattern:

1. **Repository Layer:** Generic callbacks (`on_batch_progress`)
2. **Service Layer:** `ProgressReporter` with context-aware messages
3. **Tool Layer:** Inject `ProgressReporter.from_context(ctx)`

---

## Architecture

```
Tool Layer                    Service Layer                 Repository Layer
─────────────────────────────────────────────────────────────────────────────
sync_data_tool.py            SyncService                   (direct inserts)
  └─ ProgressReporter ────────► execute_sync()
                                └─ phases, products, pages

query_metrics_tool.py        AnalyticsService              BugRepository
  └─ ProgressReporter ────────► query_metrics()             TestRepository
                                ├─ Step 1: tests ──────────► get_tests_cached_or_refresh()
                                ├─ Step 2: bugs ───────────► get_bugs_cached_or_refresh()
                                └─ Step 3: features ───────► get_features_cached_or_refresh()

get_product_quality_         MultiTestReportService        BugRepository
report_tool.py                     │
  └─ ProgressReporter ────────► generate_ebr_report()
                                └─ bugs ───────────────────► get_bugs_cached_or_refresh()
```

---

## Implementation Checklist

### Phase 0: Shared Infrastructure

Add type alias and helper function to `utilities/progress.py`.

| File | Item | Status | Notes |
|------|------|--------|-------|
| `src/testio_mcp/utilities/progress.py` | Module logger | [x] Done | `logger = logging.getLogger(__name__)` |
| `src/testio_mcp/utilities/progress.py` | `BatchProgressCallback` type alias | [x] Done | |
| `src/testio_mcp/utilities/progress.py` | `safe_batch_callback()` helper | [x] Done | DRY pattern, re-raises `CancelledError` |
| `src/testio_mcp/utilities/__init__.py` | Export new symbols + `__all__` | [x] Done | |

### Phase 1: Repository Layer (Callbacks)

Add `on_batch_progress: Callable[[int, int], Awaitable[None]] | None` parameter to read-through cache methods.

| File | Method | Status | Notes |
|------|--------|--------|-------|
| `src/testio_mcp/repositories/bug_repository.py` | `get_bugs_cached_or_refresh()` | [x] Done | Main bottleneck |
| `src/testio_mcp/repositories/test_repository.py` | `get_tests_cached_or_refresh()` | [x] Done | |
| `src/testio_mcp/repositories/feature_repository.py` | `get_features_cached_or_refresh()` | [x] Done | Usually fast |

**Callback Contract:**
```python
# Type alias (in utilities/progress.py)
BatchProgressCallback = Callable[[int, int], Awaitable[None]]
# Args: (completed_count, total_batches)

# Usage in repository (preserves asyncio.gather concurrency)
# Uses safe_batch_callback() helper - see Validation Review Enhancement 1
# Uses asyncio.Lock for thread safety - see Validation Review Enhancement 5
async def get_bugs_cached_or_refresh(
    self,
    test_ids: list[int],
    force_refresh: bool = False,
    on_batch_progress: BatchProgressCallback | None = None,
) -> tuple[dict[int, list[dict]], dict]:
    ...
    # Thread-safe counter for concurrent batch tracking (PEP 703 future-proof)
    counter_lock = asyncio.Lock()
    completed_batches = 0

    async def tracked_batch(batch: list[int]) -> BatchResult:
        nonlocal completed_batches
        result = await refresh_batch_with_locks(batch)
        # Lock protects counter increment (safe under free-threading)
        async with counter_lock:
            completed_batches += 1
            current = completed_batches
        # Uses shared helper for DRY defensive callback invocation
        await safe_batch_callback(on_batch_progress, current, len(batches))
        return result

    batch_results = await asyncio.gather(
        *[tracked_batch(batch) for batch in batches]
    )
```

### Phase 2: Service Layer (ProgressReporter)

Add `progress: ProgressReporter | None` parameter and wire up repository callbacks.

| File | Method | Status | Notes |
|------|--------|--------|-------|
| `src/testio_mcp/services/analytics_service.py` | `query_metrics()` | [x] Done | 4 phases: scope, tests, bugs, features |
| `src/testio_mcp/services/multi_test_report_service.py` | `get_product_quality_report()` | [x] Done | 3 phases: tests, bugs, report |

**Service Pattern:**
```python
async def query_metrics(
    self,
    ...,
    progress: ProgressReporter | None = None,
) -> dict:
    progress = progress or ProgressReporter.noop()

    # Phase 1: Scope identification
    await progress.report(0, 4, "Identifying query scope...", force=True)
    test_ids = await self._get_scoped_test_ids(...)

    # Phase 2: Test refresh with batch callback
    await progress.report(1, 4, f"Refreshing test metadata ({len(test_ids)} tests)...", force=True)

    async def on_test_batch(current: int, total: int) -> None:
        # current is 1-indexed from repository (no +1 needed)
        await progress.report(1, 4, f"Refreshing tests: batch {current}/{total}...")

    await test_repo.get_tests_cached_or_refresh(test_ids, on_batch_progress=on_test_batch)

    # Phase 3: Bug refresh with batch callback
    await progress.report(2, 4, f"Refreshing bug data ({len(test_ids)} tests)...", force=True)

    async def on_bug_batch(current: int, total: int) -> None:
        # current is 1-indexed from repository (no +1 needed)
        await progress.report(2, 4, f"Refreshing bugs: batch {current}/{total}...")

    await bug_repo.get_bugs_cached_or_refresh(test_ids, on_batch_progress=on_bug_batch)

    # Phase 4: Feature refresh
    await progress.report(3, 4, "Refreshing feature data...", force=True)
    await feature_repo.get_features_cached_or_refresh(product_ids)

    # Complete
    await progress.complete("Query complete")
```

### Phase 3: Tool Layer (Injection)

Inject `ProgressReporter.from_context(ctx)` and pass to service.

| File | Status | Notes |
|------|--------|-------|
| `src/testio_mcp/tools/query_metrics_tool.py` | [x] Done | |
| `src/testio_mcp/tools/product_quality_report_tool.py` | [x] Done | |

**Tool Pattern:**
```python
from testio_mcp.utilities.progress import ProgressReporter

@mcp.tool()
async def query_metrics(ctx: Context, ...) -> dict:
    reporter = ProgressReporter.from_context(ctx)

    async with get_service_context(ctx, AnalyticsService) as service:
        return await service.query_metrics(..., progress=reporter)
```

### Phase 4: Tests

| File | Status | Notes |
|------|--------|-------|
| `tests/unit/test_bug_repository.py` | [ ] Deferred | Test callback invocation |
| `tests/unit/test_test_repository.py` | [ ] Deferred | Test callback invocation |
| `tests/unit/test_feature_repository.py` | [ ] Deferred | Test callback invocation |
| `tests/unit/test_analytics_service.py` | [ ] Deferred | Test progress flow |
| `tests/services/test_multi_test_report_service_progress.py` | [ ] Deferred | **NEW FILE** - Test progress flow |
| `tests/unit/test_tools_query_metrics.py` | [ ] Deferred | Test injection |
| `tests/unit/test_tools_product_quality_report.py` | [x] Done | Updated for progress param |
| `tests/unit/test_progress_helpers.py` | [x] Done | Test `safe_batch_callback()` |

**Implemented test cases for `test_progress_helpers.py`:**
1. Callback raising generic exception is swallowed and logged
2. `CancelledError` is propagated (not swallowed)
3. `None` callback is handled gracefully (no-op)
4. Callback is invoked with correct parameters
5. Type alias is usable

---

## Progress Output Examples

### query_metrics (4 phases + batch detail)

```json
{"progress": 0, "total": 4, "message": "Identifying query scope..."}
{"progress": 1, "total": 4, "message": "Refreshing test metadata (295 tests)..."}
{"progress": 1, "total": 4, "message": "Refreshing tests: batch 3/10..."}
{"progress": 2, "total": 4, "message": "Refreshing bug data (295 tests)..."}
{"progress": 2, "total": 4, "message": "Refreshing bugs: batch 5/20..."}
{"progress": 3, "total": 4, "message": "Refreshing feature data..."}
{"progress": 100, "total": 100, "message": "Query complete"}
```

### get_product_quality_report (3 phases + batch detail)

```json
{"progress": 0, "total": 3, "message": "Loading test metadata..."}
{"progress": 1, "total": 3, "message": "Refreshing bug data (295 tests)..."}
{"progress": 1, "total": 3, "message": "Refreshing bugs: batch 8/20..."}
{"progress": 2, "total": 3, "message": "Generating report..."}
{"progress": 100, "total": 100, "message": "Report complete: 295 tests, 1,247 bugs"}
```

---

## Peer Review Feedback (2025-12-06)

Reviews from Codex and Gemini on the plan and staged implementation.

### Critical: Preserve Concurrency in BugRepository (Gemini - High)

**Problem:** The plan's example shows a sequential loop:
```python
for i, batch in enumerate(batches):
    if on_batch_progress: await on_batch_progress(i, len(batches))
    await self._refresh_batch(batch)
```

But `BugRepository.get_bugs_cached_or_refresh()` uses `asyncio.gather()` for concurrent batch execution (lines 536-538). The plan would regress performance.

**Solution:** Use a thread-safe counter with concurrent execution:
```python
# In repository - preserves concurrency with thread-safe counter (PEP 703 future-proof)
counter_lock = asyncio.Lock()
completed_batches = 0

async def tracked_batch(batch: list[int], idx: int) -> BatchResult:
    nonlocal completed_batches
    result = await refresh_batch_with_locks(batch)
    async with counter_lock:
        completed_batches += 1
        current = completed_batches
    await safe_batch_callback(on_batch_progress, current, len(batches))
    return result

batch_results = await asyncio.gather(
    *[tracked_batch(batch, i) for i, batch in enumerate(batches)]
)
```

**Note:** Progress reports may arrive out-of-order due to concurrency. This is acceptable since throttling reduces frequency anyway. The `asyncio.Lock()` ensures counter correctness under Python 3.13+ free-threading.

### Medium: Wrap Callbacks Defensively (Codex)

**Problem:** The "best-effort" promise is stated but not enforced at repository level. A callback that raises would fail the refresh.

**Solution:** Use shared `safe_batch_callback()` helper (see Validation Review Enhancement 1):
```python
# Don't duplicate try/except in each repository - use shared helper
await safe_batch_callback(on_batch_progress, current, total)
```

### Low: Consider Throttle Tuning for High-Frequency Paths (Codex)

**Issue:** Default throttle (0.5s / 5 items) may drop many per-page updates for fast API responses.

**Options:**
1. Lower throttle for specific paths: `ProgressReporter.from_context(ctx, throttle_seconds=0.1)`
2. Force every Nth page: `force=(page % 5 == 0)`
3. Accept current behavior (phase milestones still visible)

**Decision:** Defer - current behavior acceptable. Phase boundaries use `force=True` so users always see major milestones.

### Low: Define Type Alias (Gemini)

Add to `utilities/progress.py`:
```python
from typing import Callable, Awaitable

BatchProgressCallback = Callable[[int, int], Awaitable[None]]
# Args: (current_completed, total_batches)
```

---

## Peer Review Round 2 (2025-12-06)

Codex and Gemini reviewed the updated plan with enhancements.

### High: Off-by-One Batch Reporting (Codex)

**Problem:** Service pattern uses `batch {current+1}/{total}` but callback already passes incremented count (1-indexed), causing first batch to display "2/10".

**Fix:** Use `batch {current}/{total}` in service layer:
```python
# WRONG - double increment
async def on_bug_batch(current: int, total: int) -> None:
    await progress.report(2, 4, f"Refreshing bugs: batch {current+1}/{total}...")

# CORRECT - current is already 1-indexed from repository
async def on_bug_batch(current: int, total: int) -> None:
    await progress.report(2, 4, f"Refreshing bugs: batch {current}/{total}...")
```

### Medium: CancelledError Must Propagate (Codex)

**Problem:** `safe_batch_callback()` catches all `Exception`, which includes `asyncio.CancelledError`. This would swallow cancellation signals.

**Fix:** Re-raise `CancelledError`:
```python
async def safe_batch_callback(
    callback: BatchProgressCallback | None,
    current: int,
    total: int,
) -> None:
    if callback is None:
        return
    try:
        await callback(current, total)
    except asyncio.CancelledError:
        raise  # Must propagate cancellation
    except Exception as e:
        logger.debug(f"Progress callback failed (non-fatal): {e}")
```

### Medium: Logger Must Be Defined (Codex)

**Problem:** Helper uses `logger.debug()` but no logger is defined in the plan.

**Fix:** Add to `utilities/progress.py`:
```python
import logging

logger = logging.getLogger(__name__)
```

### Low: Export via `__all__` (Codex)

**Problem:** Phase 0 doesn't mention updating `__all__` in `utilities/__init__.py`.

**Fix:** Update exports:
```python
__all__ = [
    "BatchProgressCallback",
    "ProgressReporter",
    "safe_batch_callback",
]
```

### Low: Test File Naming Collision (Gemini)

**Problem:** `tests/unit/test_multi_test_report_service.py` already exists. Adding `tests/services/test_multi_test_report_service.py` causes confusion.

**Fix:** Rename to `tests/services/test_multi_test_report_service_progress.py`.

### Additional Test Cases Needed (Codex)

Add to `tests/unit/test_progress_helpers.py`:
1. Callback raising generic exception is swallowed and logged
2. `CancelledError` is propagated (not swallowed)
3. Batch strings render correctly (no off-by-one)

---

## Validation Review (2025-12-06)

Code validation against actual implementation identified these enhancements.

### Enhancement 1: DRY - Shared Callback Helper

**Problem:** The defensive try/except pattern for callbacks would be duplicated in 3 repositories.

**Solution:** Add helper to `utilities/progress.py`:
```python
import asyncio
import logging

logger = logging.getLogger(__name__)

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
    if callback is None:
        return
    try:
        await callback(current, total)
    except asyncio.CancelledError:
        raise  # Must propagate cancellation
    except Exception as e:
        logger.debug(f"Progress callback failed (non-fatal): {e}")
```

**Usage in repositories:**
```python
from testio_mcp.utilities.progress import safe_batch_callback

# Thread-safe counter (PEP 703 future-proof)
counter_lock = asyncio.Lock()
completed_batches = 0

async def tracked_batch(batch: list[int]) -> BatchResult:
    nonlocal completed_batches
    result = await refresh_batch_with_locks(batch)
    async with counter_lock:
        completed_batches += 1
        current = completed_batches
    await safe_batch_callback(on_batch_progress, current, len(batches))
    return result
```

### Enhancement 2: Export Type Alias

**Requirement:** Update `utilities/__init__.py` to export the new type alias:
```python
from testio_mcp.utilities.progress import (
    BatchProgressCallback,
    ProgressReporter,
    safe_batch_callback,
)
```

### Enhancement 3: Missing Service Test File

**Gap identified:** No progress-related tests exist for `MultiTestReportService`.

**Note:** `tests/unit/test_multi_test_report_service.py` already exists for basic functionality.

**Action:** Add to Phase 4 checklist:
- `tests/services/test_multi_test_report_service_progress.py` (NEW FILE - avoids naming collision)

### Enhancement 4: Document Test Metadata Assumption

**Observation:** `MultiTestReportService.get_product_quality_report()` calls `bug_repo.get_bugs_cached_or_refresh()` but does NOT call `test_repo.get_tests_cached_or_refresh()`.

**Design decision:** This is intentional. The service assumes test metadata was synced via:
1. Background sync (hourly)
2. Explicit `sync_data()` call before report generation

**Action:** Add docstring note to `get_product_quality_report()`:
```python
Note:
    This method refreshes bug data on-demand but assumes test metadata
    is already cached via background sync or explicit sync_data() call.
    For fresh test metadata, call sync_data(product_ids=[...]) first.
```

### Enhancement 5: Future-Proof Counter Pattern (Implemented)

**Observation:** The `nonlocal completed_batches` counter pattern relies on Python's GIL for thread safety.

**Risk:** Python 3.13+ introduces free-threading (PEP 703), which could cause race conditions.

**Decision:** Future-proof now. The `asyncio.Lock()` is cheap and makes the code correct regardless of GIL state.

**Pattern to use:**
```python
import asyncio

# Lock created once per method invocation (not shared across calls)
counter_lock = asyncio.Lock()
completed_batches = 0

async def tracked_batch(batch: list[int]) -> BatchResult:
    nonlocal completed_batches
    result = await refresh_batch_with_locks(batch)
    async with counter_lock:
        completed_batches += 1
        current = completed_batches
    await safe_batch_callback(on_batch_progress, current, len(batches))
    return result
```

**Status:** Include in Phase 1 implementation.

---

## Design Decisions

### Why Callbacks at Repository Level?

| Approach | Pros | Cons |
|----------|------|------|
| **Callbacks** | Generic, reusable, no message coupling | Slightly more complex wiring |
| **ProgressReporter in Repo** | Simpler | Couples repo to MCP, message strings in data layer |

**Decision:** Callbacks keep repositories pure. Services own the user-facing messages.

### Throttling Strategy

| Level | Throttle | Rationale |
|-------|----------|-----------|
| Phase boundaries | `force=True` | Always show phase transitions |
| Batch progress | `force=False` (0.5s) | Prevent spam for rapid batches |
| Completion | `force=True` via `complete()` | Always show final status |

### Error Handling

Progress reporting is **best-effort**:
- Callback errors are logged at DEBUG level
- Never abort the operation due to progress failure
- `ProgressReporter.noop()` used when no context available

---

## Estimated Effort

| Phase | Files | Time |
|-------|-------|------|
| Repository callbacks | 3 | ~1.5 hours |
| Service integration | 2 | ~1 hour |
| Tool injection | 2 | ~30 min |
| Shared helper (`safe_batch_callback`) | 1 | ~15 min |
| Tests | 8 | ~2.5 hours |
| **Total** | 16 | **~5.75 hours** |

---

## Future Considerations

### Additional Candidates

These tools could benefit from progress if they become slow:

| Tool | Current Duration | Add Progress? |
|------|------------------|---------------|
| `list_bugs` | 2-10s | Maybe (if >5s common) |
| `get_test_summary` | 1-2s | No (too fast) |
| `search` | <1s | No (SQLite only) |

### Client Support Status

| Client | Progress Display | Notes |
|--------|------------------|-------|
| Claude Code | Not yet | [Issue #4157](https://github.com/anthropics/claude-code/issues/4157) |
| Cursor | Buggy | [Bug #134794](https://forum.cursor.com/t/bug-report-cursor-ui-not-displaying-mcp-progress-updates/134794) |
| CopilotKit | Supported | Tool status displayed in UI |
| MCP Inspector | Partial | EventStream shows notifications |

Progress implementation is future-ready for when clients add UI support.

---

## References

- [AG-UI / CopilotKit Exploration](./agui-copilotkit-exploration.md) - Original progress notifications implementation
- [ProgressReporter Utility](../../src/testio_mcp/utilities/progress.py) - Transport-agnostic progress reporting
- [ADR-017](../architecture/adrs/ADR-017-background-sync-optimization-pull-model.md) - Read-through caching pattern
