"""
Celery Application Configuration

Configures Celery for asynchronous task execution.
"""

import os

from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get broker URL from environment
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
)

# Create Celery app
celery_app = Celery(
    "molecule_discovery",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.orchestrator"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_backend_transport_options={"master_name": "mymaster"},
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Optional: Task routes
celery_app.conf.task_routes = {
    "app.tasks.orchestrator.execute_run": {"queue": "discovery"},
}


if __name__ == "__main__":
    celery_app.start()