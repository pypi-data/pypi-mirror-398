"""
ORM models for TestIO MCP Server.

This package contains SQLModel classes that mirror the existing SQLite schema.
All models are designed to work with async SQLAlchemy sessions.

Models:
    - Product: Product information with customer isolation
    - Test: Exploratory test data with lifecycle tracking
    - Bug: Bug reports associated with tests
    - Feature: Testable product features with embedded user stories (STORY-035A, ADR-013)
    - TestFeature: Join table between Tests and Features with historical context (STORY-041)
    - SyncEvent: Sync operation tracking for observability
    - SyncMetadata: Key-value metadata storage

Note: User stories are embedded as JSON within Feature model (ADR-013).
When TestIO API is improved, we can normalize to separate UserStory table.

Reference: STORY-031 (Entity Modeling)
Epic: EPIC-006 (ORM Refactor), EPIC-005 (Data Enhancement and Serving)
"""

from testio_mcp.models.orm.bug import Bug
from testio_mcp.models.orm.feature import Feature
from testio_mcp.models.orm.product import Product
from testio_mcp.models.orm.sync_event import SyncEvent
from testio_mcp.models.orm.sync_metadata import SyncMetadata
from testio_mcp.models.orm.test import Test
from testio_mcp.models.orm.test_feature import TestFeature
from testio_mcp.models.orm.test_platform import TestPlatform
from testio_mcp.models.orm.user import User

__all__ = [
    "Product",
    "Test",
    "Bug",
    "Feature",
    "TestFeature",
    "TestPlatform",
    "SyncEvent",
    "SyncMetadata",
    "User",
]
