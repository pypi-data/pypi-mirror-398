"""Sync command for TestIO MCP CLI.

Provides manual database sync with progress reporting, date filtering,
and status inspection. Delegates to SyncService for unified orchestration.

STORY-050: CLI Sync Migration to SyncService
Reference: DESIGN-CLI-SYNC-COMMAND.md
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from testio_mcp.client import TestIOClient
from testio_mcp.config import Settings
from testio_mcp.database import PersistentCache
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.product_repository import ProductRepository
from testio_mcp.repositories.test_repository import TestRepository
from testio_mcp.services.sync_service import (
    SyncOptions,
    SyncPhase,
    SyncResult,
    SyncScope,
    SyncService,
)
from testio_mcp.utilities.date_utils import parse_flexible_date

console = Console()


async def sync_database(
    *,
    since: datetime | None = None,
    product_ids: list[int] | None = None,
    force: bool = False,
    nuke: bool = False,
    refresh: bool = False,
    incremental_only: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Sync database with optional date filtering.

    Args:
        since: Only sync tests with end_at >= this date
        product_ids: Only sync these product IDs (overrides env var)
        force: Refresh all tests using upsert (non-destructive)
        nuke: Delete database and rebuild (destructive, requires confirmation)
        refresh: (DEPRECATED) Same as default - discover new tests AND update mutable tests
        incremental_only: Fast mode - discover new tests only (skip mutable test refresh)
        dry_run: Preview sync without making changes
        verbose: Show detailed logging

    Returns:
        Sync result dictionary with stats
    """
    # Load settings
    settings = Settings()

    # Show deprecation warning for --refresh flag
    if refresh:
        console.print(
            "[yellow]⚠️  Warning: --refresh flag is deprecated and will be "
            "removed in a future version.[/yellow]"
        )
        console.print(
            "[yellow]   Hybrid refresh (discover new + update mutable) is now "
            "the default behavior.[/yellow]"
        )
        console.print("[yellow]   Use --incremental-only for fast discovery-only mode.\n[/yellow]")

    # Apply product filtering
    if product_ids is None:
        product_ids = settings.TESTIO_PRODUCT_IDS

    # Run database migrations before initializing cache (STORY-039)
    # This ensures schema is up-to-date for all CLI entry points
    if not settings.TESTIO_SKIP_MIGRATIONS:
        import subprocess

        # Ensure database directory exists
        db_path = Path(settings.TESTIO_DB_PATH).expanduser().resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Migration failed: {e}[/red]")
            console.print(e.stdout)
            console.print(e.stderr)
            raise SystemExit(1) from e
        except FileNotFoundError:
            console.print("[red]❌ alembic command not found[/red]")
            console.print("Install with: uv pip install alembic")
            raise SystemExit(1) from None

    # Create client and cache
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
        )

        await cache.initialize()

        if verbose:
            console.print(f"[dim]Database: {cache.db_path}[/dim]")
            console.print(f"[dim]Customer ID: {cache.customer_id}[/dim]")
            if product_ids:
                console.print(f"[dim]Product filter: {product_ids}[/dim]")
            if since:
                console.print(f"[dim]Date filter (since): {since.isoformat()}[/dim]")

        # Dry-run mode: Show what would be synced
        if dry_run:
            console.print("\n[yellow]DRY RUN - No changes will be made[/yellow]\n")

            # Fetch products to show what would be synced
            response = await client.get("products")

            if verbose:
                console.print(f"[dim]Raw API response keys: {list(response.keys())}[/dim]")
                console.print(f"[dim]Response count field: {response.get('count', 'N/A')}[/dim]")

            all_products = response.get("products", [])

            if verbose:
                console.print(f"[dim]API returned {len(all_products)} products[/dim]")
                if all_products and len(all_products) > 0:
                    console.print(f"[dim]Sample product: {all_products[0]}[/dim]")

            # Apply product filter and categorize products
            if product_ids:
                products_to_sync = [p for p in all_products if p.get("id") in product_ids]
                products_filtered = [p for p in all_products if p.get("id") not in product_ids]
                if verbose:
                    console.print(
                        f"[dim]Filtered to {len(products_to_sync)} products "
                        f"matching IDs: {product_ids}[/dim]"
                    )
                    console.print(
                        f"[dim]Skipped {len(products_filtered)} products not matching filter[/dim]"
                    )
            else:
                products_to_sync = all_products
                products_filtered = []
                if verbose:
                    console.print(
                        f"[dim]No product filter applied, syncing all "
                        f"{len(products_to_sync)} products[/dim]"
                    )

            # Show preview table
            table = Table(title="Sync Preview")
            table.add_column("Product ID", style="cyan")
            table.add_column("Product Name", style="white")
            table.add_column("Last Sync", style="dim")
            table.add_column("Action")

            # Get env var filter for display (if any)
            env_filter = settings.TESTIO_PRODUCT_IDS

            # Show products that will be synced
            for product in products_to_sync:
                product_id = product.get("id")

                # Get last sync time
                last_sync = await cache._repo.get_product_last_synced(product_id)
                last_sync_display = last_sync if last_sync else "Never"

                # Determine action based on mode flags and whether product exists in DB
                if nuke:
                    action = "Nuclear rebuild (destructive)"
                elif force:
                    action = "Force refresh (upsert)"
                elif refresh:
                    action = "Hybrid refresh (discover + update)"
                else:
                    # Check if product already exists in database
                    product_count = await cache._repo.count_product_tests(product_id)
                    action = "Incremental sync" if product_count > 0 else "Initial sync"

                table.add_row(
                    str(product_id),
                    product.get("name", ""),
                    last_sync_display,
                    f"[green]{action}[/green]",
                )

            # Show filtered products (if any)
            for product in products_filtered:
                product_id = product.get("id")

                # Get last sync time for filtered products too
                last_sync = await cache._repo.get_product_last_synced(product_id)
                last_sync_display = last_sync if last_sync else "Never"

                # Check if filtered by env var or CLI arg
                if env_filter and product_id not in env_filter:
                    filter_reason = "env var"
                else:
                    filter_reason = "CLI arg"

                table.add_row(
                    str(product_id),
                    product.get("name", ""),
                    last_sync_display,
                    f"[dim]Skipped ({filter_reason})[/dim]",
                )

            console.print(table)

            product_word = "products" if len(products_to_sync) != 1 else "product"
            summary = f"\n[bold]Would sync {len(products_to_sync)} {product_word}[/bold]"
            if products_filtered:
                summary += f" [dim](skipped {len(products_filtered)})[/dim]"
            console.print(summary)

            # Close cache connection before returning
            await cache.close()

            # Determine action type for result
            if nuke:
                action_type = "nuclear_rebuild"
            elif force:
                action_type = "force_refresh"
            elif incremental_only:
                action_type = "incremental_sync"
            else:
                # Default is now hybrid refresh (discover new + update mutable)
                action_type = "hybrid_refresh"

            return {
                "status": "dry_run",
                "products_previewed": len(products_to_sync),
                "products_filtered": len(products_filtered),
                "action": action_type,
            }

        # Nuclear rebuild mode: Confirm and delete existing data (STORY-021d, AC8)
        if nuke:
            console.print("[yellow]⚠️  DESTRUCTIVE: Nuclear rebuild mode[/yellow]")
            console.print("This will DELETE all local data and resync from scratch.\n")

            # STORY-050 AC8: Enhanced warning with ALL entity counts
            total_tests = await cache.count_tests()
            total_products = await cache.count_products()

            # Query additional entity counts
            async with cache.async_session_maker() as session:
                # Get bug count
                from sqlmodel import func, select

                from testio_mcp.models.orm.bug import Bug

                bug_count_result = await session.exec(select(func.count(Bug.id)))  # type: ignore[arg-type]
                total_bugs = bug_count_result.one()

                # Get feature count
                from testio_mcp.models.orm.feature import Feature

                feature_count_result = await session.exec(select(func.count(Feature.id)))  # type: ignore[arg-type]
                total_features = feature_count_result.one()

                # Get user count
                from testio_mcp.models.orm.user import User

                user_count_result = await session.exec(select(func.count(User.id)))  # type: ignore[arg-type]
                total_users = user_count_result.one()

            db_size_mb = await cache.get_db_size_mb()

            console.print(f"Database: {cache.db_path} ({db_size_mb:.1f} MB)")
            # AC8: Display all entity counts
            console.print(
                f"Current data: {total_products} products, {total_tests} tests, "
                f"{total_bugs} bugs, {total_features} features, {total_users} users\n"
            )

            # Manual confirmation required (unless --yes flag used elsewhere)
            confirm = console.input("[bold]Are you ABSOLUTELY sure? Type 'yes' to confirm: [/bold]")
            if confirm.lower() != "yes":
                console.print("[red]Nuclear rebuild cancelled[/red]")
                return {"status": "cancelled", "reason": "nuke_confirmation_declined"}

            # Delete existing data
            if product_ids:
                for product_id in product_ids:
                    await cache.delete_product_tests(product_id)
                console.print(f"[green]✓ Deleted data for {len(product_ids)} products[/green]")
            else:
                # Delete all products (recreate database)
                await cache.close()
                cache.db_path.unlink(missing_ok=True)

                # Run Alembic migrations in subprocess (can't use command.upgrade in async context)
                import subprocess

                alembic_ini_path = Path(__file__).parent.parent.parent.parent / "alembic.ini"
                migration_result = subprocess.run(
                    ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
                    capture_output=True,
                    text=True,
                )
                if migration_result.returncode != 0:
                    console.print(f"[red]Migration failed: {migration_result.stderr}[/red]")
                    raise RuntimeError(f"Alembic migration failed: {migration_result.stderr}")

                # Re-initialize cache with new schema
                await cache.initialize()
                console.print("[green]✓ Database deleted and recreated[/green]\n")

        # =============================================================================
        # STORY-050: Delegate to SyncService for all sync operations
        # =============================================================================

        # Create SyncService with repository factories
        # STORY-062: Pass cache to repositories for per-entity locks in batch operations
        customer_id = settings.TESTIO_CUSTOMER_ID
        sync_service = SyncService(
            client=client,
            cache=cache,
            product_repo_factory=lambda s: ProductRepository(s, client, customer_id),
            feature_repo_factory=lambda s: FeatureRepository(s, client, customer_id, cache),
            test_repo_factory=lambda s: TestRepository(s, client, customer_id, cache=cache),
        )

        # AC2: Map --force to SyncOptions.force_refresh=True
        # AC3: Map --incremental-only to phases=[SyncPhase.NEW_TESTS]
        # AC4: Map --nuke to SyncOptions.nuke=True (already handled above)
        # AC5: Map --product-ids to SyncScope.product_ids
        # AC6: Map --since to SyncScope.since_date

        # Determine phases based on mode flags (AC3)
        if incremental_only:
            # Fast mode: NEW_TESTS phase only
            phases = [SyncPhase.NEW_TESTS]
            mode_description = "⚡ Fast mode: Discovering new tests only"
        else:
            # Default: All 3 phases (PRODUCTS, FEATURES, NEW_TESTS)
            phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]
            if force:
                mode_description = "⟳ Force refresh mode: Updating all tests (non-destructive)"
            elif nuke:
                mode_description = "💣 Nuclear rebuild: Full resync after database deletion"
            else:
                mode_description = "⟳ Hybrid refresh mode: Discover new + update mutable tests"

        console.print(f"[cyan]{mode_description}[/cyan]\n")

        # Create SyncScope (AC5, AC6)
        scope = SyncScope(
            product_ids=product_ids,
            since_date=since,
        )

        # Create SyncOptions (AC2, AC4)
        options = SyncOptions(
            force_refresh=force,
            incremental_only=incremental_only,
            nuke=nuke,
        )

        # Execute sync via SyncService (AC1)
        if verbose:
            console.print(f"[dim]Phases: {[p.value for p in phases]}[/dim]")
            console.print(
                f"[dim]Scope: product_ids={scope.product_ids}, since={scope.since_date}[/dim]"
            )
            console.print(
                f"[dim]Options: force={options.force_refresh}, "
                f"incremental={options.incremental_only}, nuke={options.nuke}[/dim]\n"
            )

        # Show progress bar during sync (AC7: Preserve CLI output formatting)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Syncing...", total=None)

            # Execute sync
            result: SyncResult = await sync_service.execute_sync(
                phases=phases,
                scope=scope,
                options=options,
                trigger_source="manual_cli",
            )

            progress.update(task, completed=True)

        await cache.close()

        # AC7: Preserve CLI output formatting - show summary stats
        console.print(
            f"\n[green]✓ Sync complete: {result.products_synced} products, "
            f"{result.features_refreshed} features refreshed, "
            f"{result.tests_discovered} new / {result.tests_updated} updated tests"
        )

        console.print(f"[dim]Duration: {result.duration_seconds:.1f}s[/dim]")

        if result.warnings:
            console.print("\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  [yellow]{warning}[/yellow]")

        if result.errors:
            console.print("\n[red]❌ Errors:[/red]")
            for error in result.errors:
                console.print(f"  [red]{error}[/red]")

        # Return result dictionary for compatibility
        return {
            "status": "success" if not result.errors else "partial_failure",
            "products_synced": result.products_synced,
            "features_refreshed": result.features_refreshed,
            "tests_discovered": result.tests_discovered,
            "tests_updated": result.tests_updated,
            "duration_seconds": result.duration_seconds,
            "warnings": result.warnings,
            "errors": result.errors,
        }


