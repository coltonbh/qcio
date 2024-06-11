from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import field_serializer, field_validator
from typing_extensions import Self

from qcio.constants import _ELEMENTS, BOHR_TO_ANGSTROM
from qcio.helper_types import SerializableNDArray

from .base_models import QCIOModelBase

if TYPE_CHECKING:
    from pydantic.typing import ReprArgs

__all__ = ["Molecule", "Identifiers"]


class Identifiers(QCIOModelBase):
    """Molecule identifiers.

    Attributes:
        name_IUPAC: The IUPAC name of the molecule.
        name_common: The common name of the molecule.
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
        connectivity: Explicit description of the bonds between atoms. Each tuple
            contains the indices of the atoms in the bond and the order of the bond.
            E.g., [(0, 1, 1.0), (1, 2, 2.0)] indicates a single bond between atoms 0
            and 1 and a double bond between atoms 1 and 2.
        masses: Explicit masses for the atoms. If not set, default isotopic masses are
            used.
    """

    symbols: List[str]
    geometry: SerializableNDArray  # Coerced to 2D array
    charge: int = 0
    multiplicity: int = 1
    identifiers: Identifiers = Identifiers()
    connectivity: List[Tuple[int, int, float]] = []
    # masses: List[float] = []

    def __repr_args__(self) -> "ReprArgs":
        """A helper for __repr__ that returns a list of tuples of the form
        (name, value).
        """
        return [  # pragma: no cover
            ("formula", self.formula),
        ]

    @field_validator("symbols")
    @classmethod
    def camel_case(cls, v, values, **kwargs):
        """Ensure symbols are all capitalized with lowercase second letter."""
        return [symbol.capitalize() for symbol in v]

    @field_validator("geometry")
    @classmethod
    def shape_n_by_3(cls, v, values, **kwargs):
        """Ensure there is an x, y, and z coordinate for each atom."""
        n_atoms = len(values.data["symbols"])
        return np.array(v).reshape(n_atoms, 3)

    @field_serializer("connectivity")
    def serialize_connectivity(self, connectivity, _info) -> List[List[float]]:
        """Serialize connectivity to a list of tuples.

        Cannot have homogeneous data types in .toml files so must cast all values to
        floats.
        """
        return [[float(val) for val in bond] for bond in connectivity]

    @property
    def atomic_numbers(self) -> List[int]:
        """Return the atomic numbers of the atoms in the molecule."""
        return [_ELEMENTS[symbol] for symbol in self.symbols]

    @property
    def formula(self) -> str:
        """Return the molecular formula of the molecule using the Hill System.
        # noqa: E501
        https://chemistry.stackexchange.com/questions/1239/order-of-elements-in-a-formula
        """
        counter_elements = Counter(self.symbols)

        carbon_count = counter_elements.pop("C", 0)
        hydrogen_count = counter_elements.pop("H", 0)

        # Sort remaining elements alphabetically
        sorted_elements = sorted(counter_elements.items())

        if hydrogen_count > 0:
            sorted_elements = [("H", hydrogen_count)] + sorted_elements
        if carbon_count > 0:
            sorted_elements = [("C", carbon_count)] + sorted_elements

        return "".join(
            f"{element}{count if count > 1 else ''}"
            for element, count in sorted_elements
        )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Handle tuple in connectivity"""
        as_dict = super().model_dump(**kwargs)
        # Connectivity may be empty and super().dict() will remove empty values
        if (connectivity := as_dict.get("connectivity")) is not None:
            # Must cast all values to floats as toml cannot handle mixed types
            as_dict["connectivity"] = [
                [float(val) for val in bond] for bond in connectivity
            ]
        return as_dict

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
        self,
        filepath: Union[Path, str],
        exclude_none=True,
        indent: int = 4,
        **kwargs,
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
            filepath.write_text(self.to_xyz())
            return
        super().save(filepath, exclude_none, indent, **kwargs)

    def to_xyz(self) -> str:
        """Return an xyz string representation of the molecule.

        Notes:
            Will add qcio data to the comments line with a qcio_key=value format.
        """

        qcio_data = {  # These get added to comments line (line 2) in xyz file
            "qcio_charge": self.charge,
            "qcio_multiplicity": self.multiplicity,
        }
        assert isinstance(self.geometry, np.ndarray)  # For mypy
        geometry_angstrom = self.geometry * BOHR_TO_ANGSTROM

        xyz_lines = []
        xyz_lines.append(f"{len(self.symbols)}")
        xyz_lines.append(f"{' '.join([f'{k}={v}' for k, v in qcio_data.items()])}")
        for symbol, (x, y, z) in zip(self.symbols, geometry_angstrom):
            # Using 17 decimal places to capture all precision of float64
            xyz_lines.append(f"{symbol:2s} {x: >18.17f} {y: >18.17f} {z: >18.17f}")
        xyz_lines.append("")  # Append newline to end of file
        return "\n".join(xyz_lines)

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

        return cls(symbols=symbols, geometry=geometry, **qcio_kwargs)  # type: ignore
