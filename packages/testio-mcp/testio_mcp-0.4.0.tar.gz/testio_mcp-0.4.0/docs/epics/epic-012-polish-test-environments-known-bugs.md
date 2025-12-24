# TestIO MCP - Epic 012 Polish: Test Environments and Known Bugs

**Author:** leoric
**Date:** 2025-11-30
**Project Level:** Brownfield Enhancement
**Target Scale:** Production MCP Server

---

## Overview

This epic addresses missing data fields, adding test environment tracking and known bug status to the TestIO MCP Server. The changes span database schema, repository layer, service layer, and MCP tools.

**Epic Count:** 1 (single focused enhancement)
**Story Count:** 7 stories (STORY-069 through STORY-075)

---

## Functional Requirements Inventory

| FR | Description | Source |
|----|-------------|--------|
| FR1 | Store test environment information (id + title) in `tests` table | Planning Doc |
| FR2 | Store known bug status (boolean) in `bugs` table | Planning Doc |
| FR3 | Expose `test_environment` and `known_bug` as analytics dimensions | Planning Doc |
| FR4 | Surface `test_environment` in `get_test_summary`, `list_tests`, `get_product_quality_report` | Planning Doc |
| FR5 | Surface `known_bugs_count` in test summary bug statistics | Planning Doc |
| FR6 | Database migration with backfill for existing data | Planning Doc |
| FR7 | Fix read paths to thread new columns through repository layer | Planning Doc (Codex Findings) |

---

## FR Coverage Map

| Epic | FRs Covered |
|------|-------------|
| Epic 012 | FR1, FR2, FR3, FR4, FR5, FR6, FR7 |

---

## Epic 012: Test Environments and Known Bugs

**Goal:** Enable users to analyze test quality by environment and identify known/expected bugs, providing deeper insights into testing patterns and bug triage.

**User Value:** CSMs and QA leads can now:
- Filter and group quality reports by test environment (Production, Staging, QA)
- Distinguish between new bugs and known/expected issues
- Make better triage decisions with complete bug context

---

### STORY-069: Add Database Columns for Test Environment and Known Bug

As a **developer**,
I want **the database schema to include test_environment (JSON) and known (BOOLEAN) columns**,
So that **these fields can be persisted and queried efficiently**.

**Acceptance Criteria:**

**Given** the existing database schema
**When** the migration runs
**Then** the `tests` table has a new `test_environment` column (JSON, nullable)
**And** the `bugs` table has a new `known` column (BOOLEAN, NOT NULL, server_default=0)

**Given** existing test records with `test_environment` in their `data` JSON blob
**When** the migration backfill runs
**Then** the `test_environment` column is populated with `{id, title}` extracted from `data`

**Given** existing bug records with `known` in their `raw_data` JSON blob
**When** the migration backfill runs
**Then** the `known` column is populated from `raw_data` (defaulting to FALSE if absent)

**Prerequisites:** None (first story)

**Technical Notes:**
- ORM changes in `test.py` and `bug.py`
- Use `server_default="0"` for `known` column to handle concurrent inserts during migration
- Backfill SQL uses `json_extract()` for SQLite
- Use `batch_alter_table` for SQLite DROP COLUMN compatibility in downgrade

**Files to Modify:**
- `src/testio_mcp/models/orm/test.py`
- `src/testio_mcp/models/orm/bug.py`
- `alembic/versions/xxxx_add_test_env_and_known_bug.py` (new)

---

### STORY-070: Update Repository Write Paths for New Columns

As a **developer**,
I want **the repository layer to extract and store test_environment and known on writes**,
So that **new synced data populates the new columns correctly**.

**Acceptance Criteria:**

**Given** a test API response containing `test_environment: {id: 123, title: "Production", ...}`
**When** `TestRepository.insert_test()` or `update_test()` is called
**Then** the `test.test_environment` column stores `{id: 123, title: "Production"}` (only id + title for security)

**Given** a bug API response containing `known: true`
**When** `BugRepository._write_bugs_to_db()` or `refresh_bugs()` is called
**Then** the `bug.known` column is set to `True`

**Given** a bug API response missing the `known` field
**When** `BugRepository` writes the bug
**Then** the `bug.known` column defaults to `False`

**Prerequisites:** STORY-069 (database columns exist)

**Technical Notes:**
- Security: Extract only `id` and `title` from `test_environment` - discard other fields
- SQLAlchemy handles JSON serialization automatically for `test_environment`
- Update UPSERT `set_` clause in `_write_bugs_to_db` to include `known`

**Files to Modify:**
- `src/testio_mcp/repositories/test_repository.py` (~line 120, ~line 252)
- `src/testio_mcp/repositories/bug_repository.py` (~line 706, ~line 853)
- `src/testio_mcp/transformers/bug_transformers.py` (BugOrmData TypedDict)

---

### STORY-071: Update Repository Read Paths to Thread New Columns

As a **developer**,
I want **the repository layer to surface test_environment and known on reads**,
So that **services receive the new fields without manual JSON parsing**.

**Acceptance Criteria:**

