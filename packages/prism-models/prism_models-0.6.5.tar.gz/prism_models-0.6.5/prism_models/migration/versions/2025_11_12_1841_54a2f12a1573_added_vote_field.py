"""added vote field

Revision ID: 54a2f12a1573
Revises: 8c3c862b565e
Create Date: 2025-11-12 18:41:53.839421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision: str = '54a2f12a1573'
down_revision: Union[str, Sequence[str], None] = '8c3c862b565e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

messagevote_enum = postgresql.ENUM('UPVOTE', 'DOWNVOTE', name='messagevote')


def upgrade() -> None:
    """Upgrade schema."""
    # 1️⃣ Create the enum type first
    messagevote_enum.create(op.get_bind())

    # 2️⃣ Then add the column using that enum
    op.add_column(
        'conversation_message',
        sa.Column('vote', messagevote_enum, nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop column first
    op.drop_column('conversation_message', 'vote')

    # Drop enum type
    messagevote_enum.drop(op.get_bind())