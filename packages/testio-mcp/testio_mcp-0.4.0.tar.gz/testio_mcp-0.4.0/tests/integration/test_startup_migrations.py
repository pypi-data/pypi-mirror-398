"""
Integration tests for server startup migrations (STORY-034A).

Verifies that:
1. Server runs migrations on startup (creates tables)
2. Server handles existing databases correctly (idempotent)
3. TESTIO_SKIP_MIGRATIONS flag prevents migration execution
"""

import asyncio
import os
import sqlite3
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import dotenv_values

from testio_mcp.config import settings

# Skip if API token not available
pytestmark = pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="TESTIO_CUSTOMER_API_TOKEN not set - skipping integration tests",
)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary database path."""
    db_path = tmp_path / "cache.db"
    yield db_path


@pytest.fixture
def server_env(temp_db_path: Path) -> dict[str, str]:
    """Create environment for server process."""
    repo_root = Path(__file__).parent.parent.parent
    repo_env = repo_root / ".env"

    env = os.environ.copy()
    if repo_env.exists():
        env_from_file = dotenv_values(repo_env)
        env.update({k: v for k, v in env_from_file.items() if v is not None})

    # Override DB path to use temporary file
    env["TESTIO_DB_PATH"] = str(temp_db_path)
    # Ensure migrations run (default)
    env["TESTIO_SKIP_MIGRATIONS"] = "0"

    return env


def verify_tables_exist(db_path: Path) -> bool:
    """Check if all expected tables exist in the database."""
    if not db_path.exists():
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected_tables = {
            "products",
            "tests",
            "bugs",
            "features",
            "users",
            "sync_events",
            "sync_metadata",
            "search_index",
            "alembic_version",
            "test_platforms",
            "test_features",
        }
        return expected_tables.issubset(tables)
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_startup_creates_schema(
    temp_db_path: Path, server_env: dict[str, str]
) -> None:
    """Verify server creates schema on startup with fresh database."""
    # Start server in stdio mode (it should initialize and wait for input)
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "testio_mcp", "serve"],
        env=server_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait a bit for initialization (migrations take a moment)
        for _ in range(20):
            if verify_tables_exist(temp_db_path):
                break
            await asyncio.sleep(0.5)
        else:
            pytest.fail("Database tables were not created within timeout")

        # Verify specific tables
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check alembic version (should be at head after migrations)
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]

        # Get expected head dynamically from alembic
        from alembic.config import Config as AlembicConfig
        from alembic.script import ScriptDirectory

        repo_root = Path(__file__).parent.parent.parent
        alembic_cfg = AlembicConfig(str(repo_root / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(repo_root / "alembic"))
        script = ScriptDirectory.from_config(alembic_cfg)
        expected_head = script.get_current_head()

        assert version == expected_head, f"Expected {expected_head}, got {version}"

        # Check products table structure
        cursor.execute("PRAGMA table_info(products)")
        columns = {col[1] for col in cursor.fetchall()}
        assert "customer_id" in columns
        assert "data" in columns

        conn.close()

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_startup_idempotent(temp_db_path: Path, server_env: dict[str, str]) -> None:
    """Verify server startup works on existing database (idempotent)."""
    # First run: Create schema
    await test_server_startup_creates_schema(temp_db_path, server_env)

    assert temp_db_path.exists()

    # Second run: Should verify schema and continue without error
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "testio_mcp", "serve"],
        env=server_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait to ensure it doesn't crash immediately
        await asyncio.sleep(5)

        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(
                f"Server crashed on second run.\n"
                f"STDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
            )

        # Verify tables still exist
        assert verify_tables_exist(temp_db_path)

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_skip_migrations_flag(temp_db_path: Path, server_env: dict[str, str]) -> None:
    """Verify TESTIO_SKIP_MIGRATIONS prevents migration execution."""
    # Set flag to skip migrations
    server_env["TESTIO_SKIP_MIGRATIONS"] = "1"

    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "testio_mcp", "serve"],
        env=server_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait a bit
        await asyncio.sleep(5)

        # Database file might be created by PersistentCache initialization (mkdir),
        # but tables should NOT exist because migrations were skipped
        # and PersistentCache no longer creates schema

        # Note: PersistentCache.initialize() connects to DB which creates the file,
        # but since we removed initialize_schema(), tables won't be created.

        if temp_db_path.exists():
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()

            # Should be empty or only contain internal sqlite tables
            user_tables = [t[0] for t in tables if not t[0].startswith("sqlite_")]
            assert not user_tables, f"Tables created despite SKIP_MIGRATIONS: {user_tables}"
        else:
            # Even better if file doesn't exist (though PersistentCache might create it)
            pass

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
