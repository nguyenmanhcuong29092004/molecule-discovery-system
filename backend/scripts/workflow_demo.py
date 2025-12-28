"""
Workflow Demo Script

Demonstrates how to create a run and execute the workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal, Run
from app.tasks.orchestrator import execute_run_async


async def demo_workflow():
    """Demonstrate workflow execution."""
    print("=" * 70)
    print("MOLECULE DISCOVERY WORKFLOW DEMO")
    print("=" * 70)
    print()

    # Create a run
    print("1. Creating run in database...")
    async with AsyncSessionLocal() as session:
        run = Run(
            status="pending",
            objective="Demo: Generate drug-like molecules",
            config={
                "objective": "Generate drug-like molecules with good QED scores",
                "seed_smiles": ["CCO", "c1ccccc1"],
                "rounds": 3,
                "candidates_per_round": 20,
                "top_k": 10,
                "constraints": {
                    "max_mw": 500,
                    "max_logp": 5,
                    "max_hbd": 5,
                    "max_hba": 10,
                    "max_tpsa": 140,
                    "max_violations": 1,
                },
            },
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = str(run.id)
        print(f"✅ Created run: {run_id}")
        print()

    # Execute workflow
    print("2. Executing workflow...")
    print("   This will:")
    print("   - Create execution plan")
    print("   - Generate candidates for 3 rounds")
    print("   - Validate and score each molecule")
    print("   - Save to database")
    print("   - Log traces")
    print()

    try:
        result = await execute_run_async(run_id)

        print("✅ Workflow completed successfully!")
        print()
        print("Results:")
        print(f"  - Status: {result['status']}")
        print(f"  - Total molecules: {result['total_molecules']}")
        print(f"  - Total rounds: {result['total_rounds']}")
        print()

        # Show some statistics
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            from app.db import Molecule

            mol_result = await session.execute(
                select(Molecule)
                .where(Molecule.run_id == run.id)
                .order_by(Molecule.score.desc())
                .limit(5)
            )
            top_molecules = mol_result.scalars().all()

            print("Top 5 Molecules:")
            for i, mol in enumerate(top_molecules, 1):
                print(f"  {i}. {mol.smiles}")
                print(f"     Score: {mol.score:.3f}, QED: {mol.qed:.3f}")
                print(f"     MW: {mol.mw:.1f}, LogP: {mol.logp:.2f}")
                print(f"     Passed screening: {mol.passed_screening}")
                print()

    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        import traceback

        traceback.print_exc()

    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("Starting workflow demo...")
    print("Make sure PostgreSQL is running and database is initialized!")
    print()

    asyncio.run(demo_workflow())