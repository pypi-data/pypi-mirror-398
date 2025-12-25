"""rename_custom_metadata_to_metadata_in_execution_tool_calls

Revision ID: d181a3b40e71
Revises: e9f2a3b4c5d6
Create Date: 2025-12-11 10:28:12.517595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd181a3b40e71'
down_revision: Union[str, Sequence[str], None] = 'e9f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename custom_metadata column to metadata in execution_tool_calls table (if it exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='execution_tool_calls' AND column_name='custom_metadata'
            ) THEN
                ALTER TABLE execution_tool_calls RENAME COLUMN custom_metadata TO metadata;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Rename metadata column back to custom_metadata in execution_tool_calls table (if it exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='execution_tool_calls' AND column_name='metadata'
            ) THEN
                ALTER TABLE execution_tool_calls RENAME COLUMN metadata TO custom_metadata;
            END IF;
        END $$;
    """)
