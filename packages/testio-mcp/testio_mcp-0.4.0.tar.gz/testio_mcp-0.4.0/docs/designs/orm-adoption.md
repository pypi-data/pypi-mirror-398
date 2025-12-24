# Design: ORM Adoption (SQLModel)

## 1. Context
The `testio-mcp` server currently uses raw SQL with `aiosqlite` for all database interactions. As we implement the "Data Intelligence Layer" (Epic 005), the data model is becoming significantly more complex:
*   **New Entities:** `Features`, `User Stories`, `Test Features` (Junction).
*   **Relationships:** 1:N (Product -> Features), M:N (Tests <-> Features), 1:N (Test -> Bugs).
*   **Queries:** We need to perform complex joins to answer questions like "Show me bugs for features in the 'Checkout' section."

## 2. Problem Statement
Continuing with raw SQL presents several challenges:
*   **Complexity:** Manually writing `JOIN` statements and mapping rows to dictionaries is error-prone and verbose.
*   **Type Safety:** Raw SQL queries return untyped tuples/rows, losing the benefits of our Pydantic models until manual conversion.
*   **Schema Management:** We currently use manual `CREATE TABLE IF NOT EXISTS` statements. As the schema evolves, managing migrations manually becomes risky.
*   **Refactoring:** Renaming columns or changing relationships requires searching and replacing raw strings across the codebase.

