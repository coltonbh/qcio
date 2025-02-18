"""Utility functions for the models module."""

import importlib
import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from ..constants import ANGSTROM_TO_BOHR
from ..constants import periodic_table as pt
from ..models import LengthUnit

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
            f"The '{module}' module is required for this function. "
            f"Please install it with 'pip install qcio[{module}]' or "
            "'pip install qcio[all]'."
        )


def smiles_to_structure(
    smiles: str, program: str = "rdkit", force_field: str = "MMFF94s"
) -> dict[str, Any]:
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
        from rdkit import Chem  # type: ignore
        from rdkit.Chem import AllChem  # type: ignore

        # Convert SMILES to RDKit Mol object
        mol = Chem.MolFromSmiles(smiles)  # type: ignore
        assert mol is not None, f"Failed to convert SMILES to RDKit Mol: {smiles}"
        canonical_smiles = Chem.MolToSmiles(mol, canonical=True)  # type: ignore
        mol = Chem.AddHs(mol)  # type: ignore

        # Generate 3D coordinates
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())  # type: ignore
        # Optimize the molecule using the specified force field
        if force_field.upper() == "UFF":
            AllChem.UFFOptimizeMolecule(mol)  # type: ignore
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
        charge = Chem.GetFormalCharge(mol)  # type: ignore

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


def _rdkit_determine_bonds(
    structure: "Structure",
    charge: int,
    robust: bool = True,
    use_hueckel: bool = True,
    use_vdw: bool = False,
    cov_factor: float = 1.3,
    allow_charged_fragments: bool = False,
) -> "rdkit.Chem.Mol":  # type: ignore # noqa: F821
    """
    Determine the bonds in an RDKit molecule, using robust fallback parameters.

    Hueckel method is most robust; may useVdw=True use VdW radii; default method
    is connect-the-dots (fastest but least robust)"""
    _assert_module_installed("rdkit")
    from rdkit import Chem
    from rdkit.Chem import rdDetermineBonds

    mol = Chem.MolFromXYZBlock(structure.to_xyz())  # type: ignore

    try:
        # Execute the wrapped code block
        if robust:
            try:  # Original parameters
                rdDetermineBonds.DetermineBonds(
                    mol,
                    charge=charge,
                    useHueckel=use_hueckel,
                    useVdw=use_vdw,
                    covFactor=cov_factor,
                    allowChargedFragments=allow_charged_fragments,
                )
            except Exception as e:  # noqa: E722
                mol = Chem.MolFromXYZBlock(structure.to_xyz())  # type: ignore
                try:  # Swap allow_charged_fragments
                    rdDetermineBonds.DetermineBonds(
                        mol,
                        charge=charge,
                        useHueckel=use_hueckel,
                        useVdw=use_vdw,
                        covFactor=cov_factor,
                        allowChargedFragments=not allow_charged_fragments,
                    )
                except Exception:  # noqa: E722
                    mol = Chem.MolFromXYZBlock(structure.to_xyz())  # type: ignore
                    try:  # Swap method
                        rdDetermineBonds.DetermineBonds(
                            mol,
                            charge=charge,
                            useHueckel=not use_hueckel,
                            useVdw=not use_vdw,
                            covFactor=cov_factor,
                            allowChargedFragments=allow_charged_fragments,
                        )
                    except Exception:  # noqa: E722
                        mol = Chem.MolFromXYZBlock(structure.to_xyz())  # type: ignore
                        try:  # Swap method and allow_charged_fragments
                            rdDetermineBonds.DetermineBonds(
                                mol,
                                charge=charge,
                                useHueckel=not use_hueckel,
                                useVdw=not use_vdw,
                                covFactor=cov_factor,
                                allowChargedFragments=not allow_charged_fragments,
                            )
                        except Exception:
                            mol = Chem.MolFromXYZBlock(  # type: ignore
                                structure.to_xyz()
                            )
                            try:  # Try connect-the-dots method
                                rdDetermineBonds.DetermineBonds(
                                    mol,
                                    charge=charge,
                                    useHueckel=False,
                                    useVdw=False,
                                    covFactor=cov_factor,
                                    allowChargedFragments=True,
                                )
                            except Exception:
                                mol = Chem.MolFromXYZBlock(  # type: ignore
                                    structure.to_xyz()
                                )
                                try:  # Swap allow_charged_fragments
                                    rdDetermineBonds.DetermineBonds(
                                        mol,
                                        charge=charge,
                                        useHueckel=False,
                                        useVdw=False,
                                        covFactor=cov_factor,
                                        allowChargedFragments=False,
                                    )
                                except Exception:
                                    raise e
        else:
            rdDetermineBonds.DetermineBonds(
                mol,
                charge=charge,
                useHueckel=use_hueckel,
                useVdw=use_vdw,
                covFactor=cov_factor,
                allowChargedFragments=allow_charged_fragments,
            )
    finally:
        # Delete the run.out and nul files created by rdkit
        # Remove run.out and nul files if they exist
        for filename in ["run.out", "nul"]:
            file = Path(filename)
            if file.exists():
                try:
                    file.unlink()
                except Exception:
                    pass
    return mol


