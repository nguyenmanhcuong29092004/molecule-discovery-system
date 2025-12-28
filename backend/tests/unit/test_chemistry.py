"""
Unit Tests for Chemistry Module

Tests for ChemistryEngine and MoleculeTransformer classes.
"""

import pytest
from rdkit import Chem

from app.chemistry.engine import (
    ChemistryEngine,
    DEFAULT_CONSTRAINTS,
    DEFAULT_PENALTY,
    MAX_SMILES_LENGTH,
)
from app.chemistry.transforms import MoleculeTransformer


class TestValidateSmiles:
    """Tests for ChemistryEngine.validate_smiles()"""

    def test_validate_valid_smiles_ethanol(self):
        """Test validation with valid ethanol SMILES"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("CCO")
        
        assert is_valid is True
        assert canonical == "CCO"
        assert error is None

    def test_validate_valid_smiles_benzene(self):
        """Test validation with valid benzene SMILES"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("c1ccccc1")
        
        assert is_valid is True
        assert canonical == "c1ccccc1"
        assert error is None

    def test_validate_valid_smiles_isobutane(self):
        """Test validation with valid isobutane SMILES"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("CC(C)C")
        
        assert is_valid is True
        assert canonical == "CC(C)C"
        assert error is None

    def test_validate_invalid_smiles_syntax(self):
        """Test validation with invalid SMILES syntax"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("INVALID")
        
        assert is_valid is False
        assert canonical is None
        assert "Invalid SMILES" in error

    def test_validate_invalid_smiles_unclosed_ring(self):
        """Test validation with unclosed ring"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("C(C")
        
        assert is_valid is False
        assert canonical is None
        assert error is not None

    def test_validate_empty_smiles(self):
        """Test validation with empty string"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles("")
        
        assert is_valid is False
        assert canonical is None
        assert "length" in error.lower()

    def test_validate_too_long_smiles(self):
        """Test validation with SMILES exceeding max length"""
        long_smiles = "C" * (MAX_SMILES_LENGTH + 1)
        is_valid, canonical, error = ChemistryEngine.validate_smiles(long_smiles)
        
        assert is_valid is False
        assert canonical is None
        assert "length" in error.lower()

    def test_validate_special_characters(self):
        """Test validation with special characters (triple bond, double bond)"""
        # Acetonitrile: C#N
        is_valid, canonical, error = ChemistryEngine.validate_smiles("C#N")
        assert is_valid is True
        
        # Formaldehyde: C=O
        is_valid, canonical, error = ChemistryEngine.validate_smiles("C=O")
        assert is_valid is True

    def test_validate_non_string_input(self):
        """Test validation with non-string input"""
        is_valid, canonical, error = ChemistryEngine.validate_smiles(123)
        
        assert is_valid is False
        assert canonical is None
        assert "string" in error.lower()


class TestComputeProperties:
    """Tests for ChemistryEngine.compute_properties()"""

    def test_compute_properties_ethanol(self):
        """Test property computation for ethanol"""
        props = ChemistryEngine.compute_properties("CCO")
        
        # Check all required properties are present
        assert "mw" in props
        assert "logp" in props
        assert "hbd" in props
        assert "hba" in props
        assert "tpsa" in props
        assert "rotatable_bonds" in props
        assert "qed" in props
        
        # Check ethanol properties (approximate values)
        assert 46.0 < props["mw"] < 47.0  # MW ≈ 46.07
        assert props["hbd"] == 1  # One -OH group
        assert props["hba"] == 1  # Oxygen can accept H-bond

    def test_compute_properties_benzene(self):
        """Test property computation for benzene"""
        props = ChemistryEngine.compute_properties("c1ccccc1")
        
        # Check benzene properties
        assert 78.0 < props["mw"] < 79.0  # MW ≈ 78.11
        assert props["hbd"] == 0  # No H-bond donors
        assert props["hba"] == 0  # No H-bond acceptors
        assert props["tpsa"] == 0.0  # No polar surface area
        assert props["rotatable_bonds"] == 0  # No rotatable bonds

    def test_compute_properties_qed_range(self):
        """Test that QED is always in [0, 1] range"""
        test_smiles = ["CCO", "c1ccccc1", "CC(C)C", "CC(=O)O"]
        
        for smiles in test_smiles:
            props = ChemistryEngine.compute_properties(smiles)
            assert 0.0 <= props["qed"] <= 1.0, f"QED out of range for {smiles}"

    def test_compute_properties_all_seven_present(self):
        """Test that all 7 required properties are returned"""
        props = ChemistryEngine.compute_properties("CCO")
        
        required_props = ["mw", "logp", "hbd", "hba", "tpsa", "rotatable_bonds", "qed"]
        
        for prop in required_props:
            assert prop in props, f"Missing property: {prop}"

    def test_compute_properties_invalid_smiles(self):
        """Test that invalid SMILES raises ValueError"""
        with pytest.raises(ValueError, match="Invalid SMILES"):
            ChemistryEngine.compute_properties("INVALID")

    def test_compute_properties_aspirin(self):
        """Test property computation for aspirin"""
        aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
        props = ChemistryEngine.compute_properties(aspirin_smiles)
        
        # Aspirin should have reasonable drug-like properties
        assert 180 < props["mw"] < 181  # MW ≈ 180.16
        assert props["hbd"] == 1  # One carboxylic acid -OH
        assert props["hba"] == 3  # Carbonyl oxygens + ester oxygens


