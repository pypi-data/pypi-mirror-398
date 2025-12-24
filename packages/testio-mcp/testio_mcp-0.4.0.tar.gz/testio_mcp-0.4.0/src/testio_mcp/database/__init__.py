"""Database layer for TestIO MCP server.

This module provides persistent storage using SQLite with:
- PersistentCache: Main cache interface
- Schema operations: DDL and migrations
"""

from testio_mcp.database.cache import PersistentCache
from testio_mcp.database.utils import (
    configure_wal_mode,
    vacuum_database,
)

__all__ = [
    "PersistentCache",
    "configure_wal_mode",
    "vacuum_database",
]
