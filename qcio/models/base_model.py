"""The Base model from with all QCIO Model objects inherit."""
from abc import ABC
from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
from pydantic import BaseModel, Extra
from typing_extensions import Self


class QCIOModelBase(BaseModel, ABC):
    """Base Model for all QCIO objects.

    Attributes:
        version: The version of the schema.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    # NOTE: No version for now until we have a stable schema
    # or maybe have version be version of code package that generated
    # the object?
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
        # Exclude empty lists and dictionaries from serialization
        model_dict = super().dict(**kwargs)
        to_pop = []
        for key, value in model_dict.items():
            if isinstance(value, np.ndarray):
                model_dict[key] = value.tolist()
            elif not value:  # None, empty list, empty dict
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
        return cls.parse_raw(filepath.read_text())
        # pydantic v2
        # return cls.model_validate_json(filepath.read_text())

    def save(
        self, filepath: Union[Path, str], exclude_none: bool = True, **kwargs
    ) -> None:
        """Write an object to disk as json.

        Args:
            filepath: The path to write the object to.
            exclude_none: If True, do not write fields with value None to disk.
            **kwargs: Additional arguments to pass to json().
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(exist_ok=True, parents=True)
        filepath.write_text(self.json(exclude_none=exclude_none, **kwargs))
        # pydantic v2
        # filepath.write(self.model_dump())

    def __repr_args__(self):
        return [
            (name, value)
            for name, value in self.__dict__.items()
            if name != "extras"  # Ignore "extras" field
        ]
