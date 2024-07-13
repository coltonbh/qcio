"""Utility functions for the models module."""

import warnings
from typing import Any, Dict

from ..constants import ANGSTROM_TO_BOHR


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


def smiles_to_structure(
    smiles: str, program: str = "rdkit", force_field: str = "UFF"
) -> Dict[str, Any]:
    """Convert a SMILES string to a Structure object in dictionary form.

    Args:
        smiles: The SMILES string to convert.
        method: The method to use for the conversion. Defaults to "UFF".

    Returns:
        A dictionary with the keys "symbols" and "geometry".
    """
    SUPPORTED_PROGRAMS = ["rdkit"]

    # Remove newline characters if present
    smiles = smiles.strip()

    if program not in SUPPORTED_PROGRAMS:
        raise ValueError(f"Unsupported program: '{program}'.")

    if program == "rdkit":
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "The 'rdkit' module is required for this function. "
                "Please install it with 'pip install qcio[rdkit]'."
            )
        else:
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

    return {
        "symbols": atoms,
        "geometry": geometry_bohr,
        "charge": Chem.GetFormalCharge(mol),
        "identifiers": {"canonical_smiles": canonical_smiles, "smiles": smiles},
    }