def structure_to_smiles(
    structure: "Structure",
    *,
    program: str = "rdkit",
    hydrogens: bool = False,
    robust: bool = True,
    use_hueckel: bool = True,
    use_vdw: bool = False,
    cov_factor: float = 1.3,
    allow_charged_fragments: bool = False,
) -> str:
    """Convert a Structure to a SMILES string.

    Args:
        structure: The Structure object to convert.
        program: The program to use for the conversion. Can be 'rdkit' or 'openbabel'.
        hydrogens: Whether to include hydrogens in the SMILES string.
        robust: Whether to use a robust method for bond determination by trying
            different parameters for the DetermineBonds function automatically (RDKit
            only).
        use_hueckel: Whether to use the Hueckel method for bond determination (RDKit
            only).
        use_vdw: Whether to use van der Waals radii for bond determination (RDKit only).
        cov_factor: The scaling factor for the covalent radii when determining
            connectivity (RDKit only).
        allow_charged_fragments: Whether to allow charged fragments in the bond
            determination step (RDKit only). When allow_charged_fragments=False, RDKit
            avoids assigning formal charges and instead satisfies valence with radicals
            (unpaired electrons) if necessary. Bonding and valence will be reconciled
            without fragments. When True, RDKit will assign formal charges to atoms and
            reconcile bonding and valence with charged fragments.


    Returns:
        The SMILES string.
    """
    if use_hueckel and use_vdw:
        raise ValueError(
            "Cannot use both the Hueckel and Van der Waals methods for bond detection. "
            "Pass use_hueckel=False if you want to use the VdW method. Hueckel method "
            "is used by default."
        )

    if program == "rdkit":
        _assert_module_installed(program)
        from rdkit import Chem

        # Details: https://greglandrum.github.io/rdkit-blog/posts/2022-12-18-introducing-rdDetermineBonds.html  # noqa: E501
        # Create RDKit molecule and use rdDetermineBonds module to infer bonds
        mol = _rdkit_determine_bonds(
            structure,
            charge=structure.charge,
            robust=robust,
            use_hueckel=use_hueckel,
            use_vdw=use_vdw,
            cov_factor=cov_factor,
            allow_charged_fragments=allow_charged_fragments,
        )

        # Remove hydrogens if necessary
        if not hydrogens:
            mol = Chem.RemoveHs(mol)  # type: ignore

        return Chem.MolToSmiles(mol, canonical=True)  # type: ignore

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


