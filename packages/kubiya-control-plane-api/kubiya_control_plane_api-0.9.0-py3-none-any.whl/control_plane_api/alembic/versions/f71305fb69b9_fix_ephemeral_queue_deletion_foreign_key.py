"""fix_ephemeral_queue_deletion_foreign_key

Revision ID: f71305fb69b9
Revises: a7f8e9d1c2b3
Create Date: 2025-12-16 16:32:31.331980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f71305fb69b9'
down_revision: Union[str, Sequence[str], None] = 'a7f8e9d1c2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix foreign key constraint on executions.worker_queue_id to allow ephemeral queue deletion.

    When an ephemeral worker queue is deleted, we want to preserve execution history
    but set the worker_queue_id to NULL since the queue no longer exists.
    """
    # Drop the existing foreign key constraint (if it exists)
    op.drop_constraint('executions_worker_queue_id_fkey', 'executions', type_='foreignkey')

    # Recreate with ON DELETE SET NULL instead of blocking deletion
    op.create_foreign_key(
        'executions_worker_queue_id_fkey',
        'executions',
        'worker_queues',
        ['worker_queue_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new constraint
    op.drop_constraint('executions_worker_queue_id_fkey', 'executions', type_='foreignkey')

    # Recreate without ON DELETE (default behavior - blocking)
    op.create_foreign_key(
        'executions_worker_queue_id_fkey',
        'executions',
        'worker_queues',
        ['worker_queue_id'],
        ['id']
    )
