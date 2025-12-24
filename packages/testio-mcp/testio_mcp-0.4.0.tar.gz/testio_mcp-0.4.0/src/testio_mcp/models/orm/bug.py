"""
Bug ORM model.

Represents a bug report associated with an exploratory test.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.test import Test
    from testio_mcp.models.orm.test_feature import TestFeature
    from testio_mcp.models.orm.user import User


class Bug(SQLModel, table=True):
    """
    Bug entity associated with exploratory tests.

    Stores bug information from TestIO API with structured fields
    for common attributes and raw_data for complete API response.

    Attributes:
        id: Primary key (TestIO bug ID)
        customer_id: Customer identifier for multi-tenant isolation
        test_id: Foreign key to tests table
        title: Bug title/summary
        severity: Bug severity level (e.g., critical, high, medium, low)
        status: Bug status (e.g., open, closed, in_progress)
        actual_result: Actual result text (denormalized for FTS - STORY-063)
        expected_result: Expected result text (denormalized for FTS - STORY-063)
        rejection_reason: Parsed rejection reason for rejected bugs (STORY-067)
        steps: Reproduction steps text (denormalized for FTS)
        reported_at: Timestamp when bug was reported
        raw_data: Complete bug data from API as JSON text
        synced_at: Timestamp of last successful sync from API
        reported_by_user_id: Foreign key to users table (tester who reported bug)
        test_feature_id: Foreign key to test_features table (NEW - direct feature attribution)
        test: Relationship to parent Test entity
        reported_by_user: Relationship to User entity who reported this bug
        test_feature: Relationship to TestFeature entity (direct link to tested feature)
    """

    __tablename__ = "bugs"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    test_id: int = Field(foreign_key="tests.id", index=True)
    title: str = Field()
    severity: str | None = Field(default=None)
    status: str | None = Field(default=None)

    # Rich text fields for FTS (STORY-063)
    actual_result: str | None = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    expected_result: str | None = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    rejection_reason: str | None = Field(
        default=None, sa_column=sa.Column(sa.Text(), nullable=True)
    )
    steps: str | None = Field(
        default=None, sa_column=sa.Column(sa.Text(), nullable=True)
    )  # Reproduction steps (denormalized for FTS)
    known: bool = Field(
        default=False,
        sa_column=sa.Column(sa.Boolean, nullable=False, server_default=sa.text("0")),
    )

    # Timestamp fields
    reported_at: datetime | None = Field(default=None)  # When bug was reported
    raw_data: str = Field()  # JSON stored as TEXT in SQLite
    synced_at: datetime | None = Field(default=None)

    # Foreign key to users table
    reported_by_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)

    # NEW (STORY-041): Direct link to TestFeature being tested when bug was found
    test_feature_id: int | None = Field(
        default=None,
        foreign_key="test_features.id",
        index=True,
        description="Direct link to TestFeature being tested when bug was found",
    )

    # Relationship to parent test
    test: "Test" = Relationship(back_populates="bugs")

    # Relationship to User
    # Note: Must use Optional["X"] syntax for SQLAlchemy relationship forward references
    # The "X | None" syntax doesn't work with SQLAlchemy's class registry resolver
    reported_by_user: Optional["User"] = Relationship(back_populates="bugs_reported")

    # NEW (STORY-041): Relationship to TestFeature
    test_feature: Optional["TestFeature"] = Relationship()