class TestApplyScreening:
    """Tests for ChemistryEngine.apply_screening()"""

    def test_screening_pass_zero_violations(self):
        """Test screening with molecule passing all rules"""
        properties = {
            "mw": 300,
            "logp": 2.5,
            "hbd": 2,
            "hba": 4,
            "tpsa": 80,
        }
        
        result = ChemistryEngine.apply_screening(properties, DEFAULT_CONSTRAINTS)
        
        assert result["passed"] is True
        assert result["num_violations"] == 0
        assert len(result["violations"]) == 0

    def test_screening_fail_multiple_violations(self):
        """Test screening with molecule failing multiple rules"""
        properties = {
            "mw": 600,  # Exceeds 500
            "logp": 7,   # Exceeds 5
            "hbd": 2,
            "hba": 4,
            "tpsa": 80,
        }
        
        constraints = DEFAULT_CONSTRAINTS.copy()
        
        result = ChemistryEngine.apply_screening(properties, constraints)
        
        assert result["passed"] is False
        assert result["num_violations"] == 2
        assert len(result["violations"]) == 2
        
        # Check violations are properly recorded
        violation_rules = [v["rule"] for v in result["violations"]]
        assert "MW" in violation_rules
        assert "LogP" in violation_rules

    def test_screening_edge_case_exact_limit(self):
        """Test screening when value equals limit (should pass)"""
        properties = {
            "mw": 500,  # Exactly at limit
            "logp": 5,   # Exactly at limit
            "hbd": 5,
            "hba": 10,
            "tpsa": 140,
        }
        
        result = ChemistryEngine.apply_screening(properties, DEFAULT_CONSTRAINTS)
        
        # Should pass with 0 violations (≤ not <)
        assert result["passed"] is True
        assert result["num_violations"] == 0

    def test_screening_one_violation_allowed(self):
        """Test screening with max_violations = 1"""
        properties = {
            "mw": 550,  # Violates MW
            "logp": 3,
            "hbd": 2,
            "hba": 4,
            "tpsa": 80,
        }
        
        constraints = DEFAULT_CONSTRAINTS.copy()
        constraints["max_violations"] = 1
        
        result = ChemistryEngine.apply_screening(properties, constraints)
        
        assert result["passed"] is True  # 1 violation allowed
        assert result["num_violations"] == 1

    def test_screening_different_max_violations(self):
        """Test screening with different max_violations settings"""
        properties = {
            "mw": 600,
            "logp": 7,
            "hbd": 2,
            "hba": 4,
            "tpsa": 80,
        }
        
        # 2 violations present
        
        # Test with max_violations = 0
        constraints = DEFAULT_CONSTRAINTS.copy()
        constraints["max_violations"] = 0
        result = ChemistryEngine.apply_screening(properties, constraints)
        assert result["passed"] is False
        
        # Test with max_violations = 2
        constraints["max_violations"] = 2
        result = ChemistryEngine.apply_screening(properties, constraints)
        assert result["passed"] is True

    def test_screening_violation_details(self):
        """Test that violation details are correctly recorded"""
        properties = {
            "mw": 600,
            "logp": 3,
            "hbd": 2,
            "hba": 4,
            "tpsa": 80,
        }
        
        constraints = DEFAULT_CONSTRAINTS.copy()
        
        result = ChemistryEngine.apply_screening(properties, constraints)
        
        # Should have exactly 1 violation (MW)
        assert len(result["violations"]) == 1
        
        violation = result["violations"][0]
        assert violation["rule"] == "MW"
        assert violation["value"] == 600
        assert violation["limit"] == 500


class TestCalculateScore:
    """Tests for ChemistryEngine.calculate_score()"""

    def test_score_zero_violations(self):
        """Test scoring with zero violations"""
        score = ChemistryEngine.calculate_score(qed=0.8, num_violations=0)
        
        assert score == 0.8

    def test_score_with_violations(self):
        """Test scoring with violations (penalty applied)"""
        score = ChemistryEngine.calculate_score(
            qed=0.8, 
            num_violations=2, 
            penalty=0.1
        )
        
        expected = 0.8 - (0.1 * 2)
        assert abs(score - expected) < 1e-6

    def test_score_no_negative(self):
        """Test that score never goes negative"""
        score = ChemistryEngine.calculate_score(
            qed=0.3, 
            num_violations=5, 
            penalty=0.1
        )
        
        # 0.3 - 0.5 = -0.2, but should be clamped to 0.0
        assert score == 0.0

    def test_score_custom_penalty(self):
        """Test scoring with custom penalty factor"""
        score = ChemistryEngine.calculate_score(
            qed=0.9, 
            num_violations=3, 
            penalty=0.2
        )
        
        expected = 0.9 - (0.2 * 3)
        assert abs(score - expected) < 1e-6

    def test_score_default_penalty(self):
        """Test that default penalty is applied correctly"""
        score = ChemistryEngine.calculate_score(qed=0.7, num_violations=1)
        
        expected = 0.7 - (DEFAULT_PENALTY * 1)
        assert abs(score - expected) < 1e-6


