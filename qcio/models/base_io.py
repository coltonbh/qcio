"""Base classes for qcio input and output objects."""
from abc import abstractmethod
from traceback import format_exception
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Type

from ..mixins import Files
from .base_model import QCIOModelBase
from .molecule import Molecule

__all__ = ["Provenance"]


if TYPE_CHECKING:
    from pydantic.typing import ReprArgs


class Provenance(QCIOModelBase):
    """Provenance information for a QC program.

    Attributes:
        program: The name of the program that created the output.
        version: The version of the program that created the output.
        working_dir: The working directory used by the program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    program: str
    program_version: Optional[str] = None
    working_dir: Optional[str] = None

    def __repr_args__(self) -> "ReprArgs":
        return [("program", self.program), ("program_version", self.program_version)]


class ComputedPropertiesBase(QCIOModelBase):
    """Base class for all properties computed by a program"""

    pass


class ProgramArgsBase(QCIOModelBase, Files):
    """Arguments for a QC program.

    Attributes:
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """


class StructuredProgramArgsBase(ProgramArgsBase):
    """Base Program Args class for structured qcio input classes.

    This class is used to define the args for a structured qcio input class.

    Attributes:
        keywords: A dict of keywords to be passed to the program. Defaults to an empty
            dict.
        files: Files to be passed to the QC program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    keywords: Dict[str, Any] = {}


class InputBase(QCIOModelBase):
    """Base class for all program input objects.

    Attributes:
        program_args: Input arguments for the program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    program_args: ProgramArgsBase

    @abstractmethod
    def get_failed_output_class(self) -> Type["FailedOutputBase"]:
        """Return the FailedOutput class for the input object."""
        raise NotImplementedError()

    @abstractmethod
    def get_successful_output_class(self) -> Type["SuccessfulOutputBase"]:
        """Return the SuccessfulOutput class for the input object."""
        raise NotImplementedError()

    def to_success(
        self,
        provenance: Provenance,
        computed: Optional[ComputedPropertiesBase] = None,
        stdout: Optional[str] = None,
    ) -> "OutputBase":
        """Return a successful output object.

        Args:
            provenance: The provenance information for the output.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        output_class = self.get_successful_output_class()
        return output_class(
            input_data=self, provenance=provenance, computed=computed, stdout=stdout
        )

    def to_failure(self, provenance: Provenance, exc: Exception) -> "FailedOutputBase":
        """Return a failed output object.

        Args:
            provenance: The provenance information for the output.
            exc: The exception that caused the failure.
        """
        output_class = self.get_failed_output_class()
        output_class.update_forward_refs()
        stdout = getattr(exc, "stdout", None)
        computed = getattr(exc, "computed", None)
        traceback = "".join(format_exception(type(exc), exc, exc.__traceback__))

        return output_class(
            input_data=self,
            provenance=provenance,
            traceback=traceback,
            stdout=stdout,
            computed=computed,
        )

    def __repr_args__(self) -> "ReprArgs":
        return [("program_args", self.program_args)]


class StructuredInputBase(InputBase):
    """Base class for all structured qcio input classes.

    Structured inputs consist of args for a QC program and a Molecule.

    Attributes:
        program_args: Structured input arguments for the program.
        molecule: The molecule to be used in the calculation.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    program_args: StructuredProgramArgsBase
    molecule: Molecule


class OutputBase(Files, QCIOModelBase):
    """Base class for all output classes.

    Attributes:
        input_data: The input object for the computation.
        success: A boolean indicator that the operation succeeded or failed. Allows
            programmatic assessment of all outputs regardless of if they failed or
            succeeded by checking `output.success`.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        computed: An object containing the computed properties from the output.
        files: A dict mapping filename to str or bytes of files output by the program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    input_data: InputBase
    success: bool
    stdout: Optional[str] = None
    computed: Optional[ComputedPropertiesBase] = None
    provenance: Provenance

    def print_stdout(self) -> None:
        """Print the stdout text"""
        print(self.stdout)


class SuccessfulOutputBase(OutputBase):
    """Base object for any successful computation.

    Attributes:

        input_data: The input object for the computation.
        success: Always True for a successful output.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    success: Literal[True] = True


class FailedOutputBase(OutputBase):
    """Base object for any failed computation.

    Attributes:
        input_data: The input object for the computation.
        success: Always False for a Failed output.
        traceback: String representation of the traceback of the exception that caused
            the failure.
        computed: Any computed data that was able to be extracted before the exception.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    success: Literal[False] = False
    traceback: Optional[str] = None
    computed: Optional[Any] = None

    def __repr_args__(self) -> "ReprArgs":
        """A helper for __repr__ that returns a list of tuples of the form
        (name, value).
        """
        return [
            ("success", self.success),
            ("input_data", self.input_data),
            ("provenance", self.provenance),
        ]
