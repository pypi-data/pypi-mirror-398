# Architecture Decision Records - Index

**Last Updated:** 2025-11-26

---

## Active ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-api-client-dependency-injection.md) | API Client Dependency Injection | ✅ Active | 2025-11-04 |
| [ADR-002](ADR-002-concurrency-limits.md) | Concurrency Limits | ✅ Active | 2025-11-04 |
| [ADR-005](ADR-005-response-size-limits.md) | Response Size Limits | ✅ Active | 2025-11-04 |
| [ADR-006](ADR-006-service-layer-pattern.md) | Service Layer Pattern | ✅ Active | 2025-11-04 |
| [ADR-007](ADR-007-fastmcp-context-injection.md) | FastMCP Context Injection | ✅ Active | 2025-11-05 |
| [ADR-011](ADR-011-extensibility-patterns.md) | Extensibility Patterns | ✅ Active | 2025-11-06 |
| [ADR-012](ADR-012-resources-strategy-defer-to-post-mvp.md) | Resources Strategy | ✅ Active | 2025-11-06 |
| [ADR-013](ADR-013-user-story-embedding-strategy.md) | User Story Embedding Strategy | ✅ Active | 2025-11-23 |
| [ADR-015](ADR-015-feature-staleness-and-sync-strategy.md) | Feature Staleness and Sync Strategy | ⚠️ Partial | 2025-11-24 |
| [ADR-016](ADR-016-alembic-migration-strategy.md) | Alembic Migration Strategy | ✅ Active | 2025-11-24 |
| [ADR-017](ADR-017-background-sync-optimization-pull-model.md) | Background Sync Optimization - Pull Model | ✅ Active | 2025-11-26 |

---

## Partially Superseded ADRs

| ADR | Title | Status | Notes | Date |
|-----|-------|--------|-------|------|
| [ADR-015](ADR-015-feature-staleness-and-sync-strategy.md) | Feature Staleness and Sync Strategy | ⚠️ Partial | Sync phases updated by [ADR-017](ADR-017-background-sync-optimization-pull-model.md) | 2025-11-24 |

---

## Superseded ADRs

| ADR | Title | Status | Superseded By | Date |
|-----|-------|--------|---------------|------|
| [ADR-003](ADR-003-pagination-strategy.md) | Pagination Strategy | ❌ Superseded | [STORY-023d](../../stories/done/story-023d-service-refactoring.md) | 2025-11-18 |
| [ADR-004](ADR-004-cache-strategy-mvp.md) | Cache Strategy MVP | ❌ Superseded | [STORY-021](../../stories/done/story-021-local-data-store.md) | 2025-11-18 |
| [ADR-014](ADR-014-pagination-ready-caching-strategy.md) | Pagination-Ready Caching | ❌ Superseded | [STORY-023d](../../stories/done/story-023d-service-refactoring.md) | 2025-11-18 |

---

## Quick Reference

### When to Create New ADRs

Create a new ADR when:
- Changing an existing architectural decision
- Adding new major components (Redis, message queue, etc.)
- Making significant architecture changes (multi-tenancy, write operations, etc.)

### ADR Template

See [ADR-001](ADR-001-api-client-dependency-injection.md) for template structure.

**Key Sections:**
- **Status:** Accepted / Superseded / Deprecated
- **Date:** When the decision was made
- **Context:** Problem statement and alternatives considered
- **Decision:** What was decided and why
- **Consequences:** Positive, negative, and neutral outcomes

---

## ADR Lifecycle

```
Proposed → Accepted → [Active] → Superseded → Archived
                    ↓
                  Rejected
```

**Status Definitions:**
- **✅ Active:** Currently implemented and in use
- **❌ Superseded:** Replaced by newer decision (link to replacement)
- **🚫 Rejected:** Considered but not implemented
- **📋 Proposed:** Under review, not yet decided

---

## References

- **ARCHITECTURE.md:** [Architecture Decision Records Section](../ARCHITECTURE.md#architecture-decision-records)
- **ADR Process:** Follow existing pattern (Context, Decision, Consequences)
- **Supersession Process:** Mark old ADR as superseded, link to replacement story/ADR

---

**Index Version:** 1.0
**Created:** 2025-11-20
**Purpose:** Quick navigation and status tracking for all ADRs
