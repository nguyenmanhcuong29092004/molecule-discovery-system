"""
Generator Agent Module

Generates candidate molecules using various transformation strategies
including mutations, fragment replacement, and scaffold hopping.
"""

import logging
import random
from typing import Any, Dict, List, Set

from app.agents.base import AgentExecutionError, AgentValidationError, BaseAgent
from app.chemistry.engine import ChemistryEngine
from app.chemistry.transforms import MoleculeTransformer

# Configure logger
logger = logging.getLogger(__name__)


class GeneratorAgent(BaseAgent):
    """
    Generator Agent - Generates candidate molecules.
    
    Creates new molecule candidates by applying various transformation
    strategies to seed molecules. Uses Chemistry Engine for validation
    and MoleculeTransformer for structural modifications.
    
    Strategies:
        - mutation: Atom replacements (C→N, F→Cl, etc.)
        - functional_group: Add functional groups
        - hybrid: Combination of strategies
        
    Input:
        - seed_smiles: List[str] - Starting molecules
        - candidates_count: int - Number of candidates to generate
        - round_number: int - Current round number
        - strategy: str (optional) - Generation strategy
        - diversity_threshold: float (optional) - Min similarity threshold
        
    Output:
        - candidates: List[str] - Generated SMILES
        - unique_count: int - Number of unique candidates
        - invalid_count: int - Number of invalid candidates
        - strategy_used: str - Strategy that was used
        
    Example:
        ```python
        generator = GeneratorAgent()
        result = generator.execute({
            "seed_smiles": ["CCO", "c1ccccc1"],
            "candidates_count": 50,
            "round_number": 1
        })
        candidates = result["output"]["candidates"]
        ```
    """

    def __init__(self):
        """Initialize Generator Agent."""
        super().__init__(name="GeneratorAgent")

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate generator input.
        
        Args:
            input_data: Input data
            
        Raises:
            AgentValidationError: If validation fails
        """
        super().validate_input(input_data)

        # Check required fields
        required_fields = ["seed_smiles", "candidates_count", "round_number"]
        for field in required_fields:
            if field not in input_data:
                raise AgentValidationError(f"Missing required field: {field}")

        # Validate seed_smiles
        seed_smiles = input_data["seed_smiles"]
        if not isinstance(seed_smiles, list) or len(seed_smiles) == 0:
            raise AgentValidationError("seed_smiles must be a non-empty list")

        # Validate candidates_count
        candidates_count = input_data["candidates_count"]
        if not isinstance(candidates_count, int) or candidates_count < 1:
            raise AgentValidationError("candidates_count must be a positive integer")

        # Validate round_number
        round_number = input_data["round_number"]
        if not isinstance(round_number, int) or round_number < 1:
            raise AgentValidationError("round_number must be a positive integer")

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate candidate molecules.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Generation results
            
        Raises:
            AgentExecutionError: If generation fails completely
        """
        seed_smiles = input_data["seed_smiles"]
        candidates_count = input_data["candidates_count"]
        round_number = input_data["round_number"]
        strategy = input_data.get("strategy", "hybrid")

        logger.info(
            f"Generating {candidates_count} candidates from {len(seed_smiles)} seeds "
            f"(round {round_number}, strategy={strategy})"
        )

        # Validate all seed SMILES
        valid_seeds = []
        for smiles in seed_smiles:
            is_valid, canonical, error = ChemistryEngine.validate_smiles(smiles)
            if is_valid:
                valid_seeds.append(canonical)
            else:
                logger.warning(f"Invalid seed SMILES '{smiles}': {error}")

        if not valid_seeds:
            raise AgentExecutionError("No valid seed SMILES provided")

        # Generate candidates based on strategy
        candidates: Set[str] = set()
        invalid_count = 0

        if strategy == "mutation":
            candidates, invalid = self._generate_by_mutation(
                valid_seeds, candidates_count
            )
            invalid_count = invalid
        elif strategy == "functional_group":
            candidates, invalid = self._generate_by_functional_groups(
                valid_seeds, candidates_count
            )
            invalid_count = invalid
        elif strategy == "hybrid":
            candidates, invalid = self._generate_hybrid(valid_seeds, candidates_count)
            invalid_count = invalid
        else:
            # Default to hybrid
            logger.warning(f"Unknown strategy '{strategy}', using hybrid")
            candidates, invalid = self._generate_hybrid(valid_seeds, candidates_count)
            invalid_count = invalid

        # Convert to list
        candidate_list = list(candidates)

        logger.info(
            f"Generated {len(candidate_list)} unique candidates "
            f"({invalid_count} invalid filtered out)"
        )

        return {
            "candidates": candidate_list,
            "unique_count": len(candidate_list),
            "invalid_count": invalid_count,
            "strategy_used": strategy,
            "seed_count": len(valid_seeds),
        }

    def _generate_by_mutation(
        self, seeds: List[str], target_count: int
    ) -> tuple[Set[str], int]:
        """
        Generate candidates using atom mutations.
        
        Args:
            seeds: Valid seed SMILES
            target_count: Target number of candidates
            
        Returns:
            Tuple of (unique_candidates, invalid_count)
        """
        candidates: Set[str] = set()
        invalid_count = 0
        attempts = 0
        max_attempts = target_count * 10  # Prevent infinite loops

        while len(candidates) < target_count and attempts < max_attempts:
            attempts += 1

            # Randomly select a seed
            seed = random.choice(seeds)

            # Generate mutations
            mutations_per_seed = max(1, target_count // len(seeds))
            try:
                mutations = MoleculeTransformer.mutate_atoms(seed, mutations_per_seed)

                for mutation in mutations:
                    # Validate mutation
                    is_valid, canonical, _ = ChemistryEngine.validate_smiles(mutation)
                    if is_valid and canonical not in seeds:
                        candidates.add(canonical)
                    else:
                        invalid_count += 1

                    if len(candidates) >= target_count:
                        break

            except Exception as e:
                logger.debug(f"Mutation failed for {seed}: {str(e)}")
                invalid_count += 1

        return candidates, invalid_count

    def _generate_by_functional_groups(
        self, seeds: List[str], target_count: int
    ) -> tuple[Set[str], int]:
        """
        Generate candidates by adding functional groups.
        
        Args:
            seeds: Valid seed SMILES
            target_count: Target number of candidates
            
        Returns:
            Tuple of (unique_candidates, invalid_count)
        """
        candidates: Set[str] = set()
        invalid_count = 0

        for seed in seeds:
            try:
                # Generate variants with functional groups
                variants = MoleculeTransformer.add_functional_group(seed)

                for variant in variants:
                    # Validate variant
                    is_valid, canonical, _ = ChemistryEngine.validate_smiles(variant)
                    if is_valid and canonical not in seeds:
                        candidates.add(canonical)
                    else:
                        invalid_count += 1

                    if len(candidates) >= target_count:
                        break

                if len(candidates) >= target_count:
                    break

            except Exception as e:
                logger.debug(f"Functional group addition failed for {seed}: {str(e)}")
                invalid_count += 1

        return candidates, invalid_count

    def _generate_hybrid(
        self, seeds: List[str], target_count: int
    ) -> tuple[Set[str], int]:
        """
        Generate candidates using hybrid strategy.
        
        Combines mutation and functional group addition for diverse results.
        
        Args:
            seeds: Valid seed SMILES
            target_count: Target number of candidates
            
        Returns:
            Tuple of (unique_candidates, invalid_count)
        """
        # Split target between strategies
        mutation_target = target_count // 2
        fg_target = target_count - mutation_target

        # Generate using mutations
        mutation_candidates, mutation_invalid = self._generate_by_mutation(
            seeds, mutation_target
        )

        # Generate using functional groups
        fg_candidates, fg_invalid = self._generate_by_functional_groups(
            seeds, fg_target
        )

        # Combine results
        all_candidates = mutation_candidates | fg_candidates
        total_invalid = mutation_invalid + fg_invalid

        # If we don't have enough, generate more mutations
        if len(all_candidates) < target_count:
            additional_needed = target_count - len(all_candidates)
            extra_candidates, extra_invalid = self._generate_by_mutation(
                seeds, additional_needed
            )
            all_candidates |= extra_candidates
            total_invalid += extra_invalid

        return all_candidates, total_invalid