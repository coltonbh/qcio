"""File model for handling string and binary data."""

import json
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Dict, Union

from pydantic import BaseModel, validator
from typing_extensions import Self


class File(BaseModel):
    """Class for managing file data.

    Attributes:
        name: filename.
        files: str or bytes of a file.
    """

    data: Union[str, bytes]

    @validator("data", pre=True)
    def convert_base64_to_bytes(cls, value):
        """Convert base64 encoded data to bytes."""
        if isinstance(value, str) and value.startswith("base64:"):
            b64_encoded_data = value[7:]
            return b64decode(b64_encoded_data)
        return value

    def json(self, *args, **kwargs):
        """Return a JSON representation of the object."""
        return json.dumps(self.dict(*args, **kwargs))

    def dict(self, *args, **kwargs):
        """Return a dict representation of the object encoding bytes as b64 strings."""
        data = self.data
        if isinstance(self.data, bytes):
            data = f"base64:{b64encode(self.data).decode('utf-8')}"
        return {"data": data}

    @classmethod
    def from_disk(cls, filepath: Union[Path, str]) -> Self:
        """Create a File object from a file on disk."""
        filepath = Path(filepath)
        data = filepath.read_bytes()
        try:
            return cls(data=data.decode("utf-8"))  # str
        except UnicodeDecodeError:  # bytes
            return cls(data=data)

    def to_disk(self, filepath: Union[str, Path]) -> None:
        """Write file to disk."""
        filepath = Path(filepath)
        mode = "w" if isinstance(self.data, str) else "wb"
        filepath.open(mode).write(self.data)


class FilesMixin(BaseModel):
    """Mixin for models that have files that need to be serialized to JSON.

    Attributes:
        files: A dict mapping filenames to Files
    """

    files: Dict[str, File]

    def dump_files(self, directory: Union[str, Path] = Path(".")):
        """Write all files to the specified directory"""
        for filename, file in self.files.items():
            file.to_disk(filename)
