# Async Session Management & Concurrency Review
**Date:** 2025-11-27
**Context:** Epic 009 (Sync Consolidation) readiness validation
**Reviewers:** Gemini CLI (gemini-2.5-pro), Codex CLI
**Scope:** STORY-062 implementation + decoupled API/DB concurrency pattern

---

## Executive Summary

**Overall Verdict:** Architecture is **sound** but has **5 critical issues** that must be addressed before Epic 009 (SyncService) implementation.

**Key Strengths:**
- ✅ Decoupled API/DB pattern is textbook-correct for I/O-bound + write-serialized databases
- ✅ Per-operation session isolation prevents "closed database" errors
- ✅ Incremental persistence (data + timestamp atomically) is robust for multi-phase sync
- ✅ Resource management via context managers is correct

**Critical Issues Found:**
1. **🔴 HIGH:** Lock inconsistency - asyncio.Semaphore (MCP) vs FileLock (CLI) race condition
2. **🔴 HIGH:** Stale read bug - long-lived session returns cached data after isolated writes
3. **🟡 MEDIUM:** Failure attribution bug - multiple failures misreported to wrong product
4. **🟡 MEDIUM:** Config/docs mismatch - DB semaphore default (1) vs comments (~5)
5. **🟡 MEDIUM:** Missing exception hygiene - no explicit rollback in isolated session error paths

---

## Detailed Findings

### 1. Critical Race Condition: Dual Locking Mechanisms 🔴

**Issue:** MCP/background sync uses `asyncio.Semaphore` (in-process), CLI sync uses `FileLock` (cross-process). These don't coordinate, allowing concurrent writes → SQLite "database is locked" errors.

**Evidence:**
- `cache.py:146-147` - Creates asyncio.Semaphore for MCP server
- CLI uses existing file lock at `~/.testio-mcp/sync.lock`
- No coordination between the two mechanisms

**Impact:** User can trigger MCP `sync_data` while CLI sync runs → database lock errors.

**Recommendation (Gemini):**
```python
# src/testio_mcp/utilities/async_file_lock.py
import asyncio
from filelock import FileLock, Timeout

class AsyncFileLock:
    def __init__(self, lock_file, timeout=10):
        self._lock = FileLock(lock_file, timeout=timeout)
        self._loop = asyncio.get_running_loop()

    async def __aenter__(self):
        await self._loop.run_in_executor(None, self._lock.acquire)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._loop.run_in_executor(None, self._lock.release)
```

**Action:** Replace `asyncio.Semaphore` with `AsyncFileLock` for unified cross-process coordination.

---

### 2. Stale Read Bug After Isolated Writes 🔴

**Issue:** After concurrent writes via isolated sessions, results are read using the long-lived repository session (`self.session`). Because `expire_on_commit=False` and the session stays resident, its identity map can return cached/stale Feature rows, missing inserts from isolated sessions.

**Evidence:**
- `feature_repository.py:648-654` - Reads features after refresh using `self.session`
- `bug_repository.py:536-538` - Same pattern for bugs
- Long-lived session established in `cache.py:294` never expires

**Impact:** "Read from SQLite after refresh" correctness fails under concurrency. Data appears fresh but is actually stale.

**Recommendation (Codex):**
```python
# Option 1: Expire all cached data before read
await self.session.expire_all()
result = await self.session.exec(select(Feature).where(...))

# Option 2 (Better): Use fresh session for read
async with self.cache.async_session_maker() as fresh_session:
    result = await fresh_session.exec(select(Feature).where(...))
    features = result.all()
```

**Action:** Use fresh session for post-refresh reads in both `feature_repository.py:648-654` and `bug_repository.py:536-538`.

---

### 3. Failure Attribution Bug 🟡

**Issue:** Failure tuples carry `pid=None`, then failure mapping uses `results.index((pid, error))` to recover product ID. With multiple failures sharing the same error message, `index()` returns the first match, so later failures are reported against the wrong product ID.

