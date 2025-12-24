# API Limitation: User Story → Feature Linkage

**Date:** 2025-11-23
**Status:** BLOCKED - API Design Flaw
**Affects:** STORY-035B (User Stories Repository & Sync)

## Problem Statement

The TestIO Customer API has a critical design flaw that makes it **impossible to uniquely identify which feature a user story belongs to**.

### API Endpoint Analysis

**1. Features Endpoint** (`GET /products/{id}/sections/{sid}/features`):
```json
{
  "features": [
    {
      "id": 177038,
      "title": "[Editing Surfaces] Mobile Tabs",
      "user_stories": [
        "On mobile, I can tap to open the different tabs",
        "On mobile, I can close an opened sheet by swiping down"
      ]
    }
  ]
}
```
**Issues:**
- ✅ Shows feature ID
- ✅ Shows user stories belong to this feature
- ❌ User stories are **strings only** (no IDs!)

**2. User Stories Endpoint** (`GET /products/{id}/user_stories?section_id={sid}`):
```json
{
  "user_stories": [
    {
      "id": 60011,
      "path": "On mobile, I can tap to open the different tabs",
      "title": "On mobile, I can tap to open the different tabs"
    },
    {
      "id": 60012,
      "path": "On mobile, I can close an opened sheet by swiping down",
      "title": "On mobile, I can close an opened sheet by swiping down"
    }
  ]
}
```
**Issues:**
- ✅ Shows user story IDs
- ✅ Shows user story titles
- ❌ Does NOT include `feature_id` field!

### The Impossibility

**Database Model Goal:**
```python
class UserStory(SQLModel, table=True):
    id: int = Field(primary_key=True)
    feature_id: int = Field(foreign_key="features.id")  # ← How do we populate this?
    title: str
```

**Current API Reality:**
- Features endpoint knows the linkage but doesn't give us user story IDs
- User stories endpoint gives us IDs but doesn't include feature_id
- **No way to join these two datasets reliably**

## Proposed Solutions

### Option 1: Title-Based Matching (Fuzzy Join) ⚠️

**Implementation:**
```python
async def link_user_stories_to_features(self, product_id: int):
    """Match user stories to features by comparing title strings."""
    # 1. Fetch all features with embedded user story strings
    features = await self.client.get(f"products/{product_id}/sections/{sid}/features")

    # 2. Fetch all user stories with IDs
    user_stories = await self.client.get(f"products/{product_id}/user_stories?section_id={sid}")

    # 3. Match by exact title
    for feature in features["features"]:
        for us_title in feature["user_stories"]:
            # Find matching user story by title
            match = next(
                (us for us in user_stories["user_stories"] if us["title"] == us_title),
                None
            )
            if match:
                # Update UserStory.feature_id in database
                await self.session.exec(
                    update(UserStory)
                    .where(UserStory.id == match["id"])
                    .values(feature_id=feature["id"])
                )
```

**Pros:**
- Works with current API structure
- No API changes needed
- Can implement immediately

**Cons:**
- **Fragile:** Breaks if titles don't match exactly (whitespace, punctuation, encoding)
- **Not guaranteed unique:** What if two features have identical user story titles?
- **Maintenance burden:** Requires ongoing validation
- **Data quality:** Relies on TestIO maintaining exact title parity

**Risk Assessment:** 🔴 HIGH - String matching is unreliable for primary keys

---

### Option 2: Nullable feature_id (Recommended) ✅

**Implementation:**
```python
class UserStory(SQLModel, table=True):
    """User Story entity.

    NOTE: feature_id is nullable due to API limitation.

    The TestIO API does not provide feature_id in the user stories endpoint,
    and the features endpoint only returns user story titles (no IDs).

    This makes it impossible to reliably establish the feature→user_story
    relationship without fragile title-based matching.

    See: docs/architecture/api-limitation-user-story-feature-linkage.md
    """
    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    feature_id: int | None = Field(default=None, foreign_key="features.id", index=True)  # ← Nullable
    title: str
```

**Sync Strategy:**
```python
async def sync_user_stories(self, product_id: int) -> dict[str, int]:
    """Sync user stories WITHOUT feature linkage.

    Due to API limitation, feature_id will be NULL for all user stories.
    """
    user_stories_data = await self._fetch_user_stories(product_id)

    for us_data in user_stories_data:
        user_story = UserStory(
            id=us_data["id"],
            product_id=product_id,
            feature_id=None,  # ← API doesn't provide this
            title=us_data["title"],
            raw_data=json.dumps(us_data)
        )
        self.session.add(user_story)
```

**Pros:**
- ✅ Simple, honest about API limitations
- ✅ No fragile string matching
- ✅ Future-proof if API adds feature_id later
- ✅ Already implemented (feature_id is nullable in current schema)

**Cons:**
- ❌ Loses feature→user story relationship
- ❌ Query "Show user stories for feature" won't work
- ❌ Analytics like "Feature Test Coverage" require workarounds

**Risk Assessment:** 🟢 LOW - Accepts API limitation, no data integrity issues

---

### Option 3: Hybrid Approach (Best Effort)

