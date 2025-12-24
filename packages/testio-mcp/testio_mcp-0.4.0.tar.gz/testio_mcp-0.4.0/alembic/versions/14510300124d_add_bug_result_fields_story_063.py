"""Add bug result fields (STORY-063)

Denormalize actual_result and expected_result from raw_data JSON to proper columns
for FTS5 indexing in STORY-064.

Revision ID: 14510300124d
Revises: 4d6ca3b1f08b
Create Date: 2025-11-29 12:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "14510300124d"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "5dd89f70b926"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Add actual_result and expected_result columns to bugs table and backfill from JSON.
    """
    # Add two nullable TEXT columns for bug result fields
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("actual_result", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("expected_result", sa.TEXT(), nullable=True))

    # Backfill from raw_data JSON with whitespace trimming
    # Transformation rule: trim whitespace; if empty or missing, set to NULL
    op.execute("""
        UPDATE bugs
        SET
            actual_result = CASE
                WHEN trim(json_extract(raw_data, '$.actual_result')) = '' THEN NULL
                ELSE trim(json_extract(raw_data, '$.actual_result'))
            END,
            expected_result = CASE
                WHEN trim(json_extract(raw_data, '$.expected_result')) = '' THEN NULL
                ELSE trim(json_extract(raw_data, '$.expected_result'))
            END
        WHERE json_valid(raw_data)
    """)


def downgrade() -> None:
    """Downgrade schema.

    Note: Data loss on downgrade (extracted columns discarded).
    """
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.drop_column("expected_result")
        batch_op.drop_column("actual_result")
