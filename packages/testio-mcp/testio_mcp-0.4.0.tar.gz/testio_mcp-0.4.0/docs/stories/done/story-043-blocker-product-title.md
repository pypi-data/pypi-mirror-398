# BLOCKING TASK: Normalize Product.title Column

**Priority:** HIGH - Blocks STORY-043 (Analytics Service)
**Epic:** EPIC-007 (Generic Analytics Framework)
**Estimated Time:** 30-45 minutes

---

## Problem

The `Product` ORM model stores all data in a JSON `data` field without normalized columns:

```python
# Current Product model (src/testio_mcp/models/orm/product.py)
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    data: str = Field()  # JSON blob - NO title column!
    last_synced: datetime | None = Field(default=None)
    features_synced_at: datetime | None = Field(default=None)
```

This prevents analytics queries from grouping by product name:
- ❌ Cannot use `Product.title` in SQLAlchemy queries
- ❌ Would require slow `json_extract()` function calls
- ❌ Cannot index for performance

**Contrast with Feature model** (already normalized):
```python
class Feature(SQLModel, table=True):
    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    title: str = Field()  # ✅ Normalized column - works great!
    description: str | None = Field(default=None)
    # ... other normalized fields
    raw_data: str = Field()  # JSON backup
```

---

## Acceptance Criteria

### AC1: Add Product.title Column to ORM Model

**File:** `src/testio_mcp/models/orm/product.py`

**Changes:**
```python
class Product(SQLModel, table=True):
    """Product entity with customer isolation."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)

    # NEW: Denormalized fields for analytics (extracted from data JSON)
    title: str = Field()  # Product name/title from JSON

    data: str = Field()  # JSON stored as TEXT in SQLite (backup)
    last_synced: datetime | None = Field(default=None)
    features_synced_at: datetime | None = Field(default=None)
```

**Validation:**
- [ ] `title` field added with `str` type (not nullable)
- [ ] Field matches Feature.title pattern
- [ ] mypy passes: `uv run mypy src/testio_mcp/models/orm/product.py --strict`

---

### AC2: Create Alembic Migration

**Command:** `uv run alembic revision --autogenerate -m "Add Product.title column"`

**Expected Migration:**
```python
# alembic/versions/XXXX_add_product_title_column.py
def upgrade() -> None:
    # Add title column (nullable initially for backfill)
    op.add_column('products', sa.Column('title', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('products', 'title')
```

**Validation:**
- [ ] Migration file created
- [ ] Migration adds `title` column
- [ ] Column is nullable initially (for safe backfill)
- [ ] Downgrade removes column cleanly

---

### AC3: Update ProductRepository to Extract title

**File:** `src/testio_mcp/repositories/product_repository.py`

**Find:** `upsert_product()` or `insert_product()` method

**Pattern to follow** (from FeatureRepository):
```python
# Example from src/testio_mcp/repositories/feature_repository.py:125-140
def _upsert_feature(self, session: Session, feature_data: dict, product_id: int) -> None:
    """Upsert feature record with denormalized fields."""
    feature = Feature(
        id=feature_data["id"],
        product_id=product_id,
        title=feature_data.get("title", ""),  # ✅ Extract from JSON
        description=feature_data.get("description"),
        howtofind=feature_data.get("howtofind"),
        # ... other fields
        raw_data=json.dumps(feature_data),  # ✅ Backup full JSON
    )
    session.merge(feature)
```

**Changes needed:**
```python
# In ProductRepository.upsert_product() or similar method
product = Product(
    id=product_data["id"],
    customer_id=customer_id,
    title=product_data.get("title", "Untitled Product"),  # NEW: Extract title
    data=json.dumps(product_data),  # Keep JSON backup
    last_synced=datetime.now(UTC),
    # ... other fields
)
session.merge(product)
```

**Validation:**
- [ ] Repository extracts `title` from product JSON
- [ ] Falls back to "Untitled Product" if missing
- [ ] Existing `data` JSON backup still stored
- [ ] Unit test added verifying title extraction

---

### AC4: Backfill Existing Products

**Create script:** `scripts/backfill_product_title.py`

**Pattern to follow** (from STORY-042):
```python
# See tools/backfill_test_features.py for reference pattern
import asyncio
import json
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.persistent_cache import PersistentCache
from testio_mcp.models.orm import Product

async def backfill_product_titles(cache: PersistentCache) -> None:
    """Backfill Product.title from data JSON."""
    async with cache.async_session_maker() as session:
        result = await session.exec(select(Product))
        products = result.all()

        updated = 0
        for product in products:
            data = json.loads(product.data)
            product.title = data.get("title", "Untitled Product")
            session.add(product)
            updated += 1

            if updated % 100 == 0:
                await session.commit()
                print(f"Updated {updated} products...")

        await session.commit()
        print(f"✅ Backfilled {updated} products")

if __name__ == "__main__":
    cache = PersistentCache()
    asyncio.run(backfill_product_titles(cache))
```

**Run:**
```bash
uv run python scripts/backfill_product_title.py
```

