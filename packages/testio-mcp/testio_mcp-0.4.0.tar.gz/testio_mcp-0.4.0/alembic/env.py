import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from sqlmodel import SQLModel

from alembic import context

# STORY-034A: Import all ORM models for autogenerate support
# Must be imported before target_metadata assignment
from testio_mcp.models.orm import (  # noqa: F401
    Bug,
    Feature,
    Product,
    SyncEvent,
    SyncMetadata,
    Test,
    TestFeature,
    TestPlatform,
    User,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# STORY-034A: Only configure logging if not already configured
# (prevents conflicts when run from server lifespan)
if config.config_file_name is not None and not config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

# STORY-030: Load configuration from environment
# Use TESTIO_DB_PATH to set the database URL dynamically
db_path = os.getenv("TESTIO_DB_PATH", str(Path.home() / ".testio-mcp" / "cache.db"))
abs_db_path = Path(db_path).expanduser().resolve()

# Override sqlalchemy.url from alembic.ini with environment-based path
config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{abs_db_path}")

# STORY-030: Add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(
    object: object, name: str | None, type_: str, reflected: bool, compare_to: object | None
) -> bool:
    """Filter to exclude FTS5 internal tables from autogenerate.

    FTS5 virtual tables create several internal SQLite tables that should not
    be tracked in migrations:
    - search_index_config
    - search_index_content
    - search_index_data
    - search_index_docsize
    - search_index_idx

    The main virtual table 'search_index' is created via raw SQL in migrations.

    Args:
        object: The database object being considered
        name: Name of the object
        type_: Type of object ('table', 'column', etc.)
        reflected: Whether object was reflected from database
        compare_to: Object from metadata being compared to

    Returns:
        False to exclude object from autogenerate, True to include
    """
    # Exclude FTS5 internal tables (STORY-064)
    if type_ == "table" and name in (
        "search_index_config",
        "search_index_content",
        "search_index_data",
        "search_index_docsize",
        "search_index_idx",
        "search_index",  # Main virtual table (created via raw SQL, not ORM)
    ):
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # STORY-036: Enable batch mode for SQLite ALTER operations
        include_object=include_object,  # STORY-064: Exclude FTS5 internal tables
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations in async context.

    Args:
        connection: Async connection from engine
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # STORY-036: Enable batch mode for SQLite ALTER operations
        include_object=include_object,  # STORY-064: Exclude FTS5 internal tables
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable: AsyncEngine) -> None:
    """Run migrations with an async engine (STORY-030, STORY-039).

    Args:
        connectable: AsyncEngine to use for migrations

    This handles async execution using run_sync() to execute the synchronous
    migration functions in an async-compatible way.
    """
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This supports three modes (STORY-039, ADR-016):
    1. CLI mode (alembic upgrade head): Creates new async engine
    2. pytest-alembic async mode: AsyncEngine provided via config.attributes
    3. Programmatic sync mode: Sync connection provided via config.attributes

    Pattern based on pytest-alembic asyncio docs:
    https://pytest-alembic.readthedocs.io/en/latest/asyncio.html

    We detect the type of connectable and branch appropriately:
    - AsyncEngine: Run async migrations
    - Connection (sync): Run sync migrations directly
    - None: Create new async engine (CLI mode)
    """
    # Check if connection/engine is provided programmatically
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        # CLI mode: Create new async engine from config
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    # Branch based on connectable type (pytest-alembic recommended pattern)
    if isinstance(connectable, AsyncEngine):
        # Async mode: pytest-alembic with AsyncEngine or CLI mode
        asyncio.run(run_async_migrations(connectable))
    else:
        # Sync mode: Direct connection (e.g., from server startup)
        do_run_migrations(connectable)


# STORY-030: Use async migrations (AC4)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
