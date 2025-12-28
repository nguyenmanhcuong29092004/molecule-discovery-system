"""
Unit Tests for Agent System

Tests for BaseAgent, PlannerAgent, GeneratorAgent, and RankerAgent.
"""

import pytest

from app.agents import (
    AgentExecutionError,
    AgentValidationError,
    BaseAgent,
    GeneratorAgent,
    PlannerAgent,
    RankerAgent,
)


# ✅ FIX: Đổi tên từ TestAgent thành MockAgent để pytest không nhầm lẫn
class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent functionality."""

    def __init__(self):
        super().__init__(name="MockAgent")
        self.execution_count = 0

    def _execute(self, input_data: dict) -> dict:
        self.execution_count += 1
        return {"result": "success", "input": input_data}


class FailingAgent(BaseAgent):
    """Agent that always fails for testing error handling."""

    def __init__(self):
        super().__init__(name="FailingAgent")

    def _execute(self, input_data: dict) -> dict:
        raise AgentExecutionError("Intentional failure")


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = MockAgent()
        assert agent.name == "MockAgent"

    def test_execute_success(self):
        """Test successful execution."""
        agent = MockAgent()
        result = agent.execute({"test": "data"})

        assert result["success"] is True
        assert result["output"]["result"] == "success"
        assert "duration_ms" in result
        assert result["duration_ms"] >= 0

    def test_execute_with_metadata(self):
        """Test execution with metadata."""
        agent = MockAgent()
        result = agent.execute({"test": "data"}, metadata={"round": 1})

        assert result["success"] is True
        assert result["output"]["result"] == "success"

    def test_execute_calls_internal_execute(self):
        """Test that execute calls _execute."""
        agent = MockAgent()
        agent.execute({"test": "data"})

        assert agent.execution_count == 1

    def test_validate_input_non_dict(self):
        """Test input validation rejects non-dict."""
        agent = MockAgent()
        result = agent.execute("not a dict")

        assert result["success"] is False
        assert "error" in result
        assert "dictionary" in result["error"].lower()

    def test_execute_handles_agent_error(self):
        """Test execution handles AgentExecutionError."""
        agent = FailingAgent()
        result = agent.execute({"test": "data"})

        assert result["success"] is False
        assert "error" in result
        assert "Intentional failure" in result["error"]
        assert result["error_type"] == "AgentExecutionError"

    def test_timing_is_recorded(self):
        """Test that execution time is recorded."""
        agent = MockAgent()
        result = agent.execute({"test": "data"})

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    def test_repr(self):
        """Test agent string representation."""
        agent = MockAgent()
        assert "MockAgent" in repr(agent)


class TestPlannerAgent:
    """Tests for PlannerAgent."""

    def test_planner_initialization(self):
        """Test planner can be initialized."""
        planner = PlannerAgent()
        assert planner.name == "PlannerAgent"

    def test_plan_with_minimal_input(self):
        """Test planner with minimal valid input."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Generate drug-like molecules for testing",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        assert result["success"] is True
        output = result["output"]

        assert "rounds" in output
        assert "candidates_per_round" in output
        assert "strategy" in output
        assert "reasoning" in output

    def test_plan_with_single_seed(self):
        """Test planner adjusts for single seed."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Generate diverse molecules",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        output = result["output"]
        # Single seed should result in more rounds
        assert output["rounds"] >= 5

    def test_plan_with_multiple_seeds(self):
        """Test planner with multiple seeds."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Generate molecules",
                "seed_smiles": ["CCO", "c1ccccc1", "CC(C)C", "CC(=O)O"],
                "constraints": {},
            }
        )

        output = result["output"]
        # Multiple seeds should result in fewer rounds
        assert output["rounds"] >= 1

    def test_plan_exploratory_objective(self):
        """Test planner with exploratory objective."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Explore diverse chemical space for novel compounds",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        output = result["output"]
        # Exploratory should increase candidates
        assert output["strategy"] == "diverse_exploration"
        assert output["candidates_per_round"] >= 75

    def test_plan_optimization_objective(self):
        """Test planner with optimization objective."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Optimize and improve existing molecules",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        output = result["output"]
        assert output["strategy"] == "focused_optimization"

    def test_plan_strict_constraints(self):
        """Test planner with strict constraints."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Generate molecules with strict rules",
                "seed_smiles": ["CCO"],
                "constraints": {"max_violations": 0},
            }
        )

        output = result["output"]
        # Strict constraints should increase candidates to compensate
        assert output["candidates_per_round"] > 50

    def test_plan_validation_missing_objective(self):
        """Test validation catches missing objective."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        assert result["success"] is False
        assert "objective" in result["error"].lower()

    def test_plan_validation_short_objective(self):
        """Test validation catches too short objective."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Short",
                "seed_smiles": ["CCO"],
                "constraints": {},
            }
        )

        assert result["success"] is False
        assert "objective" in result["error"].lower()

    def test_plan_validation_empty_seeds(self):
        """Test validation catches empty seed list."""
        planner = PlannerAgent()
        result = planner.execute(
            {
                "objective": "Generate molecules",
                "seed_smiles": [],
                "constraints": {},
            }
        )

        assert result["success"] is False
        assert "seed_smiles" in result["error"].lower()


class TestGeneratorAgent:
    """Tests for GeneratorAgent."""

    def test_generator_initialization(self):
        """Test generator can be initialized."""
        generator = GeneratorAgent()
        assert generator.name == "GeneratorAgent"

    def test_generate_with_mutation_strategy(self):
        """Test generation with mutation strategy."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["CCO"],
                "candidates_count": 10,
                "round_number": 1,
                "strategy": "mutation",
            }
        )

        assert result["success"] is True
        output = result["output"]

        assert "candidates" in output
        assert "unique_count" in output
        assert output["strategy_used"] == "mutation"

    def test_generate_with_functional_group_strategy(self):
        """Test generation with functional group strategy."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["c1ccccc1"],
                "candidates_count": 10,
                "round_number": 1,
                "strategy": "functional_group",
            }
        )

        assert result["success"] is True
        output = result["output"]

        assert "candidates" in output
        assert output["strategy_used"] == "functional_group"
        assert len(output["candidates"]) > 0

    def test_generate_with_hybrid_strategy(self):
        """Test generation with hybrid strategy."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["CCO", "c1ccccc1"],
                "candidates_count": 20,
                "round_number": 1,
                "strategy": "hybrid",
            }
        )

        assert result["success"] is True
        output = result["output"]

        assert "candidates" in output
        assert output["strategy_used"] == "hybrid"

    def test_generate_multiple_seeds(self):
        """Test generation with multiple seeds."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["CCO", "c1ccccc1", "CC(C)C"],
                "candidates_count": 30,
                "round_number": 1,
            }
        )

        assert result["success"] is True
        output = result["output"]

        assert len(output["candidates"]) > 0
        assert output["seed_count"] == 3

    def test_generate_filters_invalid(self):
        """Test that invalid molecules are filtered."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["CCO"],
                "candidates_count": 10,
                "round_number": 1,
            }
        )

        output = result["output"]
        # All candidates should be valid SMILES
        from app.chemistry.engine import ChemistryEngine

        for smiles in output["candidates"]:
            is_valid, _, _ = ChemistryEngine.validate_smiles(smiles)
            assert is_valid

    def test_generate_validation_missing_seeds(self):
        """Test validation catches missing seed_smiles."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "candidates_count": 10,
                "round_number": 1,
            }
        )

        assert result["success"] is False
        assert "seed_smiles" in result["error"].lower()

    def test_generate_validation_invalid_count(self):
        """Test validation catches invalid candidates_count."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["CCO"],
                "candidates_count": 0,
                "round_number": 1,
            }
        )

        assert result["success"] is False
        assert "candidates_count" in result["error"].lower()

    def test_generate_handles_invalid_seed(self):
        """Test generator handles invalid seed SMILES."""
        generator = GeneratorAgent()
        result = generator.execute(
            {
                "seed_smiles": ["INVALID_SMILES"],
                "candidates_count": 10,
                "round_number": 1,
            }
        )

        # Should fail because no valid seeds
        assert result["success"] is False