**Validation:**
- [ ] Script backfills all existing products
- [ ] No NULL titles remain
- [ ] Script is idempotent (safe to re-run)
- [ ] Progress printed every 100 products

---

### AC5: Make Column NOT NULL (Second Migration)

**After backfill completes:**

```bash
uv run alembic revision -m "Make Product.title NOT NULL"
```

**Migration:**
```python
def upgrade() -> None:
    # Now that all products have titles, make NOT NULL
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('title', nullable=False)
```

**Validation:**
- [ ] Second migration created
- [ ] Column constraint changed to NOT NULL
- [ ] Alembic upgrade works cleanly

---

### AC6: Run Full Test Suite

**Commands:**
```bash
# Run all tests
uv run pytest

# Verify type checking
uv run mypy src/testio_mcp/models/orm/product.py --strict
```

**Validation:**
- [ ] All existing tests pass
- [ ] No regressions introduced
- [ ] Type checking passes

---

## Technical Context

### Why This Approach?

**Denormalized Column Strategy:**
- ✅ **Fast queries:** Indexed column vs. slow JSON extraction
- ✅ **Type safe:** SQLAlchemy knows it's a string
- ✅ **Analytics friendly:** Can group by, sort by, filter by title
- ✅ **Matches existing pattern:** Feature model already does this
- ✅ **JSON backup preserved:** `data` field unchanged for backward compatibility

**Migration Safety:**
1. Add column as nullable (safe for existing rows)
2. Backfill all rows
3. Make NOT NULL (enforces future inserts)

### Files to Reference

**Similar implementations:**
- `src/testio_mcp/models/orm/feature.py` - Normalized title pattern
- `src/testio_mcp/repositories/feature_repository.py:125-140` - Title extraction pattern
- `tools/backfill_test_features.py` - Backfill script pattern
- `alembic/versions/*_add_test_features_table.py` - Migration pattern

### Unblocks

Once complete, STORY-043 can add product dimension:
```python
# In analytics_service.py _build_dimension_registry()
"product": DimensionDef(
    key="product",
    description="Group by Product",
    column=Product.title,  # ✅ Now works!
    id_column=Product.id,
    join_path=[TestFeature, Feature, Product],
    example="Canva, Zoom, Slack",
),
```

---

## Definition of Done

- [x] AC1: Product.title column added to ORM model
- [x] AC2: Migration created and tested
- [x] AC3: Repository extracts title from JSON
- [x] AC4: Backfill script created and executed
- [x] AC5: Column made NOT NULL
- [x] AC6: All tests pass (86 integration tests passing)
- [x] mypy --strict passes
- [x] Integration test failures fixed (NULL handling for enable_* fields)

## Completion Notes

**Date Completed:** 2025-11-25

**Summary:**
Successfully normalized Product.title column and resolved all integration test failures. The blocker is fully resolved - STORY-043 can now add the product dimension to the analytics service.

**Key Achievements:**
1. ✅ Added Product.title column (denormalized from JSON)
2. ✅ Created two-phase migration strategy (nullable → backfill → NOT NULL)
3. ✅ Updated ProductRepository to extract title during upsert
4. ✅ Backfilled 6 existing products
5. ✅ Fixed integration test failures (NULL handling bug in test_repository.py)
6. ✅ All 86 integration tests passing

**Integration Test Fix:**
The test failures were caused by the API returning `null` for `enable_content`, `enable_default`, `enable_visual` fields. The repository code used `.get("field", False)` which returns `None` when the key exists with a null value. Fixed by changing to `.get("field") or False`.

**Files Modified:**
- src/testio_mcp/models/orm/product.py
- src/testio_mcp/repositories/product_repository.py
- src/testio_mcp/repositories/test_repository.py (NULL handling fix)
- alembic/versions/f2ddd8df0212_add_product_title_column.py
- alembic/versions/24c44c502fc0_make_product_title_not_null.py
- scripts/backfill_product_title.py
- tests/integration/test_startup_migrations.py (migration version update)
- tests/unit/test_persistent_cache.py
- tests/unit/test_repositories_feature.py
- tests/unit/models/orm/test_models.py

**Unblocks:** STORY-043 Analytics Service can now add product dimension

---

## Copy-Paste Command Summary

```bash
# 1. Update Product model (manual edit)
# 2. Create migration
uv run alembic revision --autogenerate -m "Add Product.title column"

# 3. Review migration file
# 4. Apply migration
uv run alembic upgrade head

# 5. Update ProductRepository (manual edit)
# 6. Create backfill script (manual create scripts/backfill_product_title.py)
# 7. Run backfill
uv run python scripts/backfill_product_title.py

# 8. Create NOT NULL migration
uv run alembic revision -m "Make Product.title NOT NULL"

# 9. Review and apply
uv run alembic upgrade head

# 10. Verify
uv run pytest
uv run mypy src/testio_mcp/models/orm/product.py --strict

# 11. Commit
git add .
git commit -m "feat(epic-007): Normalize Product.title for analytics (STORY-043 blocker)"
```

---

**Ready to copy-paste to another agent!** 🚀
