"""mark_local_exec_queues_as_ephemeral

Marks all existing worker queues with names starting with 'local-exec' as ephemeral.
These queues are temporary execution queues and should not appear in the UI or API responses.

Revision ID: a7f8e9d1c2b3
Revises: d181a3b40e71
Create Date: 2025-12-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f8e9d1c2b3'
down_revision: Union[str, Sequence[str], None] = 'd181a3b40e71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Mark all worker queues starting with 'local-exec' as ephemeral.

    This ensures that temporary local execution queues are properly flagged
    and excluded from API responses and UI displays.
    """
    # Update all existing queues that start with 'local-exec'
    op.execute(
        """
        UPDATE worker_queues
        SET ephemeral = true
        WHERE name LIKE 'local-exec%'
          AND ephemeral = false
        """
    )

    # Log the migration for debugging
    op.execute(
        """
        SELECT
            COUNT(*) as updated_count
        FROM worker_queues
        WHERE name LIKE 'local-exec%'
          AND ephemeral = true
        """
    )


def downgrade() -> None:
    """
    Revert the ephemeral flag for 'local-exec' queues.

    Note: This will mark them as non-ephemeral, but may not be desirable
    as these queues are by nature temporary. Consider carefully before downgrading.
    """
    # Revert the ephemeral flag for local-exec queues
    op.execute(
        """
        UPDATE worker_queues
        SET ephemeral = false
        WHERE name LIKE 'local-exec%'
          AND ephemeral = true
        """
    )
