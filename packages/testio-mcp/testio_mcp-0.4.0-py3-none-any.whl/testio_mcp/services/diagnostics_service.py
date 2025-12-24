"""Diagnostics service for server health and monitoring operations.

This service consolidates diagnostic operations from multiple tools:
- API connectivity (health_check)
- Database statistics (get_database_stats)
- Sync history (get_sync_history)

STORY-060: Consolidate diagnostic tools to reduce token overhead.

Responsibilities:
- Server diagnostics orchestration
- API health checks via ProductService
- Database stats aggregation via PersistentCache
- Sync history and circuit breaker status

Does NOT handle:
- MCP protocol formatting
- User-facing error messages
- HTTP transport concerns
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from testio_mcp.services.base_service import BaseService

logger = logging.getLogger(__name__)


def format_relative_time(timestamp_str: str | None) -> str | None:
    """Format timestamp as relative time (e.g., '5 minutes ago', '2 hours ago').

    Args:
        timestamp_str: ISO 8601 timestamp string (e.g., '2025-11-19T10:30:00+00:00')

    Returns:
        Human-readable relative time string, or None if timestamp is None
    """
    if timestamp_str is None:
        return None

    try:
        # Parse timestamp (handles both UTC and timezone-aware)
        timestamp = datetime.fromisoformat(timestamp_str)
        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = timestamp.replace(tzinfo=UTC)

        # Calculate time difference
        now = datetime.now(UTC)
        delta = now - timestamp

        # Format relative time
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "just now"
        elif seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
    except (ValueError, TypeError):
        return None


# Pydantic Output Models
# NOTE: Models use nested BaseModel classes for type safety.
# Schemas are post-processed with inline_schema_refs() in the tool layer.


class ApiStatus(BaseModel):
    """API connectivity status."""

    connected: bool = Field(description="API authentication successful")
    latency_ms: float | None = Field(
        default=None, description="API response latency in milliseconds"
    )
    product_count: int = Field(description="Number of products available", ge=0)
    message: str = Field(description="Status message")


class DatabaseStatus(BaseModel):
    """Database statistics."""

    size_mb: float = Field(description="Database file size in megabytes")
    path: str = Field(description="Database file path")
    test_count: int = Field(description="Total tests in database", ge=0)
    product_count: int = Field(description="Total products in database", ge=0)
    feature_count: int = Field(description="Total features in database", ge=0)
    bug_count: int = Field(description="Total bugs in database", ge=0)


class SyncStatus(BaseModel):
    """Sync operation status."""

    last_sync: str | None = Field(default=None, description="Last sync timestamp (ISO 8601)")
    last_sync_relative: str | None = Field(
        default=None, description="Last sync relative time (e.g., '5 minutes ago')"
    )
    last_sync_duration_seconds: float | None = Field(
        default=None, description="Last sync duration in seconds"
    )
    success_rate_24h: float | None = Field(
        default=None, description="Success rate over last 24 hours (%), null if no syncs"
    )
    syncs_completed_24h: int = Field(description="Completed syncs in last 24 hours", ge=0)
    syncs_failed_24h: int = Field(description="Failed syncs in last 24 hours", ge=0)
    circuit_breaker_active: bool = Field(
        description="Circuit breaker active (3+ failures in 5 min)"
    )


class StorageRange(BaseModel):
    """Test data date range."""

    oldest_test_date: str | None = Field(default=None, description="Oldest test end date")
    newest_test_date: str | None = Field(default=None, description="Newest test end date")


class SyncEvent(BaseModel):
    """Sync event details."""

    started_at: str = Field(description="Event start timestamp (ISO 8601)")
    started_at_relative: str | None = Field(
        default=None, description="Event start relative time (e.g., '5 minutes ago')"
    )
    completed_at: str | None = Field(
        default=None, description="Event completion timestamp (ISO 8601)"
    )
    status: str = Field(description="Event status (running, completed, failed)")
    duration_seconds: float | None = Field(default=None, description="Event duration in seconds")
    tests_synced: int | None = Field(default=None, description="Tests synced", ge=0)
    error: str | None = Field(default=None, description="Error message if failed")


class ServerDiagnostics(BaseModel):
    """Consolidated server diagnostics."""

    api: ApiStatus = Field(description="API connectivity status")
    database: DatabaseStatus = Field(description="Database statistics")
    sync: SyncStatus = Field(description="Sync operation status")
    storage: StorageRange = Field(description="Test data date range")
    events: list[SyncEvent] | None = Field(
        default=None, description="Recent sync events (if requested)"
    )


class DiagnosticsService(BaseService):
    """Business logic for server diagnostics operations.

    Consolidates health check, database stats, and sync history.

    Example:
        ```python
        service = DiagnosticsService(client=client, cache=cache)
        diagnostics = await service.get_server_diagnostics()
        ```
    """

    def __init__(self, client: Any, cache: Any) -> None:
        """Initialize service with API client and cache.

        Args:
            client: TestIO API client
            cache: PersistentCache for database operations
        """
        super().__init__(client)
        self.cache = cache

    async def get_server_diagnostics(
        self,
        include_sync_events: bool = False,
        sync_event_limit: int = 5,
    ) -> dict[str, Any]:
        """Get comprehensive server diagnostics.

        Orchestrates data collection from multiple sources:
        - API health via ProductService pattern
        - Database stats via PersistentCache
        - Sync status and history via PersistentCache

        Args:
            include_sync_events: Include recent sync event history
            sync_event_limit: Max sync events to return (1-20)

        Returns:
            Dictionary with api, database, sync, storage, and optional events

        Raises:
            Exception: If critical diagnostics fail (logged, not raised)
        """
        logger.info("Gathering server diagnostics")

        # Clamp sync_event_limit to valid range
        sync_event_limit = max(1, min(sync_event_limit, 20))

        # 1. API Health Check (via ProductService pattern)
        api_status = await self._check_api_health()

        # 2. Database Statistics
        database_status = await self._get_database_stats()

        # 3. Sync Status
        sync_status = await self._get_sync_status()

        # 4. Storage Range
        storage_range = await self._get_storage_range()

        # 5. Optional Sync Events
        events = None
        if include_sync_events:
            events = await self._get_sync_events(limit=sync_event_limit)

        # Build consolidated diagnostics
        result = ServerDiagnostics(
            api=api_status,
            database=database_status,
            sync=sync_status,
            storage=storage_range,
            events=events,
        )

        logger.info("Server diagnostics gathered successfully")
        return result.model_dump(by_alias=True, exclude_unset=True)

    async def _check_api_health(self) -> ApiStatus:
        """Check API connectivity and measure latency.

        Uses ProductService pattern for consistency.

        Returns:
            ApiStatus with connectivity, latency, and product count
        """
        from time import perf_counter

        from testio_mcp.services.product_service import ProductService

        try:
            # Measure API latency
            start_time = perf_counter()

            # Use ProductService for consistency (benefits from caching)
            service = ProductService(
                client=self.client,
                cache=self.cache,
                session_factory=self.cache.async_session_maker,
                customer_id=self.cache.customer_id,
            )
            result = await service.list_products()

            latency_ms = round((perf_counter() - start_time) * 1000, 2)
            product_count = result["total_count"]

            logger.info(f"API health check passed: {product_count} products, {latency_ms}ms")

            return ApiStatus(
                connected=True,
                latency_ms=latency_ms,
                product_count=product_count,
                message=f"Connected. {product_count} products available.",
            )

        except Exception as e:
            logger.error(f"API health check failed: {str(e)}")
            return ApiStatus(
                connected=False,
                latency_ms=None,
                product_count=0,
                message=f"API connection failed: {str(e)}",
            )

    async def _get_database_stats(self) -> DatabaseStatus:
        """Get database statistics.

        Returns:
            DatabaseStatus with size, path, and entity counts
        """
        return DatabaseStatus(
            size_mb=await self.cache.get_db_size_mb(),
            path=str(self.cache.db_path),
            test_count=await self.cache.count_tests(),
            product_count=await self.cache.count_products(),
            feature_count=await self.cache.count_features(),
            bug_count=await self.cache.count_bugs(),
        )

    async def _get_sync_status(self) -> SyncStatus:
        """Get sync operation status and circuit breaker state.

        Returns:
            SyncStatus with last sync info, 24h statistics, circuit breaker
        """
        # Get recent sync events for 24h statistics
        events = await self.cache.get_sync_events(limit=50)

        # Filter events from last 24 hours
        now = datetime.now(UTC)
        day_ago = now - timedelta(hours=24)

        recent_events = [e for e in events if datetime.fromisoformat(e["started_at"]) >= day_ago]

        # Calculate 24h statistics
        completed_24h = sum(1 for e in recent_events if e["status"] == "completed")
        failed_24h = sum(1 for e in recent_events if e["status"] == "failed")
        total_24h = completed_24h + failed_24h

        # Success rate is None if no syncs in 24h (more honest than defaulting to 100%)
        success_rate_24h = round((completed_24h / total_24h * 100), 1) if total_24h > 0 else None

        # Get last sync info
        last_sync = events[0] if events else None
        last_sync_timestamp = last_sync["started_at"] if last_sync else None
        last_sync_duration = last_sync.get("duration_seconds") if last_sync else None

        # Check circuit breaker (3+ failures in last 5 minutes)
        recent_failures = await self.cache.count_sync_failures_since(now - timedelta(minutes=5))
        circuit_breaker_active = recent_failures >= 3

        return SyncStatus(
            last_sync=last_sync_timestamp,
            last_sync_relative=format_relative_time(last_sync_timestamp),
            last_sync_duration_seconds=last_sync_duration,
            success_rate_24h=success_rate_24h,
            syncs_completed_24h=completed_24h,
            syncs_failed_24h=failed_24h,
            circuit_breaker_active=circuit_breaker_active,
        )

    async def _get_storage_range(self) -> StorageRange:
        """Get test data date range.

        Returns:
            StorageRange with oldest and newest test dates
        """
        return StorageRange(
            oldest_test_date=await self.cache.get_oldest_test_date(),
            newest_test_date=await self.cache.get_newest_test_date(),
        )

    async def _get_sync_events(self, limit: int) -> list[SyncEvent]:
        """Get recent sync events.

        Args:
            limit: Max events to return (already clamped to 1-20)

        Returns:
            List of SyncEvent models
        """
        events = await self.cache.get_sync_events(limit=limit)

        # Convert to SyncEvent models with relative time
        return [
            SyncEvent(
                started_at=e["started_at"],
                started_at_relative=format_relative_time(e["started_at"]),
                completed_at=e.get("completed_at"),
                status=e["status"],
                duration_seconds=e.get("duration_seconds"),
                tests_synced=e.get("tests_synced"),
                error=e.get("error"),
            )
            for e in events
        ]
