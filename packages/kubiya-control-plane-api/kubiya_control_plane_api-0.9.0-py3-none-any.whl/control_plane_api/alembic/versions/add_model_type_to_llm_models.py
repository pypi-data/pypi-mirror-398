"""add model_type column to llm_models

Revision ID: add_model_type_to_llm_models
Revises: f25de6ad895a
Create Date: 2025-01-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_model_type_to_llm_models'
down_revision = 'f25de6ad895a'
branch_labels = None
depends_on = None


def upgrade():
    # Add model_type column with default value 'text-generation'
    op.add_column('llm_models', sa.Column('model_type', sa.String(), nullable=False, server_default='text-generation'))

    # Create index on model_type for efficient filtering
    op.create_index(op.f('ix_llm_models_model_type'), 'llm_models', ['model_type'], unique=False)


def downgrade():
    # Remove index
    op.drop_index(op.f('ix_llm_models_model_type'), table_name='llm_models')

    # Remove column
    op.drop_column('llm_models', 'model_type')
