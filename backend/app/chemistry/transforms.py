"""
Molecule Transformation Module

Provides methods for generating molecular variants through atom mutations
and functional group additions.
"""

import logging
import random
from typing import List, Set

from rdkit import Chem
from rdkit.Chem import AllChem

# Configure logger
logger = logging.getLogger(__name__)

# Atom mutation mappings
ATOM_MUTATIONS = {
    "C": ["N", "O"],
    "N": ["C", "O"],
    "O": ["N", "C"],
    "F": ["Cl", "Br"],
    "Cl": ["F", "Br"],
    "Br": ["F", "Cl"],
}

# Functional groups to add
FUNCTIONAL_GROUPS = {
    "methyl": "C",
    "ethyl": "CC",
    "hydroxyl": "O",
    "amino": "N",
    "fluoro": "F",
    "chloro": "Cl",
}


class MoleculeTransformer:
    """
    Transformer for generating molecular variants.
    
    Provides methods to create new molecule candidates by:
    - Mutating atoms (e.g., C → N, F → Cl)
    - Adding functional groups (e.g., methyl, hydroxyl)
    """

    @staticmethod
    def mutate_atoms(smiles: str, num_mutations: int = 1) -> List[str]:
        """
        Generate molecular variants by mutating atoms.
        
        Creates new molecules by replacing atoms with chemically similar alternatives.
        Uses random selection of mutable positions to ensure diversity.
        
        Supported mutations:
            C ↔ N, O
            N ↔ C, O
            O ↔ N, C
            F ↔ Cl, Br
            Cl ↔ F, Br
            Br ↔ F, Cl
        
        Args:
            smiles: Original SMILES string
            num_mutations: Number of variants to generate (default: 1)
            
        Returns:
            List of new SMILES strings (mutations)
            Returns empty list if no mutations possible
            
        Examples:
            >>> variants = MoleculeTransformer.mutate_atoms("CCO", num_mutations=2)
            >>> len(variants) <= 2
            True
            >>> all(v != "CCO" for v in variants)  # All should be different from input
            True
        """
        try:
            # Parse molecule
            mol = Chem.MolFromSmiles(smiles)
            
            if mol is None:
                logger.warning(f"Failed to parse SMILES for mutation: {smiles}")
                return []
            
            # Find mutable atoms
            mutable_positions = []
            
            for atom_idx, atom in enumerate(mol.GetAtoms()):
                atom_symbol = atom.GetSymbol()
                if atom_symbol in ATOM_MUTATIONS:
                    mutable_positions.append((atom_idx, atom_symbol))
            
            if not mutable_positions:
                logger.info(f"No mutable atoms found in: {smiles}")
                return []
            
            # Generate mutations
            mutations = []
            seen_smiles: Set[str] = {smiles}  # Track unique variants
            
            # Try to generate requested number of unique mutations
            max_attempts = num_mutations * 10  # Prevent infinite loops
            attempts = 0
            
            while len(mutations) < num_mutations and attempts < max_attempts:
                attempts += 1
                
                # Randomly select a mutable position
                atom_idx, original_symbol = random.choice(mutable_positions)
                
                # Randomly select a replacement atom
                possible_replacements = ATOM_MUTATIONS[original_symbol]
                new_symbol = random.choice(possible_replacements)
                
                # Create a copy of the molecule
                mol_copy = Chem.RWMol(mol)
                
                # Replace the atom
                atom = mol_copy.GetAtomWithIdx(atom_idx)
                atom.SetAtomicNum(Chem.GetPeriodicTable().GetAtomicNumber(new_symbol))
                
                # Sanitize and convert to SMILES
                try:
                    Chem.SanitizeMol(mol_copy)
                    new_smiles = Chem.MolToSmiles(mol_copy, canonical=True)
                    
                    # Only add if unique and different from original
                    if new_smiles not in seen_smiles and new_smiles != smiles:
                        mutations.append(new_smiles)
                        seen_smiles.add(new_smiles)
                        logger.debug(
                            f"Mutation created: {original_symbol}→{new_symbol} "
                            f"at position {atom_idx}: {smiles} → {new_smiles}"
                        )
                except Exception as e:
                    logger.debug(f"Sanitization failed for mutation: {str(e)}")
                    continue
            
            logger.info(
                f"Generated {len(mutations)} mutations from {smiles} "
                f"(requested: {num_mutations}, attempts: {attempts})"
            )
            
            return mutations
            
        except Exception as e:
            logger.error(f"Error during atom mutation: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def add_functional_group(smiles: str) -> List[str]:
        """
        Generate molecular variants by adding functional groups.
        
        Creates new molecules by attaching common functional groups at available
        positions on the molecule. Tests all possible attachment points for
        each functional group.
        
        Functional groups added:
            - Methyl (C)
            - Ethyl (CC)
            - Hydroxyl (O)
            - Amino (N)
            - Fluoro (F)
            - Chloro (Cl)
        
        Args:
            smiles: Original SMILES string
            
        Returns:
            List of new SMILES strings with added functional groups
            Returns empty list if no additions possible
            
        Examples:
            >>> variants = MoleculeTransformer.add_functional_group("c1ccccc1")
            >>> len(variants) > 0  # Should create multiple variants
            True
            >>> all(Chem.MolFromSmiles(v) is not None for v in variants)
            True
        """
        try:
            # Parse molecule
            mol = Chem.MolFromSmiles(smiles)
            
            if mol is None:
                logger.warning(f"Failed to parse SMILES for functional group addition: {smiles}")
                return []
            
            variants = []
            seen_smiles: Set[str] = {smiles}
            
            # Try adding each functional group
            for group_name, group_smiles in FUNCTIONAL_GROUPS.items():
                
                # Find atoms where we can add the group
                # Typically, we look for carbons with implicit hydrogens
                for atom_idx, atom in enumerate(mol.GetAtoms()):
                    # Check if atom can accept a substituent
                    # We focus on C, N atoms with available implicit hydrogens
                    if atom.GetSymbol() in ["C", "N"] and atom.GetTotalNumHs() > 0:
                        
                        try:
                            # Create editable copy
                            mol_copy = Chem.RWMol(mol)
                            
                            # Create functional group fragment
                            group_mol = Chem.MolFromSmiles(group_smiles)
                            
                            if group_mol is None:
                                continue
                            
                            # Combine molecules
                            combined = Chem.CombineMols(mol_copy, group_mol)
                            combined_rw = Chem.RWMol(combined)
                            
                            # Add bond between attachment point and functional group
                            # The functional group atoms start after the original molecule atoms
                            group_start_idx = mol.GetNumAtoms()
                            
                            # Add bond
                            combined_rw.AddBond(
                                atom_idx, 
                                group_start_idx, 
                                Chem.BondType.SINGLE
                            )
                            
                            # Sanitize
                            Chem.SanitizeMol(combined_rw)
                            
                            # Convert to SMILES
                            new_smiles = Chem.MolToSmiles(combined_rw, canonical=True)
                            
                            # Only add if unique
                            if new_smiles not in seen_smiles and new_smiles != smiles:
                                variants.append(new_smiles)
                                seen_smiles.add(new_smiles)
                                logger.debug(
                                    f"Added {group_name} at position {atom_idx}: "
                                    f"{smiles} → {new_smiles}"
                                )
                                
                        except Exception as e:
                            logger.debug(
                                f"Failed to add {group_name} at position {atom_idx}: {str(e)}"
                            )
                            continue
            
            logger.info(
                f"Generated {len(variants)} variants by adding functional groups to {smiles}"
            )
            
            return variants
            
        except Exception as e:
            logger.error(
                f"Error during functional group addition: {str(e)}", 
                exc_info=True
            )
            return []