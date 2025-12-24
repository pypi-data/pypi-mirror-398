"""
FastMCP server for TestIO Customer API integration.

This module implements the Model Context Protocol server with:
- Shared TestIO API client instance
- Structured logging with token sanitization (AC14)
- Health check tool for authentication verification
- Lifespan handler for resource initialization/cleanup (ADR-007)
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypedDict

from fastmcp import FastMCP

from .client import TestIOClient
from .config import settings
from .database import PersistentCache
from .services.sync_service import SyncPhase, SyncScope, SyncService
from .utilities.logging import configure_logging


# Type-safe context for dependency injection (ADR-007)
class ServerContext(TypedDict):
    """Type definition for FastMCP app.context dictionary.

    This enables type-safe access to shared dependencies stored in
    the lifespan handler and accessed via Context parameter in tools.
    """

    testio_client: TestIOClient
    cache: PersistentCache


# Configure structured logging on module load (server initialization, AC14)
configure_logging(enable_file_logging=True, enable_console_logging=True)

# Logger for server operations
logger = logging.getLogger(__name__)

# Shared resources (ADR-002: global concurrency control)
# Note: _testio_client and _cache moved to lifespan handler (ADR-007)
_global_semaphore: asyncio.Semaphore | None = None

# Singleton state for lifespan idempotency (prevents duplicate initialization in HTTP mode)
_lifespan_initialized: bool = False
_lifespan_context: ServerContext | None = None
_lifespan_lock = asyncio.Lock()


def get_global_semaphore() -> asyncio.Semaphore:
    """Get or create the shared semaphore for global concurrency control (ADR-002).

    This semaphore is shared across all TestIOClient instances to enforce
    a global limit on concurrent API requests. This prevents overwhelming
    the TestIO API.

    For Story 1 (single client): provides concurrency control.
    For future stories (multiple products): ensures total concurrent requests
    across all products stays within limit.

    Returns:
        Shared semaphore instance with max_concurrent_requests limit
    """
    global _global_semaphore

    if _global_semaphore is None:
        _global_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_API_REQUESTS)
        logger.info(f"Created API semaphore with limit: {settings.MAX_CONCURRENT_API_REQUESTS}")

    return _global_semaphore


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage shared resources during server lifecycle (ADR-007).

    This lifespan handler follows FastMCP's Context injection pattern by
    initializing dependencies at startup and yielding them as a context object
    that tools can access via ctx.request_context.lifespan_context.

    Startup:
        - Create TestIOClient with connection pooling
        - Create PersistentCache with SQLite database (STORY-021 AC5)
        - Initialize database schema and WAL mode
        - Yield ServerContext for dependency injection

    Shutdown:
        - Close PersistentCache database connection
        - Automatically close TestIOClient via async context manager

    Architecture:
        - Single-tenant: Shared client/cache across all requests (current)
        - Multi-tenant: Will be extended in STORY-010 with ClientPool
        - Idempotent: Can be called multiple times (HTTP mode), but only initializes once

    Reference:
        - ADR-007: FastMCP Context Injection Pattern
        - STORY-021 AC5: SQLite-only persistent cache
        - FastMCP docs: https://gofastmcp.com/servers/context
    """
    global _lifespan_initialized, _lifespan_context

    # Prevent duplicate initialization (HTTP mode calls lifespan twice)
    async with _lifespan_lock:
        if _lifespan_initialized:
            assert _lifespan_context is not None
            logger.debug("Lifespan already initialized, reusing existing context")
            yield _lifespan_context
            return

        # Mark as initializing inside lock to prevent race condition
        logger.info("Initializing server dependencies")
        _lifespan_initialized = True

    # Get shared semaphore for global concurrency control (ADR-002)
    shared_semaphore = get_global_semaphore()

    try:
        # STORY-034B: Migrations now run before server startup (in CLI)
        # This avoids asyncio.run() deadlock issues and follows standard deployment patterns

        # Create client with async context manager
        async with TestIOClient(
            base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
            api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
            max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
            max_connections=settings.CONNECTION_POOL_SIZE,
            max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
            timeout=settings.HTTP_TIMEOUT_SECONDS,
            semaphore=shared_semaphore,
        ) as client:
            # Create persistent cache (STORY-021 AC5)
            cache = PersistentCache(
                db_path=settings.TESTIO_DB_PATH,
                client=client,
                customer_id=settings.TESTIO_CUSTOMER_ID,
                customer_name=settings.TESTIO_CUSTOMER_NAME,
            )

            # Initialize database connection and schema
            logger.info("Initializing cache...")
            await cache.initialize()
            logger.info("Cache initialized successfully")

            logger.info("Server dependencies initialized (client, persistent cache)")

            # Initialize SyncService for unified sync orchestration (STORY-049)
            sync_service = SyncService(client=client, cache=cache)
            logger.info("SyncService initialized")

            # Start background tasks (AC6)
            background_tasks: list[asyncio.Task[Any]] = []

            # Task 1: Conditional initial sync (check if needed based on last sync time)
            should_sync = await cache.should_run_initial_sync(
                settings.TESTIO_REFRESH_INTERVAL_SECONDS
            )
            if should_sync:
                # Use SyncService for initial sync with all 3 phases (STORY-049 AC1)
                async def run_initial_sync() -> None:
                    """Run initial sync using SyncService."""
                    try:
                        logger.info("Starting initial sync via SyncService")
                        # Execute all 3 phases: PRODUCTS → FEATURES → NEW_TESTS
                        phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]
                        # Parse since_date string to datetime if provided
                        since_date = None
                        if settings.TESTIO_SYNC_SINCE:
                            from datetime import datetime

                            since_date = datetime.fromisoformat(settings.TESTIO_SYNC_SINCE)
                        # Respect TESTIO_PRODUCT_IDS env var for product filtering
                        scope = SyncScope(
                            product_ids=settings.TESTIO_PRODUCT_IDS,
                            since_date=since_date,
                        )
                        result = await sync_service.execute_sync(
                            phases=phases,
                            scope=scope,
                            trigger_source="startup",
                        )
                        logger.info(
                            f"Initial sync complete: {result.products_synced} products, "
                            f"{result.features_refreshed} features, "
                            f"{result.tests_discovered} new tests discovered"
                        )
                    except Exception as e:
                        logger.error(f"Initial sync failed: {e}", exc_info=True)

                initial_sync_task = asyncio.create_task(run_initial_sync())
                background_tasks.append(initial_sync_task)
                logger.info("Started initial sync background task (non-blocking)")
            else:
                logger.info("Skipping initial sync (data is fresh)")

            # Task 2: Optional background refresh (runs periodically if enabled)
            # STORY-049 AC2: Background task only handles scheduling, SyncService handles execution
            refresh_task: asyncio.Task[Any] | None = None
            if settings.TESTIO_REFRESH_INTERVAL_SECONDS > 0:

                async def run_background_refresh() -> None:
                    """Run background refresh using SyncService.

                    Scheduling logic remains in server.py, but sync execution
                    is delegated to SyncService for unified orchestration.

                    STORY-051 AC5: Check last_sync_completed timestamp before running
                    to prevent immediate re-sync after manual/MCP sync.
                    """
                    while True:
                        try:
                            from datetime import UTC, datetime

                            # Wait for interval
                            # (STORY-049 AC3: TESTIO_REFRESH_INTERVAL_SECONDS unchanged)
                            await asyncio.sleep(settings.TESTIO_REFRESH_INTERVAL_SECONDS)

                            # STORY-051 AC5: Check if manual/MCP sync was recent
                            last_sync_str = await cache.get_metadata_value("last_sync_completed")
                            if last_sync_str:
                                last_sync = datetime.fromisoformat(last_sync_str)
                                now = datetime.now(UTC)
                                elapsed = (now - last_sync).total_seconds()

                                if elapsed < settings.TESTIO_REFRESH_INTERVAL_SECONDS:
                                    logger.info(
                                        f"Skipping background refresh (manual/MCP sync "
                                        f"{elapsed:.0f}s ago, interval: "
                                        f"{settings.TESTIO_REFRESH_INTERVAL_SECONDS}s)"
                                    )
                                    continue

                            logger.info("Starting background refresh cycle via SyncService")

                            # Execute all 3 phases: PRODUCTS → FEATURES → NEW_TESTS (STORY-049 AC1)
                            phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]
                            # Parse since_date string to datetime if provided
                            since_date = None
                            if settings.TESTIO_SYNC_SINCE:
                                since_date = datetime.fromisoformat(settings.TESTIO_SYNC_SINCE)
                            # Respect TESTIO_PRODUCT_IDS env var for product filtering
                            scope = SyncScope(
                                product_ids=settings.TESTIO_PRODUCT_IDS,
                                since_date=since_date,
                            )
                            result = await sync_service.execute_sync(
                                phases=phases,
                                scope=scope,
                                trigger_source="background",
                            )

                            # STORY-051 AC4: Update last_sync_completed after successful sync
                            await cache.set_metadata_value(
                                key="last_sync_completed",
                                value=datetime.now(UTC).isoformat(),
                            )

                            logger.info(
                                f"Background refresh complete: {result.products_synced} products, "
                                f"{result.features_refreshed} features, "
                                f"{result.tests_discovered} new tests discovered"
                            )

                        except asyncio.CancelledError:
                            logger.info("Background refresh task cancelled, shutting down")
                            raise  # Re-raise to break the loop
                        except Exception as e:
                            logger.error(f"Error in background refresh cycle: {e}", exc_info=True)
                            # Continue running despite errors

                refresh_task = asyncio.create_task(run_background_refresh())
                background_tasks.append(refresh_task)
                logger.info(
                    f"Started background refresh task "
                    f"(interval: {settings.TESTIO_REFRESH_INTERVAL_SECONDS}s)"
                )
            else:
                logger.info("Background refresh disabled (TESTIO_REFRESH_INTERVAL_SECONDS=0)")

            # Store context globally for future lifespan calls (HTTP mode)
            server_context = ServerContext(testio_client=client, cache=cache)
            _lifespan_context = server_context
            logger.debug("Lifespan initialization complete, context stored")

            # Yield context for tools to access via ctx.request_context.lifespan_context
            # Server is now available while background tasks run
            try:
                yield server_context
            finally:
                # Cleanup: Graceful shutdown with bounded wait for cancellation handlers
                try:
                    logger.info("Shutting down background tasks")
                    for task in background_tasks:
                        task.cancel()

                    # Wait for tasks to process cancellation and run cleanup code
                    # This allows sync operations to call log_sync_event_cancelled()
                    # before the database connection closes
                    if background_tasks:
                        try:
                            await asyncio.wait_for(
                                asyncio.gather(*background_tasks, return_exceptions=True),
                                timeout=settings.SHUTDOWN_GRACE_PERIOD_SECONDS,
                            )
                            logger.debug("Background tasks completed gracefully")
                        except TimeoutError:
                            logger.warning(
                                f"Background tasks did not finish within "
                                f"{settings.SHUTDOWN_GRACE_PERIOD_SECONDS}s grace period"
                            )
                        except (asyncio.CancelledError, KeyboardInterrupt):
                            # Second CTRL+C during graceful wait - force immediate shutdown
                            logger.warning(
                                "Forced shutdown (second CTRL+C), closing resources immediately"
                            )
                            raise  # Propagate to exit immediately

                    # Close cache database connection (after tasks have logged cancellation)
                    await cache.close()

                    # Client closed automatically by context manager
                    logger.info("Server dependencies cleaned up")

                    # Reset singleton state for potential restart
                    _lifespan_initialized = False
                    _lifespan_context = None
                except (asyncio.CancelledError, KeyboardInterrupt):
                    # Second CTRL+C - ensure cache closes and exit immediately
                    try:
                        await cache.close()
                    except Exception:
                        pass  # Best effort close on forced shutdown
                    raise  # Propagate to terminate
                except Exception:
                    # Other errors during shutdown - log but continue cleanup
                    logger.error("Error during shutdown", exc_info=True)
    except Exception as e:
        # Initialization failed - reset singleton state so retry can attempt again
        logger.error(f"Lifespan initialization failed: {e}", exc_info=True)
        _lifespan_initialized = False
        _lifespan_context = None
        raise


