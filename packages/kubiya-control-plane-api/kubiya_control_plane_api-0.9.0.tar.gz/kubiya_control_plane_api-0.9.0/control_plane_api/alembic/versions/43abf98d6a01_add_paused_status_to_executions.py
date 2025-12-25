"""add_paused_status_to_executions

Adds PAUSED status to the executionstatus enum type,
enabling pause/resume functionality for executions.

Revision ID: 43abf98d6a01
Revises: 2df520d4927d
Create Date: 2025-12-08 14:55:54.974711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43abf98d6a01'
down_revision: Union[str, Sequence[str], None] = '2df520d4927d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'paused' value to executionstatus enum.

    Note: The status column in the executions table is actually String(50) in the ORM,
    but we add this to the enum type for database-level validation if it exists.
    """

    op.execute("""
        DO $$
        BEGIN
            -- Check if executionstatus enum type exists
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'executionstatus') THEN
                -- Check if 'paused' value doesn't already exist
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum
                    WHERE enumlabel = 'paused'
                    AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'executionstatus')
                ) THEN
                    ALTER TYPE executionstatus ADD VALUE 'paused';
                    RAISE NOTICE 'Added "paused" value to executionstatus enum';
                ELSE
                    RAISE NOTICE '"paused" value already exists in executionstatus enum';
                END IF;
            ELSE
                RAISE NOTICE 'executionstatus enum does not exist (column is String type) - no action needed';
            END IF;
        END $$;
    """)

    # Update type comment
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'executionstatus') THEN
                COMMENT ON TYPE executionstatus IS
                    'Execution status: pending, running, waiting_for_input, paused, completed, failed, cancelled';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Downgrade is not supported for enum value additions.

    PostgreSQL does not support removing enum values without recreating
    the type, which would require table recreation and downtime.
    """
    pass
