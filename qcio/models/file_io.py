"""Basic file I/O objects for calculations."""
from pathlib import Path
from typing import List, Type, Union

from pydantic import BaseModel
from typing_extensions import Self

from .base_io import FailureBase, InputBase, ResultBase

__all__ = ["FileInput", "FileResult", "FileFailure"]


class FileInput(InputBase):
    """File and command line argument inputs for a calculation.

    Attributes:
        files: A dict mapping filename to str or bytes data.
        cmdline_args: A list of command line arguments to be passed to the program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    cmdline_args: List[str] = []

    @classmethod
    def from_directory(cls, directory: Union[Path, str], **kwargs) -> Self:
        """Collect all files from directory and instantiate an object."""
        obj = cls(**kwargs)
        directory = Path(directory)
        obj.add_files(directory)
        return obj

    def get_failed_output_class(self) -> Type["FileFailure"]:
        return FileFailure

    def get_successful_output_class(self) -> Type["FileResult"]:
        return FileResult


class FileOutputMixin(BaseModel):
    """Mixin for file based output objects.
    Attributes:
        input_data: The FileInput data for the calculation.
    """

    input_data: FileInput


class FileResult(ResultBase, FileOutputMixin):
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


class FileFailure(FailureBase, FileOutputMixin):
    """Generic output class for pure file based I/O.

    Attributes:
        input_data: input_data: The FileInput object used for the computation.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
        success: Always False for a Failure output.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
    """
