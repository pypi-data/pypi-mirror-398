"""Data Transfer Objects for service layer contracts.

These DTOs define the internal service layer representation using
database field names (id, not test_id). They provide type safety
for transformer functions that convert to API models.

Key Principle: Services work with 'id', transformers convert to 'test_id'
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServiceTestDTO(BaseModel):
    """Internal representation of test data from service layer.

    Uses database field names (id) for consistency with repository layer.
    Transformers convert this to API models with semantic names (test_id).

    Validation strategy: extra="ignore" allows forward compatibility as the API evolves.
    Required fields and types are validated, but additional fields are permitted
    (database stores full API responses). This prevents breakage when upstream adds fields.

    Attributes:
        id: Test identifier (database field name)
        title: Test title
        goal: Test objective (optional)
        status: Test lifecycle status
        review_status: Review status (optional)
        testing_type: Type of testing
        duration: Test duration in minutes (optional)
        starts_at: Test start timestamp (optional)
        ends_at: Test end timestamp (optional)
        test_environment: Test environment configuration (optional, STORY-072)
    """

    model_config = ConfigDict(extra="ignore")  # Allow extra fields (API may evolve)

    id: int = Field(description="Test ID (database field name)")
    title: str = Field(description="Test title")
    goal: str | None = Field(default=None, description="Test goal/objective")
    status: str = Field(description="Test status")
    review_status: str | None = Field(default=None, description="Review status (if applicable)")
    testing_type: str = Field(description="Testing type")
    duration: int | None = Field(default=None, description="Test duration in minutes")
    starts_at: str | None = Field(default=None, description="Test start timestamp")
    ends_at: str | None = Field(default=None, description="Test end timestamp")
    test_environment: dict[str, Any] | None = Field(
        default=None, description="Test environment configuration (STORY-072)"
    )


class ServiceProductDTO(BaseModel):
    """Internal representation of product data from service layer.

    Attributes:
        id: Product identifier (database field name)
        name: Product name
        type: Product type
    """

    id: int = Field(description="Product ID (database field name)")
    name: str = Field(description="Product name")
    type: str = Field(description="Product type")


class ServiceBugDTO(BaseModel):
    """Internal representation of bug data from service layer.

    Attributes:
        id: Bug identifier (database field name)
        title: Bug title
        severity: Bug severity level
        status: Bug status
        known: Whether bug is marked as known issue (STORY-072)
    """

    id: int = Field(description="Bug ID (database field name)")
    title: str = Field(description="Bug title")
    severity: str = Field(description="Bug severity level")
    status: str = Field(description="Bug status")
    known: bool = Field(
        default=False, description="Whether bug is marked as known issue (STORY-072)"
    )
