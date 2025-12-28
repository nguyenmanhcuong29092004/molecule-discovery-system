"""
SQLAlchemy ORM Models

Defines database schema for runs, molecules, and traces.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Run(Base):
    """
    Run model - stores workflow execution data.
    
    Represents a single molecule discovery run with configuration,
    status tracking, and summary statistics.
    
    Attributes:
        id: Unique identifier
        user_id: Optional user who created the run
        status: Current run status (pending/running/completed/failed/cancelled)
        objective: Text description of the run objective
        config: Full run configuration as JSON
        created_at: When the run was created
        started_at: When execution started
        completed_at: When execution finished
        error_message: Error details if failed
        total_generated: Total molecules generated
        total_valid: Total valid SMILES generated
        total_passed: Total molecules passing screening
    """

    __tablename__ = "runs"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique run identifier",
    )

    # User relationship (nullable for anonymous runs)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who created this run",
    )

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="Run status: pending/running/completed/failed/cancelled",
    )

    # Configuration
    objective = Column(
        Text,
        nullable=False,
        comment="Objective description for this run",
    )

    config = Column(
        JSONB,
        nullable=False,
        comment="Full run configuration as JSON",
    )

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When the run was created",
    )

    started_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When execution started",
    )

    completed_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When execution completed",
    )

    # Error tracking
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if run failed",
    )

    # Summary statistics
    total_generated = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total molecules generated",
    )

    total_valid = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total valid SMILES generated",
    )

    total_passed = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total molecules passing screening",
    )

    # Relationships
    molecules = relationship(
        "Molecule",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="select",
    )

    traces = relationship(
        "Trace",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        Index("idx_runs_status", "status"),
        Index("idx_runs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Run(id={self.id}, status={self.status})>"


class Molecule(Base):
    """
    Molecule model - stores generated molecules with properties.
    
    Stores molecular data including SMILES, computed properties,
    screening results, and metadata for tracking generation.
    
    Attributes:
        id: Unique identifier
        run_id: Parent run identifier
        smiles: Original SMILES string
        smiles_canonical: Canonicalized SMILES
        round_number: Generation round number
        mw: Molecular weight
        logp: Partition coefficient
        hbd: Hydrogen bond donors
        hba: Hydrogen bond acceptors
        tpsa: Topological polar surface area
        rotatable_bonds: Number of rotatable bonds
        qed: Drug-likeness score
        passed_screening: Whether molecule passed screening
        num_violations: Number of rule violations
        violations: List of violations as JSON
        score: Composite score
        generation_method: How molecule was generated
        parent_smiles: Parent molecule SMILES if mutated
        created_at: Creation timestamp
    """

    __tablename__ = "molecules"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique molecule identifier",
    )

    # Foreign key to run
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent run identifier",
    )

    # SMILES data
    smiles = Column(
        String(500),
        nullable=False,
        comment="Original SMILES string",
    )

    smiles_canonical = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Canonicalized SMILES string",
    )

    round_number = Column(
        Integer,
        nullable=False,
        comment="Generation round number",
    )

    # Molecular properties (from Chemistry Engine)
    mw = Column(
        Float,
        nullable=False,
        comment="Molecular weight (Da)",
    )

    logp = Column(
        Float,
        nullable=False,
        comment="Partition coefficient (lipophilicity)",
    )

    hbd = Column(
        Integer,
        nullable=False,
        comment="Hydrogen bond donors",
    )

    hba = Column(
        Integer,
        nullable=False,
        comment="Hydrogen bond acceptors",
    )

    tpsa = Column(
        Float,
        nullable=False,
        comment="Topological polar surface area (Ų)",
    )

    rotatable_bonds = Column(
        Integer,
        nullable=False,
        comment="Number of rotatable bonds",
    )

    qed = Column(
        Float,
        nullable=False,
        index=True,
        comment="Drug-likeness score (0-1)",
    )

    # Screening results
    passed_screening = Column(
        Boolean,
        nullable=False,
        comment="Whether molecule passed screening",
    )

    num_violations = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of rule violations",
    )

    violations = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of violations as JSON",
    )

    score = Column(
        Float,
        nullable=False,
        index=True,
        comment="Composite score (QED - penalty * violations)",
    )

    # Generation metadata
    generation_method = Column(
        String(100),
        nullable=False,
        comment="Generation method (mutation/fragment/scaffold)",
    )

    parent_smiles = Column(
        String(500),
        nullable=True,
        comment="Parent molecule SMILES if derived",
    )

    # Timestamp
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the molecule was created",
    )

    # Relationships
    run = relationship("Run", back_populates="molecules")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_molecules_run", "run_id"),
        Index("idx_molecules_score", "score"),
        Index("idx_molecules_qed", "qed"),
        Index("idx_molecules_canonical", "smiles_canonical"),
        UniqueConstraint(
            "run_id",
            "smiles_canonical",
            name="uq_molecules_run_canonical",
        ),
    )

    def __repr__(self) -> str:
        return f"<Molecule(id={self.id}, smiles={self.smiles_canonical}, score={self.score:.3f})>"


class Trace(Base):
    """
    Trace model - stores agent activity logs.
    
    Records all agent actions during a run for debugging,
    auditing, and analysis.
    
    Attributes:
        id: Unique identifier
        run_id: Parent run identifier
        round_number: Round number when action occurred
        agent_type: Type of agent (planner/generator/ranker)
        action: Action performed
        timestamp: When action occurred
        duration_ms: How long action took (milliseconds)
        input_data: Input data as JSON
        output_data: Output data as JSON
        trace_metadata: Additional metadata (errors, warnings, debug info)
    """

    __tablename__ = "traces"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique trace identifier",
    )

    # Foreign key to run
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent run identifier",
    )

    # Trace data
    round_number = Column(
        Integer,
        nullable=False,
        comment="Round number when action occurred",
    )

    agent_type = Column(
        String(50),
        nullable=False,
        comment="Agent type: planner/generator/ranker",
    )

    action = Column(
        String(100),
        nullable=False,
        comment="Action performed",
    )

    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When action occurred",
    )

    duration_ms = Column(
        Integer,
        nullable=True,
        comment="Action duration in milliseconds",
    )

    # JSON data
    input_data = Column(
        JSONB,
        nullable=True,
        comment="Input data as JSON",
    )

    output_data = Column(
        JSONB,
        nullable=True,
        comment="Output data as JSON",
    )

    trace_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional metadata (errors, warnings, debug info)",
    )

    # Relationships
    run = relationship("Run", back_populates="traces")

    # Indexes
    __table_args__ = (
        Index("idx_traces_run", "run_id"),
        Index("idx_traces_round", "run_id", "round_number"),
    )

    def __repr__(self) -> str:
        return f"<Trace(id={self.id}, agent={self.agent_type}, action={self.action})>"