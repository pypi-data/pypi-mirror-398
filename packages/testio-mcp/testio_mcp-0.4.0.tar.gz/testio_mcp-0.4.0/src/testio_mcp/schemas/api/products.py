"""Product-related API response schemas.

Contains schemas for product information used in API responses.
These use semantic field names (id, name, type) for external APIs.
"""

from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """Product information embedded in test/feature data."""

    id: int = Field(description="Product ID (integer from API)")
    name: str = Field(description="Product name")


class ProductInfoSummary(BaseModel):
    """Product information summary with additional metadata."""

    id: int = Field(description="Product ID (integer from API)")
    name: str = Field(description="Product name")
    type: str = Field(description="Product type")
