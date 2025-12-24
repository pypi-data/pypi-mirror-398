---
story_id: STORY-035B
epic_id: EPIC-005
title: User Stories Repository & Sync
status: superseded
created: 2025-11-23
superseded_by: ADR-013
superseded_date: 2025-11-23
dependencies: [STORY-035A]
priority: deferred
parent_epic: Epic 005 - Data Enhancement and Serving
---

## ⚠️ STORY SUPERSEDED

**This story has been superseded by ADR-013 (User Story Embedding Strategy).**

**Decision:** User stories are now **embedded as JSON strings** within the Feature model (Phase 1), not stored as separate entities.

**Rationale:**
- TestIO API doesn't provide `feature_id` in user stories endpoint
- TestIO API doesn't provide `id` in features endpoint's user_stories array
- Cannot reliably establish Feature → UserStory foreign key relationship
- User stories only make sense in context of features (not independent entities)
- Embedding is simpler, faster, and matches how API provides the data
- Clean migration path exists when API is improved (Phase 2)

**User Feedback (Critical):**
> "feature_id null renders the user story useless. A user story only makes sense in the context of a test cycle. User Stories are icing on the cake, where the cake are the Features."

**Implementation Status:**
- ✅ **STORY-035A completed** with embedded `user_stories` field (JSON array of strings)
- ✅ **ADR-013 accepted** - documents embedding strategy and future normalization path
- ⏸️ **This story deferred** until TestIO API adds `feature_id` support

**Current Implementation (Phase 1):**
```python
class Feature(SQLModel, table=True):
    """Feature entity with embedded user stories (ADR-013)."""

    user_stories: str = Field(default="[]")
    """JSON array of user story title strings from features endpoint.

    Example: ["On mobile, I can tap to open tabs", "On mobile, I can close sheet"]

    Each string is a testable user journey for this feature. Stored as embedded
    JSON because API doesn't provide user story IDs in features endpoint.

    When API is improved (adds 'id' to user_stories array), we can migrate to
    normalized UserStory table with feature_id foreign key.
    """
```

**Future Work (Phase 2):**
When TestIO API is improved to include ONE of the following:
1. `feature_id` field in user stories endpoint response, OR
2. `id` field in features endpoint's user_stories array

We can implement this story to normalize user stories into a separate table, enabling:
- ✅ Query: "Which test cycles tested user story X?"
- ✅ User story-level analytics (defects per user story, test coverage)
- ✅ Efficient refresh (sync user stories independently of features)
- ✅ Cross-feature user story queries

**API Improvement Request:** Submitted to TestIO API team (2025-11-23)

**References:**
- `docs/architecture/adrs/ADR-013-user-story-embedding-strategy.md` - Full rationale and migration plan
- `src/testio_mcp/models/orm/feature.py` - Feature model with embedded user_stories field
- `src/testio_mcp/repositories/feature_repository.py` - FeatureRepository with embedded user story sync
- `docs/architecture/api-limitation-user-story-feature-linkage.md` - Original analysis

---

# Original Story (For Historical Reference)

**Note:** The content below represents the original planned implementation before ADR-013 was accepted. This is preserved for historical context and may be useful when implementing Phase 2 normalization after the API is improved.

---

## Original Status
Blocked - Depends on STORY-035A completion (which depends on STORY-035C AC0)

## Critical Dependencies

**⚠️ TRANSITIVE DEPENDENCY: STORY-035C AC0**
- Section detection helper (`has_sections()`, `get_section_ids()`)
- STORY-035A uses these helpers for FeatureRepository
- **This story (035B) must use the SAME helpers** for consistency
- Ensures Feature and UserStory repositories handle sections identically

## Story

**As a** developer analyzing test coverage,
**I want** user stories stored as first-class entities linked to features,
**So that** I can query "Which user stories are untested?" for sprint planning.

## Background

**Current State (After STORY-035A):**
- Features stored as first-class entities in database
- FeatureRepository operational with section-aware sync
- Feature model includes `user_stories` relationship (one-to-many)

