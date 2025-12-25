"""add_disconnected_status_to_worker_heartbeats

Revision ID: 87d11cf0a783
Revises: 43abf98d6a01
Create Date: 2025-12-08 21:37:05.347985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87d11cf0a783'
down_revision: Union[str, Sequence[str], None] = '43abf98d6a01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old constraint
    op.drop_constraint('worker_heartbeats_status_check', 'worker_heartbeats', type_='check')

    # Create the new constraint with 'disconnected' added
    op.create_check_constraint(
        'worker_heartbeats_status_check',
        'worker_heartbeats',
        "status IN ('active', 'idle', 'busy', 'offline', 'disconnected')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new constraint
    op.drop_constraint('worker_heartbeats_status_check', 'worker_heartbeats', type_='check')

    # Recreate the old constraint without 'disconnected'
    op.create_check_constraint(
        'worker_heartbeats_status_check',
        'worker_heartbeats',
        "status IN ('active', 'idle', 'busy', 'offline')"
    )
