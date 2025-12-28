"""
API Package

Provides REST API endpoints for the molecule discovery application.

Modules:
    - runs: Run management endpoints (CRUD operations)

Routers:
    - runs.router: Run management API router

Usage:
    ```python
    from fastapi import FastAPI
    from app.api import runs_router
    
    app = FastAPI()
    
    # Register API routers
    app.include_router(
        runs_router,
        prefix="/api/v1/runs",
        tags=["runs"]
    )
    ```

Endpoints Overview:
    
    Run Management:
        POST   /api/v1/runs              - Create new run
        GET    /api/v1/runs              - List all runs (with filtering)
        GET    /api/v1/runs/{run_id}     - Get run details
"""

# Import routers
from .runs import router as runs_router

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Routers
    "runs_router",
    
    # Version
    "__version__",
]