class TestRankerAgent:
    """Tests for RankerAgent."""

    def test_ranker_initialization(self):
        """Test ranker can be initialized."""
        ranker = RankerAgent()
        assert ranker.name == "RankerAgent"

    def test_rank_basic_sorting(self):
        """Test basic score-based ranking."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "CCO", "score": 0.5},
                    {"smiles": "c1ccccc1", "score": 0.8},
                    {"smiles": "CC(C)C", "score": 0.3},
                ],
                "top_k": 2,
            }
        )

        assert result["success"] is True
        output = result["output"]

        ranked = output["ranked_molecules"]
        assert len(ranked) == 2
        # Should be sorted by score descending
        assert ranked[0]["score"] == 0.8
        assert ranked[1]["score"] == 0.5

    def test_rank_with_min_score(self):
        """Test ranking with minimum score threshold."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "A", "score": 0.9},
                    {"smiles": "B", "score": 0.7},
                    {"smiles": "C", "score": 0.4},
                    {"smiles": "D", "score": 0.2},
                ],
                "top_k": 3,
                "min_score": 0.5,
            }
        )

        output = result["output"]
        ranked = output["ranked_molecules"]

        # Should only include scores >= 0.5
        assert len(ranked) == 2
        assert all(mol["score"] >= 0.5 for mol in ranked)

    def test_rank_with_diversity_filter(self):
        """Test ranking with diversity filtering."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "CCO", "score": 0.9},
                    {"smiles": "CCN", "score": 0.85},  # Similar to CCO
                    {"smiles": "c1ccccc1", "score": 0.7},  # Different
                    {"smiles": "CC(C)C", "score": 0.6},
                ],
                "top_k": 3,
                "diversity_filter": True,
            }
        )

        output = result["output"]
        ranked = output["ranked_molecules"]

        assert len(ranked) == 3
        assert output["diversity_applied"] is True

    def test_rank_top_k_larger_than_list(self):
        """Test ranking when top_k > available molecules."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "A", "score": 0.9},
                    {"smiles": "B", "score": 0.7},
                ],
                "top_k": 10,
            }
        )

        output = result["output"]
        # Should return all available molecules
        assert output["selected_count"] == 2

    def test_rank_calculates_avg_score(self):
        """Test that average score is calculated."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "A", "score": 0.8},
                    {"smiles": "B", "score": 0.6},
                    {"smiles": "C", "score": 0.4},
                ],
                "top_k": 2,
            }
        )

        output = result["output"]
        # Average of 0.8 and 0.6
        assert abs(output["avg_score"] - 0.7) < 0.001

    def test_rank_validation_missing_molecules(self):
        """Test validation catches missing molecules."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "top_k": 5,
            }
        )

        assert result["success"] is False
        assert "molecules" in result["error"].lower()

    def test_rank_validation_empty_molecules(self):
        """Test validation catches empty molecules list."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [],
                "top_k": 5,
            }
        )

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_rank_validation_missing_score(self):
        """Test validation catches molecule without score."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [
                    {"smiles": "CCO"},  # Missing score
                ],
                "top_k": 1,
            }
        )

        assert result["success"] is False
        assert "score" in result["error"].lower()

    def test_rank_validation_invalid_top_k(self):
        """Test validation catches invalid top_k."""
        ranker = RankerAgent()
        result = ranker.execute(
            {
                "molecules": [{"smiles": "A", "score": 0.5}],
                "top_k": 0,
            }
        )

        assert result["success"] is False
        assert "top_k" in result["error"].lower()