**Given** a test record with `test_environment` column populated
**When** `TestRepository.get_test_with_bugs()` is called
**Then** the returned dict includes `test_environment` from the column (not from `data` JSON)

**Given** a test record with `test_environment` column populated
**When** `TestRepository.query_tests()` is called
**Then** each returned test dict includes `test_environment` from the column

**Given** a bug record with `known` column populated
**When** `BugRepository.get_bugs()` or `get_bugs_cached_or_refresh()` is called
**Then** the returned bug dict includes `known` from the column (overriding any JSON value)

**Prerequisites:** STORY-070 (write paths populate columns)

**Technical Notes:**
- Override `data["test_environment"]` with `test.test_environment` (column is source of truth)
- Override `raw_data["known"]` with `bug.known` (column is source of truth)
- This follows the existing pattern for `bug.status` override in `get_bugs_cached_or_refresh`

**Files to Modify:**
- `src/testio_mcp/repositories/test_repository.py` (~line 526, ~line 1033)
- `src/testio_mcp/repositories/bug_repository.py` (~line 106, ~line 576-582)

---

### STORY-072: Update DTOs and API Schemas

As a **developer**,
I want **the data transfer objects and API schemas to include test_environment and known fields**,
So that **type safety is maintained throughout the service layer**.

**Acceptance Criteria:**

**Given** the schema definitions
**When** reviewing `ServiceTestDTO`
**Then** it includes `test_environment: dict[str, Any] | None`

**Given** the schema definitions
**When** reviewing `ServiceBugDTO`
**Then** it includes `known: bool = False`

**Given** the API schemas
**When** reviewing `TestSummary` and `TestDetails`
**Then** they include `test_environment: dict[str, Any] | None`

**Given** the API schemas
**When** reviewing `BugSummary`
**Then** it includes `known_bugs_count: int` (default 0)

**Given** the API schemas
**When** reviewing `RecentBug`
**Then** it includes `known: bool` (default False)

**Prerequisites:** STORY-071 (repository provides data)

**Technical Notes:**
- DTOs in `src/testio_mcp/schemas/dtos.py`
- API schemas in `src/testio_mcp/schemas/api/tests.py` and `bugs.py`
- Transformers need updating to map new fields

**Files to Modify:**
- `src/testio_mcp/schemas/dtos.py`
- `src/testio_mcp/schemas/api/tests.py`
- `src/testio_mcp/schemas/api/bugs.py`
- `src/testio_mcp/transformers/test_transformers.py`
- `src/testio_mcp/transformers/bug_transformers.py`

---

### STORY-073: Update Services for Test Environment and Known Bugs

As a **developer**,
I want **the service layer to expose test_environment and known_bugs_count**,
So that **MCP tools can surface these fields to users**.

**Acceptance Criteria:**

**Given** a test with `test_environment` data
**When** `TestService.get_test_summary()` is called
**Then** the response includes `test_environment: {id, title}`

**Given** a test with bugs where some have `known: true`
**When** `TestService.get_test_summary()` is called
**Then** the response bug_summary includes `known_bugs_count` as a separate metric

**Given** tests with `test_environment` data
**When** `TestService.list_tests()` is called
**Then** each test in the response includes `test_environment`

**Prerequisites:** STORY-072 (DTOs and schemas defined)

**Technical Notes:**
- Calculate `known_bugs_count` by filtering bugs where `known == True`
- Add to existing bug severity/platform breakdown in `get_test_summary`

**Files to Modify:**
- `src/testio_mcp/services/test_service.py`

---

### STORY-074: Update Product Quality Report Tool

As a **QA lead**,
I want **the product quality report to include test_environment information**,
So that **I can analyze quality metrics per environment**.

**Acceptance Criteria:**

**Given** a product with tests in different environments
**When** `get_product_quality_report()` is called
**Then** each test in the report includes `test_environment: {id, title}`

**Given** a product quality report output
**When** reviewing the test metrics
**Then** `test_environment` is visible for each test entry

**Prerequisites:** STORY-073 (service layer provides data)

**Technical Notes:**
- Update `TestBugMetrics` Pydantic model
- Thread `test_environment` through report generation

**Files to Modify:**
- `src/testio_mcp/tools/product_quality_report_tool.py`

---

### STORY-075: Add Analytics Dimensions for Test Environment and Known Bug

As a **CSM**,
I want **to query metrics grouped by test environment or known bug status**,
So that **I can analyze patterns across environments and understand known issue impact**.

**Acceptance Criteria:**

**Given** the analytics capabilities
**When** `get_analytics_capabilities()` is called
**Then** `test_environment` and `known_bug` appear as available dimensions

**Given** tests with different `test_environment` values
**When** `query_metrics(dimensions=['test_environment'], metrics=['bug_count'])` is called
**Then** results are grouped by environment name (title)

**Given** bugs with different `known` values
**When** `query_metrics(dimensions=['known_bug'], metrics=['bug_count'])` is called
**Then** results show bug counts grouped by `true` vs `false`

**Given** tests where `test_environment` is NULL
**When** querying with `test_environment` dimension
**Then** those tests are excluded (proper null filtering)

**Prerequisites:** STORY-069 (columns exist), STORY-071 (data accessible)

