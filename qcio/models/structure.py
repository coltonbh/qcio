import warnings
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Tuple, Union

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

__all__ = ["Structure", "Identifiers", "Molecule", "DistanceUnits"]


class DistanceUnits(str, Enum):
    """Distance units for the Structure.distance method.

    Attributes:
        bohr (str): The distance in Bohr.
        angstrom (str): The distance in Angstrom.

    """

    bohr = "bohr"
    angstrom = "angstrom"


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
        extras Dict[str, Any]: Additional information to bundle with the object. Use for
            schema development and scratch space.
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


class IDs2(Identifiers):
    """Second one"""


# class Bond(QCIOModelBase):
#     """A bond object.

#     Attributes:
#         indices: The indices of the atoms in the bond.
#         order: The order of the bond.
#     """

#     indices: Tuple[int, int]
#     order: Optional[float]


class Structure(QCIOModelBase):
    """A Structure object with atoms and their corresponding cartesian coordinates,
        charge, multiplicity, and identifiers such as name, smiles, etc.

    Attributes:
        symbols: The atomic symbols of the structure.
        geometry: The geometry of the structure in Cartesian coordinates. Units are
            Bohr (AU).
        identifiers: Identifiers for the structure such as name, smiles, etc.
        charge: The molecular charge.
        multiplicity: The molecular multiplicity.
        connectivity: Explicit description of the bonds between atoms. Each tuple
            contains the indices of the atoms in the bond and the order of the bond.
            E.g., `[(0, 1, 1.0), (1, 2, 2.0)]` indicates a single bond between atoms 0
            and 1 and a double bond between atoms 1 and 2.
        extras Dict[str, Any]: Additional information to bundle with the object. Use
            for schema development and scratch space.
        ids: `@property` Shortcut to access identifiers.
        geometry_angstrom: `@property` The geometry of the structure in Angstrom.
        atomic_numbers: `@property` The atomic numbers of the atoms in the structure.
        formula: `@property` The molecular formula of the structure using the Hill
            System.
    """

    symbols: List[str]
    geometry: SerializableNDArray  # Coerced to 2D array
    charge: int = 0
    multiplicity: int = 1
    identifiers: Identifiers = Identifiers()
    connectivity: List[Tuple[int, int, float]] = []
    _xyz_comment_key: ClassVar[str] = "xyz_comments"

    def __init__(self, **data: Any):
        """Create a new Structure object.

        Example:
            ```python
            from qcio import Structure

            structure = Structure(
                symbols=["H", "O", "H"],
                geometry=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 2.0]],
                charge=0,  # optional; defaults to 0
                multiplicity=1,  # optional; defaults to 1
                identifiers={"smiles": "CCO"},  # optional
            )

            ```
        """
        # Backwards compatibility for 'ids' attribute.
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

    @classmethod
    def open(
        cls,
        filepath: Union[Path, str],
        charge: Optional[int] = None,
        multiplicity: Optional[int] = None,
    ) -> Union["Structure", List["Structure"]]:
        """Open a structure or structures from a file.

        Args:
            filepath: The path to the file to open. May be a path to a formerly saved
                Structure file or an XYZ file.
            charge: The molecular charge of the structure. Only used when opening an XYZ
                file and if not set in the file.
            multiplicity: The molecular multiplicity of the structure. Only used when
                opening an XYZ file and if not set in the file.

        Returns:
            A Structure object or a list of Structure objects for a multi-structure XYZ
                file.

        Example:
            ```python
            struct = Structure.open("path/to/structure.json")
            ```

            ```python
            struct = Structure.open("path/to/structure.xyz", charge=-1, multiplicity=3)
            ```

            ```python
            structures = Structure.open("path/to/structures.xyz")
            ```
        """
        filepath = Path(filepath)

        if (charge or multiplicity) and filepath.suffix != ".xyz":
            raise ValueError(
                "Charge and multiplicity can only be set when opening an XYZ file."
            )

        if filepath.suffix == ".xyz":
            xyz_str = filepath.read_text()
            structures = cls.from_xyz_multi(
                xyz_str, charge=charge, multiplicity=multiplicity
            )
            if len(structures) == 1:
                return structures[0]
            return structures

        return super().open(filepath)

    def save(
        self,
        filepath: Union[Path, str],
        exclude_none: bool = True,
        exclude_unset: bool = True,
        indent: int = 4,
        **kwargs,
    ) -> None:
        """Save a Structure to a file.

        Args:
            filepath: The path to save the structure to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            exclude_unset: If True, attributes that have not been set will not be
                written to the file.
            indent: The number of spaces to use for indentation in the JSON file. 0
                creates a more compact JSON file, 4 is more human-readable.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Notes:
            If the filepath has a `.xyz` extension, the structure will be saved to an
            XYZ file. qcio will automatically convert the geometry to Angstrom and add
            the charge and multiplicity to the comments line of the XYZ file.

        Example:
            ```python
            struct.save("path/to/structure.json")
            ```

            ```python
            struct.save("path/to/structure.xyz")
            ```
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            filepath.write_text(self.to_xyz(**kwargs))
            return
        super().save(filepath, exclude_none, exclude_unset, indent, **kwargs)

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
        """Create a new Structure object from a SMILES string.

        Args:
            smiles: The SMILES string.
            program: The program to use for the conversion. Defaults to "rdkit".
            force_field: The force field to use. E.g., UFF, MMFF94, MMFF94s, etc.
            multiplicity: The multiplicity of the structure.

        Returns:
            A Structure object with identifiers for SMILES and canonical SMILES.

        Example:
            ```python
            struct = Structure.from_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")

            print(struct.ids.smiles)
            # Output: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C'

            print(struct.ids.canonical_smiles)
            # Output: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C'
            ```
        """
        dict_repr = smiles_to_structure(smiles, program, force_field)
        dict_repr["multiplicity"] = multiplicity
        return cls(**dict_repr)

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
            xyz_str: The XYZ string.
            charge: The molecular charge of the structure. If not provided, will read
                from the XYZ string if set or default to 0.
            multiplicity: The molecular multiplicity of the structure. If not provided,
                will read from the XYZ string if set or default to 1.

        Note:
            Will read qcio data such as `charge` and `multiplicity` from the comments
            line with a `qcio_key=value` format (if it is present). Also will read in
            qcio__identifiers_* keys and additional non-qcio comments.

        Example:
            ```python
            struct = Structure.from_xyz(xyz_str)
            ```
        """

        lines = xyz_str.split("\n")

        num_atoms = int(lines[0])

        # Collect comments
        structure_kwargs: Dict[str, Any] = {}
        identifier_kwargs: Dict[str, Any] = {}
        other_comments: List[str] = []

        for item in lines[1].strip().split():
            if item.startswith("qcio__identifiers_"):
                key = item.split("=")[0].replace("qcio__identifiers_", "")
                value = item.split("=")[1]
                identifier_kwargs[key] = value
            elif item.startswith("qcio_"):
                key = item.split("=")[0].replace("qcio_", "")
                value = item.split("=")[1]
                structure_kwargs[key] = value
            else:
                other_comments.append(item)

        if charge is not None and "charge" in structure_kwargs:
            raise ValueError("Charge cannot be set in the file and as an argument.")
        if multiplicity is not None and "multiplicity" in structure_kwargs:
            raise ValueError(
                "Multiplicity cannot be set in the file and as an argument."
            )

        # Set charge and multiplicity if provided
        if charge is not None:
            structure_kwargs["charge"] = charge
        if multiplicity is not None:
            structure_kwargs["multiplicity"] = multiplicity

        symbols = []
        geometry = []
        for line in lines[2 : 2 + num_atoms]:
            split_line = line.split()
            symbols.append(split_line[0])
            geometry.append([float(val) / BOHR_TO_ANGSTROM for val in split_line[1:]])

        return cls(
            symbols=symbols,
            geometry=geometry,
            **structure_kwargs,
            identifiers=Identifiers(**identifier_kwargs),
            extras={cls._xyz_comment_key: other_comments},
        )

    @classmethod
    def from_xyz_multi(
        cls,
        xyz_str: str,
        charge: Optional[int] = None,
        multiplicity: Optional[int] = None,
    ) -> List["Structure"]:
        """Parse a multi-structure XYZ file into a list of Structure objects.

        Args:
            xyz_str: The multi-structure XYZ string.

        Returns:
            A list of Structure objects.
        """
        lines = xyz_str.strip().split("\n")
        structures = []
        i = 0

        while i < len(lines):
            num_atoms = int(lines[i])
            structure_block = "\n".join(lines[i : i + num_atoms + 2])
            structure = cls.from_xyz(
                structure_block, charge=charge, multiplicity=multiplicity
            )
            structures.append(structure)
            i += num_atoms + 2
            while i < len(lines) and not lines[i].strip():
                i += 1  # Skip any empty lines between structures

        return structures

    def distance(
        self, i: int, j: int, units: DistanceUnits = DistanceUnits.bohr
    ) -> float:
        """Calculate the distance between two atoms.

        Args:
            i: The index of the first atom.
            j: The index of the second atom.
            units: The units to return the distance in. Defaults to "bohr".
                May be "bohr" or "angstrom".

        Returns:
            The distance between the atoms in units (Bohr or Angstrom).

        Example:
            ```python
            struct.distance(0, 1)
            1.34
            ```
        """
        distance = np.linalg.norm(self.geometry[i] - self.geometry[j])
        if units == DistanceUnits.angstrom:
            return float(distance * BOHR_TO_ANGSTROM)
        return float(distance)

    def to_smiles(self, program: str = "rdkit", hydrogens: bool = False) -> str:
        """Generate the canonical SMILES representation of the structure.

        Args:
            program: The program to use for the conversion. Defaults to "rdkit".
            hydrogens: Whether to include hydrogens in the SMILES string. Defaults to
                False.

        Returns:
            The canonical SMILES representation of the structure.

        Example:
            ```python
            struct.to_smiles()
            'CN1C=NC2=C1C(=O)N(C(=O)N2C)C'
            ```
        """
        return structure_to_smiles(self, program=program, hydrogens=hydrogens)

    def to_xyz(self, precision: int = 17) -> str:
        """Return an xyz string representation of the structure.

        Args:
            precision: The number of decimal places to include in the xyz file. Default
                17 which captures all precision of float64.
        Notes:
            Will add qcio data such as charge and multiplicity to the comments line with
            a `qcio_key=value` format.
        """

        qcio_data = {  # These get added to comments line (line 2) in xyz file
            "qcio_charge": self.charge,
            "qcio_multiplicity": self.multiplicity,
        }

        # Add identifiers to qcio_data
        for key, value in self.identifiers.__dict__.items():
            if key != "extras" and value:
                qcio_data[f"qcio__identifiers_{key}"] = value

        assert isinstance(self.geometry, np.ndarray)  # For mypy
        geometry_angstrom = self.geometry * BOHR_TO_ANGSTROM

        xyz_lines = []
        xyz_lines.append(f"{len(self.symbols)}")
        # Add qcio data to comments line
        comments = f"{' '.join([f'{k}={v}' for k, v in qcio_data.items()])}"
        # Add any other comments
        if xyz_comments := self.extras.get(self._xyz_comment_key, []):
            comments += " " + " ".join(xyz_comments)
        xyz_lines.append(comments)

        # Create a format string using the precision parameter
        format_str = f"{{:2s}} {{: >18.{precision}f}} {{: >18.{precision}f}} {{: >18.{precision}f}}"  # noqa: E501

        for symbol, (x, y, z) in zip(self.symbols, geometry_angstrom):
            xyz_lines.append(format_str.format(symbol, x, y, z))
        xyz_lines.append("")  # Append newline to end of file
        return "\n".join(xyz_lines)

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
        program: str = "rdkit",
        hydrogens: bool = False,
    ) -> None:
        """Add SMILES data to the identifiers. The SMILES will be generated from the
            structure using the specified program.

        Args:
            program: The program to use to generate the SMILES. Defaults to "rdkit".
            hydrogens: Whether to include hydrogens in the SMILES string. Defaults to
                False.

        Example:
            ```python
            struct.add_smiles()
            struct.ids.smiles
            'CCO'
            struct.ids.canonical_smiles
            'CCO'
            ```
        """
        smiles = self.to_smiles(program=program, hydrogens=hydrogens)
        identifiers = {"smiles": smiles}

        if hydrogens:
            identifiers["canonical_explicit_hydrogen_smiles"] = smiles
        else:
            identifiers["canonical_smiles"] = smiles

        identifiers["canonical_smiles_program"] = program
        self.add_identifiers(identifiers)
        # Ensure pydantic knows the field has been set
        self.__pydantic_fields_set__.add("identifiers")

    def add_identifiers(self, identifiers: Dict[str, str]) -> None:
        """Add an identifier to the structure.

        Args:
            identifiers: The identifiers to add to the structure.

        Example:
            ```python
            struct.add_identifiers({"name": "water"})
            struct.ids.name
            'water'
            ```

            ```python
            struct.add_identifier({"smiles": "CCO"})
            struct.ids.smiles
            'CCO'
            ```
        """
        # Ensure the identifier is valid
        for identifier in identifiers.keys():
            assert hasattr(
                self.identifiers, identifier
            ), f"Invalid identifier: '{identifier}'"

        new_identifiers = self.identifiers.model_copy(update=identifiers)
        object.__setattr__(self, "identifiers", new_identifiers)

    @model_validator(mode="before")
    def _validate_symbols_and_geometry(cls, values):
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
    def _serialize_connectivity(self, connectivity, _info) -> List[List[float]]:
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
        """Return the molecular formula of the structure using the Hill System."""
        # https://chemistry.stackexchange.com/questions/1239/order-of-elements-in-a-formula

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

    def swap_indices(self, indices: List[Tuple[int, int]]) -> None:
        """Swap the indices in the symbols and geometry list.

        Args:
            indices: A list of tuples containing the indices to swap. E.g.,
                [(0, 1), (2, 3)] will swap the first and second atoms and the third
                and fourth atoms.
        """
        # Validate indices
        old_set = set()
        new_set = set()
        for old, new in indices:
            error = False
            error_message = ""
            if old in old_set:
                error_message += (
                    f"Duplicated old index: {old}. You cannot move an atom twice. "
                )
                error = True
            if new in new_set:
                error_message += (
                    f"Duplicated new index: {new}. You cannot move two atoms to the "
                    "same index."
                )
                error = True
            if error:
                raise ValueError(error_message)

            old_set.add(old)
            new_set.add(new)

        # Perform reordering
        new_symbols = [s for s in self.symbols]
        new_geometry = np.array([g for g in self.geometry])
        for old, new in indices:
            new_symbols[new] = self.symbols[old]
            new_geometry[new] = self.geometry[old]

        object.__setattr__(self, "symbols", new_symbols)
        object.__setattr__(self, "geometry", new_geometry)


@renamed_class(Structure)
class Molecule(Structure):
    pass
