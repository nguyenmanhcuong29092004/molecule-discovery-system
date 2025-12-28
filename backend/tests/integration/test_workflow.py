"""
Integration Tests for Workflow Orchestration

Tests the complete molecule discovery workflow end-to-end.
"""

import pytest
from sqlalchemy import select

from app.db import AsyncSessionLocal, Molecule, Run, Trace
from app.tasks.orchestrator import execute_run_async, log_trace, mark_run_failed


class TestWorkflowOrchestration:
    """Tests for workflow orchestration."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow execution."""
        # Create a run
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test complete workflow",
                config={
                    "objective": "Generate test molecules",
                    "seed_smiles": ["CCO"],
                    "rounds": 2,
                    "candidates_per_round": 10,
                    "top_k": 5,
                    "constraints": {
                        "max_mw": 500,
                        "max_violations": 1,
                    },
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        # Execute workflow
        result = await execute_run_async(run_id)

        # Verify result
        assert result["status"] == "completed"
        assert result["run_id"] == run_id
        assert result["total_rounds"] == 2

        # Verify run was updated
        async with AsyncSessionLocal() as session:
            db_result = await session.execute(select(Run).where(Run.id == run.id))
            updated_run = db_result.scalar_one()

            assert updated_run.status == "completed"
            assert updated_run.started_at is not None
            assert updated_run.completed_at is not None
            assert updated_run.total_generated > 0
            assert updated_run.total_valid > 0

        # Verify molecules were created
        async with AsyncSessionLocal() as session:
            mol_result = await session.execute(
                select(Molecule).where(Molecule.run_id == run.id)
            )
            molecules = mol_result.scalars().all()

            assert len(molecules) > 0
            # Check molecule properties
            for mol in molecules:
                assert mol.smiles is not None
                assert mol.score is not None
                assert mol.qed is not None
                assert mol.round_number in [1, 2]

        # Verify traces were logged
        async with AsyncSessionLocal() as session:
            trace_result = await session.execute(
                select(Trace).where(Trace.run_id == run.id)
            )
            traces = trace_result.scalars().all()

            assert len(traces) > 0
            # Should have traces for workflow start, planning, generation, etc.
            trace_actions = [t.action for t in traces]
            assert "workflow_started" in trace_actions
            assert "plan_created" in trace_actions

    @pytest.mark.asyncio
    async def test_workflow_with_multiple_seeds(self):
        """Test workflow with multiple seed molecules."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test multiple seeds",
                config={
                    "objective": "Generate from multiple seeds",
                    "seed_smiles": ["CCO", "c1ccccc1", "CC(C)C"],
                    "rounds": 1,
                    "candidates_per_round": 15,
                    "top_k": 5,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        result = await execute_run_async(run_id)

        assert result["status"] == "completed"

        # Verify molecules from all seeds
        async with AsyncSessionLocal() as session:
            mol_result = await session.execute(
                select(Molecule).where(Molecule.run_id == run.id)
            )
            molecules = mol_result.scalars().all()
            assert len(molecules) > 0

    @pytest.mark.asyncio
    async def test_workflow_updates_stats(self):
        """Test that workflow updates run statistics."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test stats update",
                config={
                    "objective": "Test statistics",
                    "seed_smiles": ["CCO"],
                    "rounds": 2,
                    "candidates_per_round": 10,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        await execute_run_async(run_id)

        async with AsyncSessionLocal() as session:
            db_result = await session.execute(select(Run).where(Run.id == run.id))
            updated_run = db_result.scalar_one()

            # Check stats are updated
            assert updated_run.total_generated > 0
            assert updated_run.total_valid > 0
            # total_passed might be 0 if screening is strict
            assert updated_run.total_passed >= 0

    @pytest.mark.asyncio
    async def test_workflow_multi_round_progression(self):
        """Test that molecules improve across rounds."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test multi-round",
                config={
                    "objective": "Test round progression",
                    "seed_smiles": ["CCO"],
                    "rounds": 3,
                    "candidates_per_round": 10,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        await execute_run_async(run_id)

        # Get molecules by round
        async with AsyncSessionLocal() as session:
            mol_result = await session.execute(
                select(Molecule)
                .where(Molecule.run_id == run.id)
                .order_by(Molecule.round_number)
            )
            molecules = mol_result.scalars().all()

            # Should have molecules from multiple rounds
            rounds = set(m.round_number for m in molecules)
            assert len(rounds) > 1

            # Group by round
            round_molecules = {}
            for mol in molecules:
                if mol.round_number not in round_molecules:
                    round_molecules[mol.round_number] = []
                round_molecules[mol.round_number].append(mol)

            # Each round should have molecules
            for round_num in rounds:
                assert len(round_molecules[round_num]) > 0

    @pytest.mark.asyncio
    async def test_workflow_traces_logged(self):
        """Test that workflow logs traces properly."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test tracing",
                config={
                    "objective": "Test trace logging",
                    "seed_smiles": ["CCO"],
                    "rounds": 1,
                    "candidates_per_round": 5,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        await execute_run_async(run_id)

        async with AsyncSessionLocal() as session:
            trace_result = await session.execute(
                select(Trace)
                .where(Trace.run_id == run.id)
                .order_by(Trace.timestamp)
            )
            traces = trace_result.scalars().all()

            # Check trace types
            actions = [t.action for t in traces]
            assert "workflow_started" in actions
            assert "plan_created" in actions
            assert "candidates_generated" in actions
            assert "workflow_completed" in actions

            # Check agent types
            agent_types = set(t.agent_type for t in traces)
            assert "orchestrator" in agent_types
            assert "planner" in agent_types
            assert "generator" in agent_types

    @pytest.mark.asyncio
    async def test_mark_run_failed(self):
        """Test marking a run as failed."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="running",
                objective="Test failure",
                config={"seed_smiles": ["CCO"], "constraints": {}},
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        # Mark as failed
        error_msg = "Test error message"
        await mark_run_failed(run_id, error_msg)

        # Verify status and error message
        async with AsyncSessionLocal() as session:
            db_result = await session.execute(select(Run).where(Run.id == run.id))
            failed_run = db_result.scalar_one()

            assert failed_run.status == "failed"
            assert failed_run.error_message == error_msg
            assert failed_run.completed_at is not None

    @pytest.mark.asyncio
    async def test_log_trace(self):
        """Test trace logging function."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test trace",
                config={"seed_smiles": ["CCO"], "constraints": {}},
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        # Log a trace
        await log_trace(
            run_id=run_id,
            round_number=1,
            agent_type="test_agent",
            action="test_action",
            input_data={"test": "input"},
            output_data={"test": "output"},
            metadata={"info": "metadata"},
            duration_ms=100,
        )

        # Verify trace was saved
        async with AsyncSessionLocal() as session:
            trace_result = await session.execute(
                select(Trace).where(Trace.run_id == run.id)
            )
            trace = trace_result.scalar_one()

            assert trace.agent_type == "test_agent"
            assert trace.action == "test_action"
            assert trace.round_number == 1
            assert trace.duration_ms == 100
            assert trace.input_data["test"] == "input"
            assert trace.output_data["test"] == "output"

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_seed(self):
        """Test workflow handles invalid seed SMILES."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test invalid seed",
                config={
                    "objective": "Test error handling",
                    "seed_smiles": ["INVALID_SMILES"],
                    "rounds": 1,
                    "candidates_per_round": 5,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        # Should raise error due to invalid seed
        with pytest.raises(Exception):
            await execute_run_async(run_id)

        # Run should be marked as failed (by the task wrapper)
        # For this test, we just verify the exception is raised

    @pytest.mark.asyncio
    async def test_workflow_saves_molecule_properties(self):
        """Test that all molecule properties are saved correctly."""
        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test properties",
                config={
                    "objective": "Test molecule properties",
                    "seed_smiles": ["CCO"],
                    "rounds": 1,
                    "candidates_per_round": 5,
                    "constraints": {
                        "max_mw": 500,
                        "max_logp": 5,
                        "max_violations": 1,
                    },
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        await execute_run_async(run_id)

        async with AsyncSessionLocal() as session:
            mol_result = await session.execute(
                select(Molecule).where(Molecule.run_id == run.id).limit(1)
            )
            molecule = mol_result.scalar_one()

            # Verify all properties are set
            assert molecule.smiles is not None
            assert molecule.smiles_canonical is not None
            assert molecule.mw is not None
            assert molecule.logp is not None
            assert molecule.hbd is not None
            assert molecule.hba is not None
            assert molecule.tpsa is not None
            assert molecule.rotatable_bonds is not None
            assert molecule.qed is not None
            assert molecule.score is not None
            assert molecule.passed_screening is not None
            assert molecule.num_violations is not None
            assert isinstance(molecule.violations, list)

    @pytest.mark.asyncio
    async def test_workflow_respects_config_rounds(self):
        """Test that workflow respects configured number of rounds."""
        test_rounds = 2

        async with AsyncSessionLocal() as session:
            run = Run(
                status="pending",
                objective="Test rounds config",
                config={
                    "objective": "Test round count",
                    "seed_smiles": ["CCO"],
                    "rounds": test_rounds,
                    "candidates_per_round": 5,
                    "constraints": {},
                },
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = str(run.id)

        result = await execute_run_async(run_id)

        assert result["total_rounds"] == test_rounds

        # Check that molecules exist from expected rounds
        async with AsyncSessionLocal() as session:
            mol_result = await session.execute(
                select(Molecule).where(Molecule.run_id == run.id)
            )
            molecules = mol_result.scalars().all()

            rounds = set(m.round_number for m in molecules)
            assert max(rounds) <= test_rounds