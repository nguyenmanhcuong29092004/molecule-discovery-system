"""
Chemistry Engine Core Module

Provides core chemistry operations using RDKit including SMILES validation,
property calculation, screening, and scoring for drug-like molecules.
"""

import logging
from typing import Dict, List, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, QED, rdMolDescriptors

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MAX_SMILES_LENGTH = 500
MIN_SMILES_LENGTH = 1

# Default Lipinski Rule of Five constraints
DEFAULT_CONSTRAINTS = {
    "max_mw": 500,
    "max_logp": 5,
    "max_hbd": 5,
    "max_hba": 10,
    "max_tpsa": 140,
    "max_violations": 1,
}

# Default scoring penalty
DEFAULT_PENALTY = 0.1


class ChemistryEngine:
    """
    Core chemistry engine for molecular property calculation and screening.
    
    Provides static methods for:
    - SMILES validation and canonicalization
    - Molecular property computation (MW, LogP, HBD, HBA, TPSA, RotB, QED)
    - Rule-based screening (Lipinski-like rules)
    - Composite scoring
    """

    @staticmethod
    def validate_smiles(smiles: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and canonicalize a SMILES string.
        
        Checks if the SMILES string is valid, within length limits, and can be
        parsed by RDKit. Returns the canonical form if valid.
        
        Args:
            smiles: SMILES string to validate
            
        Returns:
            Tuple containing:
                - is_valid (bool): True if SMILES is valid
                - canonical_smiles (str | None): Canonicalized SMILES if valid
                - error_message (str | None): Error description if invalid
                
        Examples:
            >>> ChemistryEngine.validate_smiles("CCO")
            (True, "CCO", None)
            
            >>> ChemistryEngine.validate_smiles("INVALID")
            (False, None, "Invalid SMILES syntax")
        """
        # Check input is string
        if not isinstance(smiles, str):
            error_msg = f"SMILES must be a string, got {type(smiles).__name__}"
            logger.warning(f"SMILES validation failed: {error_msg}")
            return False, None, error_msg
        
        # Check length constraints
        if len(smiles) < MIN_SMILES_LENGTH or len(smiles) > MAX_SMILES_LENGTH:
            error_msg = f"SMILES length must be {MIN_SMILES_LENGTH}-{MAX_SMILES_LENGTH} characters"
            logger.warning(f"SMILES validation failed: {error_msg}, length={len(smiles)}")
            return False, None, error_msg
        
        # Try to parse with RDKit
        try:
            mol = Chem.MolFromSmiles(smiles)
            
            if mol is None:
                error_msg = "Invalid SMILES syntax"
                logger.warning(f"SMILES validation failed: {error_msg}, smiles='{smiles}'")
                return False, None, error_msg
            
            # Get canonical SMILES
            canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
            logger.debug(f"SMILES validated successfully: '{smiles}' -> '{canonical_smiles}'")
            
            return True, canonical_smiles, None
            
        except Exception as e:
            error_msg = f"RDKit error: {str(e)}"
            logger.error(f"SMILES validation failed with exception: {error_msg}", exc_info=True)
            return False, None, error_msg

    @staticmethod
    def compute_properties(smiles: str) -> Dict[str, float]:
        """
        Compute all molecular properties for a given SMILES string.
        
        Calculates seven key properties used in drug-likeness assessment:
        - MW: Molecular Weight (Da)
        - LogP: Partition coefficient (lipophilicity)
        - HBD: Hydrogen Bond Donors
        - HBA: Hydrogen Bond Acceptors
        - TPSA: Topological Polar Surface Area (Ų)
        - Rotatable Bonds: Number of rotatable bonds
        - QED: Quantitative Estimate of Drug-likeness (0-1)
        
        Args:
            smiles: Valid SMILES string
            
        Returns:
            Dictionary containing all computed properties
            
        Raises:
            ValueError: If SMILES is invalid or cannot be processed
            
        Examples:
            >>> props = ChemistryEngine.compute_properties("CCO")
            >>> round(props["mw"], 2)
            46.07
            >>> 0.0 <= props["qed"] <= 1.0
            True
        """
        # Validate SMILES first
        is_valid, canonical_smiles, error_msg = ChemistryEngine.validate_smiles(smiles)
        
        if not is_valid:
            raise ValueError(f"Invalid SMILES: {error_msg}")
        
        try:
            # Parse molecule
            mol = Chem.MolFromSmiles(canonical_smiles)
            
            if mol is None:
                raise ValueError(f"Failed to parse SMILES: {canonical_smiles}")
            
            # Compute all properties
            properties = {
                "mw": Descriptors.MolWt(mol),
                "logp": Descriptors.MolLogP(mol),
                "hbd": rdMolDescriptors.CalcNumHBD(mol),
                "hba": rdMolDescriptors.CalcNumHBA(mol),
                "tpsa": Descriptors.TPSA(mol),
                "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
                "qed": QED.qed(mol),
            }
            
            logger.debug(f"Properties computed for '{canonical_smiles}': {properties}")
            
            return properties
            
        except Exception as e:
            error_msg = f"Failed to compute properties for '{smiles}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    @staticmethod
    def apply_screening(properties: Dict[str, float], constraints: Dict[str, float]) -> Dict:
        """
        Apply rule-based screening to molecular properties.
        
        Evaluates molecule against Lipinski-like rules and determines if it passes
        based on the maximum allowed violations. Records all violations for analysis.
        
        Args:
            properties: Dictionary of molecular properties from compute_properties()
            constraints: Dictionary of threshold values:
                - max_mw: Maximum molecular weight
                - max_logp: Maximum LogP
                - max_hbd: Maximum hydrogen bond donors
                - max_hba: Maximum hydrogen bond acceptors
                - max_tpsa: Maximum topological polar surface area
                - max_violations: Maximum number of violations allowed
                
        Returns:
            Dictionary containing screening results:
                - passed (bool): True if molecule passes screening
                - violations (list): List of violations with rule, value, and limit
                - num_violations (int): Total number of violations
                
        Examples:
            >>> props = {"mw": 300, "logp": 2.5, "hbd": 2, "hba": 4, "tpsa": 80}
            >>> constraints = DEFAULT_CONSTRAINTS.copy()
            >>> result = ChemistryEngine.apply_screening(props, constraints)
            >>> result["passed"]
            True
            >>> result["num_violations"]
            0
        """
        violations = []
        
        # Define screening rules mapping
        rules = [
            ("MW", "mw", "max_mw"),
            ("LogP", "logp", "max_logp"),
            ("HBD", "hbd", "max_hbd"),
            ("HBA", "hba", "max_hba"),
            ("TPSA", "tpsa", "max_tpsa"),
        ]
        
        # Check each rule
        for rule_name, prop_key, constraint_key in rules:
            prop_value = properties.get(prop_key)
            max_value = constraints.get(constraint_key)
            
            if prop_value is None:
                logger.warning(f"Missing property '{prop_key}' in properties dict")
                continue
                
            if max_value is None:
                logger.warning(f"Missing constraint '{constraint_key}' in constraints dict")
                continue
            
            # Check if property violates constraint
            if prop_value > max_value:
                violation = {
                    "rule": rule_name,
                    "value": prop_value,
                    "limit": max_value,
                }
                violations.append(violation)
                logger.debug(f"Violation detected: {rule_name} = {prop_value} > {max_value}")
        
        # Determine if screening passed
        num_violations = len(violations)
        max_violations = constraints.get("max_violations", DEFAULT_CONSTRAINTS["max_violations"])
        passed = num_violations <= max_violations
        
        result = {
            "passed": passed,
            "violations": violations,
            "num_violations": num_violations,
        }
        
        logger.info(
            f"Screening result: {'PASS' if passed else 'FAIL'} "
            f"({num_violations} violations, max allowed: {max_violations})"
        )
        
        return result

    @staticmethod
    def calculate_score(
        qed: float, 
        num_violations: int, 
        penalty: float = DEFAULT_PENALTY
    ) -> float:
        """
        Calculate composite score for a molecule.
        
        Computes a score that balances drug-likeness (QED) against rule violations.
        Higher scores indicate better candidates. Score is always non-negative.
        
        Args:
            qed: QED score (0-1, higher is better)
            num_violations: Number of screening rule violations
            penalty: Penalty factor per violation (default: 0.1)
            
        Returns:
            Composite score (>= 0.0)
            
        Formula:
            score = max(0.0, qed - penalty × num_violations)
            
        Examples:
            >>> ChemistryEngine.calculate_score(0.8, 0)
            0.8
            
            >>> ChemistryEngine.calculate_score(0.8, 2, penalty=0.1)
            0.6
            
            >>> ChemistryEngine.calculate_score(0.3, 5, penalty=0.1)
            0.0
        """
        # Validate inputs
        if not 0.0 <= qed <= 1.0:
            logger.warning(f"QED score out of range [0, 1]: {qed}")
            qed = max(0.0, min(1.0, qed))  # Clamp to valid range
        
        if num_violations < 0:
            logger.warning(f"Negative violations count: {num_violations}, setting to 0")
            num_violations = 0
        
        if penalty < 0:
            logger.warning(f"Negative penalty: {penalty}, setting to 0")
            penalty = 0
        
        # Calculate score with penalty
        raw_score = qed - (penalty * num_violations)
        
        # Ensure non-negative
        score = max(0.0, raw_score)
        
        logger.debug(
            f"Score calculated: QED={qed:.3f}, violations={num_violations}, "
            f"penalty={penalty:.3f} → score={score:.3f}"
        )
        
        return score