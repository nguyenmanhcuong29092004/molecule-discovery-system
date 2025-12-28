"""
Integration Tests for Database Models

Tests CRUD operations, relationships, constraints, and indexes.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, Run, Molecule, Trace
from typing import AsyncGenerator


# Test database URL (use separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/molecule_discovery_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


class TestRunModel:
    """Tests for Run model."""

    @pytest.mark.asyncio
    async def test_create_run(self, session: AsyncSession):
        """Test creating a run."""
        run = Run(
            status="pending",
            objective="Test objective",
            config={"seed_smiles": ["CCO"], "rounds": 5},
        )
        
        session.add(run)
        await session.commit()
        
        assert run.id is not None
        assert isinstance(run.id, uuid.UUID)
        assert run.status == "pending"
        assert run.total_generated == 0
        assert run.created_at is not None

    @pytest.mark.asyncio
    async def test_run_with_all_fields(self, session: AsyncSession):
        """Test creating run with all fields."""
        now = datetime.utcnow()
        
        run = Run(
            user_id=uuid.uuid4(),
            status="completed",
            objective="Generate molecules",
            config={"test": "config"},
            started_at=now,
            completed_at=now,
            total_generated=100,
            total_valid=90,
            total_passed=75,
        )
        
        session.add(run)
        await session.commit()
        
        assert run.user_id is not None
        assert run.status == "completed"
        assert run.total_generated == 100
        assert run.total_valid == 90
        assert run.total_passed == 75

    @pytest.mark.asyncio
    async def test_run_default_values(self, session: AsyncSession):
        """Test run default values."""
        run = Run(
            objective="Test",
            config={},
        )
        
        session.add(run)
        await session.commit()
        
        assert run.status == "pending"
        assert run.total_generated == 0
        assert run.total_valid == 0
        assert run.total_passed == 0
        assert run.error_message is None

    @pytest.mark.asyncio
    async def test_query_run_by_status(self, session: AsyncSession):
        """Test querying runs by status."""
        # Create multiple runs
        run1 = Run(status="pending", objective="Test 1", config={})
        run2 = Run(status="running", objective="Test 2", config={})
        run3 = Run(status="pending", objective="Test 3", config={})
        
        session.add_all([run1, run2, run3])
        await session.commit()
        
        # Query pending runs
        result = await session.execute(
            select(Run).where(Run.status == "pending")
        )
        pending_runs = result.scalars().all()
        
        assert len(pending_runs) == 2
        assert all(r.status == "pending" for r in pending_runs)


class TestMoleculeModel:
    """Tests for Molecule model."""

    @pytest.mark.asyncio
    async def test_create_molecule(self, session: AsyncSession):
        """Test creating a molecule."""
        # Create parent run first
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create molecule
        molecule = Molecule(
            run_id=run.id,
            smiles="CCO",
            smiles_canonical="CCO",
            round_number=1,
            mw=46.07,
            logp=-0.18,
            hbd=1,
            hba=1,
            tpsa=20.23,
            rotatable_bonds=0,
            qed=0.85,
            passed_screening=True,
            num_violations=0,
            violations=[],
            score=0.85,
            generation_method="seed",
        )
        
        session.add(molecule)
        await session.commit()
        
        assert molecule.id is not None
        assert molecule.run_id == run.id
        assert molecule.smiles == "CCO"
        assert molecule.mw == 46.07
        assert molecule.qed == 0.85

    @pytest.mark.asyncio
    async def test_molecule_with_violations(self, session: AsyncSession):
        """Test molecule with screening violations."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        molecule = Molecule(
            run_id=run.id,
            smiles="C" * 50,
            smiles_canonical="C" * 50,
            round_number=1,
            mw=600,
            logp=7,
            hbd=0,
            hba=0,
            tpsa=0,
            rotatable_bonds=0,
            qed=0.2,
            passed_screening=False,
            num_violations=2,
            violations=[
                {"rule": "MW", "value": 600, "limit": 500},
                {"rule": "LogP", "value": 7, "limit": 5},
            ],
            score=0.0,
            generation_method="mutation",
            parent_smiles="CCO",
        )
        
        session.add(molecule)
        await session.commit()
        
        assert molecule.passed_screening is False
        assert molecule.num_violations == 2
        assert len(molecule.violations) == 2
        assert molecule.parent_smiles == "CCO"

    @pytest.mark.asyncio
    async def test_molecule_run_relationship(self, session: AsyncSession):
        """Test molecule-run relationship."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create multiple molecules
        molecules = [
            Molecule(
                run_id=run.id,
                smiles=f"C{i}",
                smiles_canonical=f"C{i}",
                round_number=1,
                mw=50.0 + i,
                logp=0.0,
                hbd=0,
                hba=0,
                tpsa=0.0,
                rotatable_bonds=0,
                qed=0.5,
                passed_screening=True,
                num_violations=0,
                violations=[],
                score=0.5,
                generation_method="test",
            )
            for i in range(3)
        ]
        
        session.add_all(molecules)
        await session.commit()
        
        # Query run and check molecules
        result = await session.execute(
            select(Run).where(Run.id == run.id)
        )
        queried_run = result.scalar_one()
        
        # Access relationship (need to refresh)
        await session.refresh(queried_run, ["molecules"])
        
        assert len(queried_run.molecules) == 3

    @pytest.mark.asyncio
    async def test_molecule_unique_constraint(self, session: AsyncSession):
        """Test unique constraint on run_id + smiles_canonical."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create first molecule
        mol1 = Molecule(
            run_id=run.id,
            smiles="CCO",
            smiles_canonical="CCO",
            round_number=1,
            mw=46.07,
            logp=0.0,
            hbd=1,
            hba=1,
            tpsa=20.0,
            rotatable_bonds=0,
            qed=0.8,
            passed_screening=True,
            num_violations=0,
            violations=[],
            score=0.8,
            generation_method="test",
        )
        
        session.add(mol1)
        await session.commit()
        
        # Try to create duplicate
        mol2 = Molecule(
            run_id=run.id,
            smiles="CCO",
            smiles_canonical="CCO",  # Same canonical SMILES
            round_number=2,
            mw=46.07,
            logp=0.0,
            hbd=1,
            hba=1,
            tpsa=20.0,
            rotatable_bonds=0,
            qed=0.8,
            passed_screening=True,
            num_violations=0,
            violations=[],
            score=0.8,
            generation_method="test",
        )
        
        session.add(mol2)
        
        with pytest.raises(IntegrityError):
            await session.commit()

    @pytest.mark.asyncio
    async def test_cascade_delete_molecules(self, session: AsyncSession):
        """Test that deleting run cascades to molecules."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create molecules
        molecules = [
            Molecule(
                run_id=run.id,
                smiles=f"C{i}",
                smiles_canonical=f"C{i}",
                round_number=1,
                mw=50.0,
                logp=0.0,
                hbd=0,
                hba=0,
                tpsa=0.0,
                rotatable_bonds=0,
                qed=0.5,
                passed_screening=True,
                num_violations=0,
                violations=[],
                score=0.5,
                generation_method="test",
            )
            for i in range(3)
        ]
        
        session.add_all(molecules)
        await session.commit()
        
        run_id = run.id
        
        # Delete run
        await session.delete(run)
        await session.commit()
        
        # Check molecules are deleted
        result = await session.execute(
            select(Molecule).where(Molecule.run_id == run_id)
        )
        remaining = result.scalars().all()
        
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_query_molecules_by_score(self, session: AsyncSession):
        """Test querying molecules ordered by score."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create molecules with different scores
        molecules = [
            Molecule(
                run_id=run.id,
                smiles=f"C{i}",
                smiles_canonical=f"C{i}",
                round_number=1,
                mw=50.0,
                logp=0.0,
                hbd=0,
                hba=0,
                tpsa=0.0,
                rotatable_bonds=0,
                qed=0.5 + i * 0.1,
                passed_screening=True,
                num_violations=0,
                violations=[],
                score=0.5 + i * 0.1,
                generation_method="test",
            )
            for i in range(5)
        ]
        
        session.add_all(molecules)
        await session.commit()
        
        # Query top 3 by score
        result = await session.execute(
            select(Molecule)
            .where(Molecule.run_id == run.id)
            .order_by(Molecule.score.desc())
            .limit(3)
        )
        top_molecules = result.scalars().all()
        
        assert len(top_molecules) == 3
        assert top_molecules[0].score >= top_molecules[1].score
        assert top_molecules[1].score >= top_molecules[2].score


