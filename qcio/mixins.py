"""File model for handling string and binary data."""

import json
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator

from .helper_types import StrOrPath


class Files(BaseModel):
    """Mixin for models that have files that need to be serialized to JSON.

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
