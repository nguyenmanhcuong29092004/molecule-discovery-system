"""
Planner Agent Module

Creates execution plans for molecule discovery runs based on
objectives, seed molecules, and constraints.
"""

import logging
from typing import Any, Dict, List

from app.agents.base import AgentValidationError, BaseAgent

# Configure logger
logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner Agent - Creates execution plans for molecule discovery.
    
    Analyzes the objective, seed molecules, and constraints to create
    an optimized execution plan including number of rounds, candidates
    per round, and generation strategy.
    
    Input:
        - objective: str - Run objective description
        - seed_smiles: List[str] - Seed molecules
        - constraints: dict - Molecular constraints
        - max_rounds: int (optional) - Maximum rounds allowed
        
    Output:
        - plan: dict containing:
            - rounds: int - Number of rounds
            - candidates_per_round: int - Molecules to generate per round
            - strategy: str - Generation strategy
            - reasoning: str - Explanation of plan
            
    Example:
        ```python
        planner = PlannerAgent()
        result = planner.execute({
            "objective": "Generate drug-like molecules",
            "seed_smiles": ["CCO", "c1ccccc1"],
            "constraints": {"max_violations": 1}
        })
        plan = result["output"]
        print(f"Rounds: {plan['rounds']}")
        ```
    """

    def __init__(self):
        """Initialize Planner Agent."""
        super().__init__(name="PlannerAgent")

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate planner input.
        
        Args:
            input_data: Input data containing objective, seed_smiles, constraints
            
        Raises:
            AgentValidationError: If validation fails
        """
        super().validate_input(input_data)

        # Check required fields
        required_fields = ["objective", "seed_smiles", "constraints"]
        for field in required_fields:
            if field not in input_data:
                raise AgentValidationError(f"Missing required field: {field}")

        # Validate objective
        objective = input_data["objective"]
        if not isinstance(objective, str) or len(objective) < 10:
            raise AgentValidationError(
                "Objective must be a string with at least 10 characters"
            )

        # Validate seed_smiles
        seed_smiles = input_data["seed_smiles"]
        if not isinstance(seed_smiles, list) or len(seed_smiles) == 0:
            raise AgentValidationError("seed_smiles must be a non-empty list")

        # Validate constraints
        constraints = input_data["constraints"]
        if not isinstance(constraints, dict):
            raise AgentValidationError("constraints must be a dictionary")

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create execution plan based on input parameters.
        
        Uses rule-based logic to determine optimal execution parameters:
        - Number of rounds based on seed count and complexity
        - Candidates per round based on exploration needs
        - Strategy based on objective keywords
        
        Args:
            input_data: Validated input data
            
        Returns:
            Execution plan dictionary
        """
        objective = input_data["objective"]
        seed_smiles = input_data["seed_smiles"]
        constraints = input_data["constraints"]
        max_rounds = input_data.get("max_rounds", 20)

        # Analyze objective for keywords
        objective_lower = objective.lower()
        is_exploratory = any(
            word in objective_lower
            for word in ["explore", "diverse", "novel", "discover"]
        )
        is_optimization = any(
            word in objective_lower for word in ["optimize", "improve", "refine"]
        )

        # Determine number of rounds
        seed_count = len(seed_smiles)
        if seed_count == 1:
            # Single seed - need more rounds for diversity
            rounds = min(7, max_rounds)
        elif seed_count <= 3:
            # Few seeds - moderate rounds
            rounds = min(5, max_rounds)
        else:
            # Many seeds - fewer rounds needed
            rounds = min(3, max_rounds)

        # Adjust based on objective
        if is_exploratory:
            rounds = min(rounds + 2, max_rounds)
        elif is_optimization:
            rounds = max(3, rounds - 1)

        # Determine candidates per round
        if is_exploratory:
            # Exploration - generate more candidates
            candidates_per_round = 100
        elif is_optimization:
            # Optimization - focused generation
            candidates_per_round = 50
        else:
            # Balanced approach
            candidates_per_round = 75

        # Adjust based on constraints strictness
        max_violations = constraints.get("max_violations", 1)
        if max_violations == 0:
            # Strict constraints - generate more to compensate
            candidates_per_round = int(candidates_per_round * 1.5)

        # Determine strategy
        if is_exploratory:
            strategy = "diverse_exploration"
        elif is_optimization:
            strategy = "focused_optimization"
        else:
            strategy = "balanced_discovery"

        # Create reasoning
        reasoning = self._create_reasoning(
            rounds, candidates_per_round, strategy, seed_count, is_exploratory, is_optimization
        )

        plan = {
            "rounds": rounds,
            "candidates_per_round": candidates_per_round,
            "strategy": strategy,
            "reasoning": reasoning,
            "seed_count": seed_count,
            "max_violations": max_violations,
        }

        logger.info(
            f"Created plan: {rounds} rounds, {candidates_per_round} candidates/round, "
            f"strategy={strategy}"
        )

        return plan

    def _create_reasoning(
        self,
        rounds: int,
        candidates: int,
        strategy: str,
        seed_count: int,
        is_exploratory: bool,
        is_optimization: bool,
    ) -> str:
        """
        Create human-readable reasoning for the plan.
        
        Args:
            rounds: Number of rounds
            candidates: Candidates per round
            strategy: Generation strategy
            seed_count: Number of seed molecules
            is_exploratory: Whether objective is exploratory
            is_optimization: Whether objective is optimization
            
        Returns:
            Reasoning string
        """
        reasons = []

        # Rounds reasoning
        if seed_count == 1:
            reasons.append(
                f"Using {rounds} rounds due to single seed molecule - "
                "more iterations needed for diversity"
            )
        elif seed_count <= 3:
            reasons.append(
                f"Using {rounds} rounds with {seed_count} seeds for "
                "balanced exploration"
            )
        else:
            reasons.append(
                f"Using {rounds} rounds - multiple seeds ({seed_count}) "
                "provide good initial diversity"
            )

        # Candidates reasoning
        if is_exploratory:
            reasons.append(
                f"Generating {candidates} candidates per round for "
                "extensive exploration"
            )
        elif is_optimization:
            reasons.append(
                f"Generating {candidates} candidates per round for "
                "focused optimization"
            )
        else:
            reasons.append(
                f"Generating {candidates} candidates per round for "
                "balanced discovery"
            )

        # Strategy reasoning
        strategy_descriptions = {
            "diverse_exploration": "Prioritizing diversity and novel chemical space",
            "focused_optimization": "Focusing on incremental improvements",
            "balanced_discovery": "Balancing exploration and optimization",
        }
        reasons.append(
            f"Strategy: {strategy_descriptions.get(strategy, strategy)}"
        )

        return ". ".join(reasons) + "."