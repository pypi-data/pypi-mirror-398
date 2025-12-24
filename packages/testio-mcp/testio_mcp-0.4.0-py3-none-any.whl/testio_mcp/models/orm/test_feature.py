"""TestFeature ORM model.

Represents a feature included in a specific test cycle.
Acts as the join table between Tests and Features, but with historical context.
"""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.feature import Feature
    from testio_mcp.models.orm.test import Test


class TestFeature(SQLModel, table=True):
    """Represents a feature included in a specific test cycle.

    Acts as the join table between Tests and Features, but with historical context.
    Stores a snapshot of the feature's state at the time of the test.
    """

    __test__ = False
    __tablename__ = "test_features"

    # Primary Key (from API response 'id')
    id: int = Field(primary_key=True)

    # Foreign Keys
    customer_id: int = Field(index=True, description="Customer ID for security filtering")
    test_id: int = Field(foreign_key="tests.id", index=True)
    feature_id: int = Field(foreign_key="features.id", index=True)

    # Snapshotted Data (Historical Record)
    title: str = Field()
    description: str | None = Field(default=None)
    howtofind: str | None = Field(default=None)

    # Testing Context
    user_stories: str = Field(default="[]")  # JSON array of strings

    # Flags (for future use)
    enable_default: bool = Field(default=False)
    enable_content: bool = Field(default=False)
    enable_visual: bool = Field(default=False)

    # Relationships
    test: "Test" = Relationship(back_populates="test_features")
    feature: "Feature" = Relationship(back_populates="test_features")