**Evidence:**
```python
# feature_repository.py:623-633
for pid, error in results:
    if pid is not None:
        all_succeeded.append(pid)
    else:
        idx = results.index((pid, error))  # BUG: index finds FIRST match only
        failed_pid = products_to_refresh[idx]
        all_failed.append(failed_pid)
```

**Impact:** Error reporting shows wrong products failed when multiple products fail with same error.

**Recommendation (Codex):**
```python
# Return product_id even on failure
async def refresh_with_lock(product_id: int) -> tuple[int, str | None]:
    try:
        # ... refresh logic ...
        return product_id, None  # Success
    except Exception as e:
        return product_id, str(e)  # Failure with correct product_id

# Process results
for product_id, error in results:
    if error is None:
        all_succeeded.append(product_id)
    else:
        all_failed.append(product_id)
        errors.append(f"Product {product_id}: {error}")
```

**Action:** Refactor return signature to always carry `product_id` through failures.

---

### 4. Config/Docs Mismatch on DB Semaphore 🟡

**Issue:** Comments assume ~5 concurrent DB writers, but `MAX_CONCURRENT_DB_WRITES` defaults to 1. Documentation and operational expectations diverge.

**Evidence:**
- `config.py:66-76` - Default: 1
- `feature_repository.py:547-552` - Comments mention "~5 concurrent"
- `bug_repository.py:408-414` - Same assumption

**Impact:** Throughput expectations for SyncService will be wrong if ops team assumes 5 concurrent writes.

**Recommendation (Codex):**
Either:
1. Raise default to 3-5 if testing shows no lock contention
2. Update all comments to reflect serialized default (1)

**Action:** Align config default with documentation, or vice versa.

---

### 5. Missing Exception Hygiene in Isolated Sessions 🟡

**Issue:** In per-product write blocks, exceptions exit the `async with AsyncSession` without explicit rollback. Context manager closes session, but rollback releases pending transactions earlier and is safer when semaphores are tight.

**Evidence:**
- `feature_repository.py:590-608` - No try/except with rollback
- `bug_repository.py:468-499` - Same pattern

**Recommendation (Codex):**
```python
async with self.cache._write_semaphore:
    async with self.cache.async_session_maker() as isolated_session:
        try:
            # ... DB write logic ...
            await isolated_session.commit()
            return product_id, None
        except Exception as e:
            await isolated_session.rollback()  # Explicit cleanup
            logger.error(f"Failed to write: {e}")
            raise
```

**Action:** Add explicit `rollback()` in exception handlers for both repositories.

---

### 6. Lock Acquisition Without Timeout (Advisory) ⚠️

**Issue:** Batch bug refresh acquires multiple locks concurrently with no timeout. If a lock is held indefinitely (stuck tool request), whole batch waits indefinitely.

**Evidence:**
- `bug_repository.py:451-460` - `await lock.acquire()` with no timeout

**Recommendation (Codex):**
```python
async def acquire_lock_with_timeout(lock: asyncio.Lock, timeout: float = 30.0):
    try:
        await asyncio.wait_for(lock.acquire(), timeout=timeout)
        return lock
    except asyncio.TimeoutError:
        logger.error(f"Lock acquisition timeout after {timeout}s")
        raise
```

**Action:** Add timeout to prevent head-of-line blocking in batch operations.

---

## Epic 009 Readiness Assessment

### ✅ Ready (with fixes)

**Session Management:**
- Per-operation sessions are correct for SyncService
- Repositories own session scope - SyncService stays orchestration-only
- No changes needed to repository session patterns

**Incremental Persistence:**
- Atomic commits (data + timestamp) per entity/batch are robust
- Partial failures are acceptable - repos track their own timestamps
- Next sync picks up from correct checkpoint

**Lock Ordering:**
```
File lock (cross-process)
  → SyncService orchestration
    → Repo per-entity locks
      → DB write semaphore
```

**Do NOT hold file lock while awaiting per-entity locks** (deadlock risk).

### 🔴 Blockers

1. **Fix lock inconsistency** - Unified `AsyncFileLock` required
2. **Fix stale read bug** - Fresh session for post-refresh reads
3. **Fix failure attribution** - Return product_id through failures

### Recommendations for SyncService Implementation