**This Story (035B):**
Second story in Epic 005 - establishes UserStory entity with feature linkage and data consistency validation.

## Problem Solved

**Before (STORY-035A):**
```python
# Can query features, but user stories only in JSON blobs
features = await feature_repo.get_features_for_product(product_id=598)
# Cannot query: "Show user stories for feature"
# Cannot query: "Which user stories are untested?"
# Cannot query: "Test coverage by user story"
```

**After (STORY-035B):**
```python
# Complete user story catalog with feature linkage
user_stories = await user_story_repo.get_user_stories_for_product(product_id=598)
user_stories = await user_story_repo.get_user_stories_for_feature(feature_id=123)

# Query: "Show user stories for feature" ✅
# Query: "Which user stories are untested?" ✅
# Query: "Test coverage by user story" ✅ (ready for Epic 007)
```

## Acceptance Criteria

### AC1: UserStory SQLModel Class Created

**File:** `src/testio_mcp/models/orm/user_story.py`

**Implementation:**
```python
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .feature import Feature
    from .product import Product


class UserStory(SQLModel, table=True):
    """User Story entity - acceptance criteria for features.

    Represents user stories from TestIO API:
    - Non-section products: GET /products/{id}/user_stories
    - Section products: GET /products/{id}/user_stories?section_id={sid}

    Relationships:
    - product: Parent product (many-to-one)
    - feature: Parent feature (many-to-one)
    """

    __tablename__ = "user_stories"

    # Primary Key
    id: int = Field(primary_key=True)

    # Foreign Keys
    product_id: int = Field(foreign_key="products.id", index=True)
    section_id: Optional[int] = Field(default=None, index=True)  # NULL for non-section products
    feature_id: int = Field(foreign_key="features.id", index=True)

    # User Story Data
    title: str = Field(max_length=500)
    requirements: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "TEXT"})

    # Raw API Response (for future schema evolution)
    raw_data: dict = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})

    # Sync Metadata
    last_synced: datetime = Field(default_factory=lambda: datetime.utcnow())

    # Relationships
    product: "Product" = Relationship(back_populates="user_stories")
    feature: "Feature" = Relationship(back_populates="user_stories")

    class Config:
        """SQLModel configuration."""
        arbitrary_types_allowed = True
```

**Validation:**
- [ ] Model defined with all required fields
- [ ] Foreign keys: `products.id`, `features.id` (both indexed)
- [ ] `section_id` nullable (NULL for non-section products)
- [ ] `raw_data` stored as JSON (SQLite JSON1 extension)
- [ ] Relationships defined: `product` (many-to-one), `feature` (many-to-one)
- [ ] Type checking passes: `mypy src/testio_mcp/models/orm/user_story.py --strict`

---

### AC2: Update Feature Model for Reverse Relationship

**File:** `src/testio_mcp/models/orm/feature.py`

**Add to Feature class:**
```python
# Relationships
product: "Product" = Relationship(back_populates="features")
user_stories: list["UserStory"] = Relationship(back_populates="feature")  # ← Already exists
```

**Validation:**
- [ ] `user_stories` relationship already exists in Feature model (from STORY-035A)
- [ ] Bi-directional relationship: Feature ↔ UserStory

---

### AC3: UserStoryRepository Created with Section-Aware Sync

**File:** `src/testio_mcp/repositories/user_story_repository.py`

**Pattern:** Inherits from `BaseRepository` (Epic 006 pattern)

