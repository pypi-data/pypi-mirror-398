"""add test_features table and bug test_feature_id

Revision ID: 02bc5b2abef8
Revises: 0965ad59eafa
Create Date: 2025-11-25 10:29:05.974896

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "02bc5b2abef8"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "0965ad59eafa"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: Add test_features table and Bug.test_feature_id FK."""
    # AC1: Create test_features table
    op.create_table(
        "test_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("feature_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("howtofind", sa.String(), nullable=True),
        sa.Column("user_stories", sa.String(), nullable=False, server_default="[]"),
        sa.Column("enable_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("enable_content", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("enable_visual", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["test_id"],
            ["tests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["feature_id"],
            ["features.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # AC2: Create indices on test_features table
    op.create_index("ix_test_features_customer_id", "test_features", ["customer_id"])
    op.create_index("ix_test_features_test_id", "test_features", ["test_id"])
    op.create_index("ix_test_features_feature_id", "test_features", ["feature_id"])

    # Note: ix_tests_end_at and ix_tests_created_at already exist in baseline migration

    # AC3: Add test_feature_id column to bugs table (SQLite batch mode)
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("test_feature_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_bugs_test_feature_id", "test_features", ["test_feature_id"], ["id"]
        )
        batch_op.create_index("ix_bugs_test_feature_id", ["test_feature_id"])


def downgrade() -> None:
    """Downgrade schema: Remove test_features table and Bug.test_feature_id."""
    # Drop bugs.test_feature_id (reverse AC3)
    with op.batch_alter_table("bugs", schema=None) as batch_op:
        batch_op.drop_index("ix_bugs_test_feature_id")
        batch_op.drop_constraint("fk_bugs_test_feature_id", type_="foreignkey")
        batch_op.drop_column("test_feature_id")

    # Note: ix_tests_end_at and ix_tests_created_at not dropped (exist in baseline migration)

    # Drop test_features table (reverse AC1, cascades to indices)
    op.drop_index("ix_test_features_feature_id", table_name="test_features")
    op.drop_index("ix_test_features_test_id", table_name="test_features")
    op.drop_index("ix_test_features_customer_id", table_name="test_features")
    op.drop_table("test_features")
