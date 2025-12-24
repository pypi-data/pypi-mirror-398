"""Feature ORM model.

Represents testable product features from TestIO API.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.product import Product
    from testio_mcp.models.orm.test_feature import TestFeature


class Feature(SQLModel, table=True):
    """Feature entity - testable product capabilities with embedded user stories.

    Represents features from TestIO API:
    - Non-section products: GET /products/{id}/features
    - Section products: GET /products/{id}/sections/{sid}/features

    IMPORTANT: Features are SHARED across sections within a product.
    When syncing section products, the same feature ID will appear in multiple
    section API responses. The repository deduplicates these during sync.

    User Stories Strategy (ADR-013):
    User stories are embedded as JSON array of title strings. This is a temporary
    approach until TestIO API adds 'id' field to user_stories array in features
    endpoint response. When API is fixed, we can normalize to separate UserStory table.

    See: docs/architecture/adrs/ADR-013-user-story-embedding-strategy.md

    Features enable:
    - Complete product catalog visibility (not just tested features)
    - Advanced analytics (Bug Density per Feature, Untested Features)
    - Independent lifecycle (features can update without re-syncing tests)
    - Cleaner code (SQL queries instead of JSON blob parsing)
    - Test cycle queries: "What user stories can I test for this feature?"

    Attributes:
        id: Primary key (TestIO feature ID, globally unique)
        product_id: Foreign key to products table
        title: Feature name
        description: Feature description
        howtofind: Instructions on how to find the feature
        user_stories: JSON array of user story title strings (embedded, not normalized)
        raw_data: JSON blob containing full feature data from API
        last_synced: Timestamp of last successful sync from API
        product: Relationship to parent Product
        test_features: Relationship to TestFeature entities (NEW - STORY-041)
    """

    __tablename__ = "features"

    # Primary Key
    id: int = Field(primary_key=True)

    # Foreign Keys
    product_id: int = Field(foreign_key="products.id", index=True)

    # Feature Data
    title: str = Field()
    description: str | None = Field(default=None)
    howtofind: str | None = Field(default=None)

    # Embedded User Stories (ADR-013)
    user_stories: str = Field(default="[]")
    """JSON array of user story title strings from features endpoint.

    Example: ["On mobile, I can tap to open tabs", "On mobile, I can close sheet"]

    Each string is a testable user journey for this feature. Stored as embedded
    JSON because API doesn't provide user story IDs in features endpoint.

    When API is improved (adds 'id' to user_stories array), we can migrate to
    normalized UserStory table with feature_id foreign key.
    """

    # Section Membership (STORY-038)
    section_ids: str = Field(default="[]")
    """JSON array of section IDs this feature belongs to.

    Example: [123, 456, 789]

    Features are shared across sections in sectioned products. This field tracks
    which sections contain this feature. For non-sectioned products, this is empty [].

    Stored as JSON array (denormalized) to avoid junction table complexity.
    When we add a Sections table in the future, we can migrate to normalized many-to-many.
    """

    # Raw API Response (for future schema evolution)
    raw_data: str = Field()  # JSON stored as TEXT in SQLite

    # Sync Metadata
    last_synced: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    product: "Product" = Relationship(back_populates="features")

    # NEW (STORY-041): Relationship to test features
    test_features: list["TestFeature"] = Relationship(back_populates="feature")
