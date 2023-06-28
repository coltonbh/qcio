"""Basic file I/O objects for calculations."""
from pathlib import Path
from typing import List, Type, Union

from typing_extensions import Self

from ..mixins import Files
from .base_io import FailedOutputBase, InputBase, ProgramArgsBase, SuccessfulOutputBase

__all__ = ["FileArgs", "FileInput", "FileSuccessfulOutput", "FileFailedOutput"]


class FileArgs(ProgramArgsBase):
    """Program arguments for a FileInput.

    Attributes:
        cmdline_args: A list of command line arguments to be passed to the program.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    cmdline_args: List[str] = []


class FileInput(InputBase):
    """File and command line argument inputs for a calculation.

    Attributes:
        program_args: Files and command line arguments for the program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    program_args: FileArgs = FileArgs()

    @classmethod
    def from_directory(cls, directory: Union[Path, str], **kwargs) -> Self:
        """Collect all files from directory and instantiate an object."""
        obj = cls(**kwargs)
        directory = Path(directory)
        obj.program_args.add_files(directory)
        return obj

    def get_failed_output_class(self) -> Type["FileFailedOutput"]:
        return FileFailedOutput

    def get_successful_output_class(self) -> Type["FileSuccessfulOutput"]:
        return FileSuccessfulOutput


class FileOutputMixin(Files):
    """Mixin for file based output objects.
    Attributes:
        input_data: The input data for the computation.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
        success: A boolean indicator that the operation succeeded (always True)
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
    """

    input_data: FileInput


class FileSuccessfulOutput(SuccessfulOutputBase, FileOutputMixin):
    """Generic output class for pure file based I/O.

    Attributes:
        input_data: The FileInput object used for the computation.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
        success: A boolean indicator that the operation succeeded (always True)
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
    """

    input_data: FileInput


class FileFailedOutput(FailedOutputBase, FileOutputMixin):
    """Generic output class for pure file based I/O.

    Attributes:
        input_data: input_data: The FileInput object used for the computation.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
        success: Always False for a Failed output.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
    """
