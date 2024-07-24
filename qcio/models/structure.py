import warnings
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import field_serializer, model_validator
from typing_extensions import Self

from qcio.constants import BOHR_TO_ANGSTROM
from qcio.constants import periodic_table as pt
from qcio.helper_types import SerializableNDArray

from .base_models import QCIOModelBase
from .utils import renamed_class, smiles_to_structure, structure_to_smiles

if TYPE_CHECKING:
    from pydantic.typing import ReprArgs

__all__ = ["Structure", "Identifiers", "Molecule"]


class Identifiers(QCIOModelBase):
    """Structure identifiers.

    Attributes:
        name: A human-readable, common name for the structure.
        name_IUPAC: The IUPAC name of the structure.
        smiles: The SMILES representation of the structure.
        canonical_smiles: The canonical SMILES representation of the structure.
        canonical_smiles_program: The program used to generate the canonical SMILES.
        canonical_explicit_hydrogen_smiles: The canonical explicit hydrogen SMILES
            representation of the structure.
        canonical_isomeric_smiles: The canonical isomeric SMILES representation of the
            structure.
        canonical_isomeric_explicit_hydrogen_smiles: The canonical isomeric explicit
            hydrogen SMILES representation of the structure.
        canonical_isomeric_explicit_hydrogen_mapped_smiles: The canonical isomeric
            explicit hydrogen mapped SMILES representation of the structure.
        inchi: The InChI representation of the structure.
        inchikey: The InChIKey representation of the structure.
        pubchem_cid: The PubChem Compound ID of the structure.
        pubchem_sid: The PubChem Substance ID of the structure.
        pubchem_conformerid: The PubChem Conformer ID of the structure.
    """

    name: Optional[str] = None
    name_IUPAC: Optional[str] = None
    smiles: Optional[str] = None
    canonical_smiles: Optional[str] = None
    canonical_smiles_program: Optional[str] = None
    canonical_explicit_hydrogen_smiles: Optional[str] = None
    canonical_isomeric_smiles: Optional[str] = None
    canonical_isomeric_explicit_hydrogen_smiles: Optional[str] = None
    canonical_isomeric_explicit_hydrogen_mapped_smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
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


