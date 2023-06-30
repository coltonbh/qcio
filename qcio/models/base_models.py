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
from pydantic import BaseModel, Extra, validator
from typing_extensions import Self

from ..helper_types import StrOrPath

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import ReprArgs


__all__ = ["Files", "Provenance"]


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

    class Config:
        # Raises an error if extra fields are passed to model.
        extra = Extra.forbid
        # Allow numpy types in models. Pydantic will no longer raise an exception for
        # types it doesn't recognize.
        # https://docs.pydantic.dev/latest/usage/types/#arbitrary-types-allowed
        arbitrary_types_allowed = True
        # Don't allow mutation of objects
        # https://docs.pydantic.dev/latest/usage/models/#faux-immutability
        allow_mutation = False
        # convert ndarray to list for JSON serialization
        # https://docs.pydantic.dev/latest/usage/exporting_models/#json_encodershttps://docs.pydantic.dev/latest/usage/exporting_models/#json_encoders  # noqa: E501
        json_encoders = {np.ndarray: lambda v: v.tolist()}
        # exclude fields with value None from serialization
        exclude_none = True

    def dict(self, **kwargs):
        """Convert the object to a dictionary.

        Properly serialize numpy arrays. Serialization is performed in .dict() so that
        multiple string serializers can used it without duplicating logic
        (e.g. json, yaml, toml).
        """
        model_dict = super().dict(**kwargs)
        to_pop = []
        for key, value in model_dict.items():
            # Custom serialization for numpy arrays, enums, and pathlib Paths
            if isinstance(value, np.ndarray):
                model_dict[key] = value.tolist()
            elif issubclass(type(value), Enum):
                model_dict[key] = value.value
            elif isinstance(value, Path):
                model_dict[key] = str(value)

            # Exclude empty lists, dictionaries, and objects with all None values from
            # serialization
            elif value in [None, [], {}]:
                to_pop.append(key)

        for key in to_pop:
            model_dict.pop(key)

        return model_dict

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
            return cls.parse_obj(yaml.safe_load(data))
        elif filepath.suffix == ".toml":
            return cls.parse_obj(toml.loads(data))

        # Assume json for all other file extensions
        return cls.parse_raw(data)
        # pydantic v2
        # return cls.model_validate_json(filepath.read_text())

    def save(self, filepath: Union[Path, str], **kwargs) -> None:
        """Write an object to disk as json.

        Args:
            filepath: The path to write the object to.I
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(exist_ok=True, parents=True)

        if filepath.suffix in [".yaml", ".yml"]:
            data = yaml.dump(self.dict(**kwargs))

        elif filepath.suffix == ".toml":
            data = toml.dumps(self.dict(**kwargs))

        else:
            # Write data to json regardless of file extension
            data = self.json(**kwargs)

        filepath.write_text(data)
        # pydantic v2
        # filepath.write(self.model_dump())

    def __repr_args__(self) -> "ReprArgs":
        """Only show non empty fields in repr."""

        def exists(value):
            if isinstance(value, np.ndarray):
                return value.size > 0
            return bool(value)

        return [  # pragma: no cover
            (name, value) for name, value in self.__dict__.items() if exists(value)
        ]


class Files(QCIOModelBase):
    """File model for handling string and binary data.

    Binary data is encoded as base64 strings during serialization.

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
        """Replace file data with '<bytes>' or '<str>' in __repr__."""
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
