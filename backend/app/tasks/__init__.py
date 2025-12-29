"""
Tasks Package

Provides Celery tasks for asynchronous workflow execution.

Modules:
    - orchestrator: Main workflow orchestration task

Main Components:
    Celery Tasks:
        - execute_run: Main entry point for workflow execution
    
    Async Functions:
        - execute_run_async: Async workflow execution logic
        - mark_run_failed: Mark run as failed with error
        - log_trace: Log trace entries to database
    
    Exceptions:
        - WorkflowError: Workflow execution errors

Workflow Overview:
    1. Load run configuration from database
    2. Update status to "running"
    3. Create execution plan with PlannerAgent
    4. Execute rounds:
       - Generate candidates with GeneratorAgent
       - Validate and compute properties
       - Apply screening
       - Save molecules to database
       - Update run statistics
    5. Final ranking with RankerAgent
    6. Update status to "completed"

Usage:
    ```python
    from app.tasks import execute_run
    
    # Queue task for async execution
    task = execute_run.delay(str(run_id))
    
    # Get task ID
    print(f"Task ID: {task.id}")
    
    # Check task status
    result = task.get()
    ```

Task Configuration:
    - Task name: "execute_run"
    - Bound: True (self parameter for task instance)
    - Retry: Automatic retries on failure
    - Result backend: Stores task results

Monitoring:
    - All workflow steps are logged with structured logging
    - Trace entries saved to database for auditing
    - Run statistics updated in real-time
    - Error handling with automatic status updates
"""

# Import main task
from .orchestrator import execute_run

# Import async functions (for testing or direct use)
from .orchestrator import (
    execute_run_async,
    log_trace,
    mark_run_failed,
)

# Import exception
from .orchestrator import WorkflowError

# Define package version
__version__ = "1.0.0"

# Define public API
__all__ = [
    # Main Celery task
    "execute_run",
    
    # Async functions
    "execute_run_async",
    "log_trace",
    "mark_run_failed",
    
    # Exception
    "WorkflowError",
    
    # Version
    "__version__",
]