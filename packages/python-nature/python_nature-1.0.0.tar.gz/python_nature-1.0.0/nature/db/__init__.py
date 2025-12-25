"""Nature database persistence layer.

This module provides a generic SQLAlchemy-based persistence layer for
storing and retrieving evolved Species instances.

Quick Start:
    from nature.db import init_sessions, sync_session, SpeciesState

    # 1. Initialize session factories (once at startup)
    init_sessions(
        db_url="postgresql+psycopg2://user:pass@localhost/nature",
        async_db_url="postgresql+asyncpg://user:pass@localhost/nature"  # optional
    )

    # 2. Save a species
    with sync_session() as db:
        species_id = SpeciesState.save(my_species, db, tags=["experiment1"])

    # 3. Fetch it back
    species = SpeciesState.fetch_by_id(species_id)

Core Components:
    - NatureBase: Declarative base class for all entities
    - SpeciesState: Entity for storing pickled Species with metadata
    - PickleEntity: Generic entity for pickle storage
    - init_sessions: Initialize database session factories
    - sync_session: Context manager for sync database sessions
    - async_session: Context manager for async database sessions
    - Helper functions: uuid_pk, fk, utc_now
"""

from nature.db.base import NatureBase
from nature.db.models import SpeciesState
from nature.db.pickle_entity import PickleEntity
from nature.db.session import async_session, init_sessions, sync_session
from nature.db.utils import fk, utc_now, uuid_pk

__all__ = [
    # Base classes
    "NatureBase",
    "SpeciesState",
    "PickleEntity",
    # Session management
    "init_sessions",
    "sync_session",
    "async_session",
    # Utilities
    "uuid_pk",
    "fk",
    "utc_now",
]
