"""
Integration Tests for Run API

Tests all Run API endpoints with various scenarios.
"""

import pytest
from httpx import AsyncClient


class TestCreateRun:
    """Tests for POST /api/v1/runs endpoint."""

    @pytest.mark.asyncio
    async def test_create_run_success(self, client: AsyncClient):
        """Test creating a run with valid configuration."""
        payload = {
            "config": {
                "objective": "Generate drug-like molecules for testing",
                "seed_smiles": ["CCO", "c1ccccc1"],
                "rounds": 3,
                "candidates_per_round": 50,
                "top_k": 10,
                "constraints": {
                    "max_mw": 500,
                    "max_logp": 5,
                    "max_violations": 1,
                },
                "diversity_threshold": 0.7,
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["status"] == "pending"
        assert data["config"]["objective"] == payload["config"]["objective"]
        assert data["total_generated"] == 0
        assert data["total_valid"] == 0
        assert data["total_passed"] == 0
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_run_minimal_config(self, client: AsyncClient):
        """Test creating run with minimal required fields."""
        payload = {
            "config": {
                "objective": "Minimal test configuration run",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify defaults were applied
        assert data["config"]["rounds"] == 5  # Default
        assert data["config"]["candidates_per_round"] == 50  # Default
        assert data["config"]["top_k"] == 10  # Default

    @pytest.mark.asyncio
    async def test_create_run_invalid_smiles(self, client: AsyncClient):
        """Test validation with invalid SMILES."""
        payload = {
            "config": {
                "objective": "Test with invalid SMILES",
                "seed_smiles": ["INVALID_SMILES", "ANOTHER_BAD"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_run_mixed_valid_invalid_smiles(self, client: AsyncClient):
        """Test with mix of valid and invalid SMILES."""
        payload = {
            "config": {
                "objective": "Test with mixed SMILES validity",
                "seed_smiles": ["CCO", "INVALID", "c1ccccc1"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        # Should fail because one SMILES is invalid
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_objective_too_short(self, client: AsyncClient):
        """Test validation with too short objective."""
        payload = {
            "config": {
                "objective": "Short",  # Less than 10 characters
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_no_seed_smiles(self, client: AsyncClient):
        """Test validation with empty seed_smiles."""
        payload = {
            "config": {
                "objective": "Test with no seeds",
                "seed_smiles": [],
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_too_many_seeds(self, client: AsyncClient):
        """Test validation with more than 10 seed SMILES."""
        payload = {
            "config": {
                "objective": "Test with too many seeds",
                "seed_smiles": ["C"] * 11,  # 11 SMILES
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_invalid_rounds(self, client: AsyncClient):
        """Test validation with invalid rounds value."""
        payload = {
            "config": {
                "objective": "Test with invalid rounds",
                "seed_smiles": ["CCO"],
                "rounds": 0,  # Must be >= 1
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_invalid_candidates(self, client: AsyncClient):
        """Test validation with invalid candidates_per_round."""
        payload = {
            "config": {
                "objective": "Test with invalid candidates",
                "seed_smiles": ["CCO"],
                "candidates_per_round": 5,  # Must be >= 10
                "constraints": {},
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_run_custom_constraints(self, client: AsyncClient):
        """Test creating run with custom constraint values."""
        payload = {
            "config": {
                "objective": "Test with custom constraints",
                "seed_smiles": ["CCO"],
                "constraints": {
                    "max_mw": 400,
                    "max_logp": 4,
                    "max_hbd": 3,
                    "max_hba": 8,
                    "max_tpsa": 120,
                    "max_violations": 0,
                },
            }
        }

        response = await client.post("/api/v1/runs", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["config"]["constraints"]["max_mw"] == 400


class TestListRuns:
    """Tests for GET /api/v1/runs endpoint."""

    @pytest.mark.asyncio
    async def test_list_runs_empty(self, client: AsyncClient):
        """Test listing runs when database is empty."""
        response = await client.get("/api/v1/runs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_runs_with_data(self, client: AsyncClient):
        """Test listing runs after creating some."""
        # Create multiple runs
        for i in range(3):
            payload = {
                "config": {
                    "objective": f"Test run number {i + 1} for listing",
                    "seed_smiles": ["CCO"],
                    "constraints": {},
                }
            }
            await client.post("/api/v1/runs", json=payload)

        # List runs
        response = await client.get("/api/v1/runs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Verify newest first (by default)
        assert "Test run number 3" in data[0]["config"]["objective"]

    @pytest.mark.asyncio
    async def test_list_runs_pagination(self, client: AsyncClient):
        """Test pagination with skip and limit."""
        # Create 5 runs
        for i in range(5):
            payload = {
                "config": {
                    "objective": f"Pagination test run {i + 1}",
                    "seed_smiles": ["CCO"],
                    "constraints": {},
                }
            }
            await client.post("/api/v1/runs", json=payload)

        # Get first page (limit=2)
        response = await client.get("/api/v1/runs?limit=2")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1) == 2

        # Get second page (skip=2, limit=2)
        response = await client.get("/api/v1/runs?skip=2&limit=2")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2) == 2

        # Verify different runs
        assert page1[0]["id"] != page2[0]["id"]

    @pytest.mark.asyncio
    async def test_list_runs_filter_by_status(self, client: AsyncClient):
        """Test filtering by status."""
        # Create run with pending status
        payload = {
            "config": {
                "objective": "Pending status test run",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        }
        await client.post("/api/v1/runs", json=payload)

        # Filter by pending status
        response = await client.get("/api/v1/runs?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(run["status"] == "pending" for run in data)

    @pytest.mark.asyncio
    async def test_list_runs_invalid_status(self, client: AsyncClient):
        """Test filtering with invalid status value."""
        response = await client.get("/api/v1/runs?status=invalid_status")

        # Should return 422 for invalid enum value
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_runs_max_limit(self, client: AsyncClient):
        """Test that limit cannot exceed 100."""
        response = await client.get("/api/v1/runs?limit=150")

        # Should fail validation
        assert response.status_code == 422


class TestGetRun:
    """Tests for GET /api/v1/runs/{run_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_run_success(self, client: AsyncClient):
        """Test getting a specific run."""
        # Create a run
        payload = {
            "config": {
                "objective": "Test run for retrieval",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        }
        create_response = await client.post("/api/v1/runs", json=payload)
        created_run = create_response.json()
        run_id = created_run["id"]

        # Get the run
        response = await client.get(f"/api/v1/runs/{run_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["config"]["objective"] == payload["config"]["objective"]

    @pytest.mark.asyncio
    async def test_get_run_not_found(self, client: AsyncClient):
        """Test getting non-existent run."""
        # Use a valid UUID that doesn't exist
        fake_id = "123e4567-e89b-12d3-a456-426614174000"

        response = await client.get(f"/api/v1/runs/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_run_invalid_uuid(self, client: AsyncClient):
        """Test getting run with invalid UUID format."""
        response = await client.get("/api/v1/runs/not-a-uuid")

        assert response.status_code == 422


class TestAPIHealth:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"