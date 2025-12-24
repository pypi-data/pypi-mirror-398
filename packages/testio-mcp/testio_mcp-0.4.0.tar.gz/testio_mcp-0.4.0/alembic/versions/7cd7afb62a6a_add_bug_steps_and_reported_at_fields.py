"""Add bug steps and reported_at fields

Denormalize steps (reproduction steps) and reported_at (timestamp) from raw_data JSON
for FTS5 indexing and temporal filtering.

Revision ID: 7cd7afb62a6a
Revises: 14510300124d
Create Date: 2025-11-29 13:18:53.962269

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7cd7afb62a6a"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "14510300124d"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Add steps (TEXT) and reported_at (DATETIME) columns to bugs table and backfill from JSON.
    """
    # Add two columns for bug reproduction steps and report timestamp
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("steps", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("reported_at", sa.DATETIME(), nullable=True))

    # Backfill steps from raw_data JSON (array of strings → newline-separated TEXT)
    # Transformation rule: Join array elements with newlines; if empty or missing, set to NULL
    op.execute("""
        UPDATE bugs
        SET steps = (
            SELECT group_concat(value, char(10))
            FROM json_each(json_extract(raw_data, '$.steps'))
        )
        WHERE json_valid(raw_data)
          AND json_type(raw_data, '$.steps') = 'array'
    """)

    # Backfill reported_at from raw_data JSON (ISO 8601 string → DATETIME)
    # SQLite datetime() function parses ISO 8601 format automatically
    op.execute("""
        UPDATE bugs
        SET reported_at = datetime(json_extract(raw_data, '$.reported_at'))
        WHERE json_valid(raw_data)
          AND json_extract(raw_data, '$.reported_at') IS NOT NULL
    """)


def downgrade() -> None:
    """Downgrade schema.

    Note: Data loss on downgrade (extracted columns discarded).
    """
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.drop_column("reported_at")
        batch_op.drop_column("steps")
