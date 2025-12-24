"""Setup command for interactive TestIO MCP configuration.

Provides guided CLI workflow for creating ~/.testio-mcp.env configuration file.
"""

import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()

# Constants
SUBDOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$")
MIN_SUBDOMAIN_LENGTH = 1
MAX_SUBDOMAIN_LENGTH = 63  # DNS subdomain limit
MIN_TOKEN_LENGTH = 40
TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_customer_name(name: str) -> None:
    """Validate customer subdomain format.

    Rules:
    - Alphanumeric characters only (a-z, A-Z, 0-9)
    - Hyphens allowed as separators (not at start/end)
    - No whitespace, underscores, or special characters
    - Length: 1-63 characters

    Valid examples: customerName, test123, customer-name
    Invalid examples: customer_name, customer name, -invalid, invalid-

    Args:
        name: Customer subdomain to validate

    Raises:
        ValueError: If validation fails
    """
    if not name:
        raise ValueError("Subdomain cannot be empty")

    if len(name) < MIN_SUBDOMAIN_LENGTH or len(name) > MAX_SUBDOMAIN_LENGTH:
        raise ValueError(
            f"Subdomain must be between {MIN_SUBDOMAIN_LENGTH} and "
            f"{MAX_SUBDOMAIN_LENGTH} characters"
        )

    if not SUBDOMAIN_PATTERN.match(name):
        raise ValueError(
            "❌ Invalid subdomain format\n"
            "ℹ️  Subdomain must contain only letters, numbers, and hyphens\n"
            "💡 Example: customerName or customer-name (no underscores or spaces)"
        )


def validate_token_format(token: str) -> None:
    """Validate token format (basic check, not API verification).

    Rules:
    - Minimum 40 characters
    - Alphanumeric characters, dashes, and underscores only

    Args:
        token: API token to validate

    Raises:
        ValueError: If format validation fails
    """
    if len(token) < MIN_TOKEN_LENGTH:
        raise ValueError(
            f"❌ Token too short\n"
            f"ℹ️  Token must be at least {MIN_TOKEN_LENGTH} characters\n"
            f"💡 Verify you copied the complete token from TestIO"
        )

    if not TOKEN_PATTERN.match(token):
        raise ValueError(
            "❌ Invalid token format\n"
            "ℹ️  Token contains invalid characters\n"
            "💡 Token should only contain letters, numbers, dashes, and underscores"
        )


def show_token_preview(token: str) -> None:
    """Display masked token preview for verification.

    Format: {first_4}●●●●{last_4} ({length} characters)
    Example: "Token received: abcd●●●●xyz9 (64 characters)"

    Shows enough for user to verify correct paste while maintaining security.

    Args:
        token: API token to preview
    """
    first_4 = token[:4]
    last_4 = token[-4:]
    masked = f"{first_4}●●●●{last_4} ({len(token)} characters)"

    console.print(f"\n[dim]Token received: {masked}[/dim]")


def prompt_customer_name() -> str:
    """Prompt for TestIO customer subdomain name.

    Returns:
        Validated customer subdomain name

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    while True:
        try:
            customer_name = Prompt.ask(
                "[bold]TestIO subdomain[/bold]\n"
                "  [dim](e.g., if you access customerName.test.io, enter 'customerName')[/dim]"
            )

            # Validate format
            validate_customer_name(customer_name)
            return customer_name.strip()

        except ValueError as e:
            console.print(f"\n{e}\n", style="red")
        except KeyboardInterrupt:
            console.print("\n\n[dim]Setup cancelled.[/dim]")
            sys.exit(0)


def display_token_url(customer_name: str) -> None:
    """Display URL where user can get their API token.

    Args:
        customer_name: Customer subdomain name
    """
    console.print(
        f"\n[bold]🔑 Get your API token from:[/bold]\n"
        f"   [cyan]https://{customer_name}.test.io/api_integrations[/cyan]\n"
    )


def prompt_api_token() -> str:
    """Prompt for TestIO API token (masked input).

    Returns:
        Validated API token

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    while True:
        try:
            token = Prompt.ask("[bold]API Token[/bold]", password=True)

            # Validate format
            validate_token_format(token)

            # Show preview for verification
            show_token_preview(token)
            return token.strip()

        except ValueError as e:
            console.print(f"\n{e}\n", style="red")
        except KeyboardInterrupt:
            console.print("\n\n[dim]Setup cancelled.[/dim]")
            sys.exit(0)


