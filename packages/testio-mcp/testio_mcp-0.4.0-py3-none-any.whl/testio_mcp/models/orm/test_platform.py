"""
TestPlatform ORM model.

Normalized platform/OS requirements extracted from Test.data.requirements JSON.
Enables efficient analytics grouping by platform without JSON parsing at query time.
"""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.test import Test


class TestPlatform(SQLModel, table=True):
    """
    Platform requirement extracted from Test.data.requirements.

    Each test can have multiple platform requirements (e.g., iOS smartphone + iOS tablet,
    or Windows + Mac OS). This table normalizes those requirements for efficient querying.

    Attributes:
        id: Primary key (auto-generated)
        test_id: Foreign key to tests table
        operating_system_id: TestIO OS ID (for reference)
        operating_system_name: OS name for grouping (e.g., "iOS", "Android", "Windows")
        category: Device category (e.g., "smartphone", "tablet", "desktop")
        test: Relationship to parent Test entity
    """

    __tablename__ = "test_platforms"

    id: int | None = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="tests.id", index=True)
    operating_system_id: int | None = Field(default=None)
    operating_system_name: str = Field(index=True)
    category: str | None = Field(default=None, index=True)

    # Relationship to parent test
    # Note: Must use Optional["X"] syntax for SQLAlchemy relationship forward references
    test: Optional["Test"] = Relationship(back_populates="platforms")
