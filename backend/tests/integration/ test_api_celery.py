"""
Integration Tests for API-Celery Connection

Tests that API endpoints correctly trigger and manage Celery tasks.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db import Run


class TestAPICeleryIntegration:
    """Tests for API-Celery integration."""

    @pytest.mark.asyncio
    async def test_create_run_triggers_task(self, client: AsyncClient, db_session):
        """Test that creating a run triggers a Celery task."""
        payload = {
            "config": {
                "objective": "Test Celery integration",
                "seed_smiles": ["CCO"],
                "rounds": 1,
                "candidates_per_round": 5,
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "run_id" in data
        assert "task_id" in data
        assert "status" in data
        assert "message" in data

        # Verify run was created with pending status
        assert data["status"] == "pending"
        assert "queued for execution" in data["message"]

        # Verify task ID exists
        assert data["task_id"] is not None
        assert len(data["task_id"]) > 0

        # Verify run exists in database
        run_id = data["run_id"]
        result = await db_session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()

        assert run is not None
        assert run.status == "pending"

    @pytest.mark.asyncio
    async def test_create_run_returns_immediately(self, client: AsyncClient):
        """Test that create_run returns immediately without waiting for workflow."""
        import time

        payload = {
            "config": {
                "objective": "Test immediate return",
                "seed_smiles": ["CCO"],
                "rounds": 2,
                "candidates_per_round": 10,
                "constraints": {},
            }
        }

        start_time = time.time()
        response = await client.post("/api/v1/runs", json=payload)
        elapsed_time = time.time() - start_time

        assert response.status_code == 201

        # API should return in less than 1 second
        # (workflow takes 2-3 minutes)
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_multiple_runs_queued(self, client: AsyncClient):
        """Test that multiple runs can be queued."""
        task_ids = []

        for i in range(3):
            payload = {
                "config": {
                    "objective": f"Test run {i + 1}",
                    "seed_smiles": ["CCO"],
                    "rounds": 1,
                    "candidates_per_round": 5,
                    "constraints": {},
                }
            }

            response = await client.post("/api/v1/runs", json=payload)
            assert response.status_code == 201

            data = response.json()
            task_ids.append(data["task_id"])

        # All tasks should have unique IDs
        assert len(set(task_ids)) == 3

    @pytest.mark.asyncio
    async def test_create_run_with_invalid_smiles(self, client: AsyncClient):
        """Test that invalid SMILES are caught before queueing task."""
        payload = {
            "config": {
                "objective": "Test with invalid SMILES",
                "seed_smiles": ["INVALID_SMILES"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        # Should fail validation (422) before task is queued
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_task_id_format(self, client: AsyncClient):
        """Test that task ID has valid format."""
        payload = {
            "config": {
                "objective": "Test task ID format",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)
        data = response.json()

        task_id = data["task_id"]

        # Task ID should be a non-empty string
        assert isinstance(task_id, str)
        assert len(task_id) > 0
        # Celery task IDs are typically UUIDs with hyphens
        assert "-" in task_id