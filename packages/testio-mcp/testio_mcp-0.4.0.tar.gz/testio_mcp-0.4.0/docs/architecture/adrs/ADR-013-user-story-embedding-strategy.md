# ADR-013: User Story Embedding Strategy

**Date:** 2025-11-23
**Status:** Accepted
**Affects:** STORY-035A, STORY-035B (Epic 005)

## Context

The TestIO Customer API currently represents user stories in two endpoints:

1. **Features endpoint** (`GET /products/{id}/sections/{sid}/features`):
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

2. **User stories endpoint** (`GET /products/{id}/user_stories?section_id={sid}`):
   ```json
   {
     "user_stories": [
       {
         "id": 60011,
         "title": "On mobile, I can tap to open the different tabs"
         // ❌ No feature_id field!
       }
     ]
   }
   ```

**The Problem:**
- Features endpoint: Has user story **titles** but no IDs
- User stories endpoint: Has user story **IDs** but no `feature_id`
- Cannot reliably establish Feature → UserStory foreign key relationship

### Business Context

User stories are **not** independent entities in the TestIO domain model:
- User stories only make sense in the context of a feature
- Test cycles define which **features** to test, then optionally include specific **user stories** from those features
- User stories are "icing on the cake" - features are the primary testable unit
- Relationship flows: `Test Cycle → Features → User Stories`

**Critical user feedback:**
> "feature_id null renders the user story useless. A user story only makes sense in the context of a test cycle. User Stories are icing on the cake, where the cake are the Features."

### API Improvement Request

**Status:** Requested from TestIO API team (2025-11-23)

**Requested changes:**
1. Add `feature_id` field to user stories endpoint response
2. Add `id` field to `user_stories` array in features endpoint response

**Proposed improved features endpoint:**
```json
{
  "features": [
    {
      "id": 177038,
      "title": "[Editing Surfaces] Mobile Tabs",
      "user_stories": [
        {
          "id": 60011,  // ← Add this
          "title": "On mobile, I can tap to open the different tabs"
        }
      ]
    }
  ]
}
```

**Benefits when implemented:**
- ✅ Single endpoint fetch (no need for user stories endpoint)
- ✅ Efficient refresh (only fetch features, get user stories with IDs)
- ✅ Enables proper normalization (can create UserStory table with reliable feature_id)
- ✅ Supports queries like "Which test cycles tested user story X?"

## Decision

**Phase 1 (Current Implementation):** Embed user stories as JSON array of **title strings** within the Feature model.

User stories are stored exactly as the features endpoint provides them - as an array of strings. No additional API calls, no title matching complexity.

**Phase 2 (When API is Fixed):** Migrate to normalized UserStory table when TestIO adds `feature_id` to user stories endpoint or `id` to features endpoint's user_stories array.

### Schema Design (Phase 1)

```python
class Feature(SQLModel, table=True):
    """Feature entity with embedded user stories.

    User stories are stored as JSON array of title strings because:
    1. API provides user stories as string array in features endpoint
    2. User stories only exist in context of features (not independent entities)
    3. Always accessed together (never queried independently)
    4. No reliable way to get IDs without fragile title matching

    When API is fixed (adds id to user_stories array in features endpoint),
    we can normalize to separate table for queries like:
    "Which test cycles tested this user story?"

    API Improvement Request: https://github.com/testio/api-requests/issues/XXX
    """

    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    title: str
    description: str | None = Field(default=None)
    howtofind: str | None = Field(default=None)

    # Embedded user stories (JSON array of strings)
    user_stories: str = Field(default="[]")
    """JSON array of user story title strings from features endpoint:
    [
        "On mobile, I can tap to open the different tabs",
        "On mobile, I can close an opened sheet by swiping down",
        "On mobile, I can interact with the opened sheet"
    ]

    Each string is a testable user journey for this feature.
    """

    raw_data: str  # Full API response (JSON stored as TEXT)
    last_synced: datetime

    # Relationships
    product: "Product" = Relationship(back_populates="features")
```

### Sync Strategy (Phase 1)

**Simple and direct - no title matching, no extra API calls:**

