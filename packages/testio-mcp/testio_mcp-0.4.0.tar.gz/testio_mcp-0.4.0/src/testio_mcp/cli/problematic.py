"""Problematic tests command for TestIO MCP CLI.

Provides management of tests that failed to sync due to API errors.
Allows explicit mapping of test IDs to failed sync events and retry.

Reference: STORY-021e
"""

import asyncio
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import NoReturn

import psutil
from filelock import FileLock, Timeout
from rich.console import Console

from testio_mcp.client import TestIOClient
from testio_mcp.config import Settings
from testio_mcp.database import PersistentCache

console = Console()
logger = logging.getLogger(__name__)

# Lock configuration
LOCK_FILE = Path.home() / ".testio-mcp" / "sync.lock"


def acquire_sync_lock() -> FileLock:
    """Acquire cross-process sync lock with stale detection.

    Returns:
        Acquired file lock

    Raises:
        RuntimeError: If lock is held by another active process
    """
    # Ensure directory exists
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(LOCK_FILE, timeout=1)  # Non-blocking check

    try:
        lock.acquire(timeout=1)
        # Write current PID to lock file for stale detection
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return lock
    except Timeout:
        # Lock exists - check if stale
        if is_stale_lock(LOCK_FILE):
            logger.warning("Removing stale lock from crashed process")
            LOCK_FILE.unlink()
            return acquire_sync_lock()  # Retry
        else:
            raise RuntimeError("⚠️ Sync in progress. Retry in a few minutes.") from None


def is_stale_lock(lock_file: Path) -> bool:
    """Check if lock holder process is still alive.

    Args:
        lock_file: Path to lock file containing PID

    Returns:
        True if lock is stale (process dead), False if process alive
    """
    if not lock_file.exists():
        return False

    try:
        with open(lock_file) as f:
            pid = int(f.read().strip())

        # Check if process exists
        return not psutil.pid_exists(pid)
    except (ValueError, FileNotFoundError):
        # Invalid PID or file deleted - treat as stale
        return True


def get_cache() -> PersistentCache:
    """Get initialized cache instance.

    Returns:
        PersistentCache instance ready for operations
    """
    settings = Settings()

    # Create client (synchronous, not using async with)
    client = TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
        max_connections=settings.CONNECTION_POOL_SIZE,
        max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )

    cache = PersistentCache(
        client=client,
        db_path=settings.TESTIO_DB_PATH,
        customer_id=settings.TESTIO_CUSTOMER_ID,
        customer_name=settings.TESTIO_CUSTOMER_NAME,
    )

    return cache


async def list_problematic_events() -> None:
    """List all failed sync events with their mapped test IDs."""
    cache = get_cache()

    try:
        await cache.initialize()
        events = await cache.get_problematic_events()

        if not events:
            console.print("✅ No failed sync events found")
            return

        console.print("\n[bold]=== Failed Sync Events ===[/bold]\n")

        for event in events:
            # Event header
            event_id = event.get("event_id", "unknown")
            product_id = event.get("product_id", "unknown")
            console.print(f"[bold]Event: {event_id}[/bold] (Product {product_id})")
            console.print(f"  Position Range: {event.get('position_range', 'N/A')}")
            console.print(f"  Retry Attempts: {event.get('recovery_attempts', 0)}")

            # Show sync mode and command timestamp
            sync_mode = event.get("sync_mode", "unknown")
            command_run_at = event.get("command_run_at", "N/A")
            console.print(f"  Sync Mode: {sync_mode}")
            console.print(f"  Command Run At: {command_run_at}")

            # Normalize boundary timestamps to UTC for consistent display
            before_id = event.get("boundary_before_id", "N/A")
            before_end = event.get("boundary_before_end_at", "N/A")
            after_id = event.get("boundary_after_id", "N/A")
            after_end = event.get("boundary_after_end_at", "N/A")

            from testio_mcp.utilities.timezone_utils import normalize_to_utc

            if before_end != "N/A":
                try:
                    before_end = normalize_to_utc(before_end)
                except (ValueError, Exception):
                    pass  # Keep original if normalization fails

            if after_end != "N/A":
                try:
                    after_end = normalize_to_utc(after_end)
                except (ValueError, Exception):
                    pass  # Keep original if normalization fails

            console.print(f"  Boundary Before: ID {before_id}, End: {before_end}")
            console.print(f"  Boundary After:  ID {after_id}, End: {after_end}")

            # Mapped test IDs
            mapped_ids = event.get("mapped_test_ids", [])
            if mapped_ids:
                test_ids_str = ", ".join(str(tid) for tid in mapped_ids)
                count = len(mapped_ids)
                console.print(f"  [green]Mapped Test IDs: {test_ids_str}[/green] ({count} tests)")
            else:
                console.print("  [yellow]Mapped Test IDs: (none)[/yellow]")

            console.print()  # Blank line between events

        console.print(
            "[dim]Use 'map-tests <event_id> <test_id...>' to map test IDs to an event[/dim]"
        )

    finally:
        await cache.close()


