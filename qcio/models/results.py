"""Objects containing computed result values from a calculation."""
from __future__ import annotations

from typing import List, Optional

import numpy as np
from pydantic import validator

from qcio.helper_types import ArrayLike2D

from .base_models import QCIOModelBase
from .molecule import Molecule
from .outputs_base import ResultsBase

__all__ = ["SinglePointResults", "Wavefunction", "OptimizationResults"]


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

    _to_numpy = validator(
        "scf_eigenvalues_a",
        "scf_eigenvalues_b",
        "scf_occupations_a",
        "scf_occupations_b",
        allow_reuse=True,
    )(lambda x: np.asarray(x) if x is not None else None)


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
        normal_modes_cartesian: n_vibmodes*n_atoms length array containing
            un-mass-weighted Cartesian displacements of each normal mode.
        gibbs_free_energy: Gibbs free energy (i.e. thermochemical analysis) in Hartrees
            of a system where translation / rotation / vibration degrees of freedom are
            approximated using ideal gas / rigid rotor / harmonic oscillator
            respectively.
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
    normal_modes_cartesian: List[float] = []
    gibbs_free_energy: Optional[float] = None

    @validator("gradient")
    def validate_gradient_shape(cls, v: ArrayLike2D):
        """Validate gradient is n x 3"""
        if v is not None:
            return np.asarray(v).reshape(-1, 3)

    @validator("hessian")
    def validate_hessian_shape(cls, v: ArrayLike2D):
        """Validate hessian is square"""
        if v is not None:
            v = np.asarray(v)
            n = int(np.sqrt(v.size))
            return v.reshape((n, n))


class OptimizationResults(ResultsBase):
    """Computed properties for an optimization.

    Attributes:
        energies: The energies for each step of the optimization.
        # NOTE: Maybe should just be be geometries since all other data is duplicated?
        molecules: The Molecule objects for each step of the optimization. Must contain
            at least one Molecule corresponding to the final geometry.
        sp_outputs: The SinglePointOutput objects for each step of the optimization.
    """

    energies: List[float]
    molecules: List[Molecule]
    # NOTE: This is a circular import, hence the ignores.
    sp_outputs: List["SinglePointOutput"] = []  # type: ignore  # noqa: F821
