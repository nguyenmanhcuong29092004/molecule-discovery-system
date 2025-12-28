"""
Pydantic Models for Molecule and Trace API Responses

Defines response schemas for molecule and trace endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MoleculeProperties(BaseModel):
    """Molecular properties schema."""

    mw: float = Field(description="Molecular weight (Da)")
    logp: float = Field(description="Partition coefficient")
    hbd: int = Field(description="Hydrogen bond donors")
    hba: int = Field(description="Hydrogen bond acceptors")
    tpsa: float = Field(description="Topological polar surface area")
    rotatable_bonds: int = Field(description="Number of rotatable bonds")
    qed: float = Field(description="Quantitative Estimate of Drug-likeness")


class MoleculeResponse(BaseModel):
    """Response schema for molecule data."""

    id: UUID = Field(description="Molecule ID")
    smiles: str = Field(description="SMILES string")
    smiles_canonical: str = Field(description="Canonical SMILES")
    round_number: int = Field(description="Generation round")
    properties: MoleculeProperties = Field(description="Molecular properties")
    passed_screening: bool = Field(description="Whether passed screening")
    num_violations: int = Field(description="Number of constraint violations")
    violations: List[Dict] = Field(description="List of violations")
    score: float = Field(description="Composite score")
    generation_method: str = Field(description="Generation method used")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "smiles": "CCO",
                "smiles_canonical": "CCO",
                "round_number": 1,
                "properties": {
                    "mw": 46.07,
                    "logp": -0.18,
                    "hbd": 1,
                    "hba": 1,
                    "tpsa": 20.23,
                    "rotatable_bonds": 0,
                    "qed": 0.85,
                },
                "passed_screening": True,
                "num_violations": 0,
                "violations": [],
                "score": 0.85,
                "generation_method": "hybrid",
                "created_at": "2025-12-27T10:00:00Z",
            }
        },
    }

    @classmethod
    def from_orm_molecule(cls, molecule):
        """
        Create response from ORM molecule.
        
        Args:
            molecule: ORM Molecule instance
            
        Returns:
            MoleculeResponse
        """
        return cls(
            id=molecule.id,
            smiles=molecule.smiles,
            smiles_canonical=molecule.smiles_canonical,
            round_number=molecule.round_number,
            properties=MoleculeProperties(
                mw=molecule.mw,
                logp=molecule.logp,
                hbd=molecule.hbd,
                hba=molecule.hba,
                tpsa=molecule.tpsa,
                rotatable_bonds=molecule.rotatable_bonds,
                qed=molecule.qed,
            ),
            passed_screening=molecule.passed_screening,
            num_violations=molecule.num_violations,
            violations=molecule.violations or [],
            score=molecule.score,
            generation_method=molecule.generation_method or "unknown",
            created_at=molecule.created_at,
        )


class TraceResponse(BaseModel):
    """Response schema for trace data."""

    id: UUID = Field(description="Trace ID")
    round_number: int = Field(description="Round number")
    agent_type: str = Field(description="Agent type")
    action: str = Field(description="Action performed")
    timestamp: datetime = Field(description="Action timestamp")
    duration_ms: Optional[int] = Field(
        default=None, description="Duration in milliseconds"
    )
    input_data: Dict = Field(default_factory=dict, description="Input data")
    output_data: Dict = Field(default_factory=dict, description="Output data")
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata",
        validation_alias="trace_metadata",
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "round_number": 1,
                "agent_type": "planner",
                "action": "plan_created",
                "timestamp": "2025-12-27T10:00:00Z",
                "duration_ms": 150,
                "input_data": {"objective": "Generate molecules"},
                "output_data": {"rounds": 5, "strategy": "hybrid"},
                "metadata": {},
            }
        },
    }


class RunProgress(BaseModel):
    """Run progress information."""

    total_generated: int = Field(
        default=0, description="Total molecules generated"
    )
    total_valid: int = Field(default=0, description="Total valid molecules")
    total_passed: int = Field(
        default=0, description="Total molecules passing screening"
    )


class RunStatusResponse(BaseModel):
    """Response schema for run status."""

    run_id: UUID = Field(description="Run ID")
    status: str = Field(description="Current status")
    progress: RunProgress = Field(description="Progress information")
    started_at: Optional[datetime] = Field(
        default=None, description="Start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "running",
                "progress": {
                    "total_generated": 50,
                    "total_valid": 40,
                    "total_passed": 30,
                },
                "started_at": "2025-12-27T10:00:00Z",
                "completed_at": None,
                "error_message": None,
            }
        }
    }


class TaskResponse(BaseModel):
    """Response schema for task creation."""

    run_id: UUID = Field(description="Run ID")
    task_id: str = Field(description="Celery task ID")
    status: str = Field(description="Initial run status")
    message: str = Field(description="Success message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "abc123-def456-ghi789",
                "status": "pending",
                "message": "Run created and workflow queued for execution",
            }
        }
    }