class Structure(QCIOModelBase):
    """A Structure object with atoms and their corresponding cartesian coordinates;
        also charge, and multiplicity for the entire structure.

    Attributes:
        symbols: The atomic symbols of the structure.
        geometry: The geometry of the structure in Cartesian coordinates. Units are (AU)
            Bohr.
        identifiers: Identifiers for the structure such as name, smiles, etc.
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

    def __init__(self, **data: Any):
        """Backwards compatibility for 'ids' attribute."""
        if identifiers := data.pop("ids", None):
            warnings.warn(
                "Passing 'ids' is deprecated and will be removed in a future "
                "release. Please use 'identifiers' instead. Once instantiated, "
                "you can use structure.ids to access the identifiers as a shortcut.",
                category=FutureWarning,
                stacklevel=2,
            )
            data["identifiers"] = identifiers
        super().__init__(**data)

    @property
    def ids(self) -> Identifiers:
        """Shortcut to access the identifiers."""
        return self.identifiers

    @classmethod
    def from_smiles(
        cls,
        smiles: str,
        *,
        program: str = "rdkit",
        force_field: str = "MMFF94s",
        multiplicity: int = 1,
    ) -> Self:
        """Convert a SMILES string to a 3D Structure.

        Args:
            smiles: The SMILES string.
            program: The program to use for the conversion. Defaults to "rdkit".
            force_field: The force field to use. E.g., UFF, MMFF94, MMFF94s, etc.
            multiplicity: The multiplicity of the structure. Defaults to 1.

        Returns:
            A 3D Structure object with identifiers for SMILES and canonical SMILES.
        """
        dict_repr = smiles_to_structure(smiles, program, force_field)
        dict_repr["multiplicity"] = multiplicity
        return cls(**dict_repr)

    def to_smiles(self, program: str = "rdkit", hydrogens: bool = False) -> str:
        """Generate the canonical SMILES representation of the structure.

        Args:
            program: The program to use for the conversion. Defaults to "rdkit".
            hydrogens: Whether to include hydrogens in the SMILES string. Defaults to
                False.
        """
        return structure_to_smiles(self, program=program, hydrogens=hydrogens)

    def __repr_args__(self) -> "ReprArgs":
        """A helper for __repr__ that returns a list of tuples of the form
        (name, value).
        """
        return [  # pragma: no cover
            ("formula", self.formula),
        ]

    def add_smiles(
        self,
        *,
        smiles: Optional[str] = None,
        canonical_smiles: Optional[str] = None,
        canonical_smiles_program: Optional[str] = None,
        canonical_explicit_hydrogen_smiles: Optional[str] = None,
        program: str = "rdkit",
        hydrogens: bool = False,
    ) -> None:
        """Add SMILES data to the identifiers.

        If no SMILES data is provided, the SMILES will be generated from the structure
        using program.

        Args:
            smiles: The SMILES representation of the structure.
            canonical_smiles: The canonical SMILES representation of the structure.
            canonical_explicit_hydrogen_smiles: The canonical explicit hydrogen SMILES.
            canonical_smiles_program: The program used to generate the canonical SMILES.
            program: The program to use for the conversion. Defaults to "rdkit".
            hydrogens: Whether to include hydrogens in the SMILES string. Defaults to
                False.
        """
        # If no SMILES data is provided, generate it from the structure
        if not smiles and not canonical_smiles:
            smiles = self.to_smiles(program=program, hydrogens=hydrogens)
            canonical_smiles_program = program

            if hydrogens:
                canonical_explicit_hydrogen_smiles = smiles
            else:
                canonical_smiles = smiles

        # Create a new Identifiers instance with the updated values
        new_identifiers = self.identifiers.model_copy(
            update={
                "smiles": smiles,
                "canonical_smiles": canonical_smiles,
                "canonical_smiles_program": canonical_smiles_program,
                "canonical_explicit_hydrogen_smiles": canonical_explicit_hydrogen_smiles,  # noqa: E501
            }
        )

        # Replace the existing identifiers with the new instance
        object.__setattr__(self, "identifiers", new_identifiers)

    @model_validator(mode="before")
    def validate_symbols_and_geometry(cls, values):
        """Ensure symbols are valid atomic symbols and geometry is correct."""
        symbols = [symbol.capitalize() for symbol in values.get("symbols", [])]
        for symbol in symbols:
            if not hasattr(pt, symbol):
                raise ValueError(f"Invalid atomic symbol: '{symbol}'")
        values["symbols"] = symbols

        geometry = values.get("geometry")
        if geometry is not None:
            n_atoms = len(values["symbols"])
            values["geometry"] = np.array(geometry).reshape(n_atoms, 3)

        return values

    @field_serializer("connectivity")
    def serialize_connectivity(self, connectivity, _info) -> List[List[float]]:
        """Serialize connectivity to a list of tuples.

        Cannot have homogeneous data types in .toml files so must cast all values to
        floats.
        """
        return [[float(val) for val in bond] for bond in connectivity]

    @property
    def geometry_angstrom(self) -> np.ndarray:
        """Return the geometry of the structure in Angstrom."""
        return self.geometry * BOHR_TO_ANGSTROM

    @property
    def atomic_numbers(self) -> List[int]:
        """Return the atomic numbers of the atoms in the structure."""
        return [getattr(pt, symbol).number for symbol in self.symbols]

    @property
    def formula(self) -> str:
        """Return the molecular formula of the structure using the Hill System.
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
    def open(
        cls,
        filepath: Union[Path, str],
        charge: Optional[int] = None,
        multiplicity: Optional[int] = None,
    ) -> Self:
        """Open a structure from a file.

        Args:
            filepath: The path to the file to open. Maybe a path to a JSON file or an
                XYZ file.
        """
        filepath = Path(filepath)

        if (charge or multiplicity) and filepath.suffix != ".xyz":
            raise ValueError(
                "Charge and multiplicity can only be set when opening an XYZ file."
            )

        if filepath.suffix == ".xyz":
            xyz_str = filepath.read_text()
            return cls.from_xyz(xyz_str, charge=charge, multiplicity=multiplicity)

        return super().open(filepath)

    def save(
        self,
        filepath: Union[Path, str],
        exclude_none=True,
        indent: int = 4,
        **kwargs,
    ) -> None:
        """Save a Structure to a file.

        Args:
            filepath: The path to save the structure to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Notes:
            If the filepath has a .xyz extension, the structure will be saved to an XYZ
            file.
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            filepath.write_text(self.to_xyz(**kwargs))
            return
        super().save(filepath, exclude_none, indent, **kwargs)

    def to_xyz(self, precision: int = 17) -> str:
        """Return an xyz string representation of the structure.

        Args:
            precision: The number of decimal places to include in the xyz file. Default
                17 which captures all precision of float64.
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

        # Create a format string using the precision parameter
        format_str = f"{{:2s}} {{: >18.{precision}f}} {{: >18.{precision}f}} {{: >18.{precision}f}}"  # noqa: E501

        for symbol, (x, y, z) in zip(self.symbols, geometry_angstrom):
            xyz_lines.append(format_str.format(symbol, x, y, z))
        xyz_lines.append("")  # Append newline to end of file
        return "\n".join(xyz_lines)

    @classmethod
    def from_xyz(
        cls,
        xyz_str: str,
        *,
        charge: Optional[int] = None,
        multiplicity: Optional[int] = None,
    ) -> Self:
        """Create a Structure from an XYZ file or string.

        Args:
            xyx_str: The XYZ string.
            charge: The molecular charge of the structure. If not provided, will read
                from the XYZ string if set or default to 0.
            multiplicity: The molecular multiplicity of the structure. If not provided,
                will read from the XYZ string if set or default to 1.
        Notes:
            Will read qcio data from the comments line with a qcio_key=value format.
        """

        lines = xyz_str.split("\n")

        num_atoms = int(lines[0])
        qcio_kwargs: Dict[str, Any] = {
            item.split("=")[0].replace("qcio_", ""): item.split("=")[1]
            for item in lines[1].strip().split()
            if item.startswith("qcio_")
        }
        if charge is not None and "charge" in qcio_kwargs:
            raise ValueError("Charge cannot be set in the file and as an argument.")
        if multiplicity is not None and "multiplicity" in qcio_kwargs:
            raise ValueError(
                "Multiplicity cannot be set in the file and as an argument."
            )

        # Set charge and multiplicity if provided
        if charge is not None:
            qcio_kwargs["charge"] = charge
        if multiplicity is not None:
            qcio_kwargs["multiplicity"] = multiplicity

        symbols = []
        geometry = []
        for line in lines[2 : 2 + num_atoms]:
            split_line = line.split()
            symbols.append(split_line[0])
            geometry.append([float(val) / BOHR_TO_ANGSTROM for val in split_line[1:]])

        return cls(symbols=symbols, geometry=geometry, **qcio_kwargs)  # type: ignore


@renamed_class(Structure)
class Molecule(Structure):
    pass
