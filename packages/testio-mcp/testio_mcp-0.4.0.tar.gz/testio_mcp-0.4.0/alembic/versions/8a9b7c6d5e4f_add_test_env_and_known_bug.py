"""add_test_env_and_known_bug

Revision ID: 8a9b7c6d5e4f
Revises: f63655d178ae
Create Date: 2025-11-30 19:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a9b7c6d5e4f"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "f63655d178ae"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add columns
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("test_environment", sa.JSON(), nullable=True))

    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "known",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )

    # 2. Backfill test_environment from data JSON
    # Extract {id, title} from data.test_environment if it exists
    op.execute(
        """
        UPDATE tests
        SET test_environment = json_object(
            'id', json_extract(data, '$.test_environment.id'),
            'title', json_extract(data, '$.test_environment.title')
        )
        WHERE json_extract(data, '$.test_environment') IS NOT NULL
        """
    )

    # 3. Backfill known from raw_data JSON
    # Default to 0 (False) if missing or null
    op.execute(
        """
        UPDATE bugs
        SET known = COALESCE(
            json_extract(raw_data, '$.known'),
            0
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.drop_column("known")

    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.drop_column("test_environment")
