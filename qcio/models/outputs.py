"""End user output and results objects from a calculation."""

from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, Optional, Union

import numpy as np
from pydantic import field_validator

from qcio.helper_types import ArrayLike2D, ArrayLike3D

from .base_models import QCIOModelBase
from .inputs import DualProgramInput, FileInput, ProgramInput
from .molecule import Molecule
from .outputs_base import OutputBase, ResultsBase, SuccessfulOutputBase

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import ReprArgs


__all__ = [
    "FileOutput",
    "SinglePointOutput",
    "OptimizationOutput",
    "ProgramFailure",
    "SinglePointResults",
    "Wavefunction",
    "OptimizationResults",
]


class FileOutput(SuccessfulOutputBase):
    """Generic output class for pure file based I/O.

    Attributes:
        input_data: The FileInput object used for the computation.
        files: A dict mapping filename to str or bytes data.
        success: A boolean indicator that the operation succeeded (always True)
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the results.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    input_data: FileInput


class Wavefunction(QCIOModelBase):
    """The wavefunction for a single point calculation.

    Attributes:
        scf_eigenvalues_a: The SCF alpha-spin orbital eigenvalues.
        scf_eigenvalues_b: The SCF beta-spin orbital eigenvalues.
        scf_occupations_a: The SCF alpha-spin orbital occupations.
        scf_occupations_b: The SCF beta-spin orbital occupations.
    """

    scf_eigenvalues_a: Optional[ArrayLike2D] = None
    scf_eigenvalues_b: Optional[ArrayLike2D] = None
    scf_occupations_a: Optional[ArrayLike2D] = None
    scf_occupations_b: Optional[ArrayLike2D] = None

    @field_validator(
        "scf_eigenvalues_a",
        "scf_eigenvalues_b",
        "scf_occupations_a",
        "scf_occupations_b",
    )
    @classmethod
    def to_numpy(cls, val, _info) -> Optional[np.ndarray]:
        return np.asarray(val) if val is not None else None


class SinglePointResults(ResultsBase):
    """The computed results from a single point calculation.

    Attributes:
        calcinfo_natoms: The number of atoms as computed by the program.
        calcinfo_nalpha: The number of alpha electrons as computed by the program.
        calcinfo_nbeta: The number of beta electrons as computed by the program.
        calcinfo_nbasis: The number of basis functions in the calculation.
        calcinfo_nmo: The number of molecular orbitals in the calculation

        energy: The electronic energy of the molecule in Hartrees.
        gradient: The gradient of the molecule in Hartrees/Bohr.
        hessian: The hessian of the molecule in Hartrees/Bohr^2.
        nuclear_repulsion_energy: The nuclear repulsion energy of the molecule in
            Hartrees.

        wavefunction: Wavefunction data from the calculation.

        freqs_wavenumber: The frequencies of the molecule in wavenumbers.
        normal_modes_cartesian: 3D n_vibmodes x n_atoms x 3 array containing
            un-mass-weighted Cartesian displacements of each normal mode.
        gibbs_free_energy: Gibbs free energy (i.e. thermochemical analysis) in Hartrees
            of a system where translation / rotation / vibration degrees of freedom are
            approximated using ideal gas / rigid rotor / harmonic oscillator
            respectively.
        scf_dipole_moment: The x, y, z component of the dipole moment of the molecule
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
    gradient: Optional[ArrayLike2D] = None
    hessian: Optional[ArrayLike2D] = None
    nuclear_repulsion_energy: Optional[float] = None

    # Wavefunction data
    wavefunction: Optional[Wavefunction] = None

    # Frequency data
    freqs_wavenumber: List[float] = []
    normal_modes_cartesian: Optional[ArrayLike3D] = None
    gibbs_free_energy: Optional[float] = None

    # SCF results
    scf_dipole_moment: Optional[List[float]] = None

    @field_validator("normal_modes_cartesian")
    @classmethod
    def validate_normal_modes_cartesian_shape(cls, v: ArrayLike3D):
        if v is not None:
            # Assume array has length of the number of normal modes
            n_normal_modes = len(v)
            return np.asarray(v).reshape(n_normal_modes, -1, 3)

    @field_validator("gradient")
    @classmethod
    def validate_gradient_shape(cls, v: ArrayLike2D):
        """Validate gradient is n x 3"""
        if v is not None:
            return np.asarray(v).reshape(-1, 3)

    @field_validator("hessian")
    @classmethod
    def validate_hessian_shape(cls, v: ArrayLike2D):
        """Validate hessian is square"""
        if v is not None:
            v = np.asarray(v)
            n = int(np.sqrt(v.size))
            return v.reshape((n, n))


