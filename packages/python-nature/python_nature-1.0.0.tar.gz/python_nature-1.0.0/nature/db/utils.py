"""SQLAlchemy utility functions for nature persistence layer."""
from datetime import datetime
from uuid import UUID, uuid4

import pytz
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import mapped_column


def uuid_pk():
    """Primary key UUID column with auto-generation."""
    return mapped_column(Uuid, default=uuid4, primary_key=True)


def fk(table: str, column: str = "id", schema: str | None = None, **kwargs):
    """Foreign key helper with optional schema support.

    Args:
        table: Target table name
        column: Target column name (default: "id")
        schema: Optional schema name
        **kwargs: Additional ForeignKey arguments

    Returns:
        ForeignKey constraint

    Examples:
        # Simple foreign key
        fk("users")  # References users.id

        # With custom column
        fk("posts", "post_id")  # References posts.post_id

        # With schema
        fk("users", schema="my_schema")  # References my_schema.users.id
    """
    ref = f"{schema}.{table}.{column}" if schema else f"{table}.{column}"
    return ForeignKey(ref, **kwargs)


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(pytz.utc)
