"""
SQLAlchemy declarative base.
All ORM models import and inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all entity models."""
    pass
