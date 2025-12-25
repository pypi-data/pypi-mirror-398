"""Base SQLAlchemy entities for nature package."""

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class NatureBase(AsyncAttrs, DeclarativeBase):
    """Base class for all nature database entities.

    Provides async support and common utility methods.

    Can be used directly or subclassed to add schema support:
        class MyBase(NatureBase):
            __table_args__ = {"schema": "my_schema"}

    Example:
        from nature.db.base import NatureBase
        from nature.db.utils import uuid_pk
        from sqlalchemy.orm import Mapped
        from uuid import UUID

        class MyModel(NatureBase):
            __tablename__ = "my_table"

            id: Mapped[UUID] = uuid_pk()
            name: Mapped[str]
    """

    def to_dict(self) -> dict:
        """Convert model instance to dictionary of column values.

        Only includes actual column attributes, ignoring relationships
        and other SQLAlchemy internals.

        Returns:
            Dictionary mapping column names to their values

        Example:
            user = User(id=uuid4(), name="Alice")
            user_dict = user.to_dict()
            # {'id': UUID('...'), 'name': 'Alice'}
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
