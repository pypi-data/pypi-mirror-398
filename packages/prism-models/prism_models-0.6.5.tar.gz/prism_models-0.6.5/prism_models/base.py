from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, func
from sqlalchemy.orm import Mapped, declarative_base, declared_attr, mapped_column

# PostgreSQL naming convention for consistent constraint names
POSTGRES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """
    Mixin for automatic timestamp fields using database-level defaults.
    """

    # Use server_default to make the database the single source of truth.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to a model.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self):
        """Mark the object as deleted."""
        if self.deleted_at is None:
            self.deleted_at = datetime.now(UTC)

    def undelete(self):
        """Mark the object as not deleted."""
        self.deleted_at = None


class ChatSchemaMixin:
    pass


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model with common fields for all entities."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    @declared_attr.directive
    def __tablename__(cls):
        """Auto-generate table name from class name in snake_case (singular)."""
        import re

        # Convert CamelCase to snake_case
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def __repr__(self):
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(id={self.id})>"