```python
async def _upsert_features(self, product_id: int, features_data: list[dict]) -> dict:
    """Upsert features with embedded user stories."""
    created = 0
    updated = 0
    now = datetime.now(UTC)

    for feature_data in features_data:
        feature_id = feature_data.get("id")
        if not feature_id:
            continue

        # Extract user stories array (list of strings)
        user_stories = feature_data.get("user_stories", [])

        # Check if feature exists
        result = await self.session.exec(select(Feature).where(Feature.id == feature_id))
        existing = result.first()

        if existing:
            # Update existing feature
            existing.title = feature_data.get("title", "")
            existing.description = feature_data.get("description")
            existing.howtofind = feature_data.get("howtofind")
            existing.user_stories = json.dumps(user_stories)  # Store as JSON
            existing.raw_data = json.dumps(feature_data)
            existing.last_synced = now
            updated += 1
        else:
            # Create new feature
            feature = Feature(
                id=feature_id,
                product_id=product_id,
                title=feature_data.get("title", ""),
                description=feature_data.get("description"),
                howtofind=feature_data.get("howtofind"),
                user_stories=json.dumps(user_stories),  # Store as JSON
                raw_data=json.dumps(feature_data),
                last_synced=now,
            )
            self.session.add(feature)
            created += 1

    await self.session.commit()

    return {
        "created": created,
        "updated": updated,
        "total": created + updated,
    }
```

**That's it! No title matching, no complexity.**

### Schema Design (Phase 2 - When API is Fixed)

**After TestIO adds `feature_id` to user stories endpoint:**

```python
class UserStory(SQLModel, table=True):
    """UserStory entity - normalized from embedded strings.

    This table is created AFTER API adds feature_id support.
    Until then, user stories live as JSON in features.user_stories.
    """

    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    feature_id: int = Field(foreign_key="features.id", index=True)  # Now reliable!
    title: str
    requirements: str | None = Field(default=None)
    raw_data: str
    last_synced: datetime

    # Relationships
    product: "Product" = Relationship()
    feature: "Feature" = Relationship(back_populates="user_stories")
```

**Migration script:**
```python
async def migrate_embedded_user_stories_to_table():
    """One-time migration when API is fixed.

    Fetch user stories endpoint (now with feature_id), populate table.
    """
    all_user_stories = await client.get("products/{id}/user_stories")

    for us_data in all_user_stories["user_stories"]:
        user_story = UserStory(
            id=us_data["id"],
            product_id=us_data["product_id"],
            feature_id=us_data["feature_id"],  # ← Now provided by API!
            title=us_data["title"],
            requirements=us_data.get("requirements"),
            raw_data=json.dumps(us_data),
            last_synced=datetime.now(UTC)
        )
        session.add(user_story)

    await session.commit()

    # Optionally deprecate features.user_stories column
    # (or keep for caching/denormalization)
```

## Consequences

### Positive (Phase 1)

✅ **Extremely simple** - just copy user_stories array from API to database
✅ **No title matching complexity** - no fuzzy logic, no normalization functions
✅ **No extra API calls** - only fetch features endpoint
✅ **Fast sync** - fewer API calls, less processing
✅ **Features are source of truth** - user stories always live with their feature
✅ **No orphaned data** - user stories can't exist without a feature
✅ **Honest representation** - stores exactly what API provides
✅ **Test cycle queries work** - "What can I test for this feature?" → parse JSON
✅ **Clean migration path** - when API is fixed, can normalize to table

### Negative (Phase 1)

❌ **No user story IDs** - can't link to specific user story entities
❌ **Can't query "Which test cycles tested user story X?"** - requires normalization
❌ **No user story-level analytics** - e.g., "How many tests did user story X get?"
❌ **String comparison only** - can search by title substring, not by ID

### Positive (Phase 2 - After API Fix)

✅ **Full normalization** - separate UserStory table with reliable feature_id
✅ **User story-level queries** - "Which test cycles tested user story X?"
✅ **Analytics enabled** - test coverage by user story, defects by user story
✅ **Efficient refresh** - can sync user stories independently of features

## Trade-offs Accepted

**Current Implementation (Embedded Strings):**
- ✅ Simple, fast, reliable, matches API exactly
- ❌ No user story-level analytics

**Future Implementation (Normalized Table):**
- ✅ Full analytics, cross-feature queries, efficient refresh
- ✅ Requires API fix (TestIO cooperation)
- ⏳ Timeline: Pending TestIO API team response

