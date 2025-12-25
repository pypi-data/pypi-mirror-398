"""Base model classes for Sonnerrise entities.

Provides common base classes and mixins for all database models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from sonnerrise_core.database.base import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base model with common fields.

    All Sonnerrise entities should inherit from this class.
    Provides:
    - Auto-incrementing integer primary key
    - Created/updated timestamps
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


def import_all_models() -> None:
    """Import all Sonnerrise models to register them with SQLAlchemy metadata.

    This function should be called before create_tables() when testing
    to ensure all models (and their foreign key relationships) are
    properly registered.

    Models from packages that aren't installed will be silently skipped.
    """
    # Import models from each package to register them with Base.metadata
    # Use try/except to handle cases where packages aren't installed

    try:
        from sonnerrise_personas.models import Persona  # noqa: F401
    except ImportError:
        pass

    try:
        from sonnerrise_definitions.models import Definition, DefinitionLink  # noqa: F401
    except ImportError:
        pass

    try:
        from sonnerrise_tracks.models import Track, TrackEvent, TrackLink  # noqa: F401
    except ImportError:
        pass

    try:
        from sonnerrise_promo.models import Promo, PromoLink  # noqa: F401
    except ImportError:
        pass

    try:
        from sonnerrise_calendar.models import CalendarEvent  # noqa: F401
    except ImportError:
        pass
