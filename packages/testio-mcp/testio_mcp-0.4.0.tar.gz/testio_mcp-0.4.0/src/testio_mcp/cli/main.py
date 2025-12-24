"""Command-line interface for TestIO MCP Server.

Provides CLI entry point with support for:
- Standard flags: --help, --version
- Credential loading: --env-file
- Config overrides: cache TTLs, logging, concurrency
- Signal handling: graceful shutdown on CTRL+C
"""

import argparse
import asyncio
import os
import signal
import sys
import threading
from pathlib import Path
from types import TracebackType
from typing import NoReturn

from dotenv import load_dotenv


def setup_exception_hook() -> None:
    """Set up custom exception hook to suppress shutdown errors.

    Filters out CancelledError exceptions during shutdown to avoid
    printing stack traces for expected cancellation of background tasks.
    Also suppresses threading exceptions from aiosqlite during shutdown.
    """
    original_excepthook = sys.excepthook

    def custom_excepthook(
        exc_type: type, exc_value: BaseException, exc_traceback: TracebackType | None
    ) -> None:
        """Custom exception handler that suppresses shutdown errors.

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
        """
        # Suppress expected shutdown exceptions
        if exc_type in (asyncio.CancelledError, KeyboardInterrupt):
            return

        # For all other exceptions, use original handler
        original_excepthook(exc_type, exc_value, exc_traceback)

    def threading_excepthook(args: threading.ExceptHookArgs) -> None:
        """Custom threading exception handler that suppresses shutdown errors.

        Args:
            args: Threading exception info (exc_type, exc_value, exc_traceback, thread)
        """
        # Suppress "Event loop is closed" errors from aiosqlite during shutdown
        if isinstance(args.exc_value, RuntimeError):
            if "Event loop is closed" in str(args.exc_value):
                return

        # For all other exceptions, use default handler (print to stderr)
        if args.exc_value is not None:
            sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = custom_excepthook
    threading.excepthook = threading_excepthook


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown.

    Handles SIGINT (CTRL+C) and SIGTERM for clean exit.
    Only used for sync/problematic commands - serve command uses uvicorn's handlers.
    """

    def signal_handler(signum: int, frame: object) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print("\n\n✨ Shutting down gracefully...", file=sys.stderr)
        sys.exit(0)

    # Register handlers for SIGINT (CTRL+C) and SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_version() -> str:
    """Get package version from metadata.

    Returns:
        Version string (e.g., "0.1.0")
    """
    try:
        from importlib.metadata import version

        return version("testio-mcp")
    except Exception:
        return "unknown"


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all CLI flags and subcommands.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="testio-mcp",
        description="TestIO MCP Server - AI-first API integration for TestIO Customer API",
        epilog="Credentials must be provided via environment variables or --env-file. "
        "See https://github.com/test-IO/customer-mcp for documentation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Standard flags
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"testio-mcp {get_version()}",
    )

    # Credential loading (global flag)
    parser.add_argument(
        "--env-file",
        type=Path,
        metavar="PATH",
        help="Path to .env file with credentials (default: .env in current directory)",
    )

    # Create subcommands
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands (default: serve)",
        dest="command",
        metavar="COMMAND",
    )

    # === SERVE SUBCOMMAND (default behavior) ===
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start MCP server (default)",
        description="Start the TestIO MCP server for AI tool integration",
    )

    # Background refresh configuration (serve only)
    cache_group = serve_parser.add_argument_group("background refresh configuration")
    cache_group.add_argument(
        "--refresh-interval",
        type=int,
        metavar="SECONDS",
        help="Background refresh interval for mutable tests in seconds (default: 900, 0=disabled)",
    )
    cache_group.add_argument(
        "--force-sync",
        action="store_true",
        help="Force initial sync on startup regardless of last sync timestamps",
    )

    # Logging configuration (serve only)
    logging_group = serve_parser.add_argument_group("logging configuration")
    logging_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO)",
    )
    logging_group.add_argument(
        "--log-format",
        choices=["json", "text"],
        help="Log output format (default: json)",
    )

    # HTTP client configuration (serve only)
    http_group = serve_parser.add_argument_group("http client configuration")
    http_group.add_argument(
        "--max-concurrent-requests",
        type=int,
        metavar="N",
        help="Maximum concurrent API requests (default: 10, range: 1-50)",
    )
    http_group.add_argument(
        "--connection-pool-size",
        type=int,
        metavar="N",
        help="HTTP connection pool size (default: 20, range: 1-100)",
    )
    http_group.add_argument(
        "--http-timeout",
        type=float,
        metavar="SECONDS",
        help="HTTP request timeout in seconds (default: 30.0, range: 1-300)",
    )

    # Transport configuration (serve only)
    transport_group = serve_parser.add_argument_group("transport configuration")
    transport_group.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help=(
            "Transport mode: stdio (default, for MCP clients) "
            "or http (streamable-http for multiple clients)"
        ),
    )
    transport_group.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP server host (default: 127.0.0.1, localhost-only)",
    )
    transport_group.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP server port (default: 8080)",
    )
    transport_group.add_argument(
        "--api-mode",
        choices=["mcp", "rest", "hybrid"],
        default="hybrid",
        help=(
            "API mode: hybrid (default, both MCP + REST + Swagger docs), "
            "mcp (MCP protocol only), or rest (REST API only)"
        ),
    )

    # === SYNC SUBCOMMAND ===
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync local database with TestIO API",
        description="Manually sync the local database with TestIO Customer API",
    )

    # Date filtering
    sync_parser.add_argument(
        "--since",
        type=str,
        metavar="DATE",
        help=(
            "Only sync tests ending on/after this date "
            '(e.g., "2024-01-01", "3 days ago", "last week")'
        ),
    )

    # Product filtering
    sync_parser.add_argument(
        "--product-ids",
        type=int,
        nargs="+",
        metavar="ID",
        help=(
            "Only sync these product IDs (overrides TESTIO_PRODUCT_IDS env var). "
            "Example: --product-ids 598 1024"
        ),
    )

    # Sync behavior
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh all tests using upsert (non-destructive, updates + adds)",
    )
    sync_parser.add_argument(
        "--nuke",
        action="store_true",
        help="Delete database and rebuild (destructive, needs confirmation)",
    )
    sync_parser.add_argument(
        "--incremental-only",
        action="store_true",
        help="Fast mode: discover new tests only (skip mutable test refresh)",
    )
    sync_parser.add_argument(
        "--refresh",
        action="store_true",
        help="(DEPRECATED) Same as default behavior - discover new tests AND update mutable tests",
    )
    sync_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts (for automation)",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sync without making changes",
    )

    # Status and output
    sync_parser.add_argument(
        "--status",
        action="store_true",
        help="Show current database sync status and exit",
    )
    sync_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed sync progress and logging",
    )

    # === SETUP SUBCOMMAND ===
    subparsers.add_parser(
        "setup",
        help="Interactive setup for TestIO MCP configuration",
        description="Guided workflow to create ~/.testio-mcp.env configuration file",
    )

    # === PROBLEMATIC SUBCOMMAND ===
    problematic_parser = subparsers.add_parser(
        "problematic",
        help="Manage tests that failed to sync",
        description="View, clear, and retry tests that failed with API errors",
    )

    # Nested subcommands for list/map-tests/retry/clear
    problematic_subparsers = problematic_parser.add_subparsers(
        dest="problematic_action",
        required=True,
        metavar="ACTION",
        help="Action to perform",
    )

    # list action
    problematic_subparsers.add_parser(
        "list",
        help="Show failed sync events and their mapped test IDs",
    )

    # map-tests action
    map_tests_parser = problematic_subparsers.add_parser(
        "map-tests",
        help="Map test IDs to a specific failed event",
    )
    map_tests_parser.add_argument(
        "event_id",
        type=str,
        help="Event ID (from problematic list output)",
    )
    map_tests_parser.add_argument(
        "test_ids",
        type=int,
        nargs="+",
        help="One or more test IDs to map to this event",
    )

    # retry action
    retry_parser = problematic_subparsers.add_parser(
        "retry",
        help="Retry fetching all tracked test IDs for a product",
    )
    retry_parser.add_argument(
        "product_id",
        type=int,
        help="Product ID to retry",
    )

    # clear action
    clear_parser = problematic_subparsers.add_parser(
        "clear",
        help="Remove all problematic records (position ranges AND test IDs)",
    )
    clear_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    return parser


def load_env_file(env_file: Path | None) -> None:
    """Load environment variables with precedence order.

    Precedence:
    1. --env-file PATH (if provided) - explicit user override
    2. ~/.testio-mcp.env (if exists) - setup command default
    3. .env in current directory (if exists) - local development

    Args:
        env_file: Path to .env file, or None to use default precedence

    Raises:
        SystemExit: If specified env_file doesn't exist
    """
    if env_file:
        # Explicit --env-file takes highest precedence
        if not env_file.exists():
            print(f"Error: --env-file '{env_file}' not found", file=sys.stderr)
            sys.exit(1)
        load_dotenv(env_file, override=True)
    else:
        # Check ~/.testio-mcp.env first (setup command default)
        global_env = Path.home() / ".testio-mcp.env"
        if global_env.exists():
            load_dotenv(global_env, override=True)
        else:
            # Fall back to .env in current directory (local dev)
            load_dotenv(override=False)


def apply_config_overrides(args: argparse.Namespace) -> None:
    """Apply CLI config overrides to environment variables.

    Args:
        args: Parsed command-line arguments
    """
    # Only apply serve-specific overrides if in serve mode
    if args.command in (None, "serve"):
        # Background refresh interval override
        if hasattr(args, "refresh_interval") and args.refresh_interval is not None:
            os.environ["TESTIO_REFRESH_INTERVAL_SECONDS"] = str(args.refresh_interval)

        # Force initial sync override
        if hasattr(args, "force_sync") and args.force_sync:
            os.environ["TESTIO_FORCE_INITIAL_SYNC"] = "true"

        # Logging overrides
        if hasattr(args, "log_level") and args.log_level:
            os.environ["LOG_LEVEL"] = args.log_level
        if hasattr(args, "log_format") and args.log_format:
            os.environ["LOG_FORMAT"] = args.log_format

        # HTTP client overrides
        if hasattr(args, "max_concurrent_requests") and args.max_concurrent_requests is not None:
            os.environ["MAX_CONCURRENT_API_REQUESTS"] = str(args.max_concurrent_requests)
        if hasattr(args, "connection_pool_size") and args.connection_pool_size is not None:
            os.environ["CONNECTION_POOL_SIZE"] = str(args.connection_pool_size)
        if hasattr(args, "http_timeout") and args.http_timeout is not None:
            os.environ["HTTP_TIMEOUT_SECONDS"] = str(args.http_timeout)


def main() -> NoReturn:
    """CLI entry point for TestIO MCP Server.

    Parses command-line arguments, loads environment configuration,
    sets up signal handlers, and dispatches to subcommand handlers.
    """
    # Set up exception hook to suppress shutdown errors
    setup_exception_hook()

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Load environment variables from .env file
    load_env_file(args.env_file)

    # Apply CLI config overrides
    apply_config_overrides(args)

    # Dispatch to subcommand handler
    command = args.command or "serve"  # Default to serve if no subcommand specified

    if command == "serve":
        # Run database migrations before starting server (STORY-034B)
        # This runs as a separate subprocess to avoid asyncio.run() conflicts
        from testio_mcp.config import settings

        if not settings.TESTIO_SKIP_MIGRATIONS:
            import subprocess
            from pathlib import Path

            # Ensure database directory exists
            db_path = Path(settings.TESTIO_DB_PATH).expanduser().resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)

            print("Running database migrations...", file=sys.stderr)
            try:
                result = subprocess.run(
                    ["alembic", "upgrade", "head"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Only show output if there were actual migrations
                if "Running upgrade" in result.stdout:
                    print(result.stdout, file=sys.stderr, end="")
                print("✅ Migrations complete", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(f"❌ Migration failed: {e}", file=sys.stderr)
                print(e.stdout, file=sys.stderr)
                print(e.stderr, file=sys.stderr)
                print(
                    "\nTo skip migrations (dev/CI only), set TESTIO_SKIP_MIGRATIONS=1",
                    file=sys.stderr,
                )
                sys.exit(1)
            except FileNotFoundError:
                print("❌ alembic command not found", file=sys.stderr)
                print("Install with: uv pip install alembic", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                "⚠️  TESTIO_SKIP_MIGRATIONS=1: Skipping database migrations.",
                file=sys.stderr,
            )
            print("Database schema may be out of sync! Use only for dev/CI.", file=sys.stderr)

        # Get transport mode (default: stdio for MCP clients)
        transport = getattr(args, "transport", "stdio")

        # Get API mode (default: "hybrid" for best UX - MCP + REST + Swagger docs)
        # Note: api_mode only applies to HTTP transport
        api_mode = getattr(args, "api_mode", "hybrid")

        # HTTP transport with hybrid/REST mode: Use FastAPI wrapper
        if transport == "http" and api_mode in ("hybrid", "rest"):
            # Import FastAPI app AFTER env setup
            # Import uvicorn for HTTP server
            import uvicorn

            from testio_mcp.api import api
            from testio_mcp.config import settings

            # Configure uvicorn for quick shutdown response (STORY-107)
            # timeout_graceful_shutdown: reduce wait time for connections to close
            # This allows single CTRL+C to exit quickly instead of requiring two presses
            # Start uvicorn with FastAPI app (this blocks until shutdown)
            # CLI args override env vars (getattr returns None if not provided)
            uvicorn.run(
                api,
                host=getattr(args, "host", None) or settings.TESTIO_HTTP_HOST,
                port=getattr(args, "port", None) or settings.TESTIO_HTTP_PORT,
                log_level="info",
                ws="websockets-sansio",  # Use SansIO API (avoid legacy deprecation)
                timeout_graceful_shutdown=2,  # Wait max 2 seconds for connections to close
            )

            # Unreachable code (uvicorn.run() blocks forever)
            sys.exit(0)

        # MCP-only mode OR stdio transport: Use standard MCP server
        # Import server AFTER env setup (so Pydantic Settings picks up values)
        from testio_mcp.config import settings
        from testio_mcp.server import mcp

        # Start server with appropriate transport (this blocks until shutdown)
        if transport == "http":
            # HTTP mode: Single server process for multiple clients
            # Use streamable-http (modern) instead of "http"/"sse" (legacy with shutdown issues)
            #
            # Configure uvicorn for quick shutdown response (STORY-107):
            # - timeout_graceful_shutdown: Wait max 2 seconds for connections to close
            # - This allows single CTRL+C to exit quickly instead of requiring two presses
            #
            # CLI args override env vars (getattr returns None if not provided)
            mcp.run(
                transport="streamable-http",
                host=getattr(args, "host", None) or settings.TESTIO_HTTP_HOST,
                port=getattr(args, "port", None) or settings.TESTIO_HTTP_PORT,
                uvicorn_config={
                    "ws": "websockets-sansio",  # Use SansIO (avoid deprecation)
                    "timeout_graceful_shutdown": 2,  # Quick shutdown (max 2 seconds)
                },
            )
        else:
            # stdio mode: Default behavior (backward compatible)
            # Explicitly specify stdio to avoid any default behavior changes
            mcp.run(transport="stdio")

        # Unreachable code (mcp.run() blocks forever)
        sys.exit(0)

    elif command == "sync":
        # Set up signal handlers for sync command
        setup_signal_handlers()

        # Import sync module and dispatch
        from testio_mcp.cli.sync import sync_command_main

        # Handle --yes flag for automation
        if hasattr(args, "yes") and args.yes:
            # Auto-confirm for force mode
            import builtins

            original_input = builtins.input
            builtins.input = lambda *args, **kwargs: "yes"
            try:
                sync_command_main(args)
            finally:
                builtins.input = original_input
        else:
            sync_command_main(args)

    elif command == "setup":
        # Import setup module and dispatch
        from testio_mcp.cli.setup import setup_command_main

        setup_command_main()

    elif command == "problematic":
        # Set up signal handlers for problematic command
        setup_signal_handlers()

        # Import problematic module and dispatch
        from testio_mcp.cli.problematic import problematic_command_main

        problematic_command_main(args)

    else:
        # Should never reach here due to argparse validation
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        sys.exit(1)
