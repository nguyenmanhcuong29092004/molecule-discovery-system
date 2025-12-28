"""
Database Package

Provides database configuration, ORM models, and session management
for the molecule discovery application.

Modules:
    - session: Async database session and engine configuration
    - models: SQLAlchemy ORM models (Run, Molecule, Trace)
    - base: Base class for all models

Main Components:
    - Database Models: Run, Molecule, Trace
    - Session Management: get_db, AsyncSessionLocal, engine
    - Database Utilities: init_db, drop_db

Usage:
    ```python
    from app.db import get_db, Run, Molecule, Trace
    
    # Get database session
    async with get_db() as session:
        result = await session.execute(select(Run))
    
    # Initialize database
    from app.db import init_db
    await init_db()
    ```
"""

# Import database session components
from .session import (
    AsyncSessionLocal,
    DATABASE_URL,
    engine,
    get_db,
    init_db,
    drop_db,
)

# Import ORM models
from .models import (
    Run,
    Molecule,
    Trace,
)

# Import base class
from .base import Base

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Session management
    "get_db",
    "AsyncSessionLocal",
    "engine",
    "DATABASE_URL",
    
    # Database utilities
    "init_db",
    "drop_db",
    
    # ORM Models
    "Run",
    "Molecule",
    "Trace",
    
    # Base class
    "Base",
    
    # Version
    "__version__",
]