"""
Run API Schemas (Pydantic Models)

Defines request/response schemas for run management API endpoints.
Separated from database models for clean architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Run status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunConfig(BaseModel):
    """Run configuration schema."""

    objective: str = Field(
        description="Objective description for the run",
        min_length=10,
        max_length=1000,
    )
    seed_smiles: List[str] = Field(
        description="List of seed SMILES molecules to start from",
        min_length=1,
        max_length=10,
    )
    rounds: int = Field(
        default=5,
        description="Number of generation rounds",
        ge=1,
        le=50,
    )
    candidates_per_round: int = Field(
        default=50,
        description="Number of candidate molecules to generate per round",
        ge=10,
        le=1000,
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Molecular constraints and screening rules",
    )
    top_k: int = Field(
        default=10,
        description="Number of top molecules to select",
        ge=1,
        le=100,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "objective": "Generate drug-like molecules with high QED",
                "seed_smiles": ["CCO", "c1ccccc1"],
                "rounds": 5,
                "candidates_per_round": 50,
                "constraints": {
                    "max_mw": 500,
                    "max_logp": 5,
                    "max_violations": 1,
                },
                "top_k": 10,
            }
        }
    }


class RunCreate(BaseModel):
    """Request schema for creating a new run."""

    config: RunConfig = Field(description="Run configuration")

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "objective": "Generate drug-like molecules",
                    "seed_smiles": ["CCO", "c1ccccc1"],
                    "rounds": 5,
                    "candidates_per_round": 50,
                    "constraints": {
                        "max_mw": 500,
                        "max_violations": 1,
                    },
                    "top_k": 10,
                }
            }
        }
    }


class RunResponse(BaseModel):
    """Response schema for run data."""

    id: UUID = Field(description="Run ID")
    user_id: Optional[UUID] = Field(default=None, description="User ID")
    status: str = Field(description="Current status")
    objective: str = Field(description="Run objective")
    config: Dict[str, Any] = Field(description="Run configuration")
    created_at: datetime = Field(description="Creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None, description="Start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    total_generated: int = Field(default=0, description="Total molecules generated")
    total_valid: int = Field(default=0, description="Total valid molecules")
    total_passed: int = Field(
        default=0, description="Total molecules passing screening"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": None,
                "status": "completed",
                "objective": "Generate drug-like molecules",
                "config": {
                    "objective": "Generate drug-like molecules",
                    "seed_smiles": ["CCO", "c1ccccc1"],
                    "rounds": 5,
                    "candidates_per_round": 50,
                    "constraints": {},
                    "top_k": 10,
                },
                "created_at": "2025-12-27T10:00:00Z",
                "started_at": "2025-12-27T10:00:01Z",
                "completed_at": "2025-12-27T10:05:00Z",
                "error_message": None,
                "total_generated": 50,
                "total_valid": 45,
                "total_passed": 30,
            }
        },
    }


class RunCreateResponse(RunResponse):
    """
    Response schema for create run endpoint.
    
    Extends RunResponse with additional fields for async task tracking.
    """

    task_id: str = Field(description="Celery task ID for async execution")
    run_id: str = Field(description="Run ID (string format for convenience)")
    message: str = Field(description="Status message")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "pending",
                "message": "Run queued for execution",
                "objective": "Generate drug-like molecules",
                "config": {
                    "objective": "Generate drug-like molecules",
                    "seed_smiles": ["CCO"],
                    "rounds": 5,
                    "candidates_per_round": 50,
                },
                "created_at": "2025-12-29T10:00:00Z",
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "user_id": None,
                "total_generated": 0,
                "total_valid": 0,
                "total_passed": 0,
            }
        },
    }