def prompt_customer_id() -> str:
    """Prompt for Customer ID with clear instructions for both roles.

    Returns:
        Customer ID as string (default: "1")

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    try:
        customer_id = Prompt.ask(
            "[bold]Customer ID[/bold]\n"
            "  [dim]→ TestIO employees: Enter internal customer ID[/dim]\n"
            "  [dim]→ Customers: Press Enter to use default (1)[/dim]",
            default="1",
        )
        return customer_id.strip()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)


def prompt_log_format() -> str:
    """Prompt for log format preference.

    Returns:
        "text" or "json"

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    try:
        console.print("\n[bold]Log Format[/bold]")
        console.print("  [1] Text (human-readable, colorized)")
        console.print("  [2] JSON (machine-parseable, for log analysis)")

        choice = Prompt.ask("Select format", choices=["1", "2"], default="1")
        return "text" if choice == "1" else "json"
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)


def prompt_log_level() -> str:
    """Prompt for log verbosity level.

    Returns:
        "DEBUG", "INFO", or "WARNING"

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    try:
        console.print("\n[bold]Log Verbosity[/bold]")
        console.print("  [1] INFO (normal - recommended)")
        console.print("  [2] DEBUG (detailed - for troubleshooting)")
        console.print("  [3] WARNING (minimal - only important messages)")

        choice = Prompt.ask("Select level", choices=["1", "2", "3"], default="1")
        return {"1": "INFO", "2": "DEBUG", "3": "WARNING"}[choice]
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)


def prompt_product_ids() -> str:
    """Prompt for optional product ID filtering.

    Returns:
        Comma-separated product IDs or empty string

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    try:
        console.print("\n[bold]Product Filtering (Optional)[/bold]")
        console.print("  Filter sync to specific products to reduce sync time")
        console.print("  [dim]Press Enter to sync all products[/dim]")

        product_ids = Prompt.ask(
            "Product IDs (comma-separated)",
            default="",
        )
        return product_ids.strip()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)


