"""Drop bugs.created_at and bugs.acceptance_state columns

Revision ID: 5dd89f70b926
Revises: 4d6ca3b1f08b
Create Date: 2025-11-28 12:26:48.011886

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5dd89f70b926"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "4d6ca3b1f08b"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop bugs.created_at and bugs.acceptance_state columns (never populated by API)."""
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("acceptance_state")


def downgrade() -> None:
    """Re-add bugs.created_at and bugs.acceptance_state columns for rollback."""
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column("acceptance_state", sa.VARCHAR(), nullable=True))
