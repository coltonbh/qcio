"""Base (non end user) classes for output models."""
from typing import TYPE_CHECKING, Literal, Optional

from .base_models import Files, Provenance, QCIOModelBase
from .inputs_base import InputBase

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import ReprArgs


__all__ = [
    "ResultsBase",
    "OutputBase",
]


class ResultsBase(QCIOModelBase):
    """Base class for all results computed by a program.

    Currently this is just a placeholder class. Perhaps some day Results objects will
    have some common interface. Helpful for generic type annotations in qcop.
    """

    pass


class OutputBase(Files):
    """Base class for all output classes.

    Attributes:
        input_data: The input object for the computation.
        success: A boolean indicator that the operation succeeded or failed. Allows
            programmatic assessment of all outputs regardless of if they failed or
            succeeded by checking `output.success`.
        results: An object containing the results computed by the program.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
    """

    input_data: InputBase
    success: bool
    stdout: Optional[str] = None
    results: ResultsBase = ResultsBase()
    provenance: Provenance

    @property
    def pstdout(self) -> None:
        """Print the stdout text"""
        print(self.stdout)

    def __repr_args__(self) -> "ReprArgs":
        """Exclude stdout from the repr"""
        return [
            (key, value if key != "stdout" else "<...>")
            for key, value in super().__repr_args__()
        ]


class SuccessfulOutputBase(OutputBase):
    """Base object for any successful computation.

    Attributes:
        success: Always True for a successful output.
    """

    success: Literal[True] = True
