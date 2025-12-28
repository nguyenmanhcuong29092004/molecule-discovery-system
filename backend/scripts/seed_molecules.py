#!/usr/bin/env python3
"""
Seed Molecules Script

Creates 10 test molecules for validating the chemistry engine.
Includes both drug-like and non-drug-like molecules for comprehensive testing.
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.chemistry.engine import ChemistryEngine, DEFAULT_CONSTRAINTS


# Test molecule dataset
TEST_MOLECULES = [
    {
        "name": "Ethanol",
        "smiles": "CCO",
        "description": "Simple alcohol, highly drug-like",
    },
    {
        "name": "Aspirin",
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "description": "Common pain reliever",
    },
    {
        "name": "Caffeine",
        "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "description": "Stimulant found in coffee",
    },
    {
        "name": "Ibuprofen",
        "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "description": "Anti-inflammatory drug",
    },
    {
        "name": "Benzene",
        "smiles": "c1ccccc1",
        "description": "Simple aromatic, low QED",
    },
    {
        "name": "Glucose",
        "smiles": "C(C1C(C(C(C(O1)O)O)O)O)O",
        "description": "Simple sugar, many HBD/HBA",
    },
    {
        "name": "Paracetamol",
        "smiles": "CC(=O)Nc1ccc(O)cc1",
        "description": "Common fever reducer",
    },
    {
        "name": "Cholesterol",
        "smiles": "CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C",
        "description": "Large lipid molecule, violates MW",
    },
    {
        "name": "Penicillin G",
        "smiles": "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O",
        "description": "Classic antibiotic",
    },
    {
        "name": "Octanol",
        "smiles": "CCCCCCCCCO",
        "description": "Long-chain alcohol, high LogP",
    },
]


def format_property_value(value):
    """Format property value for display"""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def main():
    """Main execution function"""
    print_separator()
    print("MOLECULE SEED DATA GENERATOR")
    print_separator()
    print(f"\nCreating {len(TEST_MOLECULES)} test molecules...\n")
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for idx, mol_data in enumerate(TEST_MOLECULES, 1):
        name = mol_data["name"]
        smiles = mol_data["smiles"]
        description = mol_data["description"]
        
        print(f"\n{idx}. {name}")
        print(f"   SMILES: {smiles}")
        print(f"   Description: {description}")
        
        # Validate SMILES
        is_valid, canonical, error = ChemistryEngine.validate_smiles(smiles)
        
        if not is_valid:
            print(f"   ❌ INVALID SMILES: {error}")
            failed_count += 1
            continue
        
        try:
            # Compute properties
            props = ChemistryEngine.compute_properties(canonical)
            
            # Apply screening
            screening_result = ChemistryEngine.apply_screening(
                props, 
                DEFAULT_CONSTRAINTS
            )
            
            # Calculate score
            score = ChemistryEngine.calculate_score(
                props["qed"],
                screening_result["num_violations"]
            )
            
            # Print properties
            print(f"\n   Properties:")
            print(f"   ├─ MW:         {format_property_value(props['mw'])} Da")
            print(f"   ├─ LogP:       {format_property_value(props['logp'])}")
            print(f"   ├─ HBD:        {props['hbd']}")
            print(f"   ├─ HBA:        {props['hba']}")
            print(f"   ├─ TPSA:       {format_property_value(props['tpsa'])} Ų")
            print(f"   ├─ Rot. Bonds: {props['rotatable_bonds']}")
            print(f"   └─ QED:        {format_property_value(props['qed'])}")
            
            # Print screening result
            print(f"\n   Screening:")
            
            if screening_result["passed"]:
                print(f"   ✅ PASS (0 violations)")
                passed_count += 1
            else:
                print(f"   ❌ FAIL ({screening_result['num_violations']} violations)")
                failed_count += 1
                
                # Show violations
                if screening_result["violations"]:
                    print(f"\n   Violations:")
                    for violation in screening_result["violations"]:
                        print(
                            f"   ├─ {violation['rule']}: "
                            f"{format_property_value(violation['value'])} "
                            f"> {violation['limit']}"
                        )
            
            print(f"\n   Score: {format_property_value(score)}")
            
            # Store result
            result = {
                "name": name,
                "smiles": canonical,
                "passed": screening_result["passed"],
                "qed": props["qed"],
                "score": score,
                "violations": screening_result["num_violations"],
            }
            results.append(result)
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed_count += 1
    
    # Summary
    print_separator()
    print("\nSUMMARY")
    print_separator()
    print(f"Total molecules:  {len(TEST_MOLECULES)}")
    print(f"Passed screening: {passed_count} ✅")
    print(f"Failed screening: {failed_count} ❌")
    print(f"Success rate:     {passed_count/len(TEST_MOLECULES)*100:.1f}%")
    
    # Top molecules by score
    if results:
        print("\n" + "=" * 80)
        print("TOP 5 MOLECULES BY SCORE")
        print("=" * 80)
        
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        
        for idx, result in enumerate(sorted_results[:5], 1):
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(
                f"\n{idx}. {result['name']:<20} "
                f"Score: {result['score']:.3f}  "
                f"QED: {result['qed']:.3f}  "
                f"{status}"
            )
            print(f"   {result['smiles']}")
    
    # Optional: Save to CSV
    try:
        import csv
        from datetime import datetime
        
        output_dir = backend_dir / "data" / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"seed_molecules_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['name', 'smiles', 'passed', 'qed', 'score', 'violations']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"\n✅ Results saved to: {csv_path}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save CSV: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Seed data generation completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()