**Implementation:**
```python
async def sync_user_stories(self, product_id: int) -> dict[str, int]:
    """Sync user stories with best-effort feature linkage."""
    # 1. Fetch user stories (has IDs, no feature_id)
    user_stories_data = await self._fetch_user_stories(product_id)

    # 2. Create user stories with feature_id=NULL initially
    for us_data in user_stories_data:
        user_story = UserStory(
            id=us_data["id"],
            product_id=product_id,
            feature_id=None,  # Start as NULL
            title=us_data["title"]
        )
        self.session.add(user_story)

    await self.session.commit()

    # 3. OPTIONAL: Attempt title-based matching
    await self._link_user_stories_to_features_by_title(product_id)

    return stats

async def _link_user_stories_to_features_by_title(self, product_id: int):
    """Best-effort feature linkage using title matching.

    This is a post-processing step. If matching fails, feature_id stays NULL.
    """
    features_data = await self._fetch_features(product_id)

    for feature_data in features_data:
        feature_id = feature_data["id"]
        us_titles = feature_data.get("user_stories", [])

        for us_title in us_titles:
            # Exact match only (avoid false positives)
            result = await self.session.exec(
                select(UserStory)
                .where(UserStory.product_id == product_id)
                .where(UserStory.title == us_title)
                .where(UserStory.feature_id.is_(None))  # Only update unlinked
            )
            user_story = result.first()

            if user_story:
                user_story.feature_id = feature_id
                logger.info(f"Linked user story {user_story.id} to feature {feature_id}")
            else:
                logger.warning(
                    f"Could not match user story title '{us_title}' to any ID "
                    f"(feature {feature_id})"
                )

    await self.session.commit()
```

**Pros:**
- ✅ User stories always stored (even if matching fails)
- ✅ Links features when possible (best effort)
- ✅ Graceful degradation (NULL feature_id is acceptable)
- ✅ Can track matching success rate

**Cons:**
- ⚠️ More complex than Option 2
- ⚠️ Still has title matching fragility issues
- ⚠️ Requires fetching features endpoint (extra API calls)

**Risk Assessment:** 🟡 MEDIUM - Added complexity, partial reliability

---

### Option 4: Contact TestIO API Team (Long-term)

**Request:**
> The user stories endpoint (`GET /products/{id}/user_stories`) should include a `feature_id` field to indicate which feature each user story belongs to.
>
> **Current Issue:**
> - Features endpoint shows user stories as strings (no IDs)
> - User stories endpoint shows IDs but no feature relationship
> - Impossible to build feature→user_story foreign key
>
> **Requested Change:**
> ```json
> {
>   "user_stories": [
>     {
>       "id": 60011,
>       "feature_id": 177038,  // ← Add this field
>       "title": "On mobile, I can tap to open..."
>     }
>   ]
> }
> ```

**Pros:**
- ✅ Fixes root cause
- ✅ Enables proper relational model
- ✅ Benefits all API consumers

**Cons:**
- ❌ Requires TestIO cooperation
- ❌ Timeline uncertain (could be months or never)
- ❌ Blocks STORY-035B until resolved

---

## Recommendation

**Phase 1 (Immediate - STORY-035B):**
- Implement **Option 2: Nullable feature_id**
- Document API limitation in code and ADR
- Store user stories without feature linkage
- Mark `feature_id` as NULL for all synced user stories

**Phase 2 (Future - STORY-035C or separate):**
- Evaluate need for feature→user_story queries in actual use cases
- If critical, implement **Option 3: Hybrid Approach** as enhancement
- Track matching success rate and data quality

**Phase 3 (Long-term - API Advocacy):**
- Contact TestIO API team with **Option 4** request
- Provide this analysis as evidence of design flaw
- If API is fixed, run migration to populate feature_id retroactively

## Impact Analysis

### Affected Queries (Won't Work)

**❌ "Show user stories for feature":**
```python
# BLOCKED - feature_id is NULL
user_stories = await repo.get_user_stories_for_feature(feature_id=177038)
```

**❌ "Test coverage by feature":**
```sql
-- BLOCKED - can't join features to user_stories reliably
SELECT f.title, COUNT(us.id) as story_count, COUNT(t.id) as test_count
FROM features f
LEFT JOIN user_stories us ON us.feature_id = f.id  -- ← NULL values!
LEFT JOIN tests t ON t.feature_id = f.id
GROUP BY f.id
```

### Queries That Still Work

**✅ "All user stories for product":**
```python
user_stories = await repo.get_user_stories_for_product(product_id=598)
```

**✅ "Untested user stories":**
```sql
SELECT us.id, us.title
FROM user_stories us
WHERE us.id NOT IN (SELECT user_story_id FROM tests WHERE user_story_id IS NOT NULL)
```

## Updated Schema

**Current Implementation (STORY-035A):**
```python
class UserStory(SQLModel, table=True):
    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    feature_id: int | None = Field(default=None, foreign_key="features.id", index=True)
    # ↑ Already nullable! Just needs documentation update
```

**No schema change needed** - `feature_id` is already nullable.

## Documentation Updates Required

1. **UserStory model docstring** - Add API limitation note
2. **STORY-035B acceptance criteria** - Remove feature linkage validation
3. **New ADR** - Document decision to leave feature_id as NULL
4. **This document** - Reference from code comments

## Action Items

- [ ] Update `UserStory` model docstring (API limitation note)
- [ ] Rewrite STORY-035B acceptance criteria (remove feature linkage)
- [ ] Create ADR-012: User Story Feature Linkage Strategy
- [ ] Update Epic 005 architecture diagram (dotted line for nullable FK)
- [ ] Document workaround queries for feature-level analytics
- [ ] Contact TestIO API team (low priority, long-term request)

## References

- **STORY-035A:** Feature Repository & Sync (completed)
- **STORY-035B:** User Stories Repository & Sync (BLOCKED by this issue)
- **Epic 005:** Data Enhancement and Serving
- **TestIO API Docs:** (no documentation for this endpoint behavior)
