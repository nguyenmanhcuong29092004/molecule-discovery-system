#!/usr/bin/env python3
"""
Initialize Database

Creates all tables and verifies database connection.

Usage:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.db import engine, init_db, Run, Molecule, Trace


async def verify_connection() -> bool:
    """
    Verify database connection.
    
    Returns:
        bool: True if connection successful
    """
    try:
        async with engine.connect() as conn:
            # Fix: Use scalar instead of execute + fetchone
            result = await conn.scalar(text("SELECT 1"))
            return result == 1
    except OperationalError as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


async def check_tables() -> dict:
    """
    Check which tables exist.
    
    Returns:
        dict: Table existence status
    """
    async with engine.connect() as conn:
        def _get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()
        
        existing_tables = await conn.run_sync(_get_tables)
    
    expected_tables = ["runs", "molecules", "traces"]
    
    status = {}
    for table in expected_tables:
        status[table] = table in existing_tables
    
    return status


async def check_indexes() -> dict:
    """
    Check if indexes exist.
    
    Returns:
        dict: Index existence status
    """
    async with engine.connect() as conn:
        def _get_indexes(connection):
            inspector = inspect(connection)
            indexes = {}
            
            # Check runs indexes
            try:
                runs_indexes = inspector.get_indexes("runs")
                indexes["idx_runs_status"] = any(
                    idx["name"] == "idx_runs_status" for idx in runs_indexes
                )
                indexes["idx_runs_created"] = any(
                    idx["name"] == "idx_runs_created" for idx in runs_indexes
                )
            except Exception:
                pass
            
            # Check molecules indexes
            try:
                molecules_indexes = inspector.get_indexes("molecules")
                indexes["idx_molecules_run"] = any(
                    idx["name"] == "idx_molecules_run" for idx in molecules_indexes
                )
                indexes["idx_molecules_score"] = any(
                    idx["name"] == "idx_molecules_score" for idx in molecules_indexes
                )
                indexes["idx_molecules_qed"] = any(
                    idx["name"] == "idx_molecules_qed" for idx in molecules_indexes
                )
            except Exception:
                pass
            
            # Check traces indexes
            try:
                traces_indexes = inspector.get_indexes("traces")
                indexes["idx_traces_run"] = any(
                    idx["name"] == "idx_traces_run" for idx in traces_indexes
                )
            except Exception:
                pass
            
            return indexes
        
        try:
            return await conn.run_sync(_get_indexes)
        except Exception:
            return {}


def print_separator(char="=", length=80):
    """Print separator line."""
    print(char * length)


async def main():
    """Main execution function."""
    print_separator()
    print("DATABASE INITIALIZATION")
    print_separator()
    
    # Step 1: Verify connection
    print("\n1. Verifying database connection...")
    if not await verify_connection():
        print("\n❌ Cannot connect to database.")
        print("\nPlease check:")
        print("  - PostgreSQL is running")
        print("  - DATABASE_URL is correct in .env")
        print("  - Database exists")
        return 1
    
    print("   ✅ Database connection successful")
    
    # Step 2: Check existing tables
    print("\n2. Checking existing tables...")
    tables_status = await check_tables()
    
    all_exist = all(tables_status.values())
    
    for table, exists in tables_status.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
    
    # Step 3: Create tables if needed
    if not all_exist:
        print("\n3. Creating missing tables...")
        try:
            await init_db()
            print("   ✅ Tables created successfully")
        except Exception as e:
            print(f"   ❌ Error creating tables: {str(e)}")
            return 1
    else:
        print("\n3. All tables already exist")
    
    # Step 4: Verify tables again
    print("\n4. Verifying table creation...")
    tables_status = await check_tables()
    
    for table, exists in tables_status.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
    
    if not all(tables_status.values()):
        print("\n❌ Some tables are missing!")
        return 1
    
    # Step 5: Check indexes
    print("\n5. Checking indexes...")
    indexes_status = await check_indexes()
    
    if indexes_status:
        for index, exists in indexes_status.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {index}")
    else:
        print("   ⚠️  Could not verify indexes")
    
    # Step 6: Show summary
    print_separator()
    print("SUMMARY")
    print_separator()
    
    print(f"\nDatabase URL: {engine.url}")
    print(f"Tables created: {len([t for t in tables_status.values() if t])}/3")
    
    if indexes_status:
        print(f"Indexes verified: {len([i for i in indexes_status.values() if i])}/{len(indexes_status)}")
    
    print("\n✅ Database initialization completed successfully!")
    print_separator()
    
    # Step 7: Show next steps
    print("\nNext steps:")
    print("  1. Run migrations: alembic upgrade head")
    print("  2. Verify in psql: psql -d molecule_discovery -c '\\dt'")
    print("  3. Run tests: pytest tests/integration/test_database.py")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)