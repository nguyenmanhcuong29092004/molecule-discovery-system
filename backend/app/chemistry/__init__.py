"""
Chemistry Package

A comprehensive chemistry toolkit for molecular analysis and transformation.

Modules:
    - engine: Core chemistry operations (validation, properties, screening, scoring)
    - transforms: Molecular transformation operations (mutations, functional groups)

Main Classes:
    - ChemistryEngine: Core chemistry operations
    - MoleculeTransformer: Molecular transformation operations

Constants:
    - DEFAULT_CONSTRAINTS: Default Lipinski Rule of Five constraints
    - DEFAULT_PENALTY: Default scoring penalty per violation
    - ATOM_MUTATIONS: Supported atom mutation mappings
    - FUNCTIONAL_GROUPS: Available functional groups for addition
"""

# Import main classes
from .engine import ChemistryEngine
from .transforms import MoleculeTransformer

# Import constants for external use
from .engine import (
    DEFAULT_CONSTRAINTS,
    DEFAULT_PENALTY,
    MAX_SMILES_LENGTH,
    MIN_SMILES_LENGTH,
)

from .transforms import (
    ATOM_MUTATIONS,
    FUNCTIONAL_GROUPS,
)

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Classes
    "ChemistryEngine",
    "MoleculeTransformer",
    
    # Constants from engine
    "DEFAULT_CONSTRAINTS",
    "DEFAULT_PENALTY",
    "MAX_SMILES_LENGTH",
    "MIN_SMILES_LENGTH",
    
    # Constants from transforms
    "ATOM_MUTATIONS",
    "FUNCTIONAL_GROUPS",
    
    # Version
    "__version__",
]