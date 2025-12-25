"""a

Revision ID: 91520433aafc
Revises: f25de6ad895a
Create Date: 2025-11-29 10:57:24.435772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91520433aafc'
down_revision: Union[str, Sequence[str], None] = 'f25de6ad895a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('executions_worker_queue_id_fkey'), 'executions', type_='foreignkey')
    op.create_foreign_key(None, 'executions', 'worker_queues', ['worker_queue_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_team_org_name', 'teams', ['organization_id', 'name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_team_org_name', 'teams', type_='unique')
    op.drop_constraint(None, 'executions', type_='foreignkey')
    op.create_foreign_key(op.f('executions_worker_queue_id_fkey'), 'executions', 'worker_queues', ['worker_queue_id'], ['id'])
