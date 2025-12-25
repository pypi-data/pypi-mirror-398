"""add_ephemeral_queue_support

Adds ephemeral queue support for on-demand workers.
This enables automatic provisioning and cleanup of temporary worker queues.

Revision ID: e9f2a3b4c5d6
Revises: 87d11cf0a783
Create Date: 2025-12-11 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = '87d11cf0a783'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add ephemeral queue support columns to worker_queues table.

    New columns:
    - ephemeral: Mark queue as temporary/ephemeral
    - single_execution_mode: Worker processes one task then exits
    - auto_cleanup_after_seconds: TTL for automatic cleanup
    - parent_execution_id: Track the execution that created this queue
    """

    # Add ephemeral flag (default false for backward compatibility)
    op.add_column('worker_queues',
        sa.Column('ephemeral', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )

    # Add single execution mode flag (default false)
    op.add_column('worker_queues',
        sa.Column('single_execution_mode', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )

    # Add auto cleanup TTL (nullable - only set for ephemeral queues)
    op.add_column('worker_queues',
        sa.Column('auto_cleanup_after_seconds', sa.Integer(), nullable=True)
    )

    # Add parent execution ID for tracking (nullable)
    op.add_column('worker_queues',
        sa.Column('parent_execution_id', sa.Text(), nullable=True)
    )

    # Create index for efficient ephemeral queue cleanup queries
    op.create_index(
        'idx_worker_queues_ephemeral_cleanup',
        'worker_queues',
        ['ephemeral', 'created_at'],
        postgresql_where=sa.text("ephemeral = true")
    )

    # Create index for parent execution tracking
    op.create_index(
        'idx_worker_queues_parent_execution',
        'worker_queues',
        ['parent_execution_id'],
        postgresql_where=sa.text("parent_execution_id IS NOT NULL")
    )


def downgrade() -> None:
    """
    Remove ephemeral queue support columns.
    """

    # Drop indexes first
    op.drop_index('idx_worker_queues_parent_execution', table_name='worker_queues')
    op.drop_index('idx_worker_queues_ephemeral_cleanup', table_name='worker_queues')

    # Drop columns
    op.drop_column('worker_queues', 'parent_execution_id')
    op.drop_column('worker_queues', 'auto_cleanup_after_seconds')
    op.drop_column('worker_queues', 'single_execution_mode')
    op.drop_column('worker_queues', 'ephemeral')
