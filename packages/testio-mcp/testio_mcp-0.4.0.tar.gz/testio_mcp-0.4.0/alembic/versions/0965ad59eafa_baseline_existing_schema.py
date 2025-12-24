"""Baseline: Complete schema (frozen 2025-11-24)

Revision ID: 0965ad59eafa
Revises:
Create Date: 2025-11-22 21:32:29.435259

FROZEN DDL - Do not modify after creation (STORY-039, ADR-016).
New schema changes must be added as new migrations using:
    alembic revision --autogenerate -m "Add field X"

This baseline creates explicit DDL capturing the schema as of 2025-11-24.
The schema includes:
- products: Product information with customer isolation
- tests: Exploratory test data with user fields (created_by, submitted_by, FKs)
- bugs: Bug reports with user field (reported_by_user_id FK)
- users: Customer and tester users with multi-tenant isolation (customer_id)
- features: Product features with embedded user stories
- sync_events: Sync operation tracking for observability
- sync_metadata: Key-value metadata storage

All tables include proper indexes and foreign key constraints.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0965ad59eafa"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables with explicit DDL (frozen schema).

    IMPORTANT: Do not modify this function. If you need to change the schema,
    create a new migration using `alembic revision --autogenerate -m "description"`.
    """
    # Products table
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("last_synced", sa.DateTime(), nullable=True),
        sa.Column("features_synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_customer_id", "products", ["customer_id"])

    # Sync events table
    op.create_table(
        "sync_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("started_at", sa.String(), nullable=False),
        sa.Column("completed_at", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("products_synced", sa.Integer(), nullable=True),
        sa.Column("tests_discovered", sa.Integer(), nullable=True),
        sa.Column("tests_refreshed", sa.Integer(), nullable=True),
        sa.Column("features_refreshed", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("trigger_source", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_events_status", "sync_events", ["status"])
    op.create_index("ix_sync_events_started_at", "sync_events", ["started_at"])

    # Sync metadata table
    op.create_table(
        "sync_metadata",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("user_type", sa.String(50), nullable=False),
        sa.Column("raw_data", sa.String(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_customer_id", "users", ["customer_id"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_user_type", "users", ["user_type"])

    # Features table (depends on products)
    op.create_table(
        "features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("howtofind", sa.String(), nullable=True),
        sa.Column("user_stories", sa.String(), nullable=False),
        sa.Column("section_ids", sa.String(), nullable=False),
        sa.Column("raw_data", sa.String(), nullable=False),
        sa.Column("last_synced", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_features_product_id", "features", ["product_id"])

    # Tests table (depends on users)
    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("bugs_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("submitted_by", sa.String(255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_tests_customer_id", "tests", ["customer_id"])
    op.create_index("ix_tests_product_id", "tests", ["product_id"])
    op.create_index("ix_tests_status", "tests", ["status"])
    op.create_index("ix_tests_created_at", "tests", ["created_at"])
    op.create_index("ix_tests_start_at", "tests", ["start_at"])
    op.create_index("ix_tests_end_at", "tests", ["end_at"])
    op.create_index("ix_tests_created_by", "tests", ["created_by"])
    op.create_index("ix_tests_submitted_by", "tests", ["submitted_by"])
    op.create_index("ix_tests_created_by_user_id", "tests", ["created_by_user_id"])
    op.create_index("ix_tests_submitted_by_user_id", "tests", ["submitted_by_user_id"])

    # Bugs table (depends on tests, users)
    op.create_table(
        "bugs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("acceptance_state", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("raw_data", sa.String(), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("reported_by_user_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.ForeignKeyConstraint(["reported_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_bugs_customer_id", "bugs", ["customer_id"])
    op.create_index("ix_bugs_test_id", "bugs", ["test_id"])
    op.create_index("ix_bugs_reported_by_user_id", "bugs", ["reported_by_user_id"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order.

    WARNING: This will delete all data!
    Only use for testing or if you have a backup.
    """
    # Drop tables in reverse dependency order
    op.drop_table("bugs")
    op.drop_table("tests")
    op.drop_table("features")
    op.drop_table("users")
    op.drop_table("sync_metadata")
    op.drop_table("sync_events")
    op.drop_table("products")
