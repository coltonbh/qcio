"""Abstract Base Classes for all QCIO objects."""

from typing import Literal, Optional

from .abc_base import QCIOBaseModel
from .file import FilesMixin
from .molecule import Molecule


class SpecificationBase(FilesMixin, QCIOBaseModel):
    """Basic inputs required to power a QC program.

    Attributes:
        program: The name of the program.
    """

    program: str


class InputBase(QCIOBaseModel):
    """Base class for all input classes.

    Attributes:
        molecule: The Molecule for the computation.
    """

    spec: SpecificationBase


class QCIOInputBase(InputBase):
    """Base class for all structured qcio input classes."""

    molecule: Molecule


class ResultBase(FilesMixin, QCIOBaseModel):
    """Base class for all result classes.

    Attributes:
        input_data: The input data for the computation.
        success: A boolean indicator that the operation succeeded or failed. Allows
            programmatic assessment of all results regardless of if they failed or
            succeeded by checking `result.success`.
        stdout: The primary logging output of the program, whether natively standard
            output or a file. Contains a union or stdout and stderr.
    """

    input_data: InputBase
    success: bool
    stdout: Optional[str] = None


class SuccessfulResultBase(ResultBase):
    """Base object for any successful result

    Attributes:
        success: Always True for a successful result.
    """

    success: Literal[True] = True