async def show_sync_status(*, verbose: bool = False) -> None:
    """Show current database sync status.

    Args:
        verbose: Show detailed sync information
    """
    settings = Settings()

    # Run database migrations before initializing cache (STORY-039)
    if not settings.TESTIO_SKIP_MIGRATIONS:
        import subprocess

        db_path = Path(settings.TESTIO_DB_PATH).expanduser().resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Silently fail - status command should work even if migrations fail
            pass

    # Create cache (read-only)
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
        )

        await cache.initialize()

        # Gather stats
        total_tests = await cache.count_tests()
        total_products = await cache.count_products()
        db_size_mb = await cache.get_db_size_mb()
        oldest_test_date = await cache.get_oldest_test_date()
        newest_test_date = await cache.get_newest_test_date()

        # Display status table
        table = Table(title="Database Sync Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Database Path", str(cache.db_path))
        table.add_row("Customer ID", str(cache.customer_id))
        table.add_row("Database Size", f"{db_size_mb:.2f} MB")
        table.add_row("Total Products", str(total_products))
        table.add_row("Total Tests", str(total_tests))
        table.add_row("Oldest Test Date", oldest_test_date or "N/A")
        table.add_row("Newest Test Date", newest_test_date or "N/A")

        console.print(table)

        # Verbose: Show per-product stats
        if verbose:
            synced_products = await cache.get_synced_products_info()

            if synced_products:
                console.print("\n[bold]Products Synced:[/bold]")
                product_table = Table()
                product_table.add_column("Product ID", style="cyan")
                product_table.add_column("Test Count", style="white")
                product_table.add_column("Last Synced", style="dim")

                for product_info in synced_products:
                    product_table.add_row(
                        str(product_info["id"]),
                        str(product_info["test_count"]),
                        product_info.get("last_synced", "N/A"),
                    )

                console.print(product_table)

        await cache.close()