def prompt_disable_capabilities_tool() -> bool:
    """Prompt whether to disable the get_analytics_capabilities tool.

    This tool lists available analytics dimensions/metrics. It's mainly useful
    for discovery, but query_metrics works fine without it. Most users can disable it.

    Returns:
        True if user wants to disable the capabilities tool, False otherwise

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    try:
        console.print("\n[bold]Advanced: Analytics Capabilities Tool (Optional)[/bold]")
        console.print(
            "  The 'get_analytics_capabilities' tool lists available analytics dimensions/metrics"
        )
        console.print(
            "  [dim]It's redundant - you can still run analytics queries without it[/dim]"
        )

        return Confirm.ask(
            "Disable get_analytics_capabilities tool?",
            default=True,  # Default to disabled (redundant)
        )
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)


async def check_api_connectivity(token: str, customer_name: str) -> tuple[bool, str]:
    """Test API connectivity with provided token.

    Uses TestIOClient for SEC-002 compliant token sanitization.

    Args:
        token: API token to test
        customer_name: Customer subdomain name

    Returns:
        Tuple of (success: bool, error_message: str or empty)
    """
    try:
        # Lazy import to avoid loading heavy dependencies during setup
        from testio_mcp.client import TestIOClient
        from testio_mcp.exceptions import TestIOAPIError

        base_url = "https://api.test.io/customer/v2"

        # Use TestIOClient for automatic token sanitization (SEC-002)
        async with TestIOClient(base_url=base_url, api_token=token, timeout=30.0) as client:
            # Minimal API call for validation (per_page=1)
            await client.get("products", params={"per_page": 1})
            return (True, "")

    except TestIOAPIError as e:
        # TestIOClient already sanitizes tokens in error messages (SEC-002)
        if e.status_code == 401:
            return (False, "Invalid token (401 Unauthorized)")
        elif e.status_code == 403:
            return (False, "Access denied (403 Forbidden)")
        else:
            return (False, f"API returned status {e.status_code}")

    except Exception:
        # Generic fallback for any other errors (SEC-002)
        return (False, "Connection failed. Please check your network and try again.")


async def validate_token_with_retry(token: str, customer_name: str) -> str:
    """Validate token with API connectivity test and retry options.

    Flow:
    1. Test API connectivity
    2. On success: Continue
    3. On failure: Offer [1] Retry, [2] Force save, [3] Cancel

    Args:
        token: API token to validate
        customer_name: Customer subdomain name

    Returns:
        Validated token (may be updated if user retries)

    Raises:
        SystemExit: If user cancels
    """
    while True:
        with console.status("🔄 Testing API connectivity..."):
            success, error_msg = await check_api_connectivity(token, customer_name)

        if success:
            console.print("[green]✅ Token validated successfully![/green]\n")
            return token

        # Validation failed - show error and options
        console.print(f"\n[red]❌ Token validation failed: {error_msg}[/red]\n")
        console.print("[yellow]Options:[/yellow]")
        console.print("  [1] Retry with a different token")
        console.print("  [2] Force save anyway (skip validation)")
        console.print("  [3] Cancel setup\n")

        try:
            choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
        except KeyboardInterrupt:
            console.print("\n\n[dim]Setup cancelled.[/dim]")
            sys.exit(0)

        if choice == "1":
            # Re-prompt for token
            token = prompt_api_token()
            continue  # Retry validation loop

        elif choice == "2":
            # Force save with double confirmation
            try:
                if Confirm.ask(
                    "[yellow]⚠️  Saving unvalidated token. Server may not work. Continue?[/yellow]",
                    default=False,
                ):
                    console.print("[yellow]⚠️  Token validation skipped[/yellow]\n")
                    return token  # Proceed without validation
                else:
                    continue  # Back to options menu
            except KeyboardInterrupt:
                console.print("\n\n[dim]Setup cancelled.[/dim]")
                sys.exit(0)

        else:  # choice == "3"
            console.print("[dim]Setup cancelled.[/dim]")
            sys.exit(0)


def show_confirmation_summary(config: dict[str, object]) -> str:
    """Show configuration summary and get user confirmation.

    Args:
        config: Configuration dictionary with all settings

    Returns:
        "save" | "edit" | "cancel"

    Raises:
        SystemExit: If user cancels (Ctrl+C)
    """
    # Create summary table
    table = Table(title="Configuration Summary", show_header=False)
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="white")

    customer_name = str(config["customer_name"])
    table.add_row("Subdomain", customer_name)

    # Masked token preview
    token = str(config["token"])
    masked_token = f"{token[:4]}●●●●{token[-4:]} ({len(token)} chars)"
    table.add_row("API Token", masked_token)

    customer_id = str(config["customer_id"])
    table.add_row("Customer ID", customer_id)

    # New settings
    log_format = str(config.get("log_format", "json"))
    table.add_row("Log Format", log_format)

    log_level = str(config.get("log_level", "INFO"))
    table.add_row("Log Level", log_level)

    product_ids = str(config.get("product_ids", ""))
    product_ids_display = product_ids if product_ids else "[dim]All products[/dim]"
    table.add_row("Product Filter", product_ids_display)

    # Capabilities tool setting
    disable_capabilities = bool(config.get("disable_capabilities", True))
    capabilities_display = "[dim]Disabled[/dim]" if disable_capabilities else "Enabled"
    table.add_row("Capabilities Tool", capabilities_display)

    table.add_row("File Path", str(config["file_path"]))

    console.print()
    console.print(table)
    console.print()

    console.print("[bold]Options:[/bold]")
    console.print("  [S] Save configuration")
    console.print("  [E] Edit (start over)")
    console.print("  [C] Cancel setup\n")

    try:
        choice = Prompt.ask(
            "Select option", choices=["s", "S", "e", "E", "c", "C"], default="S"
        ).lower()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)

    if choice == "s":
        return "save"
    elif choice == "e":
        console.print("\n[yellow]Starting over...[/yellow]\n")
        return "edit"
    else:  # cancel
        console.print("[dim]Setup cancelled.[/dim]")
        return "cancel"


def handle_file_overwrite(env_path: Path) -> None:
    """Check for existing file and handle overwrite with backup.

    - If file doesn't exist: Continue
    - If file exists: Prompt to overwrite
      - If yes: Create backup, continue
      - If no: Exit with preservation message

    Args:
        env_path: Path to environment file

    Raises:
        SystemExit: If user declines overwrite or cancels (Ctrl+C)
    """
    if not env_path.exists():
        return  # No file to overwrite

    console.print(f"\n[yellow]⚠️  Configuration file already exists:[/yellow] {env_path}\n")

    try:
        if not Confirm.ask("Overwrite existing configuration?", default=False):
            console.print("\n[dim]Setup cancelled. Existing configuration preserved.[/dim]")
            console.print(f"[dim]To reconfigure, delete {env_path} and run setup again.[/dim]")
            sys.exit(0)
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)

    # Create backup before overwriting
    console.print("[dim]Backing up existing file...[/dim]")
    backup_path = env_path.with_suffix(".env.backup")
    shutil.copy(env_path, backup_path)
    console.print(f"[dim]Backup saved to: {backup_path}[/dim]\n")


def copy_docs_to_config_dir() -> list[str]:
    """Copy bundled documentation to ~/.testio-mcp/ for easy access.

    Copies README.md, MCP_SETUP.md, ANALYTICS.md, and .env.example from package to config directory.
    Users installing via uvx don't have access to repo files.

    Returns:
        List of successfully copied doc filenames.
    """
    copied: list[str] = []
    try:
        from importlib.resources import files

        config_dir = Path.home() / ".testio-mcp"
        config_dir.mkdir(parents=True, exist_ok=True)

        docs_package = files("testio_mcp.docs")
        for doc_name in ["README.md", "MCP_SETUP.md", "ANALYTICS.md", ".env.example"]:
            try:
                doc_file = docs_package.joinpath(doc_name)
                doc_content = doc_file.read_text()
                dest_path = config_dir / doc_name
                dest_path.write_text(doc_content)
                copied.append(doc_name)
            except (FileNotFoundError, TypeError):
                # Doc not bundled (e.g., editable install), skip silently
                pass
            except Exception as e:
                # Unexpected error - warn user
                console.print(f"[yellow]Warning: Could not copy {doc_name}: {e}[/yellow]")
    except Exception as e:
        # Config dir creation or importlib error
        console.print(f"[yellow]Warning: Could not copy docs: {e}[/yellow]")

    return copied


def write_env_file(config: dict[str, object]) -> None:
    """Write environment file with secure permissions (0o600).

    File format:
    TESTIO_CUSTOMER_API_TOKEN=...
    TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2
    TESTIO_CUSTOMER_NAME=...
    TESTIO_CUSTOMER_ID=...
    LOG_FORMAT=...
    LOG_LEVEL=...
    TESTIO_PRODUCT_IDS=... (optional)

    Args:
        config: Configuration dictionary with all settings
    """
    env_path_obj = config["file_path"]
    assert isinstance(env_path_obj, Path)  # Type narrowing for mypy
    base_url = "https://api.test.io/customer/v2"

    with console.status("💾 Writing configuration..."):
        # Build file content
        content = (
            "# TestIO MCP Server Configuration\n"
            "# Generated by: uvx testio-mcp setup\n"
            "\n"
            "# API Credentials\n"
            f"TESTIO_CUSTOMER_API_TOKEN={config['token']}\n"
            f"TESTIO_CUSTOMER_API_BASE_URL={base_url}\n"
            f"TESTIO_CUSTOMER_NAME={config['customer_name']}\n"
            f"TESTIO_CUSTOMER_ID={config['customer_id']}\n"
            "\n"
            "# Logging\n"
            f"LOG_FORMAT={config.get('log_format', 'json')}\n"
            f"LOG_LEVEL={config.get('log_level', 'INFO')}\n"
            "LOG_FILE=~/.testio-mcp/logs/server.log\n"
            "\n"
            "# HTTP Server (for --transport http mode)\n"
            "TESTIO_HTTP_HOST=127.0.0.1\n"
            "TESTIO_HTTP_PORT=8080\n"
            "\n"
            "# Data Store\n"
            "TESTIO_DB_PATH=~/.testio-mcp/cache.db\n"
            "TESTIO_REFRESH_INTERVAL_SECONDS=3600  # Background sync (1 hour, 0=disabled)\n"
            "CACHE_TTL_SECONDS=3600  # Data staleness threshold (1 hour)\n"
            "# TESTIO_SYNC_SINCE=  # Optional: limit sync to recent data (e.g., '90 days ago')\n"
        )

        # Add product IDs section (always include for discoverability)
        product_ids = str(config.get("product_ids", "")).strip()
        content += "\n# Product Filtering\n"
        if product_ids:
            content += f"TESTIO_PRODUCT_IDS={product_ids}  # Sync only these products\n"
        else:
            content += (
                "# TESTIO_PRODUCT_IDS=  # Optional: filter to specific products (e.g., 598,1024)\n"
            )

        # Add disabled tools if user chose to disable capabilities tool
        disable_capabilities = bool(config.get("disable_capabilities", True))
        if disable_capabilities:
            content += "\n# Tool Configuration\nDISABLED_TOOLS=get_analytics_capabilities\n"

        env_path_obj.write_text(content)

        # Set secure permissions (user read/write only)
        env_path_obj.chmod(0o600)


def show_success_message(env_path: Path) -> None:
    """Display success message with next steps.

    Args:
        env_path: Path to created environment file
    """
    # Copy docs to config dir for easy access
    copied_docs = copy_docs_to_config_dir()

    console.print("\n[green]✅ Configuration saved![/green]\n")
    console.print(f"[dim]Config:[/dim] {env_path}")
    if copied_docs:
        docs_list = ", ".join(copied_docs)
        console.print(f"[dim]Docs:[/dim]   ~/.testio-mcp/{docs_list}\n")
    else:
        console.print()  # Just add spacing if no docs copied

    console.print("[bold]Next:[/bold]")
    console.print("  [cyan]uvx testio-mcp serve --transport http[/cyan]")
    console.print()
    console.print("[bold]Then open:[/bold]")
    console.print("  [cyan]http://127.0.0.1:8080/docs[/cyan]  (Swagger UI)")
    console.print("  [cyan]http://127.0.0.1:8080/health[/cyan] (Health check)")


async def run_setup_flow() -> None:
    """Execute the full setup workflow.

    Main flow with retry loop for confirmation:
    1. Prompt for customer name
    2. Display token URL
    3. Prompt for API token
    4. Prompt for customer ID
    5. Prompt for log format
    6. Prompt for log level
    7. Prompt for product IDs (optional)
    8. Prompt for tool disabling (optional - get_analytics_capabilities)
    9. Validate token with retry
    10. Show confirmation summary
    11. Handle file overwrite
    12. Write configuration
    13. Show success message

    Raises:
        SystemExit: On cancellation or errors
    """
    while True:
        # 1. Customer Name Prompt
        customer_name = prompt_customer_name()

        # 2. API Token URL Display
        display_token_url(customer_name)

        # 3. API Token Prompt
        token = prompt_api_token()

        # 4. Customer ID Prompt
        customer_id = prompt_customer_id()

        # 5. Log Format Prompt
        log_format = prompt_log_format()

        # 6. Log Level Prompt
        log_level = prompt_log_level()

        # 7. Product IDs Prompt (optional)
        product_ids = prompt_product_ids()

        # 8. Capabilities Tool Prompt (optional)
        disable_capabilities = prompt_disable_capabilities_tool()

        # 9. Token Validation (with retry loop)
        token = await validate_token_with_retry(token, customer_name)

        # 10. Confirmation Summary
        config = {
            "customer_name": customer_name,
            "token": token,
            "customer_id": customer_id,
            "log_format": log_format,
            "log_level": log_level,
            "product_ids": product_ids,
            "disable_capabilities": disable_capabilities,
            "file_path": Path.home() / ".testio-mcp.env",
        }

        choice = show_confirmation_summary(config)
        if choice == "save":
            break  # Exit retry loop
        elif choice == "edit":
            continue  # Restart from step 1
        else:  # cancel
            sys.exit(0)

    # 7. File Overwrite Check
    file_path = config["file_path"]
    assert isinstance(file_path, Path)  # Type narrowing for mypy
    handle_file_overwrite(file_path)

    # 8. Write Configuration
    write_env_file(config)

    # 9. Success Message
    show_success_message(file_path)


def setup_command_main() -> NoReturn:
    """Entry point for setup command.

    Executes interactive setup workflow for ~/.testio-mcp.env configuration.

    Raises:
        SystemExit: Always (normal exit after completion or cancellation)
    """
    import asyncio

    try:
        asyncio.run(run_setup_flow())
        sys.exit(0)
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled.[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Setup failed: {e}[/red]")
        sys.exit(1)
