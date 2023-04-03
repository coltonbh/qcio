"""Abstract Base Classes for all QCIO objects."""

from abc import ABC
from pathlib import Path
from typing import Any, Dict, Union

from pydantic import BaseModel
from typing_extensions import Self


class QCIOBaseModel(BaseModel, ABC):
    """Base Model for all QCIO objects.

    Attributes:
        version: The version of the schema.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    # NOTE: No version for now until we have a stable schema
    # version: ClassVar[Literal["v1"]] = "v1"
    extras: Dict[str, Any] = {}

    @classmethod
    def from_file(cls, filepath: Union[Path, str]) -> Self:
        """Create an object from a filepath."""
        filepath = Path(filepath)
        return cls.parse_raw(filepath.read_text())
        # v2
        # return cls.model_validate_json(filepath.read_text())

    def to_file(self, filepath: Union[Path, str]) -> None:
        """Write an object to disk as json."""
        filepath = Path(filepath)
        filepath.write_text(self.json())
        # v2
        # filepath.write(self.model_dump())
