# Design: Feature & User Story Repositories

**Epic:** 005 (Data Enhancement)
**Date:** November 21, 2025
**Status:** Draft

## 1. Overview

To support advanced analytics (e.g., "Bug Density per Feature", "Test Coverage"), we need to treat `Features` and `User Stories` as first-class entities in our local database. Instead of extracting them from `Test` JSON blobs (which only shows *tested* features), we will fetch them from their dedicated API endpoints to build a complete "Catalog" of what *could* be tested.

## 2. Architecture

We will introduce a **Repository Pattern** using **SQLModel** (as established in Epic 006) to manage the lifecycle of these entities.

### 2.1. The Repository Interface
Repositories will be responsible for:
1.  **Fetching** data from the TestIO Customer API.
2.  **Persisting** data to the local SQLite database.
3.  **Retrieving** data for the Service Layer.

### 2.2. New Repositories

#### `FeatureRepository`
*   **Source:** `GET /products/{product_id}/features`
*   **Storage:** `features` table (Structured columns + `raw_data` JSON)
*   **Key Responsibility:** Maintain the master list of features for a product.

#### `UserStoryRepository`
*   **Source:** `GET /products/{product_id}/user_stories`
*   **Storage:** `user_stories` table (Structured columns + `raw_data` JSON)
*   **Key Responsibility:** Maintain the master list of user stories, linked to Features.

## 3. Data Model

### 3.1. Schema (SQLModel)
We will define these as SQLModel classes in `src/testio_mcp/models/orm/` (see Epic 006 for base configuration).

**Feature Model:**
```python
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.product import Product
    from testio_mcp.models.orm.user_story import UserStory
    from testio_mcp.models.orm.test import Test

# Import TestFeature directly (no TYPE_CHECKING needed - breaks circular import)
from testio_mcp.models.orm.test_feature import TestFeature

class Feature(SQLModel, table=True):
    """Feature entity - represents a testable feature of a product.

    Features can be organized into sections (if product.has_sections=true).
    Features are linked to tests via the TestFeature junction table (M:N).
    """
    __tablename__ = "features"

    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    section_id: Optional[int] = Field(default=None, index=True)  # Null for non-section products
    title: str
    description: Optional[str] = None
    howtofind: Optional[str] = None  # Instructions for testers on how to access this feature
    raw_data: dict = Field(sa_column=JSON())  # Full API response - JSON column for automatic serialization
    last_synced: datetime

    # Relationships
    product: Product = Relationship(back_populates="features")
    user_stories: list[UserStory] = Relationship(back_populates="feature")
    tests: list[Test] = Relationship(back_populates="features", link_model=TestFeature)  # Class reference, not string
```

**UserStory Model:**
```python
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.feature import Feature

class UserStory(SQLModel, table=True):
    """User Story entity - represents a user journey or acceptance criterion.

    User stories belong to features and guide test design.

    NOTE: product_id and section_id are redundant with feature.product_id/section_id
    but enable fast filtering without joins (e.g., "all stories for section X").
    Sync logic MUST validate consistency: feature.product_id == user_story.product_id
    """
    __tablename__ = "user_stories"

    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)  # Direct product link for fast queries
    section_id: Optional[int] = Field(default=None, index=True)     # Section tracking (null for non-section products)
    feature_id: int = Field(foreign_key="features.id", index=True)
    title: str
    requirements: Optional[str] = None  # Acceptance criteria
    raw_data: dict = Field(sa_column=JSON())  # Full API response - JSON column for automatic serialization
    last_synced: datetime

    # Relationships
    feature: Feature = Relationship(back_populates="user_stories")
```

**TestFeature Junction Table (M:N):**

**⚠️ DEFERRED TO FUTURE EPIC:** The TestFeature junction table is **not included in Epic-005 scope**. Test-to-feature relationships will remain in JSON blobs (`test.features` field) for now. This junction table will be added in a future epic once the base ORM architecture (Features, User Stories, Users) is established and proven.

