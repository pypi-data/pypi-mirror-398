"""Normalize key fields (STORY-054)

Extract frequently-queried fields from JSON to proper columns:
- products.product_type (for filtering)
- tests.title (for sorting/display)
- tests.testing_type (for filtering)
- tests.goal, instructions, out_of_scope (rich text fields)
- tests.enable_low, enable_high, enable_critical (configuration flags)
- Drop tests.created_at (unused/null)

Revision ID: 4d6ca3b1f08b
Revises: c322bcc06196
Create Date: 2025-11-28 01:31:15.046999

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d6ca3b1f08b"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "c322bcc06196"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Part A: Add product_type to products
    Part B: Add title, testing_type, and rich fields to tests
    Part C: Drop tests.created_at (unused)
    """
    # Part A: products.product_type
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("product_type", sa.VARCHAR(length=50), nullable=True))
        batch_op.create_index("ix_products_product_type", ["product_type"])

    # Backfill product_type from JSON
    op.execute("""
        UPDATE products
        SET product_type = json_extract(data, '$.type')
        WHERE json_valid(data)
    """)

    # Part B: tests table - add new columns
    with op.batch_alter_table("tests", schema=None) as batch_op:
        # Display/sorting fields
        batch_op.add_column(sa.Column("title", sa.VARCHAR(length=500), nullable=True))
        batch_op.add_column(sa.Column("testing_type", sa.VARCHAR(length=50), nullable=True))

        # Rich text fields
        batch_op.add_column(sa.Column("goal", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("instructions", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("out_of_scope", sa.TEXT(), nullable=True))

        # Configuration flags (boolean)
        batch_op.add_column(sa.Column("enable_low", sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column("enable_high", sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column("enable_critical", sa.BOOLEAN(), nullable=True))

        # Create indices for querying/sorting
        batch_op.create_index("ix_tests_title", ["title"])
        batch_op.create_index("ix_tests_testing_type", ["testing_type"])

    # Backfill tests fields from JSON
    op.execute("""
        UPDATE tests
        SET
            title = json_extract(data, '$.title'),
            testing_type = json_extract(data, '$.testing_type'),
            goal = json_extract(data, '$.goal_text'),
            instructions = json_extract(data, '$.instructions_text'),
            out_of_scope = json_extract(data, '$.out_of_scope_text'),
            enable_low = json_extract(data, '$.enable_low'),
            enable_high = json_extract(data, '$.enable_high'),
            enable_critical = json_extract(data, '$.enable_critical')
        WHERE json_valid(data)
    """)

    # Part C: Drop tests.created_at (unused, always NULL)
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.drop_index("ix_tests_created_at")
        batch_op.drop_column("created_at")


def downgrade() -> None:
    """Downgrade schema.

    Note: Data loss on downgrade (extracted columns discarded).
    """
    # Restore tests.created_at
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DATETIME(), nullable=True))
        batch_op.create_index("ix_tests_created_at", ["created_at"])

    # Drop tests columns
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.drop_index("ix_tests_testing_type")
        batch_op.drop_index("ix_tests_title")
        batch_op.drop_column("enable_critical")
        batch_op.drop_column("enable_high")
        batch_op.drop_column("enable_low")
        batch_op.drop_column("out_of_scope")
        batch_op.drop_column("instructions")
        batch_op.drop_column("goal")
        batch_op.drop_column("testing_type")
        batch_op.drop_column("title")

    # Drop products.product_type
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_index("ix_products_product_type")
        batch_op.drop_column("product_type")
