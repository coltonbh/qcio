from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

import numpy as np
from pydantic import BaseModel, validator

from qcio.helper_types import ArrayLike2D

from .base_io import (
    ComputedPropsBase,
    FailureBase,
    ProgramArgs,
    ProgramInputBase,
    Provenance,
    ResultBase,
)
from .base_model import QCIOModelBase

if TYPE_CHECKING:  # pragma: no cover
    pass

__all__ = [
    "Model",
    "SinglePointCalcType",
    "SinglePointInput",
    "SinglePointResult",
    "SinglePointFailure",
    "SinglePointComputedProps",
    "Wavefunction",
]


class SinglePointCalcType(str, Enum):
    """The single point calculation type."""

    energy = "energy"
    gradient = "gradient"
    hessian = "hessian"

    def __repr__(self) -> str:
        """Custom repr for CalcType"""
        return f"'{self.name}'"  # pragma: no cover


class Model(BaseModel):
    """The model for the quantum chemistry calculation.

    Attributes:
        method: The name of the method to be used in the calculation. Named according to
            the convention of the program being called. If an MM calculation the name of
            the force field.
        basis: The name of the basis set to be used in the calculation. Named according
            to the convention of the program being called.
    """

    method: str
    basis: Optional[str] = None


class SinglePointArgs(ProgramArgs):
    """The arguments for a single point calculation. Breaks out model from keywords.

    Attributes:
        model: The model for the quantum chemistry calculation.
        keywords: A dict of keywords to be passed to the program. Defaults to an empty
            dict.
        files: Files to be passed to the QC program.
        extras: Additional information to bundle with the object. Use for schema
    """

    model: Model


class SinglePointInput(SinglePointArgs, ProgramInputBase):
    """Input for a single point calculation.

    Attributes:
        calctype: The type of calculation to perform.
        model: The model for the quantum chemistry calculation.
        keywords: A dict of keywords to be passed to the program. Defaults to an empty
            dict.
        files: Files to be passed to the QC program.
        molecule: The molecule to be used in the calculation.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    calctype: SinglePointCalcType

    def get_failed_output_class(self) -> Type["SinglePointFailure"]:
        """Return the FailedOutput class for this input class."""
        return SinglePointFailure

    def get_successful_output_class(self) -> Type[ResultBase]:
        return SinglePointResult

    def to_qcel(self) -> Dict[str, Any]:
        """Return the QCElemental v1 input schema representation of the input
        (AtomicInput dict).

        Returns:
            The QCElemental v1 dict representation of an AtomicInput object.
        """
        return {
            "molecule": {
                "symbols": self.molecule.symbols,
                "geometry": self.molecule.geometry,
                "molecular_charge": self.molecule.charge,
                "molecular_multiplicity": self.molecule.multiplicity,
                "identifiers": {
                    key: value
                    for key, value in self.molecule.identifiers.dict().items()
                    if key not in ["name_IUPAC", "name_common"]  # not on qcel model
                },
            },
            "driver": self.calctype,
            "model": self.model.dict(),
            "keywords": self.keywords,
            "extras": self.extras,
        }

    def to_output_from_qcel(
        self,
        qcel_output: Dict[str, Any],
    ) -> Union["SinglePointResult", "SinglePointFailure"]:
        """Create a SinglePointSuccessfulOutput or SinglePointFailedOutput from the
        QCElemental v1 output schema representation of the output (AtomicResult dict).

        Args:
            provenance: The qcio Provenance object for the output.
            qcel_output: The QCElemental v1 output schema representation of the output.
                May be a dict representing an AtomicResult or FailedOperation.
        """
        prov_extras = {"NOTE": "Computed by QCEngine"}

        if qcel_output["success"] is False:
            return SinglePointFailure(
                input_data=self,
                traceback=qcel_output["error"]["error_message"],
                provenance=Provenance(
                    program=qcel_output["input_data"]["provenance"]["creator"],
                    program_version=qcel_output["input_data"]["provenance"].get(
                        "version"
                    ),
                    wall_time=qcel_output["input_data"]["provenance"].get("wall_time"),
                    extras=prov_extras,
                ),
                extras=qcel_output["extras"] or {},  # Because .extras may be None
            )
        else:
            # Collect values from keys that exist in qcio
            qcio_to_qcel = {
                "calcinfo_natoms": "calcinfo_natom",
                "energy": "return_energy",
                "gradient": "return_gradient",
                "hessian": "return_hessian",
            }
            computed = {}
            for key in SinglePointComputedProps.__annotations__:
                if key in qcio_to_qcel:
                    qcel_key = qcio_to_qcel[key]
                else:
                    qcel_key = key
                computed[key] = qcel_output["properties"].get(qcel_key)

            if qcel_output["wavefunction"]:
                computed["wfn"] = {
                    key: value
                    for key, value in qcel_output["wavefunction"].items()
                    if key in Wavefunction.__annotations__
                }

            return SinglePointResult(
                input_data=self,
                stdout=qcel_output["stdout"],
                computed=SinglePointComputedProps(**computed),
                provenance=Provenance(
                    program=qcel_output["provenance"]["creator"],
                    program_version=qcel_output["provenance"].get("version"),
                    wall_time=qcel_output["provenance"].get("wall_time"),
                    extras=prov_extras,
                ),
            )


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


class SinglePointComputedProps(ComputedPropsBase):
    """The computed properties from a single point calculation.

    Attributes:
        calcinfo_natoms: The number of atoms as computed by the program.
        calcinfo_nalpha: The number of alpha electrons as computed by the program.
        calcinfo_nbeta: The number of beta electrons as computed by the program.
        calcinfo_nbasis: The number of basis functions in the calculation.
        calcinfo_nmo: The number of molecular orbitals in the calculation

        energy: The energy of the molecule in Hartrees.
        gradient: The gradient of the molecule in Hartrees/Bohr.
        hessian: The hessian of the molecule in Hartrees/Bohr^2.
        nuclear_repulsion_energy: The nuclear repulsion energy of the molecule in
            Hartrees.
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

    wfn: Optional[Wavefunction] = None

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


class SinglePointOutputMixin(BaseModel):
    """Output for a single point calculation.

    Attributes:
        input_data: The SinglePointInput object for the computation.
    """

    input_data: SinglePointInput


class SinglePointResult(SinglePointOutputMixin, ResultBase):
    """Result from a successful single point calculation.

    Attributes:
        input_data: The SinglePointInput object for the computation.
        success: Always True for a successful computation.
        computed: The results computed by the program.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the results.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    computed: SinglePointComputedProps = SinglePointComputedProps()

    @property
    def return_result(self) -> Union[float, ArrayLike2D]:
        """Return the result of the calculation.

        Returns:
            The explicitly requested result of the calculation, i.e., the energy,
                gradient, or hessian.
        """
        return getattr(self.computed, self.input_data.calctype.value)


class SinglePointFailure(SinglePointOutputMixin, FailureBase):
    """A failed SinglePoint calculation.

    Attributes:
        success: Always False for a Failed output.
        traceback: String representation of the traceback of the exception that caused
            the failure.
        computed: Any computed data that was able to be extracted before the exception.
        input_data: The input object for the computation.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """
