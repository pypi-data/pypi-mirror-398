"""
SyncEvent ORM model.

Represents a sync operation event for observability and circuit breaker functionality.
"""

from sqlmodel import Field, SQLModel


class SyncEvent(SQLModel, table=True):
    """
    Sync event entity for observability and circuit breaker.

    Tracks sync operations (initial sync, background refresh, CLI sync) with
    timing, statistics, and error information for monitoring and
    debugging sync issues.

    Attributes:
        id: Primary key (auto-increment)
        event_type: Type of sync event (e.g., initial_sync, background_refresh, cli_sync)
        started_at: Event start timestamp (TEXT in SQLite)
        completed_at: Event completion timestamp (TEXT in SQLite, nullable)
        status: Event status (e.g., success, failure, running)
        products_synced: Number of products synced in this event
        tests_discovered: Number of tests discovered in this event
        tests_refreshed: Number of tests refreshed in this event
        features_refreshed: Number of features refreshed in this event (STORY-038)
        duration_seconds: Event duration in seconds
        error_message: Error message if event failed (nullable)
        trigger_source: Source that triggered the sync (e.g., startup, scheduled, manual)
    """

    __tablename__ = "sync_events"

    id: int | None = Field(default=None, primary_key=True)
    event_type: str = Field()
    started_at: str = Field(index=True)  # TEXT in SQLite
    completed_at: str | None = Field(default=None)  # TEXT in SQLite
    status: str = Field(index=True)
    products_synced: int | None = Field(default=None)
    tests_discovered: int | None = Field(default=None)
    tests_refreshed: int | None = Field(default=None)
    features_refreshed: int | None = Field(default=None)  # NEW (STORY-038)
    duration_seconds: float | None = Field(default=None)
    error_message: str | None = Field(default=None)
    trigger_source: str | None = Field(default=None)