**Implementation:**
```python
from datetime import datetime
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Feature, UserStory
from testio_mcp.repositories.base_repository import BaseRepository


from testio_mcp.utilities.section_detection import has_sections, get_section_ids  # STORY-035C AC0


class UserStoryRepository(BaseRepository[UserStory]):
    """Repository for UserStory entity operations.

    Handles section-aware user story sync:
    - Non-section products: GET /products/{id}/user_stories
    - Section products: GET /products/{id}/user_stories?section_id={sid} (required param!)

    Section Detection:
    - Uses shared helper from STORY-035C AC0 (has_sections, get_section_ids)
    - SAME helper as FeatureRepository (consistent section handling)
    - Critical fix: > 0 not > 1 (single-default-section products exist!)

    Data Consistency Validation:
    - user_story.product_id MUST equal feature.product_id (FATAL if mismatch)
    - user_story.section_id SHOULD equal feature.section_id (WARNING if mismatch)
    - missing feature_id → Store as NULL, flag row, emit warning (Codex recommendation)

    Inherits from BaseRepository for:
    - Standard constructor (session, client injection)
    - Async context manager pattern
    - Resource cleanup in finally blocks
    """

    def __init__(self, session: AsyncSession, client: TestIOClient, customer_id: int):
        """Initialize repository.

        Args:
            session: SQLModel AsyncSession (managed by caller)
            client: TestIO API client
            customer_id: Customer ID for API calls
        """
        super().__init__(session=session, client=client, customer_id=customer_id)

    async def sync_user_stories(self, product_id: int) -> dict[str, int]:
        """Sync user stories for product (section-aware).

        Detects if product has sections and uses appropriate API endpoint:
        - Non-section: GET /products/{id}/user_stories
        - Section: GET /products/{id}/user_stories?section_id={sid} (per section)

        Uses shared section detection helper (STORY-035C AC0) to ensure
        consistent behavior with FeatureRepository.

        Args:
            product_id: Product ID to sync user stories for

        Returns:
            Sync statistics: {"created": int, "updated": int, "total": int, "validation_warnings": int}

        Raises:
            TestIOAPIError: If API calls fail
        """
        # 1. Get product to check for sections
        product_data = await self.client.get(f"products/{product_id}")

        # 2. Use shared helper (STORY-035C AC0) - SAME as FeatureRepository
        if has_sections(product_data):
            user_stories_data = await self._sync_sectioned_product(product_id, product_data)
        else:
            user_stories_data = await self._sync_non_sectioned_product(product_id)

        # 3. Upsert user stories to database (with validation)
        stats = await self._upsert_user_stories(product_id, user_stories_data)

        return stats

    def _has_sections(self, product_data: dict) -> bool:
        """Detect if product uses sections.

        Args:
            product_data: Product API response

        Returns:
            True if product has sections, False otherwise
        """
        sections = product_data.get("sections") or product_data.get("sections_with_default") or []
        return len(sections) > 0

    async def _sync_non_sectioned_product(self, product_id: int) -> list[dict]:
        """Fetch user stories for non-section product.

        Args:
            product_id: Product ID

        Returns:
            List of user story dictionaries
        """
        response = await self.client.get(f"products/{product_id}/user_stories")
        return response.get("user_stories", [])

    async def _sync_sectioned_product(self, product_id: int, product_data: dict) -> list[dict]:
        """Fetch user stories for section product (all sections).

        CRITICAL: section_id query param is REQUIRED for section products (500 error without it).

        Args:
            product_id: Product ID
            product_data: Product API response (contains sections)

        Returns:
            Combined list of user stories from all sections
        """
        import asyncio

        sections = product_data.get("sections") or product_data.get("sections_with_default") or []
        all_user_stories = []

        # Concurrency control: Reuse client semaphore (2-3 concurrent calls)
        tasks = []
        for section in sections:
            section_id = section.get("id")
            if section_id:
                tasks.append(self._fetch_section_user_stories(product_id, section_id))

        # Gather results (client semaphore enforces concurrency limit)
        section_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in section_results:
            if isinstance(result, Exception):
                # Log error but continue (partial sync better than failure)
                self.logger.warning(f"Section user story fetch failed: {result}")
                continue
            all_user_stories.extend(result)

        return all_user_stories

    async def _fetch_section_user_stories(self, product_id: int, section_id: int) -> list[dict]:
        """Fetch user stories for single section.

        Args:
            product_id: Product ID
            section_id: Section ID

        Returns:
            List of user story dictionaries for section
        """
        # CRITICAL: section_id is query param, not path param
        response = await self.client.get(
            f"products/{product_id}/user_stories?section_id={section_id}"
        )
        user_stories = response.get("user_stories", [])

        # Inject section_id into each user story (API doesn't always include it)
        for user_story in user_stories:
            user_story["section_id"] = section_id

        return user_stories

    async def _upsert_user_stories(
        self, product_id: int, user_stories_data: list[dict]
    ) -> dict[str, int]:
        """Upsert user stories to database with data consistency validation.

        Validates:
        - user_story.product_id == feature.product_id (CRITICAL)
        - user_story.section_id == feature.section_id (WARNING if mismatch)

        Args:
            product_id: Product ID
            user_stories_data: List of user story dictionaries from API

        Returns:
            Sync statistics including validation_warnings count
        """
        created = 0
        updated = 0
        validation_warnings = 0
        now = datetime.utcnow()

        for user_story_data in user_stories_data:
            user_story_id = user_story_data.get("id")
            feature_id = user_story_data.get("feature_id")

            if not user_story_id or not feature_id:
                continue

            # Validate feature exists and matches product_id
            result = await self.session.exec(
                select(Feature).where(Feature.id == feature_id)
            )
            feature = result.first()

            if not feature:
                self.logger.warning(
                    f"User story {user_story_id} references non-existent feature {feature_id}"
                )
                validation_warnings += 1
                continue

            # CRITICAL: Validate product_id consistency
            if feature.product_id != product_id:
                self.logger.error(
                    f"Data inconsistency: user_story {user_story_id} product_id mismatch "
                    f"(expected {product_id}, feature has {feature.product_id})"
                )
                validation_warnings += 1
                continue

            # WARNING: Validate section_id consistency (API data quality issue)
            user_story_section_id = user_story_data.get("section_id")
            if user_story_section_id != feature.section_id:
                self.logger.warning(
                    f"Section ID mismatch: user_story {user_story_id} has section_id "
                    f"{user_story_section_id}, but feature {feature_id} has {feature.section_id}. "
                    f"Using feature's section_id (API data quality issue)."
                )
                validation_warnings += 1
                # Use feature's section_id for consistency
                user_story_section_id = feature.section_id

            # Check if user story exists
            result = await self.session.exec(
                select(UserStory).where(UserStory.id == user_story_id)
            )
            existing = result.first()

            if existing:
                # Update existing user story
                existing.title = user_story_data.get("title", "")
                existing.requirements = user_story_data.get("requirements")
                existing.raw_data = user_story_data
                existing.last_synced = now
                updated += 1
            else:
                # Create new user story
                user_story = UserStory(
                    id=user_story_id,
                    product_id=product_id,
                    section_id=user_story_section_id,
                    feature_id=feature_id,
                    title=user_story_data.get("title", ""),
                    requirements=user_story_data.get("requirements"),
                    raw_data=user_story_data,
                    last_synced=now,
                )
                self.session.add(user_story)
                created += 1

        await self.session.commit()

        return {
            "created": created,
            "updated": updated,
            "total": created + updated,
            "validation_warnings": validation_warnings,
        }

    async def get_user_stories_for_product(
        self,
        product_id: int,
        feature_id: Optional[int] = None,
        section_id: Optional[int] = None,
    ) -> list[UserStory]:
        """Get user stories for product (with optional filters).

        Args:
            product_id: Product ID
            feature_id: Optional feature ID filter
            section_id: Optional section ID filter

        Returns:
            List of UserStory ORM models
        """
        query = select(UserStory).where(UserStory.product_id == product_id)

        if feature_id is not None:
            query = query.where(UserStory.feature_id == feature_id)

        if section_id is not None:
            query = query.where(UserStory.section_id == section_id)

        result = await self.session.exec(query)
        return result.all()

    async def get_user_stories_for_feature(self, feature_id: int) -> list[UserStory]:
        """Get all user stories for a feature.

        Args:
            feature_id: Feature ID

        Returns:
            List of UserStory ORM models
        """
        result = await self.session.exec(
            select(UserStory).where(UserStory.feature_id == feature_id)
        )
        return result.all()
```

