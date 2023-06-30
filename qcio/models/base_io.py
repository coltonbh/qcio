"""Base classes for qcio input and output objects."""

import json
from abc import abstractmethod
from base64 import b64decode, b64encode
from pathlib import Path
from traceback import format_exception
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, validator

from ..helper_types import StrOrPath
from .base_model import QCIOModelBase
from .molecule import Molecule

__all__ = [
    "Provenance",
    "ProgramArgs",
    "Files",
    "InputBase",
    "ComputedPropsBase",
    "OutputBase",
]


if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import ReprArgs


class Provenance(QCIOModelBase):
    """Provenance information for a QC program.

    Attributes:
        program: The name of the program that created the output.
        version: The version of the program that created the output.
        working_dir: The working directory used by the program.
        wall_time: The wall time used by the program.
        hostname: The hostname of the machine the program was run on.
        hostcpus: The number of logical cpus on the host machine where the program ran.
        hostmem: The amount of memory on the host machine where the program ran in GiB.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    program: str
    program_version: Optional[str] = None
    working_dir: Optional[Path] = None
    wall_time: Optional[float] = None
    hostname: Optional[str] = None
    hostcpus: Optional[int] = None
    hostmem: Optional[int] = None


class ComputedPropsBase(QCIOModelBase):
    """Base class for all properties computed by a program"""

    pass


class Files(BaseModel):
    """File model for handling string and binary data.

    Attributes:
        files: A dict mapping filename to str or bytes data.
    """

    files: Dict[str, Union[str, bytes]] = {}

    @validator("files", pre=True)
    def convert_base64_to_bytes(cls, value):
        """Convert base64 encoded data to bytes."""
        for filename, data in value.items():
            if isinstance(data, str) and data.startswith("base64:"):
                value[filename] = b64decode(data[7:])
        return value

    def dict(self, *args, **kwargs):
        """Return a dict representation of the object encoding bytes as b64 strings."""
        dict = super().dict(*args, **kwargs)
        if self.files:  # clause so that empty files dict is not included in dict
            files = {}
            for filename, data in self.files.items():
                if isinstance(data, bytes):
                    data = f"base64:{b64encode(data).decode('utf-8')}"
                files[filename] = data
            dict["files"] = files
        return dict

    def json(self, *args, **kwargs):
        """Return a JSON representation of the object."""
        return json.dumps(self.dict(*args, **kwargs))

    def add_file(
        self, filepath: Union[Path, str], relative_dir: Optional[Path] = None
    ) -> None:
        """Create a File object from a file on disk.

        Args:
            filepath: The path to the file.
            relative_dir: The directory to make the file relative to. Helpful when
                adding files from a subdirectory.
        """
        filepath = Path(filepath)
        raw_bytes = filepath.read_bytes()
        try:
            data: Union[str, bytes] = raw_bytes.decode("utf-8")  # str
        except UnicodeDecodeError:
            data = raw_bytes  # bytes

        # Set filename relative to relative_dir
        if relative_dir:
            filename = str(filepath.relative_to(relative_dir))
        else:
            filename = filepath.name

        self.files[filename] = data

    def add_files(
        self,
        directory: StrOrPath,
        recursive: bool = False,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """Add all files in a directory to the object.

        Args:
            directory: The directory to add files from.
            recursive: Whether to recursively add files from subdirectories.
            exclude: A list of filenames to exclude from the directory.
        """
        directory = Path(directory)
        if exclude is None:
            exclude = []
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")
        for filepath in files:
            if filepath.is_file() and filepath.name not in exclude:
                self.add_file(filepath, directory)

    def write_files(self, directory: StrOrPath = Path(".")) -> None:
        """Write all files to the specified directory"""
        directory = Path(directory)
        directory.mkdir(exist_ok=True)
        for filename, data in self.files.items():
            mode = "w" if isinstance(data, str) else "wb"
            filepath = directory / filename
            # In case filename is a relative path, create the parent directories
            filepath.parent.mkdir(exist_ok=True, parents=True)
            filepath.open(mode).write(data)

    def __repr_args__(self) -> "ReprArgs":
        """Replace file data with <bytes> or <str> in __repr__."""
        rargs = super().__repr_args__()
        return [
            (k, v)
            if k != "files"
            else (
                k,
                {
                    name: bytes if isinstance(data, bytes) else str
                    for name, data in v.items()
                },
            )
            for k, v in rargs
        ]


class InputBase(QCIOModelBase, Files):
    """Base class for all program input objects.

    Attributes:
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    @abstractmethod
    def get_failed_output_class(self) -> Type["FailureBase"]:
        """Return the FailedOutput class for the input object."""

    @abstractmethod
    def get_successful_output_class(self) -> Type["ResultBase"]:
        """Return the SuccessfulOutput class for the input object."""

    def to_success(
        self,
        provenance: Provenance,
        computed: Optional[ComputedPropsBase] = None,
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

    def to_failure(self, provenance: Provenance, exc: Exception) -> "FailureBase":
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


class ProgramArgs(InputBase):
    """Core arguments for a program including keywords and files.

    Attributes:
        keywords: A dict of keywords to be passed to the program. Defaults to an empty
            dict.
        files: A dict mapping filename to str or bytes data.
        extras: Additional information to bundle with the object. Use for schema

    """

    keywords: Dict[str, Any] = {}


class ProgramInputBase(ProgramArgs):
    """Base class for all structured qcio input classes. ProgramArgs plus a Molecule.

    Structured inputs consist of args for a QC program and a Molecule.

    Attributes:
        keywords: A dict of keywords to be passed to the program. Defaults to an empty
            dict.
        files: A dict mapping filename to str or bytes data.
        molecule: The molecule to be used in the calculation.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    molecule: Molecule


class OutputBase(Files, QCIOModelBase):
    """Base class for all output classes.

    Attributes:
        input_data: The input object for the computation.
        success: A boolean indicator that the operation succeeded or failed. Allows
            programmatic assessment of all outputs regardless of if they failed or
            succeeded by checking `output.success`.
        computed: An object containing the computed properties from the output.
        files: A dict mapping filename to str or bytes of files output by the program.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    input_data: InputBase
    success: bool
    stdout: Optional[str] = None
    computed: Optional[ComputedPropsBase] = ComputedPropsBase()
    provenance: Provenance

    @property
    def pstdout(self) -> None:
        """Print the stdout text"""
        print(self.stdout)

    @property
    def prov(self) -> Provenance:
        """Alias for provenance"""
        return self.provenance

    def __repr_args__(self):
        """Exclude stdout from the repr"""
        return [
            (key, value if key != "stdout" else "<...>")
            for key, value in super().__repr_args__()
        ]


class ResultBase(OutputBase):
    """Base object for any successful computation.

    Attributes:

        input_data: The input object for the computation.
        success: Always True for a successful output.
        computed: Any computed data that was able to be extracted.
        files: A dict mapping filename to str or bytes of files output by the program.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    success: Literal[True] = True


class FailureBase(OutputBase):
    """Base object for any failed computation.

    Attributes:
        input_data: The input object for the computation.
        success: Always False for a Failed output.
        computed: Any computed data that was able to be extracted before the exception.
        files: A dict mapping filename to str or bytes of files output by the program.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
        traceback: String representation of the traceback of the exception that caused
            the failure.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    success: Literal[False] = False
    traceback: Optional[str] = None

    @property
    def ptraceback(self) -> None:
        """Print the traceback text"""
        print(self.traceback)
