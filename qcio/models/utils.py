"""Utility functions for the models module."""

import importlib
import warnings
from typing import TYPE_CHECKING, Any, Dict

import numpy as np

from ..constants import ANGSTROM_TO_BOHR
from ..constants import periodic_table as pt

if TYPE_CHECKING:
    from qcio.models.structure import Structure


def deprecated_function(new_name: str):
    """Notify users that a function is deprecated and will be removed in the future.
    Works equally well on functions and methods.

    Usage:
        @deprecated("new_name")
        def old_name():
            pass
    """

    def decorator(func):
        def wrapped(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed in future "
                f"versions. Please use {new_name} instead.",
                FutureWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapped

    return decorator


def deprecated_class(new_name: str):
    """Notify users that a class is deprecated and will be removed in the future.
    Works only on Pydantic models since it relies on the model_post_init method.

    Usage:
        @deprecated_class("new_name")
        class OldName:
            pass
    """

    def class_decorator(cls):
        orig_init = cls.__init__

        def new_init(self, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} is deprecated and will be removed in a future "
                f"release. Please use '{new_name}' instead.",
                category=FutureWarning,
                stacklevel=2,
            )
            orig_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return class_decorator


def renamed_class(new_cls: Any):
    """Notify users that a class is deprecated and has been renamed.

    Usage:
        @renamed_class(NewClass)
        class OldClass:
            pass
    """

    def decorator(cls):
        def return_new_cls(cls, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} is deprecated and and will be removed in a future "
                f"release. Please use '{new_cls.__name__}' instead.",
                category=FutureWarning,
                stacklevel=2,
            )
            return new_cls(*args, **kwargs)

        cls.__new__ = return_new_cls
        return cls

    return decorator


def _assert_module_installed(module: str):
    """Raise an error if the module is not installed."""
    try:
        importlib.import_module(module)
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "The 'rdkit' module is required for this function. "
            f"Please install it with 'pip install qcio[{module}]'."
        )


def smiles_to_structure(
    smiles: str, program: str = "rdkit", force_field: str = "MMFF94s"
) -> Dict[str, Any]:
    """Convert a SMILES string to a Structure object in dictionary form.

    Args:
        smiles: The SMILES string to convert.
        method: The method to use for the conversion. Defaults to "MMFF94s".

    Returns:
        A dictionary representation of the Structure object.
    """
    # Remove newline characters if present
    smiles = smiles.strip()

    if program == "rdkit":
        if "." in smiles:
            raise ValueError(
                "Multiple molecules are not supported by RDKit. "
                "Please provide a single molecule or use openbabel for the program."
            )
        _assert_module_installed(program)
        from rdkit import Chem
        from rdkit.Chem import AllChem

        # Convert SMILES to RDKit Mol object
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, f"Failed to convert SMILES to RDKit Mol: {smiles}"
        canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
        mol = Chem.AddHs(mol)

        # Generate 3D coordinates
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        # Optimize the molecule using the specified force field
        if force_field.upper() == "UFF":
            AllChem.UFFOptimizeMolecule(mol)
        elif force_field.upper() == "MMFF94":
            AllChem.MMFFOptimizeMolecule(mol, mmffVariant="MMFF94")  # type: ignore
        elif force_field.upper() == "MMFF94S":
            AllChem.MMFFOptimizeMolecule(mol, mmffVariant="MMFF94s")  # type: ignore
        else:
            raise ValueError(f"Unsupported force_field: {force_field}")

        # Get atom symbols
        atoms = [atom.GetSymbol() for atom in mol.GetAtoms()]  # type: ignore

        # Get atom positions
        conf = mol.GetConformer()
        geometry_angstrom = conf.GetPositions()
        geometry_bohr = geometry_angstrom * ANGSTROM_TO_BOHR

        # Get charge
        charge = Chem.GetFormalCharge(mol)

    elif program == "openbabel":
        _assert_module_installed(program)
        from openbabel import pybel

        # Convert SMILES to Open Babel Mol object
        mol = pybel.readstring("smi", smiles)
        assert mol is not None, f"Failed to convert SMILES to Open Babel Mol: {smiles}"

        # Add hydrogens
        mol.addh()  # type: ignore

        # Generate 3D coordinates and optimize
        mol.make3D(forcefield=force_field.lower(), steps=250)  # type: ignore

        # Get atom symbols
        atoms = [pt.number(atom.atomicnum).symbol for atom in mol.atoms]  # type: ignore

        # Get atom positions
        geometry_angstrom = np.array([atom.coords for atom in mol.atoms])  # type: ignore # noqa: E501
        geometry_bohr = geometry_angstrom * ANGSTROM_TO_BOHR

        # Get canonical SMILES
        canonical_smiles = mol.write("can").strip()  # type: ignore

        # Get charge
        charge = mol.charge  # type: ignore

    else:
        raise ValueError(f"Unsupported program: '{program}'.")

    return {
        "symbols": atoms,
        "geometry": geometry_bohr,
        "charge": charge,
        "identifiers": {
            "canonical_smiles": canonical_smiles,
            "smiles": smiles,
            "canonical_smiles_program": program,
        },
    }