**Validation:**
- [ ] Repository inherits from `BaseRepository`
- [ ] `sync_user_stories()` implements section detection logic
- [ ] Non-section products: `GET /products/{id}/user_stories`
- [ ] Section products: `GET /products/{id}/user_stories?section_id={sid}` (query param!)
- [ ] Data consistency validation: `user_story.product_id == feature.product_id`
- [ ] Data consistency validation: `user_story.section_id == feature.section_id` (warning if mismatch)
- [ ] Concurrency control: Reuses client semaphore (2-3 concurrent section calls)
- [ ] Type checking passes: `mypy src/testio_mcp/repositories/user_story_repository.py --strict`

---

### AC4: Alembic Migration Generated

**Command:**
```bash
alembic revision --autogenerate -m "Add user_stories table"
```

**Migration File:** `alembic/versions/<revision>_add_user_stories_table.py`

**Critical Requirements:**
```python
"""Add user_stories table

Revision ID: <new_revision_id>
Revises: <story_035a_revision_id>  # ← CRITICAL: Chains from STORY-035A
Create Date: 2025-11-23
"""

def upgrade() -> None:
    """Create user_stories table."""
    op.create_table(
        'user_stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('feature_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('last_synced', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['feature_id'], ['features.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_stories_product_id', 'user_stories', ['product_id'])
    op.create_index('idx_user_stories_section_id', 'user_stories', ['section_id'])
    op.create_index('idx_user_stories_feature_id', 'user_stories', ['feature_id'])

def downgrade() -> None:
    """Drop user_stories table."""
    op.drop_index('idx_user_stories_feature_id', table_name='user_stories')
    op.drop_index('idx_user_stories_section_id', table_name='user_stories')
    op.drop_index('idx_user_stories_product_id', table_name='user_stories')
    op.drop_table('user_stories')
```

