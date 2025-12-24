"""
Test ORM model.

Represents an exploratory test with lifecycle tracking and bug relationships.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.bug import Bug
    from testio_mcp.models.orm.test_feature import TestFeature
    from testio_mcp.models.orm.test_platform import TestPlatform
    from testio_mcp.models.orm.user import User


class Test(SQLModel, table=True):
    """
    Exploratory test entity with lifecycle tracking.

    Note: __test__ = False prevents pytest from collecting this as a test class.

    Stores test information from TestIO API with JSON data field
    for flexible schema evolution. Includes multiple timestamps
    for lifecycle tracking and bug sync optimization.

    STORY-054: Added title, testing_type, rich text fields (goal, instructions, out_of_scope),
    and configuration flags (enable_low/high/critical). Removed created_at (unused).

    Attributes:
        id: Primary key (TestIO test ID)
        customer_id: Customer identifier for multi-tenant isolation
        product_id: Foreign key to products table
        data: JSON blob containing full test data from API
        status: Test lifecycle status (running, locked, archived, etc.)
        title: Test title (denormalized for display/sorting - STORY-054)
        testing_type: Test type - coverage/focused/rapid (denormalized for filtering - STORY-054)
        start_at: Test start timestamp
        end_at: Test end timestamp
        synced_at: Timestamp of last successful sync from API
        bugs_synced_at: Timestamp of last bug sync for this test
        goal: Test goal rich text (denormalized - STORY-054)
        instructions: Test instructions rich text (denormalized - STORY-054)
        out_of_scope: Out of scope details rich text (denormalized - STORY-054)
        enable_low: Enable low severity bugs flag (STORY-054)
        enable_high: Enable high severity bugs flag (STORY-054)
        enable_critical: Enable critical severity bugs flag (STORY-054)
        created_by: Customer username who created the test (denormalized)
        submitted_by: Customer username who submitted the test (denormalized)
        created_by_user_id: Foreign key to users table (customer who created)
        submitted_by_user_id: Foreign key to users table (customer who submitted)
        bugs: Relationship to associated Bug entities
        test_features: Relationship to associated TestFeature entities (NEW - STORY-041)
        created_by_user: Relationship to User entity who created this test
        submitted_by_user: Relationship to User entity who submitted this test
    """

    __tablename__ = "tests"
    __test__ = False  # Prevent pytest collection

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    product_id: int = Field(index=True)
    data: str = Field()  # JSON stored as TEXT in SQLite
    status: str = Field(index=True)

    # Display/sorting fields (STORY-054)
    title: str | None = Field(default=None, max_length=500, index=True)
    testing_type: str | None = Field(default=None, max_length=50, index=True)

    # Timestamps
    start_at: datetime | None = Field(default=None, index=True)
    end_at: datetime | None = Field(default=None, index=True)
    synced_at: datetime | None = Field(default=None)
    bugs_synced_at: datetime | None = Field(default=None)

    # Rich text fields (STORY-054)
    goal: str | None = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    instructions: str | None = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    out_of_scope: str | None = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    test_environment: dict[str, Any] | None = Field(
        default=None, sa_column=sa.Column(sa.JSON, nullable=True)
    )

    # Configuration flags (STORY-054)
    enable_low: bool | None = Field(default=None)
    enable_high: bool | None = Field(default=None)
    enable_critical: bool | None = Field(default=None)

    # Customer user metadata (denormalized for query performance)
    created_by: str | None = Field(default=None, max_length=255, index=True)
    submitted_by: str | None = Field(default=None, max_length=255, index=True)

    # Foreign keys to users table
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    submitted_by_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)

    # Relationship to bugs
    bugs: list["Bug"] = Relationship(back_populates="test")

    # NEW (STORY-041): Relationship to test features
    # CASCADE DELETE: When test is deleted, delete associated test_features
    test_features: list["TestFeature"] = Relationship(
        back_populates="test", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Platform requirements extracted from data.requirements JSON
    # CASCADE DELETE: When test is deleted, delete associated platforms
    platforms: list["TestPlatform"] = Relationship(
        back_populates="test", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Relationships to User
    # Note: Must use Optional["X"] syntax for SQLAlchemy relationship forward references
    # The "X | None" syntax doesn't work with SQLAlchemy's class registry resolver
    created_by_user: Optional["User"] = Relationship(
        back_populates="tests_created",
        sa_relationship_kwargs={"foreign_keys": "Test.created_by_user_id"},
    )
    submitted_by_user: Optional["User"] = Relationship(
        back_populates="tests_submitted",
        sa_relationship_kwargs={"foreign_keys": "Test.submitted_by_user_id"},
    )
