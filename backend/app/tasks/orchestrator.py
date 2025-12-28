"""
Workflow Orchestrator Task

Orchestrates the complete molecule discovery workflow:
1. Planning
2. Multi-round generation
3. Validation and scoring
4. Database persistence
5. Final ranking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select

from app.agents import GeneratorAgent, PlannerAgent, RankerAgent
from app.celery_app import celery_app
from app.chemistry import ChemistryEngine, DEFAULT_CONSTRAINTS
from app.db import AsyncSessionLocal, Molecule, Run, Trace

# Configure logger
logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    pass


@celery_app.task(bind=True, name="execute_run")
def execute_run(self, run_id: str) -> Dict:
    """
    Execute a complete molecule discovery run.
    
    This is the main entry point for async workflow execution.
    Wraps the async workflow in sync context for Celery.
    
    Args:
        run_id: UUID of the run to execute
        
    Returns:
        Dictionary with execution results
    """
    import asyncio

    try:
        # Run async workflow in event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(execute_run_async(run_id))
        return result

    except Exception as e:
        logger.error(f"Run {run_id} failed: {str(e)}", exc_info=True)
        # Try to update run status to failed
        try:
            loop.run_until_complete(mark_run_failed(run_id, str(e)))
        except Exception as update_error:
            logger.error(
                f"Failed to update run status: {str(update_error)}", exc_info=True
            )

        raise


async def execute_run_async(run_id: str) -> Dict:
    """
    Execute workflow asynchronously.
    
    Workflow steps:
    1. Load run config from DB
    2. Update status to "running"
    3. Call Planner → get plan
    4. Loop for N rounds:
       a. Call Generator → get candidates
       b. Validate each with Chemistry Engine
       c. Compute properties for valid ones
       d. Apply screening
       e. Save molecules to DB
       f. Update run stats
       g. Log traces
    5. Call Ranker → get top K overall
    6. Update status to "completed"
    
    Args:
        run_id: UUID of the run
        
    Returns:
        Execution results
        
    Raises:
        WorkflowError: If workflow fails
    """
    logger.info(f"Starting workflow for run {run_id}")

    # Step 1: Load run from database
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == UUID(run_id)))
        run = result.scalar_one_or_none()

        if run is None:
            raise WorkflowError(f"Run {run_id} not found")

        # Extract config
        config = run.config
        objective = config.get("objective", "Generate molecules")
        seed_smiles = config.get("seed_smiles", [])
        constraints = config.get("constraints", DEFAULT_CONSTRAINTS)
        max_rounds = config.get("rounds", 5)
        candidates_per_round = config.get("candidates_per_round", 50)
        top_k = config.get("top_k", 10)

        logger.info(
            f"Run config: {max_rounds} rounds, {candidates_per_round} candidates/round, "
            f"{len(seed_smiles)} seeds"
        )

    # Step 2: Update status to running
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == UUID(run_id)))
        run = result.scalar_one()
        run.status = "running"
        run.started_at = datetime.utcnow()
        await session.commit()

    # Create trace for workflow start
    await log_trace(
        run_id=run_id,
        round_number=0,
        agent_type="orchestrator",
        action="workflow_started",
        output_data={"config": config},
    )

    # Step 3: Create execution plan
    planner = PlannerAgent()
    plan_result = planner.execute(
        {
            "objective": objective,
            "seed_smiles": seed_smiles,
            "constraints": constraints,
            "max_rounds": max_rounds,
        }
    )

    if not plan_result["success"]:
        raise WorkflowError(f"Planning failed: {plan_result['error']}")

    plan = plan_result["output"]
    logger.info(f"Plan created: {plan['rounds']} rounds, strategy={plan['strategy']}")

    await log_trace(
        run_id=run_id,
        round_number=0,
        agent_type="planner",
        action="plan_created",
        output_data=plan,
        duration_ms=plan_result["duration_ms"],
    )

    # Use plan values if not overridden in config
    actual_rounds = config.get("rounds", plan["rounds"])
    actual_candidates = config.get("candidates_per_round", plan["candidates_per_round"])

    # Track all molecules across rounds
    all_molecules: List[Dict] = []
    current_seeds = seed_smiles.copy()

    # Step 4: Execute rounds
    for round_num in range(1, actual_rounds + 1):
        logger.info(f"Starting round {round_num}/{actual_rounds}")

        # 4a. Generate candidates
        generator = GeneratorAgent()
        gen_result = generator.execute(
            {
                "seed_smiles": current_seeds,
                "candidates_count": actual_candidates,
                "round_number": round_num,
                "strategy": plan.get("strategy", "hybrid"),
            }
        )

        if not gen_result["success"]:
            logger.error(f"Generation failed in round {round_num}: {gen_result['error']}")
            await log_trace(
                run_id=run_id,
                round_number=round_num,
                agent_type="generator",
                action="generation_failed",
                metadata={"error": gen_result["error"]},
            )
            continue

        candidates = gen_result["output"]["candidates"]
        logger.info(f"Round {round_num}: generated {len(candidates)} candidates")

        await log_trace(
            run_id=run_id,
            round_number=round_num,
            agent_type="generator",
            action="candidates_generated",
            output_data={
                "count": len(candidates),
                "strategy": gen_result["output"]["strategy_used"],
            },
            duration_ms=gen_result["duration_ms"],
        )

        # 4b-e. Process each candidate
        round_molecules = []
        valid_count = 0
        invalid_count = 0

        for candidate in candidates:
            # Validate SMILES
            is_valid, canonical, error = ChemistryEngine.validate_smiles(candidate)
            if not is_valid:
                invalid_count += 1
                continue

            valid_count += 1

            # Compute properties
            try:
                props = ChemistryEngine.compute_properties(canonical)

                # Apply screening
                screening = ChemistryEngine.apply_screening(props, constraints)

                # Calculate score
                score = ChemistryEngine.calculate_score(
                    props["qed"], screening["num_violations"]
                )

                # Create molecule data
                mol_data = {
                    "smiles": canonical,
                    "round_number": round_num,
                    "mw": props["mw"],
                    "logp": props["logp"],
                    "hbd": props["hbd"],
                    "hba": props["hba"],
                    "tpsa": props["tpsa"],
                    "rotatable_bonds": props["rotatable_bonds"],
                    "qed": props["qed"],
                    "passed_screening": screening["passed"],
                    "num_violations": screening["num_violations"],
                    "violations": screening["violations"],
                    "score": score,
                }

                round_molecules.append(mol_data)

            except Exception as e:
                logger.warning(f"Failed to process {canonical}: {str(e)}")
                invalid_count += 1

        logger.info(
            f"Round {round_num}: {valid_count} valid, {invalid_count} invalid"
        )

        # 4f. Save molecules to database
        async with AsyncSessionLocal() as session:
            for mol_data in round_molecules:
                molecule = Molecule(
                    run_id=UUID(run_id),
                    smiles=mol_data["smiles"],
                    smiles_canonical=mol_data["smiles"],
                    round_number=mol_data["round_number"],
                    mw=mol_data["mw"],
                    logp=mol_data["logp"],
                    hbd=mol_data["hbd"],
                    hba=mol_data["hba"],
                    tpsa=mol_data["tpsa"],
                    rotatable_bonds=mol_data["rotatable_bonds"],
                    qed=mol_data["qed"],
                    passed_screening=mol_data["passed_screening"],
                    num_violations=mol_data["num_violations"],
                    violations=mol_data["violations"],
                    score=mol_data["score"],
                    generation_method=plan.get("strategy", "hybrid"),
                )
                session.add(molecule)

            await session.commit()

        # Add to all molecules
        all_molecules.extend(round_molecules)

        # 4g. Update run stats
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Run).where(Run.id == UUID(run_id)))
            run = result.scalar_one()
            run.total_generated += len(candidates)
            run.total_valid += valid_count
            run.total_passed += sum(
                1 for m in round_molecules if m["passed_screening"]
            )
            await session.commit()

        await log_trace(
            run_id=run_id,
            round_number=round_num,
            agent_type="orchestrator",
            action="round_completed",
            output_data={
                "molecules_saved": len(round_molecules),
                "valid": valid_count,
                "invalid": invalid_count,
            },
        )

        # Select top molecules from this round as seeds for next round
        if round_num < actual_rounds and round_molecules:
            # Sort by score
            sorted_mols = sorted(
                round_molecules, key=lambda x: x["score"], reverse=True
            )
            # Take top 5 as seeds for next round
            current_seeds = [m["smiles"] for m in sorted_mols[:5]]

    # Step 5: Final ranking across all rounds
    if all_molecules:
        ranker = RankerAgent()
        rank_result = ranker.execute(
            {
                "molecules": all_molecules,
                "top_k": top_k,
                "diversity_filter": True,
                "min_score": 0.3,
            }
        )

        if rank_result["success"]:
            top_molecules = rank_result["output"]["ranked_molecules"]
            avg_score = rank_result["output"]["avg_score"]

            logger.info(
                f"Final ranking: {len(top_molecules)} molecules, avg score {avg_score:.3f}"
            )

            await log_trace(
                run_id=run_id,
                round_number=actual_rounds,
                agent_type="ranker",
                action="final_ranking",
                output_data={
                    "top_k": len(top_molecules),
                    "avg_score": avg_score,
                },
                duration_ms=rank_result["duration_ms"],
            )

    # Step 6: Update status to completed
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == UUID(run_id)))
        run = result.scalar_one()
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        await session.commit()

    await log_trace(
        run_id=run_id,
        round_number=actual_rounds,
        agent_type="orchestrator",
        action="workflow_completed",
        output_data={
            "total_molecules": len(all_molecules),
            "total_rounds": actual_rounds,
        },
    )

    logger.info(f"Workflow completed for run {run_id}")

    return {
        "run_id": run_id,
        "status": "completed",
        "total_molecules": len(all_molecules),
        "total_rounds": actual_rounds,
    }


async def mark_run_failed(run_id: str, error_message: str) -> None:
    """
    Mark a run as failed with error message.
    
    Args:
        run_id: UUID of the run
        error_message: Error message to store
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == UUID(run_id)))
        run = result.scalar_one_or_none()

        if run:
            run.status = "failed"
            run.error_message = error_message
            run.completed_at = datetime.utcnow()
            await session.commit()

    await log_trace(
        run_id=run_id,
        round_number=0,
        agent_type="orchestrator",
        action="workflow_failed",
        metadata={"error": error_message},
    )


async def log_trace(
    run_id: str,
    round_number: int,
    agent_type: str,
    action: str,
    input_data: Optional[Dict] = None,
    output_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    duration_ms: Optional[int] = None,
) -> None:
    """
    Log a trace entry to the database.
    
    Args:
        run_id: UUID of the run
        round_number: Round number
        agent_type: Type of agent (planner/generator/ranker/orchestrator)
        action: Action performed
        input_data: Optional input data
        output_data: Optional output data
        metadata: Optional metadata
        duration_ms: Optional duration in milliseconds
    """
    async with AsyncSessionLocal() as session:
        trace = Trace(
            run_id=UUID(run_id),
            round_number=round_number,
            agent_type=agent_type,
            action=action,
            input_data=input_data or {},
            output_data=output_data or {},
            metadata=metadata or {},
            duration_ms=duration_ms,
        )
        session.add(trace)
        await session.commit()