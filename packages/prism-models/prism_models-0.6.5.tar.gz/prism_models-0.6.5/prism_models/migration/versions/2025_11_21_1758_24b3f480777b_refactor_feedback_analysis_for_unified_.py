"""Refactor feedback analysis for unified event log

Revision ID: 24b3f480777b
Revises: e7ae98ce2121
Create Date: 2025-11-21 17:58:54.032653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24b3f480777b'
down_revision: Union[str, Sequence[str], None] = 'e7ae98ce2121'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
