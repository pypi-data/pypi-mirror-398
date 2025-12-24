"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables with type validation.
"""

from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # TestIO API Configuration
    TESTIO_CUSTOMER_API_BASE_URL: str = Field(
        default="https://api.stage-a.space/customer/v2",
        description="TestIO Customer API base URL",
    )
    TESTIO_CUSTOMER_API_TOKEN: str = Field(
        ...,
        description="TestIO Customer API authentication token (required)",
    )

    # HTTP Client Configuration
    MAX_CONCURRENT_API_REQUESTS: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent API requests (semaphore limit)",
    )
    CONNECTION_POOL_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="HTTP connection pool size",
    )
    CONNECTION_POOL_MAX_KEEPALIVE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum connections to keep alive",
    )
    HTTP_TIMEOUT_SECONDS: float = Field(
        default=90.0,
        ge=1.0,
        le=300.0,
        description="HTTP request timeout in seconds",
    )
    MAX_ACQUIRE_TIMEOUT_SECONDS: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Maximum time to wait for connection pool (prevents indefinite blocking)",
    )

    # Database Concurrency Configuration (STORY-062 follow-up)
    MAX_CONCURRENT_DB_WRITES: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum concurrent database write operations. "
        "Controls how many async batch operations can write to SQLite simultaneously. "
        "SQLite serializes writes internally (even with WAL mode), so this primarily "
        "limits memory/connection pressure from queued sessions. "
        "Default: 1 (most conservative, recommended for SQLite). "
        "Higher values (2-5) allow overlapping API I/O with DB writes for batch operations.",
    )

    # Pagination Configuration (STORY-020)
    TESTIO_DEFAULT_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=200,
        description="Default page size for list_tests tool. "
        "Configurable via environment variable. Default: 100",
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format (json or text)",
    )
    LOG_FILE: str = Field(
        default="~/.testio-mcp/logs/server.log",
        description="Log file path for file-based logging. "
        "Enables debugging during MCP operation. Default: ~/.testio-mcp/logs/server.log",
    )

    # HTTP Server Configuration (STORY-027)
    TESTIO_HTTP_HOST: str = Field(
        default="127.0.0.1",
        description="HTTP server host for http transport mode. "
        "Default: 127.0.0.1 (localhost-only for security). "
        "Use 0.0.0.0 to allow external connections (not recommended for production).",
    )
    TESTIO_HTTP_PORT: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="HTTP server port for http transport mode. "
        "Default: 8080. Valid range: 1024-65535 (unprivileged ports).",
    )

    # Auto-Acceptance Configuration (STORY-005c)
    AUTO_ACCEPTANCE_ALERT_THRESHOLD: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Alert when auto-acceptance rate exceeds this threshold (0.0-1.0). "
        "Auto-acceptance occurs when bugs timeout after 10 days without customer review. "
        "Default 0.20 (20%) indicates significant feedback loop degradation.",
    )

    # Playbook Thresholds - Health Indicator Configuration
    # These thresholds determine health status (healthy/warning/critical) for key metrics.
    # Reference: CSM Playbook - Quick Reference: Key Thresholds
    # Direction: "above" = high values are bad, "below" = low values are bad
    PLAYBOOK_REJECTION_WARNING: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Rejection rate warning threshold. "
        "Rates above this trigger 'warning' status. Default: 20%",
    )
    PLAYBOOK_REJECTION_CRITICAL: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Rejection rate critical threshold. "
        "Rates above this trigger 'critical' status. Default: 35%",
    )
    PLAYBOOK_AUTO_ACCEPTANCE_WARNING: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Auto-acceptance rate warning threshold. "
        "Rates above this trigger 'warning' status. Default: 20%",
    )
    PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Auto-acceptance rate critical threshold. "
        "Rates above this trigger 'critical' status. Default: 40%",
    )
    PLAYBOOK_REVIEW_WARNING: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Review rate warning threshold. "
        "Rates BELOW this trigger 'warning' status. Default: 80%",
    )
    PLAYBOOK_REVIEW_CRITICAL: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Review rate critical threshold. "
        "Rates BELOW this trigger 'critical' status. Default: 60%",
    )

    # Local Data Store Configuration (STORY-021)
    TESTIO_CUSTOMER_ID: int = Field(
        default=1,
        gt=0,
        description="Customer ID for local database isolation (default: 1). "
        "For single-tenant deployments, the default value is sufficient. "
        "For multi-tenant deployments (STORY-010), use unique IDs per customer. "
        "Note: This is a local identifier and does not need to match TestIO's "
        "internal customer ID.",
    )
    TESTIO_CUSTOMER_NAME: str = Field(
        default="default",
        description="Human-friendly customer name for display purposes. "
        "This is optional and defaults to 'default'.",
    )
    TESTIO_DB_PATH: str = Field(
        default="~/.testio-mcp/cache.db",
        description="SQLite database path for persistent local cache. "
        "Defaults to ~/.testio-mcp/cache.db",
    )
    TESTIO_REFRESH_INTERVAL_SECONDS: int = Field(
        default=3600,
        ge=0,
        description="Background refresh interval for mutable tests in seconds. "
        "Set to 0 to disable periodic background refresh "
        "(initial sync on startup still runs if data is stale). "
        "Default: 3600 (1 hour).",
    )
    TESTIO_FORCE_INITIAL_SYNC: bool = Field(
        default=False,
        description="Force initial sync on startup regardless of last sync timestamps. "
        "When True, bypasses staleness checks and always runs full initial sync. "
        "Useful for development and testing. Default: False",
    )
    TESTIO_PRODUCT_IDS: list[int] | None = Field(
        default=None,
        description="Comma-separated list of product IDs to sync/query. "
        "If set, only these products will be synced and queried. "
        "Accepts comma-separated string (e.g., '25073,598,1024') or JSON array. "
        "Default: None (sync/query all products).",
    )
    TESTIO_SYNC_SINCE: str | None = Field(
        default=None,
        description="Default date filter for sync operations (ISO date or relative). "
        "Only syncs tests with end_at >= this date. Applies to both background refresh "
        "and CLI sync commands (can be overridden with --since flag). "
        "Examples: '2023-01-01', '90 days ago', 'last year'. "
        "Default: None (sync all tests).",
    )
    TESTIO_SKIP_MIGRATIONS: bool = Field(
        default=False,
        description="⚠️ DEV/CI ONLY: Skip Alembic database migrations on server startup. "
        "When enabled, server starts without running migrations. "
        "WARNING: Database schema may be out of sync! "
        "Use only for development or CI environments where migrations are managed separately. "
        "Default: False (migrations run on startup).",
    )

    # Bug Caching Configuration (STORY-024)
    # Unified Cache TTL Configuration (STORY-046, Epic-007)
    CACHE_TTL_SECONDS: int = Field(
        default=3600,  # 1 hour
        ge=60,  # Min 1 minute
        le=86400,  # Max 24 hours
        description="Unified staleness threshold for cached data in seconds. "
        "Applies to: bugs, features, and mutable test metadata. "
        "Data older than this threshold will be refreshed from API on demand. "
        "Mutable tests (running, locked, customer_finalized, etc.) refresh metadata "
        "if older than this threshold. Immutable tests (archived, cancelled) "
        "never refresh. Default: 3600 (1 hour). "
        "BREAKING CHANGE: Replaces BUG_CACHE_TTL_SECONDS, FEATURE_CACHE_TTL_SECONDS, "
        "and TEST_CACHE_TTL_SECONDS from previous versions.",
    )
    BUG_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable/disable bug caching entirely. "
        "When False, bugs are always fetched from API. "
        "Default: True (caching enabled).",
    )
    BUG_CACHE_BYPASS: bool = Field(
        default=False,
        description="⚠️ DEBUG ONLY: Bypass bug caching (behaves as if force_refresh=True). "
        "When enabled, bug data is always refreshed from API on every read. "
        "Logs warning when active. Use for debugging stale bug data issues. "
        "Note: Currently applies only to bug caching; test caching unaffected. "
        "Default: False (caching enabled).",
    )

    # Test Mutability Constants (ClassVar - not env-configurable)
    # These match the pattern in cache.py and test_repository.py
    MUTABLE_TEST_STATUSES: ClassVar[list[str]] = [
        "customer_finalized",  # Customer review phase, can still change
        "waiting",  # Waiting to start
        "running",  # Test actively running, bugs being reported
        "locked",  # Finalized but not archived yet (still mutable!)
        "initialized",  # Test created but not started
    ]

    IMMUTABLE_TEST_STATUSES: ClassVar[list[str]] = [
        "archived",  # Test completed and archived (final state)
        "cancelled",  # Test cancelled (final state)
    ]

    # Server Lifecycle Configuration
    SHUTDOWN_GRACE_PERIOD_SECONDS: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Graceful shutdown timeout in seconds. "
        "Time to wait for background tasks to complete cancellation handlers "
        "before forcibly closing resources. Allows sync events to be marked "
        "as 'cancelled' rather than orphaned in 'running' state. "
        "Default: 10 seconds.",
    )

    # Tool Enable/Disable Configuration (STORY-015)
    ENABLED_TOOLS: str | list[str] | None = Field(
        default=None,
        description="Allowlist of tool names to enable (all others disabled). "
        "Tool names come from function names (e.g., 'get_test_status', 'list_products'). "
        "Accepts comma-separated string or JSON array. "
        "Cannot be used with DISABLED_TOOLS. Default: None (all tools enabled).",
    )
    DISABLED_TOOLS: str | list[str] | None = Field(
        default=None,
        description="Denylist of tool names to disable (all others enabled). "
        "Tool names come from function names (e.g., 'get_test_status', 'list_products'). "
        "Accepts comma-separated string or JSON array. "
        "Cannot be used with ENABLED_TOOLS. Default: None (all tools enabled).",
    )

    @field_validator("TESTIO_PRODUCT_IDS", mode="before")
    @classmethod
    def parse_product_ids(cls, v: Any) -> list[int] | None:
        """Parse product ID list from comma-separated string or JSON array.

        Args:
            v: Raw value from environment variable

        Returns:
            Parsed list of product IDs, or None if not set

        Examples:
            "25073,598,1024" -> [25073, 598, 1024]
            "[25073, 598, 1024]" -> [25073, 598, 1024]
            None -> None

        Raises:
            ValueError: If product IDs cannot be parsed as integers
        """
        if v is None:
            return None

        # If already a list, convert to integers
        if isinstance(v, list):
            return [int(pid) for pid in v]

        # Parse comma-separated string
        if isinstance(v, str):
            # Strip whitespace, filter empty strings, convert to int
            return [int(pid.strip()) for pid in v.split(",") if pid.strip()]

        return None

    @field_validator("ENABLED_TOOLS", "DISABLED_TOOLS", mode="before")
    @classmethod
    def parse_tool_list(cls, v: Any) -> list[str] | None:
        """Parse tool list from comma-separated string or JSON array.

        Args:
            v: Raw value from environment variable

        Returns:
            Parsed list of tool names, or None if not set

        Examples:
            "health_check,list_products" -> ["health_check", "list_products"]
            '["health_check", "list_products"]' -> ["health_check", "list_products"]
            None -> None
        """
        if v is None:
            return None

        # If already a list (from JSON parsing), return as-is
        if isinstance(v, list):
            return v

        # Parse comma-separated string
        if isinstance(v, str):
            # Strip whitespace and filter empty strings
            return [tool.strip() for tool in v.split(",") if tool.strip()]

        # v is already list[str] or None from Pydantic's type coercion
        return None if v is None else v

    @model_validator(mode="after")
    def validate_tool_enablement_mutual_exclusion(self) -> "Settings":
        """Validate that ENABLED_TOOLS and DISABLED_TOOLS are mutually exclusive.

        Returns:
            The validated Settings instance

        Raises:
            ValueError: If both ENABLED_TOOLS and DISABLED_TOOLS are set
        """
        enabled = self.ENABLED_TOOLS
        disabled = self.DISABLED_TOOLS

        # Both set is an error - must choose one approach
        if enabled is not None and disabled is not None:
            raise ValueError(
                "ENABLED_TOOLS and DISABLED_TOOLS cannot be used simultaneously. "
                "Choose one approach: allowlist (ENABLED_TOOLS) or denylist (DISABLED_TOOLS)."
            )

        return self


def load_settings() -> Settings:
    """Load settings from environment with fallback for testing.

    Returns:
        Settings instance loaded from environment variables

    Note:
        With pydantic mypy plugin enabled, mypy understands that
        Settings() reads from environment variables, so no type
        ignores are needed.
    """
    try:
        return Settings()
    except Exception:
        # Fallback for testing environments without .env
        import os

        os.environ["TESTIO_CUSTOMER_API_TOKEN"] = "test_token_placeholder"
        # TESTIO_CUSTOMER_ID defaults to 1, no need to set explicitly
        return Settings()


# Global settings instance
settings = load_settings()