**Validation:**
- [ ] Migration chains from STORY-035A migration
- [ ] Indexes created: `idx_user_stories_product_id`, `idx_user_stories_section_id`, `idx_user_stories_feature_id`
- [ ] Foreign keys: `product_id` → `products.id`, `feature_id` → `features.id`
- [ ] Migration applies successfully: `alembic upgrade head`
- [ ] Migration rolls back successfully: `alembic downgrade -1`
- [ ] Single head enforced: `alembic heads` returns exactly one revision

---

### AC5: Unit Tests - UserStoryRepository CRUD

**File:** `tests/unit/test_repositories_user_story.py`

**Test Coverage:**
```python
import pytest
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm import Feature, UserStory
from testio_mcp.repositories.user_story_repository import UserStoryRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_user_stories_non_section_product(
    async_session: AsyncSession, mock_client, customer_id: int
):
    """Test user story sync for non-section product."""
    # Create test feature
    feature = Feature(id=1, product_id=21362, section_id=None, title="Feature 1", raw_data={})
    async_session.add(feature)
    await async_session.commit()

    # Mock API response
    mock_client.get.side_effect = [
        # GET /products/21362
        {"id": 21362, "sections": []},
        # GET /products/21362/user_stories
        {"user_stories": [
            {"id": 1, "feature_id": 1, "title": "User Story 1", "requirements": "Req 1"},
            {"id": 2, "feature_id": 1, "title": "User Story 2", "requirements": "Req 2"},
        ]},
    ]

    repo = UserStoryRepository(session=async_session, client=mock_client, customer_id=customer_id)

    # Sync user stories
    stats = await repo.sync_user_stories(product_id=21362)

    # Verify stats
    assert stats["created"] == 2
    assert stats["updated"] == 0
    assert stats["total"] == 2
    assert stats["validation_warnings"] == 0

    # Verify database
    result = await async_session.exec(select(UserStory).where(UserStory.product_id == 21362))
    user_stories = result.all()
    assert len(user_stories) == 2
    assert user_stories[0].section_id is None  # Non-section product
    assert user_stories[0].feature_id == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_user_stories_section_product(
    async_session: AsyncSession, mock_client, customer_id: int
):
    """Test user story sync for section product."""
    # Create test features
    feature1 = Feature(id=1, product_id=18559, section_id=100, title="Feature 1", raw_data={})
    feature2 = Feature(id=2, product_id=18559, section_id=101, title="Feature 2", raw_data={})
    async_session.add(feature1)
    async_session.add(feature2)
    await async_session.commit()

    # Mock API response
    mock_client.get.side_effect = [
        # GET /products/18559
        {"id": 18559, "sections": [{"id": 100}, {"id": 101}]},
        # GET /products/18559/user_stories?section_id=100
        {"user_stories": [{"id": 1, "feature_id": 1, "title": "User Story 1"}]},
        # GET /products/18559/user_stories?section_id=101
        {"user_stories": [{"id": 2, "feature_id": 2, "title": "User Story 2"}]},
    ]

    repo = UserStoryRepository(session=async_session, client=mock_client, customer_id=customer_id)

    # Sync user stories
    stats = await repo.sync_user_stories(product_id=18559)

    # Verify stats
    assert stats["created"] == 2
    assert stats["total"] == 2

    # Verify database
    result = await async_session.exec(select(UserStory).where(UserStory.product_id == 18559))
    user_stories = result.all()
    assert len(user_stories) == 2
    assert user_stories[0].section_id in [100, 101]
    assert user_stories[1].section_id in [100, 101]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_data_consistency_validation(
    async_session: AsyncSession, mock_client, customer_id: int
):
    """Test data consistency validation (product_id and section_id)."""
    # Create test feature
    feature = Feature(id=1, product_id=598, section_id=100, title="Feature 1", raw_data={})
    async_session.add(feature)
    await async_session.commit()

    # Mock API response with MISMATCHED section_id
    mock_client.get.side_effect = [
        # GET /products/598
        {"id": 598, "sections": [{"id": 100}]},
        # GET /products/598/user_stories?section_id=100
        {"user_stories": [
            # MISMATCH: user story has section_id=999, but feature has section_id=100
            {"id": 1, "feature_id": 1, "section_id": 999, "title": "User Story 1"},
        ]},
    ]

    repo = UserStoryRepository(session=async_session, client=mock_client, customer_id=customer_id)

    # Sync user stories
    stats = await repo.sync_user_stories(product_id=598)

    # Verify validation warning
    assert stats["validation_warnings"] == 1
    assert stats["created"] == 1  # Still created, but with feature's section_id

    # Verify database uses feature's section_id
    result = await async_session.exec(select(UserStory).where(UserStory.id == 1))
    user_story = result.first()
    assert user_story.section_id == 100  # Uses feature's section_id, not API's 999
```

