"""rename_metadata_to_additional_data

Revision ID: f2013b08daac
Revises: 3219fec0bb10
Create Date: 2025-09-16 16:27:07.722003

"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2013b08daac"
down_revision: str | Sequence[str] | None = "3219fec0bb10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename metadata columns to additional_data
    op.alter_column("source", "metadata", new_column_name="additional_data")
    op.alter_column("collection", "metadata", new_column_name="additional_data")
    op.alter_column("document", "metadata", new_column_name="additional_data")
    op.alter_column("chunk_config", "metadata", new_column_name="additional_data")
    op.alter_column("vector", "metadata", new_column_name="additional_data")


def downgrade() -> None:
    """Downgrade schema."""
    # Rename additional_data columns back to metadata
    op.alter_column("source", "additional_data", new_column_name="metadata")
    op.alter_column("collection", "additional_data", new_column_name="metadata")
    op.alter_column("document", "additional_data", new_column_name="metadata")
    op.alter_column("chunk_config", "additional_data", new_column_name="metadata")
    op.alter_column("vector", "additional_data", new_column_name="metadata")
