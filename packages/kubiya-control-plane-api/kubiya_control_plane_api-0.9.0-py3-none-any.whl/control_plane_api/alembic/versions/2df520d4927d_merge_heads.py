"""merge_heads

Revision ID: 2df520d4927d
Revises: add_model_type_to_llm_models, 91520433aafc
Create Date: 2025-12-08 14:55:51.006126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2df520d4927d'
down_revision: Union[str, Sequence[str], None] = ('add_model_type_to_llm_models', '91520433aafc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