# Initialize FastMCP server with lifespan and middleware (ADR-007)
from testio_mcp.middleware import PromptErrorMiddleware  # noqa: E402

mcp = FastMCP(
    "TestIO MCP Server",
    lifespan=lifespan,
    middleware=[PromptErrorMiddleware()],  # User-friendly prompt error messages
)


# Tools registered below
# (get_testio_client and get_cache removed - replaced by Context injection, ADR-007)


# Auto-discover and register all tools (STORY-012 AC4, STORY-015)
# Uses pkgutil to find all modules in tools/ package
# Must be at end of file to avoid circular imports
import pkgutil  # noqa: E402

import testio_mcp.tools  # noqa: E402

# Discover all tool modules in the tools package
for module_info in pkgutil.iter_modules(testio_mcp.tools.__path__):
    # Import each tool module to trigger @mcp.tool() registration
    module_name = module_info.name
    __import__(f"testio_mcp.tools.{module_name}")
    logger.debug(f"Auto-discovered and registered tool module: {module_name}")

# Apply tool filtering based on configuration (STORY-015)
if settings.ENABLED_TOOLS is not None or settings.DISABLED_TOOLS is not None:
    all_tools = list(mcp._tool_manager._tools.keys())
    tools_to_remove = []

    for tool_name in all_tools:
        # Allowlist mode: Keep only tools in ENABLED_TOOLS
        if settings.ENABLED_TOOLS is not None:
            if tool_name not in settings.ENABLED_TOOLS:
                tools_to_remove.append(tool_name)
                logger.info(f"Filtering out tool (not in ENABLED_TOOLS): {tool_name}")
        # Denylist mode: Remove tools in DISABLED_TOOLS
        elif settings.DISABLED_TOOLS is not None:
            if tool_name in settings.DISABLED_TOOLS:
                tools_to_remove.append(tool_name)
                logger.info(f"Filtering out tool (in DISABLED_TOOLS): {tool_name}")

    # Remove filtered tools from registry
    for tool_name in tools_to_remove:
        del mcp._tool_manager._tools[tool_name]

    logger.info(f"Tool filtering complete: {len(tools_to_remove)} tools removed")

# Log total tools registered (access internal _tools dict)
tool_count = len(mcp._tool_manager._tools)
tool_names = list(mcp._tool_manager._tools.keys())
logger.info(f"Auto-discovery complete: {tool_count} tools registered: {tool_names}")

# Register MCP prompts (STORY-059)
# Import prompts package to trigger @mcp.prompt() registration
import testio_mcp.prompts  # noqa: E402, F401

logger.info("MCP prompts registered")

# Register MCP resources (STORY-066)
from testio_mcp.resources import register_resources  # noqa: E402

register_resources(mcp)
logger.info("MCP resources registered")
