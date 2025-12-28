"""
Database Base Configuration

Provides the declarative base class for all ORM models.
"""

from sqlalchemy.orm import declarative_base

# Create declarative base class
# All ORM models should inherit from this base
Base = declarative_base()

# Metadata is accessible via Base.metadata
# This is used for creating/dropping tables
__all__ = ["Base"]