async def map_tests_to_event(event_id: str, test_ids: list[int]) -> None:
    """Map test IDs to a specific failed event.

    Args:
        event_id: UUID of failed sync event
        test_ids: List of test IDs to map
    """
    cache = get_cache()

    try:
        await cache.initialize()
        await cache.map_test_ids_to_event(event_id, test_ids)

        test_ids_str = ", ".join(str(tid) for tid in test_ids)
        console.print(f"✅ Mapped {len(test_ids)} test IDs to event {event_id}")
        console.print(f"   Test IDs: {test_ids_str}")

    except ValueError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    finally:
        await cache.close()


async def retry_problematic_tests(product_id: int) -> None:
    """Retry all tracked test IDs with locking.

    Args:
        product_id: Product ID to retry
    """
    lock = acquire_sync_lock()  # Acquire lock BEFORE any writes

    settings = Settings()

    # Create client with async context manager (Critical fix from Codex review)
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
        max_connections=settings.CONNECTION_POOL_SIZE,
        max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    ) as client:
        cache = PersistentCache(
            client=client,
            db_path=settings.TESTIO_DB_PATH,
            customer_id=settings.TESTIO_CUSTOMER_ID,
            customer_name=settings.TESTIO_CUSTOMER_NAME,
        )

        try:
            await cache.initialize()
            result = await cache.retry_problematic_tests(product_id)

            console.print(f"✅ Retried {result['tests_retried']} test IDs")
            console.print(f"   Succeeded: {result['tests_succeeded']}")
            console.print(f"   Failed: {result['tests_failed']} (kept in tracking)")

            if result["errors"]:
                console.print("[yellow]Errors:[/yellow]")
                for err in result["errors"]:
                    console.print(f"  - {err}")

        finally:
            await cache.close()
            lock.release()  # Always release lock


async def clear_problematic_tests(confirm: bool = True) -> None:
    """Clear all problematic records with confirmation.

    Args:
        confirm: Whether to ask for confirmation (False for --yes flag)
    """
    cache = get_cache()

    try:
        await cache.initialize()

        # Get counts before clearing
        events = await cache.get_problematic_events()
        if not events:
            console.print("✅ No problematic tests to clear")
            return

        # Count total mapped test IDs
        total_mapped = sum(len(e.get("mapped_test_ids", [])) for e in events)

        # Confirmation prompt
        if confirm:
            console.print(
                f"\n[yellow]⚠️  About to clear {len(events)} failed events "
                f"and {total_mapped} mapped test IDs[/yellow]"
            )
            response = input("Continue? (yes/no): ").strip().lower()
            if response not in ("yes", "y"):
                console.print("Cancelled")
                return

        # Clear
        result = await cache.clear_problematic_tests()

        console.print(
            f"✅ Cleared {result['position_ranges_cleared']} position ranges "
            f"and {result['test_ids_cleared']} test ID mappings"
        )

    finally:
        await cache.close()


def problematic_command_main(args: Namespace) -> NoReturn:
    """Entry point for problematic command.

    Args:
        args: Parsed command-line arguments
    """
    try:
        if args.problematic_action == "list":
            asyncio.run(list_problematic_events())
        elif args.problematic_action == "map-tests":
            asyncio.run(map_tests_to_event(args.event_id, args.test_ids))
        elif args.problematic_action == "retry":
            asyncio.run(retry_problematic_tests(args.product_id))
        elif args.problematic_action == "clear":
            asyncio.run(clear_problematic_tests(confirm=not args.yes))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Problematic command failed: {e}")
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
