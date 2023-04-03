from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
from pydantic import validator
from typing_extensions import Self

from qcio.constants import BOHR_TO_ANGSTROM
from qcio.helper_types import ArrayLike2D

from .base_model import QCIOModelBase

if TYPE_CHECKING:
    from pydantic.typing import ReprArgs

__all__ = ["Molecule", "Identifiers"]


class Identifiers(QCIOModelBase):
    """Molecule identifiers.

    Attributes:
        name_IUPAC: The IUPAC name of the molecule.
        name_common: the common name of the molecule.
        molecule_hash: A hash of the molecule.
        smiles: The SMILES representation of the molecule.
        inchi: The InChI representation of the molecule.
        inchikey: The InChIKey representation of the molecule.
        canonical_explicit_hydrogen_smiles: The canonical explicit hydrogen SMILES
            representation of the molecule.
        canonical_isomeric_explicit_hydrogen_mapped_smiles: The canonical isomeric
            explicit hydrogen mapped SMILES representation of the molecule.
        canonical_isomeric_explicit_hydrogen_smiles: The canonical isomeric explicit
            hydrogen SMILES representation of the molecule.
        canonical_isomeric_smiles: The canonical isomeric SMILES representation of the
            molecule.
        canonical_smiles: The canonical SMILES representation of the molecule.
        pubchem_cid: The PubChem Compound ID of the molecule.
        pubchem_sid: The PubChem Substance ID of the molecule.
        pubchem_conformerid: The PubChem Conformer ID of the molecule.
    """

    name_IUPAC: Optional[str] = None
    name_common: Optional[str] = None
    molecule_hash: Optional[str] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
    canonical_explicit_hydrogen_smiles: Optional[str] = None
    canonical_isomeric_explicit_hydrogen_mapped_smiles: Optional[str] = None
    canonical_isomeric_explicit_hydrogen_smiles: Optional[str] = None
    canonical_isomeric_smiles: Optional[str] = None
    canonical_smiles: Optional[str] = None
    pubchem_cid: Optional[str] = None
    pubchem_sid: Optional[str] = None
    pubchem_conformerid: Optional[str] = None


# class Bond(QCIOModelBase):
#     """A bond object.

#     Attributes:
#         indices: The indices of the atoms in the bond.
#         order: The order of the bond.
#     """

#     indices: Tuple[int, int]
#     order: Optional[float]


class Molecule(QCIOModelBase):
    """A molecule object.

    Attributes:
        symbols: The atomic symbols of the molecule.
        geometry: The geometry of the molecule in Cartesian coordinates. Units are (AU)
            Bohr.
        identifiers: Identifiers for the molecule such as name, smiles, etc.
        charge: The molecular charge.
        connectivity: Explicit description of the bonds between atoms.
        multiplicity: The molecular multiplicity.
        masses: Explicit masses for the atoms. If not set, default isotopic masses are
            used.
    """

    symbols: List[str]
    geometry: ArrayLike2D
    charge: int = 0
    multiplicity: int = 1
    identifiers: Identifiers = Identifiers()
    # masses: Optional[List[float]] = None
    # connectivity: Optional[List[Bond]] = None

    def __repr_args__(self) -> "ReprArgs":
        """A helper for __repr__ that returns a list of tuples of the form
        (name, value).
        """
        return [("name", self.identifiers.name_common), ("symbols", self.symbols)]

    @validator("geometry")
    def shape_n_by_3(cls, v, values, **kwargs):
        """Ensure there is an x, y, and z coordinate for each atom."""
        n_atoms = len(values["symbols"])
        return np.array(v).reshape(n_atoms, 3)

    @classmethod
    def open(cls, filepath: Union[Path, str]) -> Self:
        """Open a molecule from a file.

        Args:
            filepath: The path to the file to open. Maybe a path to a JSON file or an
                XYZ file.
        """

        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            return cls._from_xyz(filepath)
        return super().open(filepath)

    def save(
        self, filepath: Union[Path, str], exclude_none: bool = True, **kwargs
    ) -> None:
        """Save a molecule to a file.

        Args:
            filepath: The path to save the molecule to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Notes:
            If the filepath has a .xyz extension, the molecule will be saved to an XYZ
            file.
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            self._to_xyz(filepath)
            return
        super().save(filepath, **kwargs)

    def _to_xyz(self, filepath: Union[Path, str]) -> None:
        """Write a molecule to an XYZ file.

        Notes:
            Will export qcio data to the comments line with a qcio_key=value format.
        """
        filepath = Path(filepath)

        qcio_kwargs = {
            "qcio_charge": self.charge,
            "qcio_multiplicity": self.multiplicity,
        }
        assert isinstance(self.geometry, np.ndarray)  # For mypy
        geometry_angstrom = self.geometry * BOHR_TO_ANGSTROM

        with open(filepath, "w") as f:
            f.write(f"{len(self.symbols)}\n")
            f.write(f"{' '.join([f'{k}={v}' for k, v in qcio_kwargs.items()])}\n")
            for symbol, (x, y, z) in zip(self.symbols, geometry_angstrom):
                f.write(f"{symbol:2s} {x: >18.12f} {y: >18.12f} {z: >18.12f}\n")

    @classmethod
    def _from_xyz(cls, filepath: Union[Path, str]) -> Self:
        """Create a molecule from an XYZ file.

        Notes:
            Will read qcio data from the comments line with a qcio_key=value format.
        """
        filepath = Path(filepath)

        with open(filepath, "r") as f:
            lines = f.readlines()

        num_atoms = int(lines[0])
        qcio_kwargs: Dict[str, Any] = {
            item.split("=")[0].replace("qcio_", ""): item.split("=")[1]
            for item in lines[1].strip().split()
            if item.startswith("qcio_")
        }
        symbols = []
        geometry = []
        for line in lines[2 : 2 + num_atoms]:
            split_line = line.split()
            symbols.append(split_line[0])
            geometry.append([float(val) / BOHR_TO_ANGSTROM for val in split_line[1:]])

        return cls(symbols=symbols, geometry=geometry, **qcio_kwargs)