class SinglePointOutput(SuccessfulOutputBase):
    """Output from a successful single point calculation.

    Attributes:
        input_data: The SinglePointInput object for the computation.
        success: Always True for a successful computation.
        results: The results computed by the program.
        files: A dict mapping filename to str or bytes data.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the results.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    input_data: ProgramInput
    results: SinglePointResults

    @property
    def return_result(self) -> Union[float, ArrayLike2D]:
        """Return the result of the calculation.

        Returns:
            The explicitly requested result of the calculation, i.e., the energy,
                gradient, or hessian.
        """
        return getattr(self.results, self.input_data.calctype.value)


class OptimizationResults(ResultsBase):
    """Computed properties for an optimization.

    Attributes:
        energies: The energies for each step of the optimization.
        molecules: The Molecule objects for each step of the optimization.
        final_molecule: The final, optimized molecule.
        trajectory: The SinglePointOutput objects for each step of the optimization.
    """

    trajectory: List[SinglePointOutput] = []

    @property
    def final_molecule(self) -> Optional[Molecule]:
        """The final molecule in the optimization."""
        try:
            return self.trajectory[-1].input_data.molecule
        except IndexError:  # Empty trajectory
            return None

    @property
    def energies(self) -> List[float]:
        """The energies for each step of the optimization."""
        # or 0.0 covers null case for mypy
        return [output.results.energy or 0.0 for output in self.trajectory]

    @property
    def molecules(self) -> List[Molecule]:
        """The Molecule objects for each step of the optimization."""
        return [output.input_data.molecule for output in self.trajectory]

    def __repr_args__(self):
        """Custom repr to avoid printing the entire collection objects."""
        return [
            ("final_molecule", f"{self.final_molecule}"),
            ("trajectory", "[...]"),
            ("energies", "[...]"),
            ("molecules", "[...]"),
        ]

    def save(
        self,
        filepath: Union[Path, str],
        exclude_none=True,
        indent: int = 4,
        **kwargs,
    ) -> None:
        """Save an OptimizationOutput to a file.

        Args:
            filepath: The path to save the molecule to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Notes:
            If the filepath has a .xyz extension, the trajectory will be saved to an XYZ
            file.
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            text = "".join(
                sp_output.input_data.molecule.to_xyz() for sp_output in self.trajectory
            )
            filepath.write_text(text)
            return
        super().save(filepath, exclude_none, indent, **kwargs)


class OptimizationOutput(SuccessfulOutputBase):
    """Output from a successful optimization.

    Attributes:
        input_data: The OptimizationInput object for the computation.
        results: The results computed by the program.
    """

    input_data: Union[DualProgramInput, ProgramInput]
    results: OptimizationResults


class ProgramFailure(OutputBase):
    """A object containing details about a failed calculation.

    Attributes:
        input_data: The input object for the computation.
        success: Always False for a Failed output.
        traceback: String representation of the traceback of the exception that caused
            the failure.
        results: Any compted data that was able to be extracted before program failed.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
    """

    input_data: Union[DualProgramInput, ProgramInput, FileInput]
    success: Literal[False] = False
    traceback: Optional[str] = None

    @property
    def ptraceback(self) -> None:
        """Print the traceback text"""
        print(self.traceback)

    def __repr_args__(self) -> "ReprArgs":
        """Exclude traceback from the repr"""
        return [
            (key, value if key != "traceback" else "<...>")
            for key, value in super().__repr_args__()
        ]
