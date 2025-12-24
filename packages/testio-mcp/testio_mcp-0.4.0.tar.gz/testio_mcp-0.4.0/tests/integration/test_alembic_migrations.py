"""Alembic migration consistency tests (STORY-039, ADR-016).

Uses pytest-alembic built-in tests to verify:
1. Single head revision (no diverging branches)
2. Upgrade path works (base to head)
3. ORM matches migrations (no forgotten migrations)
4. Downgrade consistency (all downgrades succeed)

These tests ensure the migration chain is healthy and that ORM model
changes are always accompanied by corresponding migrations.

Reference:
- ADR-016: Alembic Migration Strategy
- pytest-alembic docs: https://pytest-alembic.readthedocs.io/
"""

import pytest

# Import built-in tests for explicit collection
# (alternative to --test-alembic flag, allows running via pytest path)
from pytest_alembic.tests import (
    test_model_definitions_match_ddl,
    test_single_head_revision,
    test_up_down_consistency,
    test_upgrade,
)

# Mark all tests as integration (require database setup)
pytestmark = pytest.mark.integration

# Re-export tests to make them discoverable by pytest
# The imports above make the test functions available in this module's namespace
__all__ = [
    "test_model_definitions_match_ddl",
    "test_single_head_revision",
    "test_up_down_consistency",
    "test_upgrade",
]
