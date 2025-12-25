"""adding feedback enum

Revision ID: ed91cdf82ef3
Revises: df5b1cdc2c36
Create Date: 2025-11-17 17:16:40.643991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed91cdf82ef3'
down_revision: Union[str, Sequence[str], None] = 'df5b1cdc2c36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add FEEDBACK to existing Postgres enum `conversationtype`
    op.execute("ALTER TYPE conversationtype ADD VALUE IF NOT EXISTS 'FEEDBACK';")


def downgrade() -> None:
    # Removing an enum value is non-trivial; usually we leave this as a no-op.
    # If you really need to support downgrade, you'll have to recreate the type.
    pass
