"""Fix reported_at format consistency

Re-backfill reported_at to match synced_at format (ISO 8601 with microseconds).
Previous migration used datetime() which stripped microseconds.

Revision ID: 061ba7016275
Revises: 7cd7afb62a6a
Create Date: 2025-11-29 13:24:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "061ba7016275"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "7cd7afb62a6a"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Re-backfill reported_at with full ISO 8601 format to match synced_at format.
    SQLite's datetime() function strips microseconds, but we want consistency.
    """
    # Re-backfill reported_at preserving full ISO 8601 format
    # Store as-is and let SQLAlchemy/Python handle the conversion
    op.execute("""
        UPDATE bugs
        SET reported_at = json_extract(raw_data, '$.reported_at')
        WHERE json_valid(raw_data)
          AND json_extract(raw_data, '$.reported_at') IS NOT NULL
    """)


def downgrade() -> None:
    """Downgrade schema.

    Revert to datetime() format (loses microseconds but acceptable for downgrade).
    """
    op.execute("""
        UPDATE bugs
        SET reported_at = datetime(json_extract(raw_data, '$.reported_at'))
        WHERE json_valid(raw_data)
          AND json_extract(raw_data, '$.reported_at') IS NOT NULL
    """)
