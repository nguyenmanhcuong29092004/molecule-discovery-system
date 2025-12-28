"""
Ranker Agent Module

Selects top K molecules based on scores with optional diversity filtering.
"""

import logging
from typing import Any, Dict, List

from app.agents.base import AgentValidationError, BaseAgent

# Configure logger
logger = logging.getLogger(__name__)


class RankerAgent(BaseAgent):
    """
    Ranker Agent - Selects top K molecules.
    
    Ranks molecules by score and selects the top K candidates.
    Optionally ensures diversity by filtering out similar molecules.
    
    Input:
        - molecules: List[dict] - Molecules with scores
            Each dict must contain:
                - smiles: str
                - score: float
                - qed: float (optional)
                - passed_screening: bool (optional)
        - top_k: int - Number of molecules to select
        - diversity_filter: bool (optional) - Enable diversity filtering
        - min_score: float (optional) - Minimum score threshold
        
    Output:
        - ranked_molecules: List[dict] - Top K molecules
        - total_evaluated: int - Total molecules evaluated
        - selected_count: int - Number of molecules selected
        - avg_score: float - Average score of selected molecules
        
    Example:
        ```python
        ranker = RankerAgent()
        result = ranker.execute({
            "molecules": [
                {"smiles": "CCO", "score": 0.8},
                {"smiles": "c1ccccc1", "score": 0.6},
                {"smiles": "CC(C)C", "score": 0.9}
            ],
            "top_k": 2
        })
        top_molecules = result["output"]["ranked_molecules"]
        # → [{"smiles": "CC(C)C", "score": 0.9}, 
        #    {"smiles": "CCO", "score": 0.8}]
        ```
    """

    def __init__(self):
        """Initialize Ranker Agent."""
        super().__init__(name="RankerAgent")

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate ranker input.
        
        Args:
            input_data: Input data
            
        Raises:
            AgentValidationError: If validation fails
        """
        super().validate_input(input_data)

        # Check required fields
        required_fields = ["molecules", "top_k"]
        for field in required_fields:
            if field not in input_data:
                raise AgentValidationError(f"Missing required field: {field}")

        # Validate molecules
        molecules = input_data["molecules"]
        if not isinstance(molecules, list):
            raise AgentValidationError("molecules must be a list")

        if len(molecules) == 0:
            raise AgentValidationError("molecules list cannot be empty")

        # Validate molecule structure
        for idx, mol in enumerate(molecules):
            if not isinstance(mol, dict):
                raise AgentValidationError(
                    f"Molecule at index {idx} must be a dictionary"
                )

            if "smiles" not in mol:
                raise AgentValidationError(
                    f"Molecule at index {idx} missing 'smiles' field"
                )

            if "score" not in mol:
                raise AgentValidationError(
                    f"Molecule at index {idx} missing 'score' field"
                )

            # Validate score is numeric
            try:
                float(mol["score"])
            except (TypeError, ValueError):
                raise AgentValidationError(
                    f"Molecule at index {idx} has non-numeric score"
                )

        # Validate top_k
        top_k = input_data["top_k"]
        if not isinstance(top_k, int) or top_k < 1:
            raise AgentValidationError("top_k must be a positive integer")

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select top K molecules by score.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Ranking results
        """
        molecules = input_data["molecules"]
        top_k = input_data["top_k"]
        diversity_filter = input_data.get("diversity_filter", False)
        min_score = input_data.get("min_score", 0.0)

        logger.info(
            f"Ranking {len(molecules)} molecules, selecting top {top_k} "
            f"(diversity={diversity_filter}, min_score={min_score})"
        )

        # Filter by minimum score
        filtered_molecules = [
            mol for mol in molecules if float(mol["score"]) >= min_score
        ]

        logger.info(
            f"Filtered to {len(filtered_molecules)} molecules with score >= {min_score}"
        )

        if len(filtered_molecules) == 0:
            logger.warning("No molecules meet minimum score threshold")
            return {
                "ranked_molecules": [],
                "total_evaluated": len(molecules),
                "selected_count": 0,
                "avg_score": 0.0,
                "filtered_by_score": len(molecules),
            }

        # Sort by score (descending)
        sorted_molecules = sorted(
            filtered_molecules, key=lambda x: float(x["score"]), reverse=True
        )

        # Apply diversity filtering if requested
        if diversity_filter:
            selected_molecules = self._apply_diversity_filter(sorted_molecules, top_k)
        else:
            selected_molecules = sorted_molecules[:top_k]

        # Calculate statistics
        avg_score = (
            sum(float(mol["score"]) for mol in selected_molecules)
            / len(selected_molecules)
            if selected_molecules
            else 0.0
        )

        logger.info(
            f"Selected {len(selected_molecules)} molecules with avg score {avg_score:.3f}"
        )

        return {
            "ranked_molecules": selected_molecules,
            "total_evaluated": len(molecules),
            "selected_count": len(selected_molecules),
            "avg_score": avg_score,
            "filtered_by_score": len(molecules) - len(filtered_molecules),
            "diversity_applied": diversity_filter,
        }

    def _apply_diversity_filter(
        self, sorted_molecules: List[Dict], top_k: int
    ) -> List[Dict]:
        """
        Apply diversity filtering to select diverse molecules.
        
        Uses a simple greedy algorithm: always select the highest scoring
        molecule that is sufficiently different from already selected ones.
        
        For now, uses a simple structural diversity measure based on
        SMILES length and composition as a proxy. In production, would
        use molecular fingerprints and Tanimoto similarity.
        
        Args:
            sorted_molecules: Molecules sorted by score
            top_k: Number of molecules to select
            
        Returns:
            Diverse subset of molecules
        """
        if len(sorted_molecules) <= top_k:
            return sorted_molecules

        selected = []
        candidates = sorted_molecules.copy()

        # Always select the top-scoring molecule
        selected.append(candidates.pop(0))

        # Select remaining molecules ensuring diversity
        while len(selected) < top_k and candidates:
            # Find the most diverse candidate
            best_candidate = None
            best_diversity_score = -1

            for candidate in candidates:
                # Calculate diversity score (higher is more diverse)
                diversity_score = self._calculate_diversity_score(
                    candidate, selected
                )

                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                candidates.remove(best_candidate)
            else:
                break

        logger.info(
            f"Diversity filtering: selected {len(selected)} diverse molecules "
            f"from {len(sorted_molecules)} candidates"
        )

        return selected

    def _calculate_diversity_score(
        self, candidate: Dict, selected: List[Dict]
    ) -> float:
        """
        Calculate diversity score for a candidate.
        
        Simple diversity measure based on structural differences.
        Higher score means more diverse from selected molecules.
        
        Args:
            candidate: Candidate molecule
            selected: Already selected molecules
            
        Returns:
            Diversity score (higher is more diverse)
        """
        candidate_smiles = candidate["smiles"]

        # Calculate minimum distance to any selected molecule
        min_distance = float("inf")

        for selected_mol in selected:
            selected_smiles = selected_mol["smiles"]

            # Simple structural difference measures
            # (In production, use molecular fingerprints)

            # Length difference
            length_diff = abs(len(candidate_smiles) - len(selected_smiles))

            # Character composition difference
            candidate_chars = set(candidate_smiles)
            selected_chars = set(selected_smiles)
            char_diff = len(candidate_chars ^ selected_chars)

            # Combined distance
            distance = length_diff + char_diff * 2

            min_distance = min(min_distance, distance)

        return min_distance