class TestMutateAtoms:
    """Tests for MoleculeTransformer.mutate_atoms()"""

    def test_mutate_creates_valid_smiles(self):
        """Test that mutations produce valid SMILES"""
        mutations = MoleculeTransformer.mutate_atoms("CCO", num_mutations=3)
        
        # All mutations should be parseable by RDKit
        for smiles in mutations:
            mol = Chem.MolFromSmiles(smiles)
            assert mol is not None, f"Invalid mutation: {smiles}"

    def test_mutate_different_from_input(self):
        """Test that mutations are different from input"""
        input_smiles = "CCO"
        mutations = MoleculeTransformer.mutate_atoms(input_smiles, num_mutations=5)
        
        for smiles in mutations:
            assert smiles != input_smiles, "Mutation should differ from input"

    def test_mutate_respects_num_mutations(self):
        """Test that number of mutations is respected (up to limit)"""
        # Ethanol has limited mutation possibilities
        mutations = MoleculeTransformer.mutate_atoms("CCO", num_mutations=5)
        
        # Should create some mutations (may be less than requested if molecule is small)
        assert len(mutations) > 0
        assert len(mutations) <= 5

    def test_mutate_invalid_smiles(self):
        """Test mutation with invalid SMILES returns empty list"""
        mutations = MoleculeTransformer.mutate_atoms("INVALID", num_mutations=3)
        
        assert mutations == []

    def test_mutate_unique_variants(self):
        """Test that mutations are unique"""
        mutations = MoleculeTransformer.mutate_atoms("c1ccccc1", num_mutations=10)
        
        # All should be unique
        assert len(mutations) == len(set(mutations))


class TestAddFunctionalGroup:
    """Tests for MoleculeTransformer.add_functional_group()"""

    def test_add_functional_group_creates_variants(self):
        """Test that functional groups are added successfully"""
        variants = MoleculeTransformer.add_functional_group("c1ccccc1")
        
        # Benzene should allow multiple functional group additions
        assert len(variants) > 0

    def test_add_functional_group_all_valid(self):
        """Test that all variants with functional groups are valid"""
        variants = MoleculeTransformer.add_functional_group("c1ccccc1")
        
        for smiles in variants:
            mol = Chem.MolFromSmiles(smiles)
            assert mol is not None, f"Invalid variant: {smiles}"

    def test_add_functional_group_different_from_input(self):
        """Test that variants are different from input"""
        input_smiles = "c1ccccc1"
        variants = MoleculeTransformer.add_functional_group(input_smiles)
        
        for smiles in variants:
            assert smiles != input_smiles

    def test_add_functional_group_invalid_smiles(self):
        """Test functional group addition with invalid SMILES"""
        variants = MoleculeTransformer.add_functional_group("INVALID")
        
        assert variants == []

    def test_add_functional_group_ethanol(self):
        """Test functional group addition to ethanol"""
        variants = MoleculeTransformer.add_functional_group("CCO")
        
        # Should create at least some variants
        assert len(variants) > 0


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_full_workflow_ethanol(self):
        """Test complete workflow: validate → compute → screen → score"""
        smiles = "CCO"
        
        # Step 1: Validate
        is_valid, canonical, error = ChemistryEngine.validate_smiles(smiles)
        assert is_valid is True
        
        # Step 2: Compute properties
        props = ChemistryEngine.compute_properties(canonical)
        assert "qed" in props
        
        # Step 3: Screen
        result = ChemistryEngine.apply_screening(props, DEFAULT_CONSTRAINTS)
        assert "num_violations" in result
        
        # Step 4: Score
        score = ChemistryEngine.calculate_score(
            props["qed"], 
            result["num_violations"]
        )
        assert score >= 0.0

    def test_full_workflow_benzene(self):
        """Test complete workflow with benzene"""
        smiles = "c1ccccc1"
        
        # Validate
        is_valid, canonical, _ = ChemistryEngine.validate_smiles(smiles)
        assert is_valid
        
        # Compute
        props = ChemistryEngine.compute_properties(canonical)
        
        # Screen
        result = ChemistryEngine.apply_screening(props, DEFAULT_CONSTRAINTS)
        
        # Benzene should pass (small, simple molecule)
        assert result["passed"] is True
        
        # Score
        score = ChemistryEngine.calculate_score(
            props["qed"],
            result["num_violations"]
        )
        assert 0.0 <= score <= 1.0