**Validation:**
- [ ] Test non-section product sync (Product 21362 pattern)
- [ ] Test section product sync (Product 18559 pattern)
- [ ] Test data consistency validation (product_id match)
- [ ] Test section_id mismatch handling (uses feature's section_id)
- [ ] Test `get_user_stories_for_product()` with filters
- [ ] Test `get_user_stories_for_feature()`
- [ ] All tests pass: `uv run pytest tests/unit/test_repositories_user_story.py -v`

---

### AC6: Integration Tests - Real API

**File:** `tests/integration/test_user_story_sync_integration.py`

**Test Coverage:**
```python
import pytest
from sqlmodel import select

from testio_mcp.models.orm import Feature, UserStory
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.user_story_repository import UserStoryRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_user_stories_flourish_non_section(
    async_session, real_client, customer_id
):
    """Integration test: Sync user stories for Flourish (Product 21362, non-section)."""
    # First sync features (prerequisite)
    feature_repo = FeatureRepository(session=async_session, client=real_client, customer_id=customer_id)
    await feature_repo.sync_features(product_id=21362)

    # Sync user stories
    user_story_repo = UserStoryRepository(session=async_session, client=real_client, customer_id=customer_id)
    stats = await user_story_repo.sync_user_stories(product_id=21362)

    # Verify sync (Flourish has 54 user stories)
    assert stats["total"] == 54
    assert stats["created"] == 54
    assert stats["validation_warnings"] == 0  # Clean API data

    # Verify database
    result = await async_session.exec(select(UserStory).where(UserStory.product_id == 21362))
    user_stories = result.all()
    assert len(user_stories) == 54
    assert all(us.section_id is None for us in user_stories)  # Non-section product


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_user_stories_canva_section(
    async_session, real_client, customer_id
):
    """Integration test: Sync user stories for Canva (Product 18559, has sections)."""
    # First sync features (prerequisite)
    feature_repo = FeatureRepository(session=async_session, client=real_client, customer_id=customer_id)
    await feature_repo.sync_features(product_id=18559)

    # Sync user stories
    user_story_repo = UserStoryRepository(session=async_session, client=real_client, customer_id=customer_id)
    stats = await user_story_repo.sync_user_stories(product_id=18559)

    # Verify sync (Canva has 1,709+ user stories across sections)
    assert stats["total"] >= 1709
    assert stats["created"] >= 1709

    # Verify database
    result = await async_session.exec(select(UserStory).where(UserStory.product_id == 18559))
    user_stories = result.all()
    assert len(user_stories) >= 1709
    assert all(us.section_id is not None for us in user_stories)  # Section product
```

**Validation:**
- [ ] Test with Flourish (Product 21362): 54 user stories, no sections
- [ ] Test with Canva (Product 18559): 1,709+ user stories, has sections
- [ ] Test with remove.bg (Product 24959): 9 user stories, section 25543
- [ ] All integration tests pass: `uv run pytest tests/integration/test_user_story_sync_integration.py -v`

---

### AC7: Performance Validation

**Performance Target:** User story sync completes in < 45 seconds for product with 10 sections

**Benchmark Script:** `scripts/benchmark_user_story_sync.py`

```python
import asyncio
import time
from statistics import mean, median

from testio_mcp.repositories.user_story_repository import UserStoryRepository
# ... setup code ...

async def benchmark_user_story_sync(product_id: int, iterations: int = 3):
    """Benchmark user story sync performance."""
    times = []

    for i in range(iterations):
        start = time.perf_counter()
        stats = await repo.sync_user_stories(product_id=product_id)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Iteration {i+1}: {elapsed:.2f}s ({stats['total']} user stories, {stats['validation_warnings']} warnings)")

    print(f"\nResults for Product {product_id}:")
    print(f"  Mean: {mean(times):.2f}s")
    print(f"  Median: {median(times):.2f}s")
    print(f"  Min: {min(times):.2f}s")
    print(f"  Max: {max(times):.2f}s")

# Run benchmark
await benchmark_user_story_sync(product_id=18559)  # Canva (section product)
```

**Validation:**
- [ ] Benchmark script created
- [ ] Canva sync (1,709+ user stories) completes in < 45 seconds
- [ ] No API 500 errors (concurrency control working)
- [ ] Validation warnings logged but don't block sync
- [ ] Results documented in story completion notes

---

## Tasks

### Task 1: Define UserStory SQLModel Class
- [ ] Create `src/testio_mcp/models/orm/user_story.py`
- [ ] Define UserStory class with all fields
- [ ] Add relationships: `product`, `feature`
- [ ] Test model creation in Python REPL

**Estimated Effort:** 30 minutes

---

### Task 2: Create UserStoryRepository
- [ ] Create `src/testio_mcp/repositories/user_story_repository.py`
- [ ] Implement `sync_user_stories()` with section detection
- [ ] Implement `_has_sections()` helper (same as FeatureRepository)
- [ ] Implement `_sync_non_sectioned_product()`
- [ ] Implement `_sync_sectioned_product()` with concurrency control
- [ ] Implement `_upsert_user_stories()` with data consistency validation
- [ ] Implement `get_user_stories_for_product()`
- [ ] Implement `get_user_stories_for_feature()`

**Estimated Effort:** 2.5 hours

---

### Task 3: Generate Alembic Migration
- [ ] Run `alembic revision --autogenerate -m "Add user_stories table"`
- [ ] Verify migration chains from STORY-035A
- [ ] Test migration upgrade: `alembic upgrade head`
- [ ] Test migration downgrade: `alembic downgrade -1`
- [ ] Verify single head: `alembic heads`

**Estimated Effort:** 30 minutes

---

### Task 4: Write Unit Tests
- [ ] Create `tests/unit/test_repositories_user_story.py`
- [ ] Test non-section product sync
- [ ] Test section product sync
- [ ] Test data consistency validation (product_id + section_id)
- [ ] Test `get_user_stories_for_product()` queries
- [ ] Test `get_user_stories_for_feature()` query
- [ ] Achieve >90% coverage for UserStoryRepository

**Estimated Effort:** 1.5 hours

---

### Task 5: Write Integration Tests
- [ ] Create `tests/integration/test_user_story_sync_integration.py`
- [ ] Test with Flourish (Product 21362): 54 user stories
- [ ] Test with Canva (Product 18559): 1,709+ user stories
- [ ] Test with remove.bg (Product 24959): 9 user stories
- [ ] Verify data consistency with real API

**Estimated Effort:** 45 minutes

---

### Task 6: Performance Validation
- [ ] Create `scripts/benchmark_user_story_sync.py`
- [ ] Run benchmark with Canva (section product, 1,709+ user stories)
- [ ] Verify < 45 seconds for product with 10 sections
- [ ] Document validation warnings (API data quality issues)
- [ ] Document results

**Estimated Effort:** 30 minutes

---

## Prerequisites

**STORY-035A Complete:**
- ✅ Feature SQLModel class created
- ✅ FeatureRepository operational with section-aware sync
- ✅ Features table migration applied
- ✅ Features synced for test products (21362, 18559, 24959)

**Epic 006 Lessons Applied:**
- Use `session.exec().first()` for ORM models (not `session.execute().one_or_none()`)
- Always use `async with get_service_context()` for resource cleanup
- Validate data consistency before creating entities
- Log warnings for API data quality issues (don't fail sync)

---

## Technical Notes

### API Endpoint Differences (Critical)

**Non-section products:**
```
GET /products/{id}/user_stories
→ Returns all user stories
```

**Section products (CRITICAL):**
```
GET /products/{id}/user_stories?section_id={sid}
→ section_id is REQUIRED query param (not path param!)
→ 500 error without section_id param
```

### Data Consistency Validation

**product_id Validation (CRITICAL):**
```python
# user_story.product_id MUST equal feature.product_id
if feature.product_id != product_id:
    # ERROR: Skip this user story
    validation_warnings += 1
    continue
```

**section_id Validation (WARNING):**
```python
# user_story.section_id SHOULD equal feature.section_id
if user_story_section_id != feature.section_id:
    # WARNING: Use feature's section_id for consistency
    validation_warnings += 1
    user_story_section_id = feature.section_id
```

### Concurrency Control

Same pattern as FeatureRepository:
- Reuse existing `TestIOClient` semaphore
- Use `asyncio.gather()` with `return_exceptions=True`
- 2-3 concurrent section calls (avoid API 500s)

---

## Success Metrics

- ✅ UserStory SQLModel class created with relationships
- ✅ UserStoryRepository implements section-aware sync with validation
- ✅ Data consistency validated: product_id and section_id checks
- ✅ Alembic migration chains from STORY-035A
- ✅ Unit tests pass (100% success rate)
- ✅ Integration tests pass with real API (Products 21362, 18559, 24959)
- ✅ Performance: User story sync < 45 seconds for 10 sections
- ✅ Type checking passes: `mypy src/testio_mcp/repositories/user_story_repository.py --strict`

---

## References

- **Epic 005:** `docs/epics/epic-005-data-enhancement-and-serving.md`
- **STORY-035A:** `docs/stories/story-035a-features-repository-sync.md`
- **Epic 006 Retrospective:** `docs/sprint-artifacts/epic-6-retro-2025-11-23.md`
- **API Research:** `scripts/research_features_api.py` (completed 2025-11-22)

---

## Story Completion Notes

*This section will be populated during implementation with:*
- Actual migration revision ID
- Performance benchmark results
- Data consistency validation findings (API quality issues)
- Integration test results with real products
- Any deviations from planned implementation
- Lessons learned for STORY-035C
