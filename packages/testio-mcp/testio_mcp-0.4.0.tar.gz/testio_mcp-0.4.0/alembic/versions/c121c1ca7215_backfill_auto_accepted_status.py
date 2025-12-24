"""backfill_auto_accepted_status

STORY-047: Normalize Bug Auto-Accepted Status

This data migration updates existing bugs in the database to use the enriched
status value "auto_accepted" instead of relying on the auto_accepted JSON field.

Backfill Logic:
    UPDATE bugs
    SET status = 'auto_accepted'
    WHERE status = 'accepted'
      AND json_extract(raw_data, '$.auto_accepted') = 1;

This is idempotent - safe to run multiple times:
- Only affects bugs with status='accepted' AND auto_accepted=true in raw_data
- Bugs already with status='auto_accepted' are not modified
- No data loss - raw_data JSON preserves original API response

Expected Results (based on data analysis):
    Before: 5,695 accepted (mixed), 0 auto_accepted
    After:  ~4,117 accepted, ~1,578 auto_accepted
    Total remains same (no data loss)

Revision ID: c121c1ca7215
Revises: 24c44c502fc0
Create Date: 2025-11-26 14:23:43.212447

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c121c1ca7215"
down_revision: str | Sequence[str] | None = "24c44c502fc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill status='auto_accepted' for bugs with auto_accepted=true in raw_data.

    Uses SQLite's json_extract() to check the auto_accepted field in the raw_data
    JSON column. Only bugs with status='accepted' AND auto_accepted=true are updated.

    This is a data-only migration (no schema changes).
    """
    # SQLite json_extract returns 1 for true, 0 for false, NULL for missing
    op.execute(
        """
        UPDATE bugs
        SET status = 'auto_accepted'
        WHERE status = 'accepted'
          AND json_extract(raw_data, '$.auto_accepted') = 1
        """
    )


def downgrade() -> None:
    """Revert auto_accepted status back to accepted.

    This restores the original status='accepted' for all bugs that were
    marked as 'auto_accepted'. The auto_accepted flag in raw_data is preserved.
    """
    op.execute(
        """
        UPDATE bugs
        SET status = 'accepted'
        WHERE status = 'auto_accepted'
        """
    )
