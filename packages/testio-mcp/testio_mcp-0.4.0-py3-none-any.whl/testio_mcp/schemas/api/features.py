"""Feature-related API response schemas.

Contains schemas for feature information used in API responses.
These use semantic field names for external APIs.
"""

from pydantic import BaseModel, Field


class FeatureInfo(BaseModel):
    """Feature information embedded in test data."""

    id: int = Field(description="Feature ID (integer from API)")
    name: str = Field(description="Feature name")
