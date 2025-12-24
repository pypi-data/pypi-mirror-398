"""Make Product.title NOT NULL

Revision ID: 24c44c502fc0
Revises: f2ddd8df0212
Create Date: 2025-11-25 12:24:12.715060

"""

from collections.abc import Sequence

import sqlmodel  # noqa: F401

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24c44c502fc0"
down_revision: str | Sequence[str] | None = "f2ddd8df0212"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - make title NOT NULL after backfill."""
    # Now that all products have titles, make NOT NULL
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column("title", nullable=False)


def downgrade() -> None:
    """Downgrade schema - make title nullable again."""
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column("title", nullable=True)