class TestTraceModel:
    """Tests for Trace model."""

    @pytest.mark.asyncio
    async def test_create_trace(self, session: AsyncSession):
        """Test creating a trace."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        trace = Trace(
            run_id=run.id,
            round_number=1,
            agent_type="planner",
            action="plan_created",
            duration_ms=100,
            input_data={"test": "input"},
            output_data={"test": "output"},
        )
        
        session.add(trace)
        await session.commit()
        
        assert trace.id is not None
        assert trace.run_id == run.id
        assert trace.agent_type == "planner"
        assert trace.duration_ms == 100

    @pytest.mark.asyncio
    async def test_trace_with_metadata(self, session: AsyncSession):
        """Test trace with metadata."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        trace = Trace(
            run_id=run.id,
            round_number=1,
            agent_type="generator",
            action="molecules_generated",
            trace_metadata={"error": "test error", "warning": "test warning"},
        )
        
        session.add(trace)
        await session.commit()
        
        assert trace.trace_metadata is not None
        assert trace.trace_metadata["error"] == "test error"

    @pytest.mark.asyncio
    async def test_cascade_delete_traces(self, session: AsyncSession):
        """Test that deleting run cascades to traces."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create traces
        traces = [
            Trace(
                run_id=run.id,
                round_number=i,
                agent_type="test",
                action=f"action_{i}",
            )
            for i in range(3)
        ]
        
        session.add_all(traces)
        await session.commit()
        
        run_id = run.id
        
        # Delete run
        await session.delete(run)
        await session.commit()
        
        # Check traces are deleted
        result = await session.execute(
            select(Trace).where(Trace.run_id == run_id)
        )
        remaining = result.scalars().all()
        
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_query_traces_by_round(self, session: AsyncSession):
        """Test querying traces by round number."""
        run = Run(objective="Test", config={})
        session.add(run)
        await session.commit()
        
        # Create traces for different rounds
        traces = [
            Trace(
                run_id=run.id,
                round_number=round_num,
                agent_type="test",
                action=f"action_{i}",
            )
            for round_num in [1, 1, 2, 2, 3]
            for i in range(1)
        ]
        
        session.add_all(traces)
        await session.commit()
        
        # Query round 2 traces
        result = await session.execute(
            select(Trace)
            .where(Trace.run_id == run.id)
            .where(Trace.round_number == 2)
        )
        round_2_traces = result.scalars().all()
        
        assert len(round_2_traces) == 1
        assert all(t.round_number == 2 for t in round_2_traces)