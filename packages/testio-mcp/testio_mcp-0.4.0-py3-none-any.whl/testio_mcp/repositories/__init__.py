"""
Data access layer (repositories) for testio-mcp.

This module provides clean separation between business logic and database operations.
Repositories handle pure SQL queries while services handle orchestration.

STORY-023c: Added BaseRepository and BugRepository for SQLite-first architecture.
"""

from testio_mcp.repositories.base_repository import BaseRepository
from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.repositories.test_repository import TestRepository

__all__ = ["BaseRepository", "BugRepository", "TestRepository"]