```python
# src/testio_mcp/models/orm/test_feature.py
# IMPORTANT: Isolate in its own module to avoid circular imports
# Both Feature and Test import this module, not vice versa

from sqlmodel import Field, SQLModel

class TestFeature(SQLModel, table=True):
    """Junction table linking Tests to Features (many-to-many relationship).

    Populated during test sync by parsing test.features from API response.
    Enables queries like 'all tests for feature X' and 'all features tested in test Y'.

    IMPORTANT: This model MUST be in its own module (test_feature.py) to avoid
    circular imports between feature.py and test.py. Both models import TestFeature,
    but TestFeature imports neither.
    """
    __tablename__ = "test_features"

    test_id: int = Field(foreign_key="tests.id", primary_key=True)
    feature_id: int = Field(foreign_key="features.id", primary_key=True)

    # Composite primary key enforces one row per test-feature pair
    # No additional fields needed for MVP (can add later: test_result, coverage_percentage, etc.)
```

**Database Indexes:**
Alembic migration will create indexes automatically based on `Field(index=True)`:
- `idx_features_product_id` - For filtering features by product
- `idx_features_section_id` - For section-based feature fetching
- `idx_user_stories_product_id` - For fast product-level story queries
- `idx_user_stories_section_id` - For section-based story queries
- `idx_user_stories_feature_id` - For fetching stories by feature
- Composite primary key on `test_features` creates implicit index

**Data Consistency Validation:**

During sync, repositories MUST validate redundant fields for consistency:

```python
# In UserStoryRepository.sync_user_stories()
async def _validate_story_consistency(
    self, story_data: dict, feature: Feature
) -> None:
    """Ensure user story product/section match parent feature."""
    story_product_id = story_data.get("product_id")
    story_section_id = story_data.get("section_id")

    if story_product_id != feature.product_id:
        raise DataConsistencyError(
            f"User story product_id ({story_product_id}) doesn't match "
            f"feature product_id ({feature.product_id})"
        )

    if story_section_id != feature.section_id:
        logger.warning(
            f"User story section_id ({story_section_id}) doesn't match "
            f"feature section_id ({feature.section_id}). Using feature value."
        )
        # Override with feature's section for consistency
        story_data["section_id"] = feature.section_id
```

## 4. Sync Strategy

The sync process will evolve from a single "Test Sync" to a multi-stage "Product Catalog Sync".

**New Sync Flow:**
1.  **Sync Products:** Fetch all products.
2.  **Sync Catalog (Per Product):**
    *   Call `FeatureRepository.sync_features(product_id)`
    *   Call `UserStoryRepository.sync_user_stories(product_id)`
3.  **Sync Tests:** Fetch tests.
    *   *Enhancement:* When saving a Test, parse its `features` list and populate the `test_features` junction table.

## 5. Benefits

1.  **True Coverage Analysis:** We can now calculate "Untested Features" (Features in DB - Features in `test_features`).
2.  **Independent Lifecycle:** Features can be updated/renamed without needing to re-sync old tests.
3.  **Cleaner Code:** `analyze_yoy_trends.py` stops parsing JSON and starts querying SQL.

## 6. API Integration Details

**RESEARCH COMPLETED:** 2025-11-22
**Script:** `scripts/research_features_api.py`

### 6.1. Section Detection

Products can be organized with or without sections. Detection logic:

```python
def has_sections(product: dict) -> bool:
    """Detect if product uses section-based organization."""
    sections = product.get("sections", [])
    sections_with_default = product.get("sections_with_default", [])

    # Product has sections if:
    # - sections list is non-empty, OR
    # - sections_with_default has more than just the default section
    return len(sections) > 0 or len(sections_with_default) > 1
```

**Key Insight:** All products have at least one "default-section" in `sections_with_default`. Products with actual sections will have 2+ entries.

### 6.2. Features Endpoint Behavior

**TWO DIFFERENT ENDPOINTS** based on product type:

| Product Type | Endpoint Pattern | Status | Verified |
|--------------|------------------|--------|----------|
| **WITHOUT sections** | `GET /products/{id}/features` | 200 OK ✅ | Product 21362: 28 features |
| **WITH sections** | `GET /products/{id}/sections/{sid}/features` | 200 OK ✅ | Product 18559: 288 features |
| WITH sections (wrong) | `GET /products/{id}/features` | 422 Error ❌ | Product 18559: fails |