We accept the current limitations because:
1. User stories are **feature metadata**, not independent test targets
2. Test cycles select **features**, then optionally include user stories
3. Analytics on features are more valuable than analytics on user stories
4. Simple implementation reduces bugs and maintenance
5. Clean migration path exists when API is fixed

## Alternatives Considered

### Alternative 1: Title-Based Matching (Call Both Endpoints)

Fetch both features endpoint and user stories endpoint, match by normalized title.

**Rejected because:**
- 🔴 High risk of false matches (experts rated as HIGH risk)
- Adds significant complexity (normalization, fuzzy matching, collision detection)
- Requires extra API calls (2x slower sync)
- Fragile to title changes, whitespace, punctuation
- Non-unique titles cause arbitrary linkage
- **Violates YAGNI** - we don't need IDs yet, API provides strings

### Alternative 2: Nullable feature_id (Separate Table)

Store user stories as separate entities with `feature_id = NULL`.

**Rejected because:**
- Renders user stories useless (can't query "user stories for feature")
- Creates orphaned data with no context
- Doesn't match domain model (user stories need features)
- More complex than embedding (extra table, migration, queries)

### Alternative 3: Wait for API Fix

Block STORY-035B until TestIO adds `feature_id` or `id` to endpoints.

**Rejected because:**
- Timeline uncertain (could be weeks/months)
- Blocks Epic 005 deliverables
- Can implement simple embedding now, normalize later

## Implementation Notes

### Current Queries (Phase 1)

**Get user stories for feature:**
```python
feature = await feature_repo.get_feature(feature_id)
user_stories = json.loads(feature.user_stories)  # Returns list[str]

for title in user_stories:
    print(f"User Story: {title}")
```

**Count features with user stories:**
```sql
SELECT COUNT(*)
FROM features
WHERE user_stories != '[]'
```

**Search user stories by keyword:**
```python
features = await session.exec(select(Feature))
matches = []
for feature in features:
    user_stories = json.loads(feature.user_stories)
    if any("mobile" in us.lower() for us in user_stories):
        matches.append(feature)
```

### Future Queries (Phase 2 - After API Fix)

**Get user stories for feature (normalized):**
```python
user_stories = await session.exec(
    select(UserStory).where(UserStory.feature_id == feature_id)
)
```

**Which test cycles tested user story X:**
```python
test_cycles = await session.exec(
    select(TestCycle)
    .join(TestCycleFeature)
    .join(Feature)
    .join(UserStory)
    .where(UserStory.id == user_story_id)
)
```

### Migration Detection

**Code can detect when API is fixed:**
```python
# Check if features endpoint now includes user story IDs
feature_response = await client.get("products/{id}/features")
first_feature = feature_response["features"][0]

if isinstance(first_feature.get("user_stories", [None])[0], dict):
    # API fixed! user_stories is now list[dict] with 'id' field
    logger.info("API improvement detected - user stories now have IDs!")
    # Trigger migration to normalized table
    await migrate_to_normalized_user_stories()
else:
    # Still list[str] - continue with embedded approach
    logger.info("Using embedded user stories (API not yet updated)")
```

## Data Quality Monitoring

Track user story coverage during sync:
```python
stats = {
    "total_features": 0,
    "features_with_user_stories": 0,
    "total_user_story_count": 0,
    "avg_user_stories_per_feature": 0.0
}
```

Example log output:
```
INFO: Feature sync complete for product 18559
INFO: 156 features synced (134 with user stories)
INFO: 1,709 user stories embedded across features
INFO: Average 12.8 user stories per feature
```

## References

- **Analysis Document:** `docs/architecture/api-limitation-user-story-feature-linkage.md`
- **Expert Recommendations:** Codex + Gemini consultation (2025-11-23)
- **STORY-035A:** Feature Repository & Sync (completed)
- **STORY-035B:** User Stories Repository & Sync (simplified to embedding)
- **Epic 005:** Data Enhancement and Serving
- **API Improvement Request:** Pending TestIO API team response

## Decision Log

- **2025-11-23:** Initial analysis, explored 4 options
- **2025-11-23:** Consulted Codex + Gemini (recommended nullable + best-effort)
- **2025-11-23:** User feedback: "feature_id null renders user story useless"
- **2025-11-23:** **ACCEPTED** - Embed user stories as string array (simplest approach)
- **2025-11-23:** API improvement requested from TestIO team
- **Future:** Normalize to UserStory table when API adds feature_id support
