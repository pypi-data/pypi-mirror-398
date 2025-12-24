"""
Product ORM model.

Represents a TestIO product with customer isolation and JSON data storage.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from testio_mcp.models.orm.feature import Feature


class Product(SQLModel, table=True):
    """
    Product entity with customer isolation.

    Stores product information from TestIO API with denormalized fields
    for analytics and JSON data field for backup. Includes last_synced
    timestamp for background sync staleness tracking.

    STORY-062: Simplified to single last_synced timestamp (removed features_synced_at).
    SyncService updates last_synced after all phases complete.

    STORY-054: Added product_type for filtering without JSON extraction.

    Attributes:
        id: Primary key (TestIO product ID)
        customer_id: Customer identifier for multi-tenant isolation
        title: Product name/title (denormalized from JSON for analytics)
        product_type: Product type (denormalized from JSON for filtering)
        data: JSON blob containing full product data from API (backup)
        last_synced: Timestamp of last successful background sync
    """

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)

    # Denormalized fields for analytics (extracted from data JSON)
    title: str = Field()  # Product name from JSON
    product_type: str | None = Field(
        default=None, max_length=50, index=True
    )  # Product type (STORY-054)

    data: str = Field()  # JSON stored as TEXT in SQLite (backup)
    last_synced: datetime | None = Field(default=None)

    # Relationships
    features: list["Feature"] = Relationship(back_populates="product")
