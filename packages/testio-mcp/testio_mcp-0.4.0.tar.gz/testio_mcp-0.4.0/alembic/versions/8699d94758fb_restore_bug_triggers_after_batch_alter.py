"""Restore bug triggers after batch_alter_table (STORY-064 hotfix)

Root Cause:
- Migration 8a9b7c6d5e4f used batch_alter_table on bugs table to add 'known' column
- SQLite's batch_alter_table recreates the table, which drops all triggers
- Bug search triggers (bugs_ai, bugs_au, bugs_ad) were lost
- Result: 1279 bugs in database but 0 indexed for search

This migration:
1. Recreates the three bug triggers (INSERT, UPDATE, DELETE)
2. Backfills all existing bugs into search_index
3. Ensures future bug operations are automatically indexed

Revision ID: 8699d94758fb
Revises: a7dff4777ffb
Create Date: 2025-12-03 15:04:12.157486

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8699d94758fb"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "a7dff4777ffb"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Restore bug triggers and backfill search index."""

    # 1. Recreate INSERT trigger (from ec0a2f912117:181-196)
    op.execute("""
        CREATE TRIGGER bugs_ai AFTER INSERT ON bugs BEGIN
            INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
            SELECT
                'bug',
                NEW.id,
                tests.product_id,
                NEW.reported_at,
                NEW.title,
                NEW.title || ' ' ||
                COALESCE(NEW.steps, '') || ' ' ||
                COALESCE(NEW.actual_result, '') || ' ' ||
                COALESCE(NEW.expected_result, '')
            FROM tests
            WHERE tests.id = NEW.test_id;
        END
    """)

    # 2. Recreate UPDATE trigger (from ec0a2f912117:198-210)
    op.execute("""
        CREATE TRIGGER bugs_au AFTER UPDATE ON bugs BEGIN
            UPDATE search_index
            SET
                timestamp = NEW.reported_at,
                title = NEW.title,
                content = NEW.title || ' ' ||
                          COALESCE(NEW.steps, '') || ' ' ||
                          COALESCE(NEW.actual_result, '') || ' ' ||
                          COALESCE(NEW.expected_result, '')
            WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)

    # 3. Recreate DELETE trigger (from ec0a2f912117:212-217)
    op.execute("""
        CREATE TRIGGER bugs_ad AFTER DELETE ON bugs BEGIN
            DELETE FROM search_index
            WHERE entity_type = 'bug' AND entity_id = OLD.id;
        END
    """)

    # 4. Backfill existing bugs into search_index (from ec0a2f912117:266-280)
    # Clear any stale bug entries first (defensive - there should be 0)
    op.execute("DELETE FROM search_index WHERE entity_type = 'bug'")

    # Insert all bugs with proper JOIN to get product_id
    op.execute("""
        INSERT INTO search_index(entity_type, entity_id, product_id, timestamp, title, content)
        SELECT
            'bug',
            bugs.id,
            tests.product_id,
            bugs.reported_at,
            bugs.title,
            bugs.title || ' ' ||
            COALESCE(bugs.steps, '') || ' ' ||
            COALESCE(bugs.actual_result, '') || ' ' ||
            COALESCE(bugs.expected_result, '')
        FROM bugs
        JOIN tests ON tests.id = bugs.test_id
    """)


def downgrade() -> None:
    """Remove bug triggers and search index entries.

    NOTE: This downgrade is destructive - it removes bug search capability.
    Only use if you need to revert to pre-trigger state.
    """
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS bugs_ad")
    op.execute("DROP TRIGGER IF EXISTS bugs_au")
    op.execute("DROP TRIGGER IF EXISTS bugs_ai")

    # Remove bug entries from search index
    op.execute("DELETE FROM search_index WHERE entity_type = 'bug'")
