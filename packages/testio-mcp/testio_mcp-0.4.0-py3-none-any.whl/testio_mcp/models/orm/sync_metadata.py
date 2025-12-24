"""
SyncMetadata ORM model.

Represents key-value metadata storage for sync state and configuration.
"""

from sqlmodel import Field, SQLModel


class SyncMetadata(SQLModel, table=True):
    """
    Sync metadata entity for key-value storage.

    Stores metadata such as schema version, problematic test tracking,
    and other configuration values needed for sync operations.

    Attributes:
        key: Primary key (metadata key name)
        value: JSON value stored as TEXT in SQLite
    """

    __tablename__ = "sync_metadata"

    key: str = Field(primary_key=True)
    value: str | None = Field(default=None)  # JSON stored as TEXT in SQLite