def structure_to_smiles(
    structure: "Structure",
    *,
    program: str = "rdkit",
    hydrogens: bool = False,
) -> str:
    """Convert a Structure to a SMILES string.

    Args:
        structure: The Structure object to convert.
        program: The program to use for the conversion. Can be 'rdkit' or 'openbabel'.
        hydrogens: Whether to include hydrogens in the SMILES string.

    Returns:
        The SMILES string.
    """

    if program == "rdkit":
        _assert_module_installed(program)
        from rdkit import Chem
        from rdkit.Chem import rdDetermineBonds

        # Details: https://greglandrum.github.io/rdkit-blog/posts/2022-12-18-introducing-rdDetermineBonds.html  # noqa: E501
        # Create RDKit molecule
        mol = Chem.MolFromXYZBlock(structure.to_xyz())  # type: ignore

        # Use rdDetermineBonds to infer bond information
        rdDetermineBonds.DetermineBonds(mol, charge=structure.charge)

        # Remove hydrogens if necessary
        if not hydrogens:
            mol = Chem.RemoveHs(mol)

        return Chem.MolToSmiles(mol, canonical=True)

    elif program == "openbabel":
        _assert_module_installed(program)
        from openbabel import openbabel as ob
        from openbabel import pybel

        # Must remove data in second line for Open Babel
        xyz_lines = structure.to_xyz().splitlines()
        xyz_lines[1] = ""

        # Create Open Babel OBMol object
        mol = pybel.readstring("xyz", "\n".join(xyz_lines))

        # Assign charges
        partial_charges = mol.calccharges()

        # Check if the sum of the partial charges matches the total charge
        if sum(partial_charges) != structure.charge:
            raise ValueError(
                f"Charge mismatch. Open Babel: {sum(partial_charges)} vs Structure: "
                f"{structure.charge}"
            )

        # Set the formal charges on the atoms
        if sum(partial_charges) != 0:
            for atom, charge in zip(mol.atoms, partial_charges):
                atom.OBAtom.SetFormalCharge(int(round(charge)))

        # Ensure the total charge matches the structure
        if mol.charge != structure.charge:
            raise ValueError(
                f"Charge mismatch. Open Babel: {sum(partial_charges)} vs Structure: "
                f"{structure.charge}"
            )

        # Create an OBConversion object to handle output format
        conv = ob.OBConversion()
        conv.SetOutFormat("can")

        if hydrogens:
            conv.AddOption("h", ob.OBConversion.OUTOPTIONS)

        # Generate canonical SMILES with explicit hydrogens
        return conv.WriteString(mol.OBMol).strip()

    else:
        raise ValueError(f"Unsupported program: '{program}'.")
