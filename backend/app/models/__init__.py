"""
Pydantic Models Package

Provides request/response schemas for the molecule discovery API.

Modules:
    - molecule: Molecule and trace response schemas
    - run: Run request and response schemas

Main Components:
    Request Models:
        - RunCreate: Create new run request
        - RunConfig: Run configuration schema
    
    Response Models:
        - RunResponse: Complete run information
        - RunStatusResponse: Run status and progress
        - MoleculeResponse: Molecule data with properties
        - TraceResponse: Agent activity trace
        - TaskResponse: Task creation response
    
    Supporting Models:
        - MoleculeProperties: Molecular property values
        - RunProgress: Progress statistics
        - RunStatus: Run status enum

Usage:
    ```python
    from app.models import RunCreate, RunResponse, MoleculeResponse
    
    # Create run request
    run_data = RunCreate(config=RunConfig(...))
    
    # Response models
    run_response = RunResponse.model_validate(run_orm)
    molecule_response = MoleculeResponse.from_orm_molecule(mol_orm)
    ```
"""

# Import molecule-related models
from .molecule import (
    MoleculeProperties,
    MoleculeResponse,
    RunProgress,
    RunStatusResponse,
    TaskResponse,
    TraceResponse,
)

# Import run-related models
from .run import (
    RunConfig,
    RunCreate,
    RunResponse,
    RunStatus,
)

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Request models
    "RunCreate",
    "RunConfig",
    
    # Response models
    "RunResponse",
    "RunStatusResponse",
    "MoleculeResponse",
    "TraceResponse",
    "TaskResponse",
    
    # Supporting models
    "MoleculeProperties",
    "RunProgress",
    
    # Enums
    "RunStatus",
    
    # Version
    "__version__",
]