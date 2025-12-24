"""User ORM model.

Represents users extracted from bug reports (testers) and test metadata (customers).
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.bug import Bug
    from testio_mcp.models.orm.test import Test


class User(SQLModel, table=True):
    """User entity - testers and customer users.

    Represents users extracted from:
    - Bug reports (author.name field) → Tester users
    - Test metadata (created_by, submitted_by fields) → Customer users

    Relationships:
    - bugs_reported: Bugs reported by this user (one-to-many, testers only)
    - tests_created: Tests created by this user (one-to-many, customers only)
    - tests_submitted: Tests submitted by this user (one-to-many, customers only)

    Attributes:
        id: Primary key (auto-increment)
        customer_id: Customer identifier for multi-tenant isolation
        username: User's name/username (unique per customer for deduplication)
        user_type: User classification ("tester" or "customer")
        raw_data: Raw API data for this user (JSON stored as TEXT in SQLite)
        first_seen: Timestamp when user was first extracted
        last_seen: Timestamp when user was last seen in API data
        bugs_reported: Bugs reported by this tester user
        tests_created: Tests created by this customer user
        tests_submitted: Tests submitted by this customer user
    """

    __tablename__ = "users"

    # Primary Key
    id: int | None = Field(default=None, primary_key=True)

    # Multi-tenant Isolation
    customer_id: int = Field(index=True)

    # User Profile
    username: str = Field(max_length=255, index=True)
    user_type: str = Field(max_length=50, index=True)  # "tester", "customer"

    # Raw API Data (for future schema evolution if API adds more fields)
    raw_data: str = Field(default="{}")  # JSON stored as TEXT in SQLite

    # Activity Tracking
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    bugs_reported: list["Bug"] = Relationship(back_populates="reported_by_user")
    tests_created: list["Test"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "Test.created_by_user_id"},
    )
    tests_submitted: list["Test"] = Relationship(
        back_populates="submitted_by_user",
        sa_relationship_kwargs={"foreign_keys": "Test.submitted_by_user_id"},
    )

    @model_validator(mode="after")
    def ensure_timezone_aware(self) -> Self:
        """Ensure datetime fields are timezone-aware.

        SQLAlchemy's default DateTime type returns naive datetimes when reading
        from SQLite, even if timezone-aware datetimes were written. This validator
        ensures all datetimes are consistently timezone-aware by converting naive
        datetimes to UTC.

        Returns:
            Self with timezone-aware datetimes
        """
        if self.first_seen is not None and self.first_seen.tzinfo is None:
            self.first_seen = self.first_seen.replace(tzinfo=UTC)
        if self.last_seen is not None and self.last_seen.tzinfo is None:
            self.last_seen = self.last_seen.replace(tzinfo=UTC)
        return self
