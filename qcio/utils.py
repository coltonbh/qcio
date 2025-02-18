"""Utility functions for working with qcio objects."""

import json
from collections import Counter
from typing import Union

import numpy as np
from pydantic import BaseModel

from .constants import ANGSTROM_TO_BOHR
from .models import LengthUnit, Structure
from .models.utils import (
    _assert_module_installed,
    _rdkit_determine_connectivity,
    _rdkit_mol_from_structure,
)

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


def json_dumps(obj: Union[BaseModel, list[BaseModel]]) -> str:
    """Serialization helper for lists of pydantic objects."""
    if isinstance(obj, list):
        return json.dumps([o.model_dump() for o in obj])
    return obj.model_dump_json()


def align(
    struct: Structure,
    refstruct: Structure,
    symmetry: bool = True,
    use_hueckel: bool = True,
    use_vdw: bool = False,
    cov_factor: float = 1.3,
    length_unit: LengthUnit = LengthUnit.BOHR,
) -> tuple[Structure, float]:
    """
    Return a new structure that is optimally aligned to the reference structure and
    the RMSD between the two structures in Bohr or Angstroms.

    May lead to a 'combinatorial explosion' especially if many molecule symmetries
    (e.g., many hydrogens) are present.If this function is taking a long time to
    compute, consider passing `symmetry=False` to disable symmetry consideration.

    Args:
        struct: The structure to align.
        refstruct: The reference structure.
        symmetry: Whether to consider symmetries in the structures before aligning and
            calculating the RMSD, i.e., to allow atom renumbering. This relies on the
            RDKit's `GetBestAlignmentTransform` method and `GetBestRMS` functions. If False, the RMSD is
            calculated with alignment but without considering symmetry, i.e., naively
            assuming the atoms are already correctly indexed across structures.
        use_hueckel: Whether to use Hueckel method when determining connectivity.
            Applies only to `best=True`.
        use_vdw: Whether to use Van der Waals radii when determining connectivity.
            Applies only to `best=True`.
        cov_factor: The scaling factor for the covalent radii when determining
            connectivity. Applies only to `best=True`.
        length_unit: The unit of length to use for the RMSD calculation. Default is
            "bohr". If "angstrom", the RMSD will be in Angstroms.

    Returns:
        Tuple of the aligned structure and the RMSD in Angstroms.
    """
    _assert_module_installed("rdkit")
    from rdkit.Chem import rdMolAlign  # type: ignore

    # Create RDKit molecules
    mol = _rdkit_mol_from_structure(struct)
    refmol = _rdkit_mol_from_structure(refstruct)

    # Determine connectivity
    _rdkit_determine_connectivity(
        mol,
        charge=struct.charge,
        use_hueckel=use_hueckel,
        use_vdw=use_vdw,
        cov_factor=cov_factor,
    )
    _rdkit_determine_connectivity(
        refmol,
        charge=refstruct.charge,
        use_hueckel=use_hueckel,
        use_vdw=use_vdw,
        cov_factor=cov_factor,
    )

    # Compute RMSD and align mol to refmol
    if symmetry:
        rmsd_val, trnsfm_matrix, atm_map = rdMolAlign.GetBestAlignmentTransform(
            mol, refmol
        )  # type: ignore # noqa: E501
    else:
        rmsd_val, trnsfm_matrix = rdMolAlign.GetAlignmentTransform(mol, refmol)

    # Convert to homogeneous coordinates in Angstroms
    coords_homogeneous = np.hstack(
        [struct.geometry_angstrom, np.ones((struct.geometry.shape[0], 1))]
    )

    # Apply the transformation matrix
    transformed_coords_homogeneous = coords_homogeneous @ trnsfm_matrix.T

    # Extract the transformed 3D coordinates and convert to Bohr
    transformed_coords = transformed_coords_homogeneous[:, :3] * ANGSTROM_TO_BOHR

    # Reorder the atoms to match the reference structure
    if symmetry:
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
            geometry[ref_idx] = transformed_coords[probe_idx]

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
        rmsd_val * ANGSTROM_TO_BOHR if length_unit == LengthUnit.BOHR else rmsd_val,
    )