## 3. Proposed Solution: SQLModel
We propose adopting **[SQLModel](https://sqlmodel.tiangolo.com/)**, which combines Pydantic and SQLAlchemy.

### Why SQLModel?
*   **Pydantic Integration:** We already use Pydantic heavily. SQLModel classes *are* Pydantic models, allowing us to reuse them for API responses and validation.
*   **Async Support:** Built on SQLAlchemy 1.4/2.0, it supports `asyncio` natively.
*   **Relationship Management:** Handles fetching related entities (e.g., `test.features`) automatically or via explicit joins.
*   **Migration Support:** Integrates with **Alembic** for auto-generating schema migrations.

## 4. Analysis

| Feature | Raw SQL (Current) | SQLModel (Proposed) |
| :--- | :--- | :--- |
| **Query Writing** | Manual strings, high control, verbose | Pythonic expressions, type-checked |
| **Relationships** | Manual JOINs and ID mapping | Object-oriented traversal (`test.features`) |
| **Type Safety** | None (until manual conversion) | High (static analysis support) |
| **Performance** | Fastest (minimal overhead) | Slight overhead (usually negligible for SQLite) |
| **Migrations** | Manual SQL scripts | Auto-generated via Alembic |
| **Dependencies** | `aiosqlite` | `sqlmodel`, `alembic` |

## 5. Migration Strategy
We will adopt a **"Refactor First"** strategy. We will migrate the entire existing codebase to SQLModel/Alembic *before* introducing any new entities. This ensures a stable foundation and avoids maintaining two database access patterns simultaneously.

### Phase 1: Infrastructure & Parity (Epic 006)
1.  **Setup:** Install `sqlmodel`, `alembic`. Configure `AsyncEngine`.
2.  **Modeling:** Define SQLModel classes for *existing* entities (`Product`, `Test`, `Bug`, `SyncEvent`).
3.  **Refactor:** Replace `PersistentCache` (raw SQL) with Repositories (`ProductRepository`, `TestRepository`).
4.  **Migration:** Generate the baseline Alembic migration from the existing schema.

### Phase 2: Enhancement (Epic 005)

**Prerequisites:**
*   Epic 006 fully complete: All repositories using AsyncSession, tests passing, Alembic baseline migration applied.
*   Performance validated: No regressions in query times (list_tests ~10ms).

**New Entities:**
1.  Define SQLModel classes in `src/testio_mcp/models/orm/`:
    - `Feature` (1:N relationship with Product)
    - `UserStory` (1:N relationship with Feature)
    - `User` (referenced by Bugs and Tests)
    - `TestFeature` (M:N junction table linking Tests ↔ Features)

**Relationship Patterns:**

*SQLModel Relationship Fields (with proper imports):*
```python
# src/testio_mcp/models/orm/product.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.feature import Feature

class Product(SQLModel, table=True):
    id: int = Field(primary_key=True)
    # ... other fields ...
    features: list[Feature] = Relationship(back_populates="product")

# src/testio_mcp/models/orm/feature.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.product import Product
    from testio_mcp.models.orm.test import Test

# Import TestFeature directly - breaks circular dependency
from testio_mcp.models.orm.test_feature import TestFeature

class Feature(SQLModel, table=True):
    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    # ... other fields ...
    product: Product = Relationship(back_populates="features")
    tests: list[Test] = Relationship(
        back_populates="features",
        link_model=TestFeature  # Class reference, not string!
    )
```

*Querying Patterns:*
- **Lazy Loading (default):** `feature.tests` triggers separate query when accessed.
- **Eager Loading (recommended for lists):** Use `select(Feature).options(selectinload(Feature.tests))` to avoid N+1 queries.
- **Direct Joins:** For filtering, use `.join()` explicitly instead of traversing relationships.
- **Performance Testing:** Always benchmark relationship queries with cold/warm cache to detect N+1 issues.

*Junction Table Pattern (M:N):*

**CRITICAL: Junction tables MUST be in their own module to avoid circular imports.**

```python
# src/testio_mcp/models/orm/test_feature.py
# Isolated module - imported by both Feature and Test, imports neither

from sqlmodel import Field, SQLModel

class TestFeature(SQLModel, table=True):
    """Junction table linking Tests to Features (M:N).

    IMPORTANT: Must be in own module. Both Feature and Test import this,
    but this module imports neither, breaking circular dependency.
    """
    __tablename__ = "test_features"

    test_id: int = Field(foreign_key="tests.id", primary_key=True)
    feature_id: int = Field(foreign_key="features.id", primary_key=True)
```

- `TestFeature` defined as explicit model with composite primary key.
- SQLModel `link_model` parameter uses **class reference** (not string).
- Populated during test sync: Parse `test.features` from API response and insert rows.
- Enables bidirectional queries: `feature.tests` and `test.features`.

**Data Migration:**

**Prerequisites (from Epic 006):**
- Epic 006 baseline migration merged to main
- `alembic heads` returns single head (Epic 006 baseline)
- `alembic current` shows at Epic 006 baseline revision

**Migration Generation:**
1.  Verify prerequisites before generating:
    ```bash
    # Must return single head at Epic 006 baseline
    alembic heads
    alembic current
    # Must return empty (no raw SQL)
    grep -r "aiosqlite.Connection" src/
    ```

2.  Generate Alembic migration for new tables:
    ```bash
    # This will chain from Epic 006 baseline as parent
    alembic revision --autogenerate -m "Add Features, UserStories, Users, TestFeatures"
    ```

3.  Review migration file to ensure:
    - `down_revision` references Epic 006 baseline (documented in Epic 006)
    - Foreign key constraints are correct
    - Indexes added for common queries:
        - `idx_features_product_id`, `idx_features_section_id`
        - `idx_user_stories_product_id`, `idx_user_stories_section_id`, `idx_user_stories_feature_id`
    - Junction table has composite primary key
    - JSON columns use `sa.JSON()` type

4.  Test migration path:
    ```bash
    # Test upgrade
    alembic upgrade head
    # Test downgrade to Epic 006 baseline
    alembic downgrade -1
    # Verify downgrade works
    alembic current
    ```

5.  Verify single head maintained:
    ```bash
    # Must still return single head after migration
    alembic heads
    ```

**Sync Integration:**
- Update `PersistentCache.sync_product_tests()` flow:
  1. Sync Products (existing)
  2. **NEW:** Sync Features (`FeatureRepository.sync_features(product_id)`)
  3. **NEW:** Sync User Stories (`UserStoryRepository.sync_user_stories(product_id)`)
  4. Sync Tests (existing)
  5. **NEW:** Populate TestFeatures junction table during test sync

## 6. Recommendation
**Proceed with SQLModel adoption now.**
The complexity cost of adding it is lower than the technical debt of writing complex M:N join queries in raw SQL for the new features. It aligns with our goal of building a robust "Data Intelligence Layer."