**Key Finding:** The `/products/{id}/sections/{sid}/features` endpoint is **undocumented** but required for section-enabled products.

**Verified with real API:**
- Product 21362 (NO sections): `GET /products/21362/features` → **28 features** ✅
- Product 18559 (HAS sections): `GET /products/18559/features` → **422 error** ❌
- Product 18559 (HAS sections): `GET /products/18559/sections/19013/features` → **288 features** ✅
- Product 18559 (HAS sections): `GET /products/18559/sections/25618/features` → **21 features** ✅
- Product 24959 (HAS sections): `GET /products/24959/sections/25543/features` → **8 features** ✅

### 6.3. User Stories Endpoint Behavior

**`GET /products/{id}/user_stories{?section_id}`**

| Product Type | Behavior | Status Code | Notes |
|--------------|----------|-------------|-------|
| **Without sections** | Returns ALL user stories | 200 OK | Works perfectly |
| **With sections (no param)** | Returns 500 error | 500 Internal Server Error | API fails without `section_id` |
| **With sections + param** | Returns stories for section | 200 OK | Must iterate sections |

**Verified with real API:**
- Product 21362 (Flourish): No sections → 54 user stories returned ✅
- Product 18559 (Canva): Has sections, no param → 500 error ❌
- Product 18559 with `section_id=19013` → 1,709 user stories returned ✅
- Product 24959 (remove.bg) with `section_id=25543` → 9 user stories returned ✅

### 6.4. Implementation Strategy

**COMPLETE SOLUTION:** Both features and user stories work for all product types! ✅

```python
async def sync_features(self, product_id: int, product: dict) -> None:
    """Sync features with product-type-aware endpoint selection."""
    if has_sections(product):
        # Products WITH sections: Use undocumented /sections/{sid}/features endpoint
        sections = product.get("sections", []) or product.get("sections_with_default", [])
        for section in sections:
            section_id = section["id"]
            response = await self.client.get(
                f"products/{product_id}/sections/{section_id}/features"
            )
            features = response.get("features", [])
            # Store features with section_id...
    else:
        # Products WITHOUT sections: Use standard /products/{id}/features endpoint
        response = await self.client.get(f"products/{product_id}/features")
        features = response.get("features", [])
        # Store features (no section_id)...

async def sync_user_stories(self, product_id: int, product: dict) -> None:
    """Sync user stories with product-type-aware logic."""
    if has_sections(product):
        # Products WITH sections: Must provide section_id parameter
        sections = product.get("sections", []) or product.get("sections_with_default", [])
        for section in sections:
            section_id = section["id"]
            response = await self.client.get(
                f"products/{product_id}/user_stories",
                params={"section_id": section_id}
            )
            stories = response.get("user_stories", [])
            # Store stories with section_id...
    else:
        # Products WITHOUT sections: Single call without section_id
        response = await self.client.get(f"products/{product_id}/user_stories")
        stories = response.get("user_stories", [])
        # Store stories (no section_id)...
```

**Key Implementation Notes:**

1. **Complete coverage:** Both features and user stories work for ALL product types ✅
2. **Different endpoints:** Section-enabled products require different endpoint patterns
3. **Section detection:** Use `has_sections()` helper to determine which endpoint to use
4. **No workarounds needed:** All data accessible via proper API endpoints

**Performance Considerations:**
- Non-section product: 1 API call for features + 1 for user stories = 2 total
- Section product (2 sections): 2 API calls for features + 2 for user stories = 4 total
- Use existing concurrency control (semaphore) to avoid overwhelming API

### 6.5. Pagination

**No pagination observed** in API responses or documentation for these endpoints. All results returned in single response.

## 7. Implementation Plan (Draft)

1.  **Prerequisite:** Complete Epic 006 (ORM Refactor).
2.  **Schema Migration:** Create Alembic migration for new tables.
2.  **Client Update:** Add methods to `TestIOClient` for `get_features` and `get_user_stories`.
3.  **Repository Implementation:** Create `src/testio_mcp/repositories/`.
4.  **Service Integration:** Update `ProductService` to orchestrate the catalog sync.