**Technical Notes:**
- Use `func.json_extract(Test.test_environment, '$.title')` for grouping
- Cast `id_column` to Integer for proper numeric sorting
- Add proper null checks: `is_not(None)` AND `!= 'null'` (string)
- `known_bug` dimension uses `Bug.known` boolean directly

**Files to Modify:**
- `src/testio_mcp/services/analytics_service.py`

---

## FR Coverage Matrix

| FR | Stories | Verification |
|----|---------|--------------|
| FR1 | STORY-069, STORY-070, STORY-071 | `test_environment` stored and surfaced |
| FR2 | STORY-069, STORY-070, STORY-071 | `known` stored and surfaced |
| FR3 | STORY-075 | Analytics dimensions added |
| FR4 | STORY-073, STORY-074 | Tools expose `test_environment` |
| FR5 | STORY-073 | `known_bugs_count` in bug summary |
| FR6 | STORY-069 | Migration with backfill |
| FR7 | STORY-071 | Read paths fixed (Codex findings) |

---

## Summary

**Epic 012** delivers test environment tracking and known bug status across the full stack:

| Layer | Changes |
|-------|---------|
| **Database** | New columns with backfill migration |
| **Repository** | Write + read path updates |
| **Schemas** | DTOs and API models |
| **Services** | Business logic for new fields |
| **Tools** | MCP tool exposure |
| **Analytics** | Two new dimensions |

**Story Sequence:**
1. STORY-069: Database columns + migration (foundation)
2. STORY-070: Repository writes (populate on sync)
3. STORY-071: Repository reads (surface to services)
4. STORY-072: DTOs/Schemas (type safety)
5. STORY-073: Services (business logic)
6. STORY-074: Tools (user exposure)
7. STORY-075: Analytics (advanced queries)

---

_For implementation: Use the `dev-story` workflow to implement each story sequentially._


## Tech Debt: Repository Read Pattern Standardization

> [!WARNING]
> **This section documents architectural debt to address in a future epic.**
> Epic 011 Polish uses the existing "override" pattern for consistency.

### Current Problem

The repository layer has inconsistent patterns for reading data:

| Entity | Write Path | Read Path | Issue |
|--------|------------|-----------|-------|
| **Test** | Denormalizes to columns (`status`, `title`, `testing_type`, `test_environment`) | Reads `Test.data` JSON blob, ignores columns | Columns unused on read |
| **Bug** | Denormalizes to columns (`status`, `severity`, `title`, `known`) | Reads `raw_data` JSON, manually overrides `status` | Must remember to override each field |
| **Product** | Denormalizes to columns (`title`, `product_type`) | Sometimes uses columns, sometimes parses JSON | Inconsistent |
| **Feature** | Denormalizes to columns (`title`, `description`, `howtofind`) | Sometimes uses columns, sometimes parses `raw_data` | Inconsistent |

### Root Cause

1. **Write path:** Fields are denormalized for indexing/filtering/sorting
2. **Read path:** Code still parses JSON blob and manually overrides individual fields
3. **Result:** Every new denormalized field requires remembering to add override code

### Current Workaround (This Epic)

We follow the existing "override" pattern for `test_environment` and `known`:

```python
# bug_repository.py - existing pattern for status
bug_dict = json.loads(bug_orm.raw_data)
bug_dict["status"] = bug_orm.status  # Override with enriched column value
bug_dict["known"] = bug_orm.known    # NEW: Same pattern for known

# test_repository.py - new override for test_environment
test_dict = json.loads(test.data)
test_dict["test_environment"] = test.test_environment  # Override with sanitized column
```

### Proposed Future Solution

**"Columns as Source of Truth"** - Repositories should:

1. Select full ORM models (not just JSON blob)
2. Build response dicts from column values
3. Fall back to JSON only for non-denormalized fields

```python
# FUTURE: Standardized read pattern
DENORMALIZED_FIELDS = {"id", "status", "title", "severity", "test_environment", "known", ...}

async def get_bug(self, bug_id: int) -> dict[str, Any]:
    bug = await self._get_bug_orm(bug_id)

    # Start with denormalized columns (source of truth)
    result = {
        "id": bug.id,
        "status": bug.status,  # Already enriched
        "title": bug.title,
        "severity": bug.severity,
        "known": bug.known,
        # ... other denormalized fields
    }

    # Merge non-denormalized fields from JSON
    raw = json.loads(bug.raw_data)
    for key, value in raw.items():
        if key not in DENORMALIZED_FIELDS:
            result[key] = value

    return result
```

### Benefits of Standardization

1. **Single source of truth** - Columns are authoritative, no drift risk
2. **No manual overrides** - New columns automatically used
3. **Clearer intent** - Write path denormalizes, read path uses columns
4. **Better performance** - Can skip JSON parsing for common queries

### Suggested Follow-up

Create **Tech Debt Story: Standardize Repository Read Patterns**
- Scope: `test_repository.py`, `bug_repository.py`, `product_repository.py`, `feature_repository.py`
- Effort: ~2-3 days
- Risk: Medium (affects all read paths, needs thorough testing)
- Dependencies: None (can be done independently)
