"""End user output and results objects from a calculation."""

from __future__ import annotations

import sys
import warnings
from itertools import product
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_args,
)

import numpy as np
from pydantic import field_validator, model_validator
from typing_extensions import Self

from qcio.helper_types import SerializableNDArray

from .base_models import CalcType, Files, Provenance, QCIOModelBase
from .inputs import DualProgramInput, FileInput, Inputs, InputType, ProgramInput
from .structure import Structure
from .utils import deprecated_class

if TYPE_CHECKING:  # pragma: no cover
    pass


__all__ = [
    "SinglePointResults",
    "Wavefunction",
    "OptimizationResults",
    "ProgramOutput",
    "ResultsType",
    "Results",
    "SinglePointOutput",
    "ProgramFailure",
    "OptimizationOutput",
    "ConformerSearchResults",
]


class Wavefunction(QCIOModelBase):
    """The wavefunction for a single point calculation.

    Attributes:
        scf_eigenvalues_a: The SCF alpha-spin orbital eigenvalues.
        scf_eigenvalues_b: The SCF beta-spin orbital eigenvalues.
        scf_occupations_a: The SCF alpha-spin orbital occupations.
        scf_occupations_b: The SCF beta-spin orbital occupations.
    """

    scf_eigenvalues_a: Optional[SerializableNDArray] = None
    scf_eigenvalues_b: Optional[SerializableNDArray] = None
    scf_occupations_a: Optional[SerializableNDArray] = None
    scf_occupations_b: Optional[SerializableNDArray] = None

    @field_validator(
        "scf_eigenvalues_a",
        "scf_eigenvalues_b",
        "scf_occupations_a",
        "scf_occupations_b",
    )
    @classmethod
    def to_numpy(cls, val, _info) -> Optional[np.ndarray]:
        return np.asarray(val) if val is not None else None


class SinglePointResults(Files):
    """The computed results from a single point calculation.

    Attributes:
        calcinfo_natoms: The number of atoms as computed by the program.
        calcinfo_nalpha: The number of alpha electrons as computed by the program.
        calcinfo_nbeta: The number of beta electrons as computed by the program.
        calcinfo_nbasis: The number of basis functions in the calculation.
        calcinfo_nmo: The number of molecular orbitals in the calculation.

        energy: The electronic energy of the structure in `Hartrees`.
        gradient: The gradient of the structure in `Hartrees/Bohr`.
        hessian: The hessian of the structure in `Hartrees/Bohr^2`.
        nuclear_repulsion_energy: The nuclear repulsion energy of the structure in
            Hartrees.

        wavefunction: Wavefunction data from the calculation.

        freqs_wavenumber: The frequencies of the structure in wavenumbers.
        normal_modes_cartesian: 3D n_vibmodes x n_atoms x 3 array containing
            un-mass-weighted Cartesian displacements of each normal mode.
        gibbs_free_energy: Gibbs free energy (i.e. thermochemical analysis) in Hartrees
            of a system where translation / rotation / vibration degrees of freedom are
            approximated using ideal gas / rigid rotor / harmonic oscillator
            respectively.
        scf_dipole_moment: The x, y, z component of the dipole moment of the structure
            in units of e a0 (NOT Debye!).

    """

    # calcinfo contains general information about the calculation
    calcinfo_natoms: Optional[int] = None
    calcinfo_nbasis: Optional[int] = None
    calcinfo_nmo: Optional[int] = None
    calcinfo_nalpha: Optional[int] = None
    calcinfo_nbeta: Optional[int] = None

    # Core properties
    energy: Optional[float] = None
    gradient: Optional[SerializableNDArray] = None  # Coerced to 2D array
    hessian: Optional[SerializableNDArray] = None  # Coerced to 2D array
    nuclear_repulsion_energy: Optional[float] = None

    # Wavefunction data
    wavefunction: Optional[Wavefunction] = None

    # Frequency data
    freqs_wavenumber: List[float] = []
    normal_modes_cartesian: Optional[SerializableNDArray] = None  # Coerced to 3D array
    gibbs_free_energy: Optional[float] = None

    # SCF results
    scf_dipole_moment: Optional[List[float]] = None

    @field_validator("normal_modes_cartesian")
    @classmethod
    def _validate_normal_modes_cartesian_shape(cls, v: SerializableNDArray):
        if v is not None:
            # Assume array has length of the number of normal modes
            n_normal_modes = len(v)
            return np.asarray(v).reshape(n_normal_modes, -1, 3)

    @field_validator("gradient")
    @classmethod
    def _validate_gradient_shape(cls, v: SerializableNDArray):
        """Validate gradient is n x 3"""
        if v is not None:
            return np.asarray(v).reshape(-1, 3)

    @field_validator("hessian")
    @classmethod
    def _validate_hessian_shape(cls, v: SerializableNDArray):
        """Validate hessian is square"""
        if v is not None:
            v = np.asarray(v)
            n = int(np.sqrt(v.size))
            return v.reshape((n, n))

    def return_result(self, calctype: CalcType) -> Union[float, SerializableNDArray]:
        """Return the primary result of the calculation."""
        return getattr(self, calctype.value)

    @model_validator(mode="after")
    def _ensure_results(self) -> Self:
        """Ensure that at least one result is present."""
        if all(
            result is None
            for result in [
                self.energy,
                self.gradient,
                self.hessian,
            ]
        ):
            raise ValueError(
                "SinglePointResults requires either an energy, gradient, or hessian "
                "value."
            )
        return self


