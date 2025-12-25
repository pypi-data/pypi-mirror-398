"""Pickle storage entity for serializing Python objects."""

import pickle
from typing import Any, Self
from uuid import UUID

from sqlalchemy import Column, PickleType
from sqlalchemy.orm import Mapped, relationship

from nature.db.base import NatureBase
from nature.db.utils import uuid_pk


class PickleEntity(NatureBase):
    """Generic entity for storing pickled Python objects.

    Use this to persist Species or other complex objects that don't map
    cleanly to relational columns.

    The PickleEntity approach allows:
    - Storing arbitrary Python objects in the database
    - Full object graph serialization
    - Easy retrieval and deserialization

    Example:
        # Create and store a pickled object
        from nature.db.pickle_entity import PickleEntity
        from nature.db.session import sync_session

        my_object = {"data": [1, 2, 3], "nested": {"key": "value"}}
        pickle_entity = PickleEntity.from_object(my_object)

        with sync_session() as db:
            db.add(pickle_entity)
            db.commit()

            # Later, retrieve and deserialize
            retrieved = db.query(PickleEntity).filter_by(id=pickle_entity.id).first()
            original_object = retrieved.loads()
    """

    __tablename__ = "pickle"

    id: Mapped[UUID] = uuid_pk()
    data = Column(PickleType, nullable=False)

    @classmethod
    def from_object(cls, obj: Any) -> Self:
        """Create PickleEntity from any Python object.

        Args:
            obj: Any pickle-able Python object

        Returns:
            New PickleEntity instance with serialized object

        Example:
            species = MySpecies()
            pickle_entity = PickleEntity.from_object(species)
        """
        entity = cls()
        entity.data = pickle.dumps(obj)
        return entity

    def loads(self) -> Any:
        """Deserialize the pickled object.

        Returns:
            The original Python object

        Example:
            obj = pickle_entity.loads()
        """
        return pickle.loads(self.data)

    @classmethod
    def create_relationship(cls, foreign_keys: Any, **kwargs):
        """Helper to create SQLAlchemy relationship to PickleEntity.

        Args:
            foreign_keys: Foreign key column(s) for the relationship
            **kwargs: Additional relationship parameters

        Returns:
            SQLAlchemy relationship

        Example:
            class MyModel(NatureBase):
                __tablename__ = "my_model"

                id: Mapped[UUID] = uuid_pk()
                pickle_id: Mapped[UUID] = mapped_column(fk("pickle"))
                pickle = PickleEntity.create_relationship([pickle_id],
                                                          cascade="all, delete")
        """
        return relationship(cls.__name__, foreign_keys=foreign_keys, **kwargs)
