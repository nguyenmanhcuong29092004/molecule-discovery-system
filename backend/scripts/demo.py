#!/usr/bin/env python3
"""
Chemistry Engine Demo

Demonstrates all features of the Chemistry Engine Core module.
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.chemistry import ChemistryEngine, MoleculeTransformer, DEFAULT_CONSTRAINTS


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + "\n")


def demo_validation():
    """Demo SMILES validation"""
    print_header("1. SMILES VALIDATION")
    
    test_cases = [
        ("CCO", "Ethanol - valid"),
        ("c1ccccc1", "Benzene - valid"),
        ("INVALID", "Invalid syntax"),
        ("", "Empty string"),
    ]
    
    for smiles, description in test_cases:
        is_valid, canonical, error = ChemistryEngine.validate_smiles(smiles)
        
        print(f"Input: '{smiles}' ({description})")
        print(f"  Valid: {is_valid}")
        if canonical:
            print(f"  Canonical: {canonical}")
        if error:
            print(f"  Error: {error}")
        print()


def demo_properties():
    """Demo property calculation"""
    print_header("2. PROPERTY CALCULATION")
    
    molecules = [
        ("CCO", "Ethanol"),
        ("c1ccccc1", "Benzene"),
        ("CC(=O)Oc1ccccc1C(=O)O", "Aspirin"),
    ]
    
    for smiles, name in molecules:
        print(f"{name} ({smiles}):")
        
        try:
            props = ChemistryEngine.compute_properties(smiles)
            
            print(f"  MW:             {props['mw']:.2f} Da")
            print(f"  LogP:           {props['logp']:.2f}")
            print(f"  HBD:            {props['hbd']}")
            print(f"  HBA:            {props['hba']}")
            print(f"  TPSA:           {props['tpsa']:.2f} Ų")
            print(f"  Rotatable Bonds: {props['rotatable_bonds']}")
            print(f"  QED:            {props['qed']:.3f}")
            print()
            
        except Exception as e:
            print(f"  Error: {str(e)}\n")


def demo_screening():
    """Demo screening with rules"""
    print_header("3. RULE-BASED SCREENING")
    
    # Good molecule
    print("Example 1: Drug-like molecule (Ethanol)")
    props = ChemistryEngine.compute_properties("CCO")
    result = ChemistryEngine.apply_screening(props, DEFAULT_CONSTRAINTS)
    
    print(f"  MW:   {props['mw']:.2f} (limit: {DEFAULT_CONSTRAINTS['max_mw']})")
    print(f"  LogP: {props['logp']:.2f} (limit: {DEFAULT_CONSTRAINTS['max_logp']})")
    print(f"  Result: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"  Violations: {result['num_violations']}")
    print()
    
    # Molecule with violations
    print("Example 2: Molecule with violations (Large molecule)")
    large_smiles = "CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C"
    props = ChemistryEngine.compute_properties(large_smiles)
    result = ChemistryEngine.apply_screening(props, DEFAULT_CONSTRAINTS)
    
    print(f"  MW:   {props['mw']:.2f} (limit: {DEFAULT_CONSTRAINTS['max_mw']})")
    print(f"  LogP: {props['logp']:.2f} (limit: {DEFAULT_CONSTRAINTS['max_logp']})")
    print(f"  Result: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"  Violations: {result['num_violations']}")
    
    if result['violations']:
        print("  Violation details:")
        for v in result['violations']:
            print(f"    - {v['rule']}: {v['value']:.2f} > {v['limit']}")
    print()


def demo_scoring():
    """Demo composite scoring"""
    print_header("4. COMPOSITE SCORING")
    
    examples = [
        (0.9, 0, "Perfect molecule"),
        (0.8, 1, "One violation"),
        (0.5, 3, "Multiple violations"),
        (0.2, 5, "Many violations (score floored at 0)"),
    ]
    
    for qed, violations, description in examples:
        score = ChemistryEngine.calculate_score(qed, violations, penalty=0.1)
        
        print(f"{description}:")
        print(f"  QED:        {qed:.2f}")
        print(f"  Violations: {violations}")
        print(f"  Score:      {score:.2f}")
        print(f"  Formula:    max(0, {qed:.2f} - 0.1 × {violations})")
        print()


def demo_mutations():
    """Demo atom mutations"""
    print_header("5. ATOM MUTATIONS")
    
    smiles = "CCO"
    print(f"Original: {smiles} (Ethanol)")
    print(f"Generating 5 mutations...\n")
    
    mutations = MoleculeTransformer.mutate_atoms(smiles, num_mutations=5)
    
    if mutations:
        for idx, mut in enumerate(mutations, 1):
            # Validate
            is_valid, _, _ = ChemistryEngine.validate_smiles(mut)
            
            # Check if different
            different = mut != smiles
            
            print(f"  {idx}. {mut}")
            print(f"     Valid: {is_valid}, Different: {different}")
    else:
        print("  No mutations generated")
    print()


def demo_functional_groups():
    """Demo functional group addition"""
    print_header("6. FUNCTIONAL GROUP ADDITION")
    
    smiles = "c1ccccc1"
    print(f"Original: {smiles} (Benzene)")
    print(f"Adding functional groups...\n")
    
    variants = MoleculeTransformer.add_functional_group(smiles)
    
    if variants:
        print(f"Generated {len(variants)} variants:")
        
        # Show first 5
        for idx, variant in enumerate(variants[:5], 1):
            is_valid, _, _ = ChemistryEngine.validate_smiles(variant)
            print(f"  {idx}. {variant} (Valid: {is_valid})")
        
        if len(variants) > 5:
            print(f"  ... and {len(variants) - 5} more")
    else:
        print("  No variants generated")
    print()


def demo_full_workflow():
    """Demo complete workflow"""
    print_header("7. COMPLETE WORKFLOW")
    
    smiles = "CC(=O)Oc1ccccc1C(=O)O"
    print(f"Analyzing Aspirin: {smiles}\n")
    
    # Step 1: Validate
    print("Step 1: Validate SMILES")
    is_valid, canonical, error = ChemistryEngine.validate_smiles(smiles)
    print(f"  Valid: {is_valid}")
    print(f"  Canonical: {canonical}\n")
    
    if not is_valid:
        print(f"  Error: {error}")
        return
    
    # Step 2: Compute properties
    print("Step 2: Compute Properties")
    props = ChemistryEngine.compute_properties(canonical)
    print(f"  MW:   {props['mw']:.2f} Da")
    print(f"  LogP: {props['logp']:.2f}")
    print(f"  QED:  {props['qed']:.3f}\n")
    
    # Step 3: Screen
    print("Step 3: Apply Screening")
    result = ChemistryEngine.apply_screening(props, DEFAULT_CONSTRAINTS)
    print(f"  Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"  Violations: {result['num_violations']}\n")
    
    # Step 4: Score
    print("Step 4: Calculate Score")
    score = ChemistryEngine.calculate_score(
        props['qed'],
        result['num_violations']
    )
    print(f"  Final Score: {score:.3f}")
    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print(" CHEMISTRY ENGINE CORE - COMPREHENSIVE DEMO")
    print("=" * 80)
    
    try:
        demo_validation()
        demo_properties()
        demo_screening()
        demo_scoring()
        demo_mutations()
        demo_functional_groups()
        demo_full_workflow()
        
        print("=" * 80)
        print(" ✅ Demo completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()