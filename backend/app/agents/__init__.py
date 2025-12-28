"""
Agents Package

Provides intelligent agents for molecule discovery workflow orchestration.

Modules:
    - base: Abstract base class with timing, logging, and error handling
    - planner: Creates execution plans based on objectives
    - generator: Generates candidate molecules using transformations
    - ranker: Selects top molecules with optional diversity filtering

Main Components:
    Base Classes:
        - BaseAgent: Abstract base with automatic timing/logging
        - AgentError: Base exception class
        - AgentExecutionError: Execution failure exception
        - AgentValidationError: Input validation exception
    
    Agent Classes:
        - PlannerAgent: Creates execution plans
        - GeneratorAgent: Generates molecule candidates
        - RankerAgent: Ranks and selects molecules

Workflow:
    1. PlannerAgent analyzes objectives and creates execution plan
    2. GeneratorAgent creates molecule candidates each round
    3. RankerAgent selects top candidates for next round
    
Usage:
    ```python
    from app.agents import PlannerAgent, GeneratorAgent, RankerAgent
    
    # Create agents
    planner = PlannerAgent()
    generator = GeneratorAgent()
    ranker = RankerAgent()
    
    # Execute workflow
    plan = planner.execute({
        "objective": "Generate drug-like molecules",
        "seed_smiles": ["CCO"],
        "constraints": {"max_violations": 1}
    })
    
    candidates = generator.execute({
        "seed_smiles": ["CCO"],
        "candidates_count": 100,
        "round_number": 1
    })
    
    top_molecules = ranker.execute({
        "molecules": candidates["output"]["candidates"],
        "top_k": 10
    })
    ```
"""

# Import base classes and exceptions
from .base import (
    AgentError,
    AgentExecutionError,
    AgentValidationError,
    BaseAgent,
)

# Import agent implementations
from .planner import PlannerAgent
from .generator import GeneratorAgent
from .ranker import RankerAgent

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Base classes
    "BaseAgent",
    
    # Exceptions
    "AgentError",
    "AgentExecutionError",
    "AgentValidationError",
    
    # Agent implementations
    "PlannerAgent",
    "GeneratorAgent",
    "RankerAgent",
    
    # Version
    "__version__",
]