"""Nature Species persistence models."""

from datetime import datetime
from typing import Any, Sequence, Self
from uuid import UUID

import pytz
from cachetools import LRUCache
from sqlalchemy import DateTime, Float, Text, select
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, array
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, Session, selectinload

from nature.db.base import NatureBase
from nature.db.pickle_entity import PickleEntity
from nature.db.session import async_session, sync_session
from nature.db.utils import fk, utc_now, uuid_pk
from nature.species import Species
from nature.utils import get_git_info


class SpeciesState(NatureBase):
    """Persistent storage for evolved Species instances.

    Stores pickled Species objects with metadata for querying and tracking.
    Includes caching for performance.

    Example:
        from nature.db.models import SpeciesState
        from nature.db.session import init_sessions, sync_session

        # Initialize once at startup
        init_sessions(db_url="postgresql+psycopg2://user:pass@localhost/nature")

        # Save a species
        with sync_session() as db:
            species_id = SpeciesState.save(my_species, db, tags=["experiment1"])

        # Fetch it back
        retrieved = SpeciesState.fetch_by_id(species_id)
    """

    __tablename__ = "species"

    cache = LRUCache(maxsize=100)

    id: Mapped[UUID] = uuid_pk()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )

    # Code state
    class_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    git_branch: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    git_commit: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    # Tagging for organization
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}", index=True)

    # Pickled Species object
    pickle_id: Mapped[UUID] = mapped_column(fk("pickle"), index=True, nullable=False)
    pickle = PickleEntity.create_relationship([pickle_id], cascade="all, delete")

    # Hyperparameters
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, index=True)

    # Fitness values
    fitness_values: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False, index=True)

    def unpickle(self, use_cache: bool = True) -> Species:
        """Load the pickled Species instance.

        Args:
            use_cache: Whether to use/update the LRU cache

        Returns:
            Deserialized Species instance with db_id and db_table set
        """
        if use_cache and self.id in self.cache:
            return self.cache[self.id]

        species = self.pickle.loads()
        species.db_table = self.__tablename__
        species.db_id = self.id

        if use_cache:
            self.cache[self.id] = species

        return species

    @classmethod
    def save(cls, species: Species, session: Session, tags: Sequence[str] | None = None) -> UUID:
        """Save a Species instance to the database (sync).

        Args:
            species: Species instance to persist
            session: Database session (managed by caller)
            tags: Optional tags for categorization

        Returns:
            UUID of the created SpeciesState entity

        Example:
            with sync_session() as db:
                species_id = SpeciesState.save(my_species, db, tags=["v1", "production"])
        """
        entity = cls()
        entity.class_name = species.__class__.__name__

        try:
            git_branch, git_commit = get_git_info()
            entity.git_branch = git_branch
            entity.git_commit = git_commit
        except Exception:
            # Git info is optional - may not be in a git repo
            entity.git_branch = None
            entity.git_commit = None

        entity.pickle = PickleEntity.from_object(species)
        entity.params = getattr(species, "params", None)
        entity.fitness_values = species.fitness.values
        entity.tags = list(tags or [])

        session.add(entity)
        session.flush([entity.pickle, entity])

        species.db_table = entity.__tablename__
        species.db_id = entity.id

        return entity.id

    @classmethod
    def fetch_by_id(
        cls, id: UUID, session: Session | None = None, use_cache: bool = True
    ) -> Species:
        """Fetch and unpickle a Species by ID (sync).

        Args:
            id: UUID of the SpeciesState entity
            session: Optional database session (creates new if not provided)
            use_cache: Whether to use/update the LRU cache

        Returns:
            Deserialized Species instance

        Raises:
            ValueError: If species with given ID not found

        Example:
            species = SpeciesState.fetch_by_id(species_id)
        """
        if use_cache and id in cls.cache:
            return cls.cache[id]

        with sync_session(session, autocommit=False) as db:
            entity = db.scalar(select(cls).options(selectinload(cls.pickle)).filter(cls.id == id))

            if entity is None:
                raise ValueError(f"Species {id} not found")

        species = entity.pickle.loads()
        species.db_table = entity.__tablename__
        species.db_id = entity.id

        if use_cache:
            cls.cache[id] = species

        return species

    @classmethod
    def fetch_many(
        cls, ids: Sequence[UUID], session: Session | None = None, use_cache: bool = True
    ) -> list[Species]:
        """Fetch and unpickle multiple Species by IDs (sync).

        Args:
            ids: Sequence of UUIDs to fetch
            session: Optional database session
            use_cache: Whether to use/update the LRU cache

        Returns:
            List of deserialized Species instances

        Example:
            species_list = SpeciesState.fetch_many([id1, id2, id3])
        """
        species_list = []
        missing_ids = []

        # Check cache first
        if use_cache:
            for id in ids:
                if id in cls.cache:
                    species_list.append(cls.cache[id])
                else:
                    missing_ids.append(id)
        else:
            missing_ids = list(ids)

        # Fetch missing from database
        if missing_ids:
            with sync_session(session, autocommit=False) as db:
                entities = db.scalars(
                    select(cls).options(selectinload(cls.pickle)).filter(cls.id.in_(missing_ids))
                ).all()

                for entity in entities:
                    species = entity.pickle.loads()
                    species.db_table = entity.__tablename__
                    species.db_id = entity.id

                    species_list.append(species)

                    if use_cache:
                        cls.cache[entity.id] = species

        return species_list

    @classmethod
    def fetch_by_tags(
        cls,
        tags: Sequence[str],
        limit: int = 100,
        session: Session | None = None,
    ) -> list[Species]:
        """Fetch Species instances by tags (sync).

        Args:
            tags: Tags to filter by (any match)
            limit: Maximum number of results
            session: Optional database session

        Returns:
            List of Species instances matching the tags, ordered by created_at desc

        Example:
            production_species = SpeciesState.fetch_by_tags(["production", "v2"], limit=50)
        """
        with sync_session(session, autocommit=False) as db:
            entities = db.scalars(
                select(cls)
                .options(selectinload(cls.pickle))
                .filter(cls.tags.contains(array(tags)))
                .order_by(cls.created_at.desc(), cls.id.asc())
                .limit(limit)
            ).all()

            return [entity.unpickle() for entity in entities]

    @classmethod
    async def fetch_by_id_async(cls, id: UUID, session: AsyncSession | None = None) -> Self | None:
        """Fetch SpeciesState entity by ID (async, does NOT unpickle).

        Args:
            id: UUID of the SpeciesState entity
            session: Optional async database session

        Returns:
            SpeciesState entity or None if not found

        Note:
            This returns the entity itself, not the unpickled Species.
            Use the sync fetch_by_id() method if you need the unpickled Species.

        Example:
            async with async_session() as db:
                entity = await SpeciesState.fetch_by_id_async(species_id, db)
                if entity:
                    species = entity.unpickle()
        """
        async with async_session(session, autocommit=False) as db:
            return await db.scalar(select(cls).filter(cls.id == id))
