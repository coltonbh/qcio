"""The Base model from which all QCIO Model objects inherit."""

import json
from abc import ABC
from base64 import b64decode, b64encode
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import toml
import yaml
from pydantic import BaseModel, field_serializer, field_validator
from typing_extensions import Self

from ..helper_types import StrOrPath
from .utils import deprecated_function

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import ReprArgs


__all__ = ["Files", "Provenance", "Model", "CalcType"]


class QCIOModelBase(BaseModel, ABC):
    """Base Model for all QCIO objects.

    Attributes:
        version: The version of the schema.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    # NOTE: No version for now until we have a stable schema
    # Or maybe have version be version of qcio that generated the object?
    # version: ClassVar[Literal["v1"]] = "v1"
    extras: Dict[str, Any] = {}

    model_config = {
        # Raises an error if extra fields are passed to model.
        "extra": "forbid",
        # Allow numpy types in models. Pydantic will no longer raise an exception for
        # types it doesn't recognize.
        # https://docs.pydantic.dev/latest/usage/types/#arbitrary-types-allowed
        "arbitrary_types_allowed": True,
        # Don't allow mutation of objects
        # https://docs.pydantic.dev/2.3/api/config/#pydantic.config.ConfigDict.frozen
        "frozen": True,
    }

    @classmethod
    def open(cls, filepath: Union[Path, str]) -> Self:
        """Instantiate an object from data saved to disk.

        Args:
            filepath: The path to the object on disk.
            *args: Additional arguments to pass to the constructor.
            **kwargs: Additional keyword arguments to pass to the constructor.

        Returns:
            The instantiated object.
        """
        filepath = Path(filepath)
        data = filepath.read_text()

        if filepath.suffix in [".yaml", ".yml"]:
            return cls.model_validate(yaml.safe_load(data))
        elif filepath.suffix == ".toml":
            return cls.model_validate(toml.loads(data))

        # Assume json for all other file extensions
        return cls.model_validate_json(data)

    def save(
        self,
        filepath: Union[Path, str],
        exclude_none=True,
        indent: int = 4,
        **kwargs,
    ) -> None:
        """Write an object to disk as json, yaml, or toml.

        Args:
            filepath: The path to write the object to.
            exclude_none: If True, attributes with a value of None will not be written.
                Changing default behavior from pydantic.model_dump() to True.
            indent: The number of spaces to indent the json or yaml output.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(exist_ok=True, parents=True)

        model_dict = self.model_dump(mode="json", exclude_none=exclude_none, **kwargs)

        if filepath.suffix in [".yaml", ".yml"]:
            data = yaml.dump(model_dict, indent=indent)

        elif filepath.suffix == ".toml":
            data = toml.dumps(model_dict)

        else:
            # Write data to json regardless of file extension
            data = json.dumps(model_dict, indent=indent)

        filepath.write_text(data)

    def __repr_args__(self) -> "ReprArgs":
        """Only show non empty fields in repr but always show success even if false."""

        def exists(value):
            if isinstance(value, np.ndarray):
                return value.size > 0
            return bool(value)

        return [  # pragma: no cover
            (name, value)
            for name, value in self.__dict__.items()
            if name == "success" or exists(value)
        ]

    def __eq__(self, other: Any) -> bool:
        """Check equality of two objects.

        Necessary because BaseModel.__eq__ does not compare numpy arrays.
        """
        if isinstance(other, self.__class__):
            return self.model_dump() == other.model_dump()
        return False


class Files(QCIOModelBase):
    """File model for handling string and binary data.

    Binary data is encoded as base64 strings during serialization.

    Attributes:
        files: A dict mapping filename to str or bytes data.
    """

    files: Dict[str, Union[str, bytes]] = {}

    @field_validator("files")
    def convert_base64_to_bytes(cls, value):
        """Convert base64 encoded data to bytes."""
        for filename, data in value.items():
            if isinstance(data, str) and data.startswith("base64:"):
                value[filename] = b64decode(data[7:])
        return value

    @field_serializer("files")
    def serialize_files(self, files, _info) -> Dict[str, str]:
        """Serialize files to a dict of filename to base64 encoded string."""
        return {
            filename: (
                f"base64:{b64encode(data).decode('utf-8')}"
                if isinstance(data, bytes)
                else data
            )
            for filename, data in files.items()
        }

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

    @deprecated_function("add_file")
    def open_file(
        self, filepath: Union[Path, str], relative_dir: Optional[Path] = None
    ) -> None:
        self.add_file(filepath, relative_dir)

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

    @deprecated_function("add_files")
    def open_files(
        self,
        directory: StrOrPath,
        recursive: bool = False,
        exclude: Optional[List[str]] = None,
    ) -> None:
        self.add_files(directory, recursive, exclude)

    def save_files(self, directory: StrOrPath = Path(".")) -> None:
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
        """Replace file data with '<bytes>' or '<str>' in __repr__."""
        rargs = super().__repr_args__()
        return [
            (
                (k, v)
                if k != "files"
                else (
                    k,
                    {
                        name: bytes if isinstance(data, bytes) else str
                        for name, data in v.items()
                    },
                )
            )
            for k, v in rargs
        ]


class Provenance(QCIOModelBase):
    """Provenance information for a QC program.

    Attributes:
        program: The name of the program that created the output.
        version: The version of the program that created the output.
        scratch_dir: The working directory used by the program.
        wall_time: The wall time used by the program.
        hostname: The hostname of the machine the program was run on.
        hostcpus: The number of logical cpus on the host machine where the program ran.
        hostmem: The amount of memory on the host machine where the program ran in GiB.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    program: str
    program_version: Optional[str] = None
    scratch_dir: Optional[StrOrPath] = None
    wall_time: Optional[float] = None
    hostname: Optional[str] = None
    hostcpus: Optional[int] = None
    hostmem: Optional[int] = None


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


class Model(QCIOModelBase):
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