**Session Strategy:**
- Let repositories own session scope per operation
- Do NOT pass shared session into repo methods that use `asyncio.gather()`
- SyncService should create sessions only for its own orchestration queries

**Concurrency Bounds:**
- Existing API semaphore (10) + DB semaphore (1-5) are sufficient
- Do NOT add another DB semaphore at service layer (double-throttling)
- Measure lock contention and adjust `MAX_CONCURRENT_DB_WRITES` if needed

**Error Handling:**
- Partial success is acceptable (per Epic 009 design)
- Add metrics for failed entities
- Surface failures to operators via sync events table

**Performance Tuning:**
- If API/DB latency ratio changes (API faster, DB slower), bump `MAX_CONCURRENT_DB_WRITES` to 2-3
- Monitor lock wait times and timeout rates

---

## Epic 008 Considerations (REST API Parity)

### Semaphore Exhaustion Risk

**Scenario:** 100 concurrent REST `GET /products/{id}/features` requests all trigger refresh.

**Problem:** With semaphore limit of 1, 99 requests block → high latency.

**Mitigations (Gemini):**
1. **Cache-First Reads:** REST endpoints read from cache without implicit refresh
2. **Request Coalescing:** First request acquires lock and refreshes, others wait and read fresh cache
3. **Explicit Refresh:** Use `sync_data` tool as out-of-band refresh, not implicit on GET

### Session Management for FastAPI

**Rule:** FastAPI handlers should:
- Create short-lived sessions per request, OR
- Rely on repository-managed sessions
- **NEVER reuse cache's long-lived session across requests**

**Semaphore Sharing:**
- Keep the same semaphore instance in cache singleton
- MCP and REST share back-pressure
- Avoid per-request semaphores (bypass intended throttle)

---

## Action Items

### Immediate (Before Epic 009)

- [ ] **[HIGH]** Implement `AsyncFileLock` utility for unified cross-process locking
- [ ] **[HIGH]** Replace `asyncio.Semaphore` with `AsyncFileLock` in `cache.py`
- [ ] **[HIGH]** Use fresh session for post-refresh reads in `feature_repository.py:648-654`
- [ ] **[HIGH]** Use fresh session for post-refresh reads in `bug_repository.py:536-538`
- [ ] **[HIGH]** Fix failure attribution in `feature_repository.py:623-633`
- [ ] **[MEDIUM]** Add explicit rollback in exception paths (both repositories)
- [ ] **[MEDIUM]** Align `MAX_CONCURRENT_DB_WRITES` default with documentation

### Advisory (Epic 009 Implementation)

- [ ] Add lock acquisition timeout for batch operations
- [ ] Add metrics for sync failures per entity
- [ ] Document lock ordering in SyncService
- [ ] Add integration tests for concurrent MCP + CLI sync

### Future (Epic 008)

- [ ] Design cache-first REST endpoints
- [ ] Implement request coalescing for identical refresh operations
- [ ] Add FastAPI session management guidelines to CLAUDE.md
- [ ] Consider read/write locks for REST read-heavy workloads (PostgreSQL migration)

---

## References

- **STORY-062:** Async Session Management Refactor
- **Epic 009:** docs/epics/epic-009-sync-consolidation.md
- **Epic 008:** docs/epics/epic-008-mcp-layer-optimization.md
- **CLAUDE.md:** Async Session Management section
- **ARCHITECTURE.md:** Session lifecycle rules

---

## Review Metadata

**Token Usage:**
- Gemini: 15,932 tokens (2,619 cached)
- Codex: 425,063 tokens (354,176 cached)
- Total: ~441k tokens

**Duration:**
- Gemini: 45.2s
- Codex: 92.1s
- Total: ~137s

**Models:**
- Gemini: gemini-2.5-flash-lite + gemini-2.5-pro
- Codex: Default model

**Continuation IDs:**
- Gemini: `45f2adc8-a4fe-473a-9461-190f33ffd75b` (39 turns remaining)
- Codex: `a59e3ec9-6989-40eb-acea-4f8f2e346797` (39 turns remaining)
