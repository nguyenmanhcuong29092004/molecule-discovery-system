"""
Pydantic Models for Run API Requests and Responses

Defines request/response schemas for run management endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
        min_length=1,
        max_length=1000,
    )
    max_rounds: int = Field(
        default=5,
        description="Maximum number of generation rounds",
        ge=1,
        le=50,
    )
    molecules_per_round: int = Field(
        default=10,
        description="Target molecules to generate per round",
        ge=1,
        le=100,
    )
    screening_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Molecular screening rules and constraints",
    )
    generation_strategy: str = Field(
        default="hybrid",
        description="Generation strategy (mutation/fragment/scaffold/hybrid)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "objective": "Generate drug-like molecules with high QED",
                "max_rounds": 5,
                "molecules_per_round": 10,
                "screening_rules": {
                    "mw_max": 500,
                    "logp_max": 5,
                    "hbd_max": 5,
                    "hba_max": 10,
                },
                "generation_strategy": "hybrid",
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
                    "max_rounds": 5,
                    "molecules_per_round": 10,
                    "screening_rules": {},
                    "generation_strategy": "hybrid",
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
                    "max_rounds": 5,
                    "molecules_per_round": 10,
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