class OptimizationResults(Files):
    """Computed properties for an optimization.

    Attributes:
        energies: The energies for each step of the optimization.
        structures: The Structure objects for each step of the optimization.
        final_structure: The final, optimized Structure.
        trajectory: The SinglePointOutput objects for each step of the optimization.
    """

    trajectory: List[
        Union[
            ProgramOutput[ProgramInput, SinglePointResults],
            ProgramOutput[ProgramInput, Files],
        ]
    ] = []

    @property
    def final_structure(self) -> Structure:
        """The final Structure in the optimization."""
        return self.structures[-1]

    @property
    def final_molecule(self) -> Structure:
        warnings.warn(
            ".final_molecule is being depreciated and will be removed in a future. "
            "Please use .final_structure instead.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.final_structure

    @property
    def final_energy(self) -> Optional[float]:  # Optional for np.nan
        """
        The final energy in the optimization. Is `np.nan` if final calculation failed.
        """
        return self.energies[-1]

    @property
    def energies(self) -> np.ndarray:
        """The energies for each step of the optimization."""
        return np.array(
            [
                # ensure_structured_results_on_success validator ensures .results
                # is not Files if success is True so # type: ignore
                output.results.energy if output.success else np.nan  # type: ignore
                for output in self.trajectory
            ],
            dtype=float,
        )

    @property
    def structures(self) -> List[Structure]:
        """The Structure objects for each step of the optimization."""
        return [output.input_data.structure for output in self.trajectory]

    @property
    def molecules(self) -> List[Structure]:
        """The Structure objects for each step of the optimization."""
        warnings.warn(
            ".molecules is being depreciated and will be removed in a future. "
            "Please use .structures instead.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.structures

    def return_result(self, calctype: CalcType) -> Optional[Structure]:
        """Return the primary result of the calculation."""
        return self.final_structure

    def __repr_args__(self):
        """Custom repr to avoid printing the entire collection of objects."""
        return [
            ("final_structure", f"{self.final_structure}"),
            ("trajectory", "[...]"),
            ("energies", "[...]"),
            ("structures", "[...]"),
        ]

    def to_xyz(self) -> str:
        """Return the trajectory as an `xyz` string."""
        return "".join(
            prog_output.input_data.structure.to_xyz() for prog_output in self.trajectory
        )

    def save(
        self,
        filepath: Union[Path, str],
        exclude_none: bool = True,
        exclude_unset: bool = True,
        indent: int = 4,
        **kwargs: Dict[str, Any],
    ) -> None:
        """Save an OptimizationOutput to a file.

        Args:
            filepath: The path to save the molecule to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            exclude_unset: If True, attributes that have not been set will not be
                written to the file.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Note:
            If the filepath has a `.xyz` extension, the trajectory will be saved to a
            multi-structure `xyz` file.
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            filepath.write_text(self.to_xyz())
            return
        super().save(filepath, exclude_none, exclude_unset, indent, **kwargs)


class ConformerSearchResults(Files):
    """Results from a conformer search calculation.

    Conformers and rotamers are sorted by energy.

    Attributes:
        conformers: The conformers found in the search.
        conformer_energies: The energies for each conformer.
        rotamers: The rotamers found in the search.
        rotamer_energies: The energies for each rotamer.
    """

    conformers: List[Structure] = []
    conformer_energies: SerializableNDArray = np.array([])
    rotamers: List[Structure] = []
    rotamer_energies: SerializableNDArray = np.array([])

    @model_validator(mode="after")
    def _energies_size(self) -> "ConformerSearchResults":
        """Ensure the energies are the same size as the conformers and rotamers."""
        if self.conformer_energies.size > 0 and (
            self.conformer_energies.size != len(self.conformers)
        ):
            raise ValueError(
                "The number of conformer energies must match the number of conformers."
            )
        if self.rotamer_energies.size > 0 and (
            self.rotamer_energies.size != len(self.rotamers)
        ):
            raise ValueError(
                "The number of rotamer energies must match the number of rotamers."
            )
        return self

    @model_validator(mode="after")
    def _sort_by_energy(self) -> "ConformerSearchResults":
        """Sort conformers and rotamers by energy."""

        # Sort conformers and their energies together
        if self.conformer_energies.size > 0:
            sorted_indices = np.argsort(self.conformer_energies)
            self.conformers[:] = [self.conformers[i] for i in sorted_indices]
            self.conformer_energies[:] = self.conformer_energies[sorted_indices]

        # Sort rotamers and their energies together
        if self.rotamer_energies.size > 0:
            sorted_indices = np.argsort(self.rotamer_energies)
            self.rotamers[:] = [self.rotamers[i] for i in sorted_indices]
            self.rotamer_energies[:] = self.rotamer_energies[sorted_indices]

        return self

    @property
    def conformer_energies_relative(self) -> np.ndarray:
        """The relative energies for each conformer in the search."""
        if self.conformer_energies.size == 0:
            return np.array([])
        return self.conformer_energies - self.conformer_energies.min()

    @property
    def rotamer_energies_relative(self) -> np.ndarray:
        """The relative energies for each rotamer in the search."""
        if self.rotamer_energies.size == 0:
            return np.array([])
        return self.rotamer_energies - self.rotamer_energies.min()


Results = Union[Files, SinglePointResults, OptimizationResults, ConformerSearchResults]
ResultsType = TypeVar("ResultsType", bound=Results)


class ProgramOutput(QCIOModelBase, Generic[InputType, ResultsType]):
    """The core output object from a quantum chemistry calculation.

    Attributes:
        input_data: The input data for the calculation. Any of `qcio.Inputs`.
        success: Whether the calculation was successful.
        results: The results of the calculation. Contains parsed values and files.
            Any of `qcio.Results`.
        stdout: The standard output from the calculation.
        traceback: The traceback from the calculation, if it failed.
        provenance: The provenance information for the calculation.
        extras Dict[str, Any]: Additional information to bundle with the object. Use for
            schema development and scratch space.
        pstdout str: `@property` Print the stdout text.
        ptraceback str: `@property` Print the traceback text.
    """

    input_data: InputType
    success: Literal[True, False]
    results: ResultsType
    stdout: Optional[str] = None
    traceback: Optional[str] = None
    provenance: Provenance

    def __init__(self, **data: Any):
        """Backwards compatibility for files attribute."""

        if "files" in data:
            warnings.warn(
                "The 'files' attribute has been moved to 'results.files'. Please "
                "update your code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )

            # This moves files from the top level to the results attribute
            if isinstance(data["results"], dict):
                results_files_dict = data["results"].get("files", {})
            else:  # data["results"] is Files, SinglePointResults, OptimizationResults
                results_files_dict = data["results"].files

            results_files_dict.update(**data.pop("files"))

        super().__init__(**data)

    def model_post_init(self, __context) -> None:
        """Parameterize the class (if not set explicitly)."""
        # Check if the current class is still generic, do not override if explicitly set
        if self.__class__ is ProgramOutput:
            input_type = type(self.input_data)
            results_type = type(self.results)
            self.__class__ = ProgramOutput[input_type, results_type]  # type: ignore # noqa 501

    @model_validator(mode="after")
    def ensure_traceback_on_failure(self) -> Self:
        if self.success is False:
            assert (
                self.traceback is not None
            ), "A traceback must be provided for failed calculations."
        return self

    @model_validator(mode="after")
    def _ensure_structured_results_on_success(self) -> Self:
        """Ensure structured results are provided for successful, non FileInputs."""
        # Covers case of ProgramInput and DualProgramInput
        if self.success is True and isinstance(self.input_data, ProgramInput):
            assert type(self.results) is not Files, (
                "Structured results must be provided for successful, non FileInput "
                "calculations."
            )

        return self

    @model_validator(mode="after")
    def ensure_primary_result_on_success(self) -> Self:
        if type(self.results) is SinglePointResults:
            # Ensure the primary calctype result is present
            calctype_val = self.input_data.calctype.value  # type: ignore
            assert (
                getattr(self.results, calctype_val) is not None
            ), f"Missing the primary result: {calctype_val}."

        return self

    @property
    def pstdout(self) -> None:
        """Print the stdout text"""
        print(self.stdout)

    @property
    def ptraceback(self) -> None:
        """Print the traceback text"""
        print(self.traceback)

    def __repr_args__(self) -> List[Tuple[str, Any]]:
        """Exclude stdout and traceback from the repr and ensure success is first"""
        args = super().__repr_args__()

        # Replace stdout and traceback with "<...>"
        filtered_args = [
            (key, value if key not in {"stdout", "traceback"} else "<...>")
            for key, value in args
        ]
        # Ensure success is first
        success_arg = [(key, value) for key, value in filtered_args if key == "success"]
        other_args = [(key, value) for key, value in filtered_args if key != "success"]
        return success_arg + other_args

    @property
    def files(self) -> Dict[str, Union[str, bytes]]:
        """Return the files attribute."""
        # Depreciation warning
        warnings.warn(
            ".files has been moved to .results.files. "
            "Please access it there going forward.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.results.files

    @property
    def return_result(self) -> Union[float, SerializableNDArray, Optional[Structure]]:
        """Return the primary result of the calculation."""
        warnings.warn(
            ".return_result is being depreciated and will be removed in a future. "
            "Please access results directly at .results instead.",
            category=FutureWarning,
            stacklevel=2,
        )
        # For mypy
        assert self.results is not None, "No results exist on this ProgramOutput"
        assert type(self.input_data) is not FileInput, "FileInputs have no results."
        return self.results.return_result(self.input_data.calctype)  # type: ignore


# For compatibility with old API
@deprecated_class("ProgramOutput[StructuredInputs, OptimizationResults]")
class OptimizationOutput(ProgramOutput[DualProgramInput, OptimizationResults]):
    success: Literal[True] = True
    traceback: Optional[str] = None


@deprecated_class("ProgramOutput[ProgramInput, SinglePointResults]")
class SinglePointOutput(ProgramOutput[ProgramInput, SinglePointResults]):
    success: Literal[True] = True
    traceback: Optional[str] = None


@deprecated_class("ProgramOutput[StructuredInputs, Results]")
class ProgramFailure(ProgramOutput[Inputs, Results]):
    success: Literal[False] = False


# Register the concrete classes for serialization
def _register_program_output_classes():
    """Required so that pickle can find the concrete classes for serialization."""
    for input_type, results_type in product(get_args(Inputs), get_args(Results)):
        _class = ProgramOutput[input_type, results_type]
        name = _class.__name__
        this_module = sys.modules[__name__]
        if name not in this_module.__dict__:
            # Directly declare the type to ensure it is registered
            setattr(this_module, name, _class)


# Call this function during module initialization
_register_program_output_classes()