def _rdkit_mol_from_structure(
    struct: "Structure",
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


def _rdkit_determine_connectivity(
    mol: "rdkit.Chem.Mol",  # type: ignore # noqa: F821
    charge: int,
    use_hueckel: bool = True,
    use_vdw: bool = True,
    cov_factor: float = 1.3,
) -> None:
    """Determine connectivity for an RDKit molecule.

    Args:
        mol: The RDKit molecule.
        charge: The charge of the molecule.
        use_hueckel: Whether to use Hueckel method when determining connectivity.
        use_vdw: Whether to use Van der Waals radii when determining connectivity.
        cov_factor: The scaling factor for the covalent radii when determining
            connectivity.
    """
    _assert_module_installed("rdkit")
    from rdkit.Chem import rdDetermineBonds

    try:
        rdDetermineBonds.DetermineConnectivity(
            mol,
            charge=charge,
            useHueckel=use_hueckel,
            useVdw=use_vdw,
            covFactor=cov_factor,
        )
    finally:
        # Delete the run.out and nul files created by rdkit
        for filename in ["run.out", "nul"]:
            file = Path(filename)
            if file.exists():
                try:
                    file.unlink()
                except Exception:
                    pass


def rmsd(
    struct1: "Structure",
    struct2: "Structure",
    symmetry: bool = True,
    numthreads: int = 1,
    use_hueckel: bool = True,
    use_vdw: bool = False,
    cov_factor: float = 1.3,
    length_unit: LengthUnit = LengthUnit.BOHR,
) -> float:
    """
    Calculate the root mean square deviation between two structures in Bohr or Angstrom.

    May lead to a 'combinatorial explosion' especially if many molecule symmetries
    (e.g., many hydrogens) are present.If this function is taking a long time to
    compute, consider passing `symmetry=False` to disable symmetry consideration. Or
    pass `numthreads=an_integer` to increase the number of threads used for the
    symmetry consideration step.

    Args:
        struct1: The first structure.
        struct2: The second structure.
        symmetry: Whether to consider symmetries in the structures before calculating
            the RMSD, i.e., to allow atom renumbering. This relies on the  RDKit
            `DetermineConnectivity` and `GetBestRMS` functions. If False, the RMSD is
            calculated with alignment but without considering symmetry, i.e., naively
            assuming the atoms are already correctly indexed across structures.
        numthreads: The number of threads to use for the RMSD calculation. Applies only
            to the alignment step if `symmetry=True`.
        use_hueckel: Whether to use Hueckel method when determining connectivity.
            Applies only to `symmetry=True`.
        use_vdw: Whether to use Van der Waals radii when determining connectivity.
            Applies only to `symmetry=True`.
        cov_factor: The scaling factor for the covalent radii when determining
            connectivity. Applies only to `symmetry=True`.
        length_unit: The unit of length to use for the RMSD calculation. Default is
            "bohr". If "angstrom", the RMSD will be in Angstroms.

    Returns:
        The RMSD between the two structures in Angstroms.
    """
    _assert_module_installed("rdkit")
    from rdkit.Chem import rdMolAlign  # type: ignore

    # Create RDKit molecules
    mol1 = _rdkit_mol_from_structure(struct1)
    mol2 = _rdkit_mol_from_structure(struct2)

    # Compute RMSD
    if symmetry:
        # Determine connectivity
        _rdkit_determine_connectivity(
            mol1,
            charge=struct1.charge,
            use_hueckel=use_hueckel,
            use_vdw=use_vdw,
            cov_factor=cov_factor,
        )

        _rdkit_determine_connectivity(
            mol2,
            charge=struct2.charge,
            use_hueckel=use_hueckel,
            use_vdw=use_vdw,
            cov_factor=cov_factor,
        )
        # Take symmetry into account, align the two molecules, compute RMSD
        try:
            rmsd = rdMolAlign.GetBestRMS(mol2, mol1, numThreads=numthreads)
        except RuntimeError as e:  # Possible failure to make substructure match
            try:  # Swap the order of the molecules and try again.
                rmsd = rdMolAlign.GetBestRMS(mol1, mol2, numThreads=numthreads)
            except RuntimeError:  # If it fails again, raise the original error
                raise e

    else:  # Do not take symmetry into account. Structs aligned by atom index.
        rmsd, _ = rdMolAlign.GetAlignmentTransform(mol2, mol1)

    return rmsd * ANGSTROM_TO_BOHR if length_unit == LengthUnit.BOHR else rmsd


def to_multi_xyz(structures: Iterable["Structure"]) -> str:
    """Create a multi-structure XYZ string from a list of structures.

    Args:
        structures: An Iterable of Structure objects.

    Returns:
        The multi-structure XYZ string.
    """
    return "".join(struct.to_xyz() for struct in structures)
