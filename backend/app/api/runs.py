"""
Run Management API Endpoints

Provides REST API for creating and managing molecule discovery runs.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Run
from app.db.session import get_db
from app.models.run import RunCreate, RunResponse, RunStatus

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post(
    "",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new run",
    description="Create a new molecule discovery run with validated configuration.",
)
async def create_run(
    run_data: RunCreate,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Create a new molecule discovery run.
    
    The run is created with status='pending' and can be executed by workers.
    
    Validation includes:
    - Objective length (min 10 characters)
    - SMILES validity using Chemistry Engine
    - Parameter ranges (rounds, candidates, etc.)
    - Constraint values
    
    Args:
        run_data: Run configuration
        db: Database session
        
    Returns:
        RunResponse: Created run data
        
    Raises:
        HTTPException 422: If validation fails
        HTTPException 500: If database operation fails
    """
    try:
        # Create run with pending status
        run = Run(
            status=RunStatus.PENDING.value,
            objective=run_data.config.objective,
            config=run_data.config.model_dump(),
        )

        db.add(run)
        await db.commit()
        await db.refresh(run)

        logger.info(f"Created run {run.id} with status={run.status}")

        return RunResponse.model_validate(run)

    except Exception as e:
        logger.error(f"Failed to create run: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create run: {str(e)}",
        )


@router.get(
    "",
    response_model=List[RunResponse],
    summary="List runs",
    description="List all runs with optional filtering and pagination.",
)
async def list_runs(
    status_filter: Optional[RunStatus] = Query(
        None,
        alias="status",
        description="Filter by run status",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of runs to skip (pagination offset)",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of runs to return",
    ),
    db: AsyncSession = Depends(get_db),
) -> List[RunResponse]:
    """
    List all runs with filtering and pagination.
    
    Supports filtering by status and pagination using skip/limit.
    Results are ordered by creation time (newest first).
    
    Args:
        status_filter: Optional status filter
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session
        
    Returns:
        List[RunResponse]: List of runs
        
    Raises:
        HTTPException 500: If database query fails
    """
    try:
        # Build query
        query = select(Run)

        # Apply status filter if provided
        if status_filter:
            query = query.where(Run.status == status_filter.value)

        # Apply ordering (newest first)
        query = query.order_by(Run.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        runs = result.scalars().all()

        logger.info(
            f"Listed {len(runs)} runs (status={status_filter}, "
            f"skip={skip}, limit={limit})"
        )

        return [RunResponse.model_validate(run) for run in runs]

    except Exception as e:
        logger.error(f"Failed to list runs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list runs: {str(e)}",
        )


@router.get(
    "/{run_id}",
    response_model=RunResponse,
    summary="Get run details",
    description="Get detailed information about a specific run.",
)
async def get_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Get detailed information about a specific run.
    
    Args:
        run_id: Run identifier
        db: Database session
        
    Returns:
        RunResponse: Run data
        
    Raises:
        HTTPException 404: If run not found
        HTTPException 500: If database query fails
    """
    try:
        # Query run by ID
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()

        if run is None:
            logger.warning(f"Run {run_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found",
            )

        logger.info(f"Retrieved run {run_id}")

        return RunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get run: {str(e)}",
        )