"""Utility functions for working with qcio objects."""

import json
from collections import Counter
from typing import List, Tuple, Union

import numpy as np
from pydantic import BaseModel

from .constants import ANGSTROM_TO_BOHR
from .models import Structure
from .models.utils import _assert_module_installed

# Helper Structures
water = Structure(
    symbols=["O", "H", "H"],
    geometry=np.array(
        [
            [0.0253397, 0.01939466, -0.00696322],
            [0.22889176, 1.84438441, 0.16251426],
            [1.41760224, -0.62610794, -1.02954938],
        ]
    ),
    charge=0,
    multiplicity=1,
    connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
    identifiers={"name": "water"},
)


def json_dumps(obj: Union[BaseModel, List[BaseModel]]) -> str:
    """Serialization helper for lists of pydantic objects."""
    if isinstance(obj, list):
        return json.dumps([o.model_dump() for o in obj])
    return obj.model_dump_json()


def _rdkit_mol_from_structure(
    struct: Structure,
) -> "rdkit.Chem.Mol":  # type: ignore # noqa: F821
    """Create an RDKit molecule from a Structure object."""
    _assert_module_installed("rdkit")
    from rdkit import Chem

    # Create RDKit molecule
    mol = Chem.MolFromXYZBlock(struct.to_xyz())  # type: ignore

    if mol is None:
        raise ValueError("Failed create rdkit Molecule from xyz string.")

    # Ensure molecule has conformers
    if mol.GetNumConformers() == 0:
        raise ValueError("Molecule lacks 3D coordinates.")

    return mol


def rmsd(
    struct1: Structure, struct2: Structure, align: bool = True, numthreads: int = 1
) -> float:
    """
    Calculate the root mean square deviation between two structures in Angstrom.

    Args:
        struct1: The first structure.
        struct2: The second structure.
        align: Whether to align the structures before calculating the RMSD including
            atom renumbering. If True, rdkit will compute the optimal alignment of the
            two structures before calculating the RMSD. If False, the RMSD will be
            calculated without alignment.
        numthreads: The number of threads to use for the RMSD calculation. Applies only
            to the alignment step if `align=True`.


    Returns:
        The RMSD between the two structures in Angstroms.
    """
    _assert_module_installed("rdkit")
    from rdkit.Chem import rdDetermineBonds, rdMolAlign

    # Create RDKit molecules
    mol1 = _rdkit_mol_from_structure(struct1)
    mol2 = _rdkit_mol_from_structure(struct2)

    # Determine connectivity
    rdDetermineBonds.DetermineConnectivity(mol1, charge=struct1.charge)
    rdDetermineBonds.DetermineConnectivity(mol2, charge=struct2.charge)

    # Compute RMSD
    if align:
        rmsd = rdMolAlign.GetBestRMS(mol2, mol1, numThreads=numthreads)
    else:
        rmsd = rdMolAlign.CalcRMS(mol2, mol1)

    return rmsd


def align(
    struct: Structure, refstruct: Structure, reorder_atoms: bool = True
) -> Tuple[Structure, float]:
    """Return a new structure that is optimally aligned to the reference structure.

    Args:
        struct: The structure to align.
        refstruct: The reference structure.
        reorder_atoms: Reorder the atoms to match the reference structure. If False,
            the atoms will be aligned without changing their order.

    Returns:
        Tuple of the aligned structure and the RMSD in Angstroms.
    """
    _assert_module_installed("rdkit")
    from rdkit.Chem import rdDetermineBonds, rdMolAlign

    # Create RDKit molecules
    mol = _rdkit_mol_from_structure(struct)
    refmol = _rdkit_mol_from_structure(refstruct)

    # Determine connectivity
    rdDetermineBonds.DetermineConnectivity(mol, charge=struct.charge)
    rdDetermineBonds.DetermineConnectivity(refmol, charge=refstruct.charge)

    # Compute RMSD and align mol to refmol
    if reorder_atoms:
        rmsd, trnsfm_matrix, atm_map = rdMolAlign.GetBestAlignmentTransform(mol, refmol)  # type: ignore # noqa: E501
    else:
        rmsd, trnsfm_matrix = rdMolAlign.GetAlignmentTransform(mol, refmol)

    # Convert to homogeneous coordinates in Angstroms
    coords_homogeneous = np.hstack(
        [struct.geometry_angstrom, np.ones((struct.geometry.shape[0], 1))]
    )

    # Apply the transformation matrix
    transformed_coords_homogeneous = coords_homogeneous @ trnsfm_matrix.T

    # Extract the transformed 3D coordinates and convert to Bohr
    transformed_coords = transformed_coords_homogeneous[:, :3] * ANGSTROM_TO_BOHR

    # Reorder the atoms to match the reference structure
    if reorder_atoms:
        if Counter(struct.symbols) != Counter(refstruct.symbols):
            raise ValueError(
                "Structures must have the same number and type of atoms for "
                "`reorder_atoms=True` at this time. Pass "
                "`reorder_atoms=False` to align structures with different atom "
                "counts."
            )
        symbols = refstruct.symbols
        geometry = np.zeros((len(atm_map), 3))

        for probe_idx, ref_idx in atm_map:
            geometry[ref_idx] = transformed_coords[probe_idx]  # works

    # Otherwise, keep the original atom order
    else:
        symbols = struct.symbols
        geometry = transformed_coords

    return (
        Structure(
            symbols=symbols,
            geometry=geometry,
            charge=struct.charge,
            multiplicity=struct.multiplicity,
            connectivity=struct.connectivity,
            identifiers=struct.identifiers,
        ),
        rmsd,
    )
