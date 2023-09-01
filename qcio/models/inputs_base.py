"""Base (non-end user) input models for qcio. Most models here are used to collect
and organize common attributes used across multiple input objects.
"""
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_serializer

from .base_models import Files
from .molecule import Molecule

__all__ = [
    "Model",
    "CalcType",
    "ProgramArgs",
    "QCProgramArgs",
    "InputBase",
    "StructuredInputBase",
    "DualProgramArgs",
]


class CalcType(str, Enum):
    """The Calculation type."""

    energy = "energy"
    gradient = "gradient"
    hessian = "hessian"
    optimization = "optimization"
    transition_state = "transition_state"

    def __repr__(self) -> str:
        """Custom repr for CalcType"""
        return f"'{self.name}'"  # pragma: no cover


class InputBase(Files):
    """Base class for all qcio input classes.

    Useful for type annotations on functions accepting any input object.
    """

    pass


class ProgramArgs(InputBase):
    """Core arguments for a program including keywords and files.

    Attributes:
        keywords: Dict of keywords to be passed to the program. Defaults to empty dict.

    """

    keywords: Dict[str, Any] = {}


class Model(BaseModel):
    """The model for the quantum chemistry calculation.

    Attributes:
        method: The name of the method to be used in the calculation. Named according to
            the convention of the program being called. If an MM calculation then the
            name of the force field.
        basis: The name of the basis set to be used in the calculation. Named according
            to the convention of the program being called.
    """

    method: str
    basis: Optional[str] = None


class QCProgramArgs(ProgramArgs):
    """Core arguments for a calculation on a molecule. Breaks out model from keywords.

    Attributes:
        model: The model for the quantum chemistry calculation.
    """

    model: Model


class DualProgramArgs(ProgramArgs):
    """Core arguments for a DualProgramInput without calctype and molecule.

    Attributes:
        subprogram_args: The input arguments for the subprogram.
        subprogram: The name of the subprogram to be used.
    """

    subprogram_args: QCProgramArgs
    subprogram: str


class StructuredInputBase(ProgramArgs):
    """Base class for all structured qcio input classes.

    Structured inputs consist of args for a program, a Molecule, and a calctype.

    Attributes:
        molecule: The molecule to be used in the calculation.
        calctype: The type of calculation to be performed.
    """

    calctype: CalcType
    molecule: Molecule

    @field_serializer("calctype")
    def serialize_calctype(self, calctype: CalcType, _info) -> str:
        """Serialize CalcType to string"""
        return calctype.value