def sync_command_main(args: Any) -> NoReturn:
    """Entry point for sync command.

    Args:
        args: Parsed command-line arguments from argparse
    """
    # Configure logging for CLI with Rich integration
    # Use RichHandler for console output (integrates nicely with progress bars)
    # Also log to file for detailed debugging
    from testio_mcp.utilities.logging import ShutdownErrorFilter

    settings = Settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Rich handler for console (integrates with progress bars)
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=False,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    rich_handler.addFilter(ShutdownErrorFilter())

    # File handler for debugging
    log_file = Path(settings.LOG_FILE).expanduser()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)

    # Configure package logger
    logger = logging.getLogger("testio_mcp")
    logger.setLevel(log_level)

    # Parse date arguments if provided
    # Priority: --since flag > TESTIO_SYNC_SINCE env var > None
    since: datetime | None = None

    try:
        # Determine which date value to use
        date_value = args.since if args.since else settings.TESTIO_SYNC_SINCE
        date_source = "CLI flag" if args.since else "TESTIO_SYNC_SINCE env var"

        if date_value:
            # Use parse_flexible_date from utilities (supports business terms, ISO, relative dates)
            iso_string = parse_flexible_date(date_value, start_of_day=True)
            # Convert ISO string back to datetime for internal use
            since = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

            # Log where the date filter came from with parsed date
            if args.since:
                logger.info(
                    f"Using date filter from {date_source}: '{args.since}' → {since.date()}"
                )
            else:
                logger.info(
                    f"Using date filter from "
                    f"{date_source}: '{settings.TESTIO_SYNC_SINCE}' → {since.date()} "
                    f"(override with --since to change)"
                )
    except Exception as e:
        console.print(f"[red]Error parsing date from {date_source}: {e}[/red]")
        sys.exit(1)

    # Validate mutual exclusivity (STORY-021d, STORY-021g)
    mode_flags = [args.force, args.nuke, args.refresh]
    mode_count = sum(bool(flag) for flag in mode_flags)
    if mode_count > 1:
        console.print("[red]Error: Cannot combine --force, --nuke, and --refresh flags[/red]")
        console.print("[dim]  --force: Non-destructive refresh (upsert strategy)[/dim]")
        console.print("[dim]  --nuke: Destructive rebuild (delete and resync)[/dim]")
        console.print("[dim]  --refresh: Discover new + update mutable tests[/dim]")
        sys.exit(1)

    # Parse product IDs if provided
    product_ids: list[int] | None = None
    if args.product_ids:
        # Validate against env var filter if set
        if settings.TESTIO_PRODUCT_IDS:
            invalid_ids = [
                pid for pid in args.product_ids if pid not in settings.TESTIO_PRODUCT_IDS
            ]
            if invalid_ids:
                console.print(
                    f"[red]Error: Product ID(s) {', '.join(map(str, invalid_ids))} "
                    f"not in TESTIO_PRODUCT_IDS filter[/red]"
                )
                console.print(
                    f"[yellow]Allowed products: "
                    f"{', '.join(map(str, settings.TESTIO_PRODUCT_IDS))}[/yellow]"
                )
                console.print(
                    "[dim]Tip: This ensures manual syncs match your configured "
                    "product filter for scheduled syncs[/dim]"
                )
                sys.exit(1)
        product_ids = args.product_ids

    # Status flag: Show sync status and exit
    if args.status:
        asyncio.run(show_sync_status(verbose=args.verbose))
        sys.exit(0)

    # Sync database
    try:
        result = asyncio.run(
            sync_database(
                since=since,
                product_ids=product_ids,
                force=args.force,
                nuke=args.nuke,
                refresh=args.refresh,
                incremental_only=getattr(args, "incremental_only", False),
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
        )

        # Exit code based on result
        if result.get("status") == "cancelled":
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error during sync: {e}[/red]")
        if args.verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)
