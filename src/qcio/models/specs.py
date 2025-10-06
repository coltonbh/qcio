"""Input models for quantum chemistry calculations."""

import warnings
from pathlib import Path
from typing import Any, TypeVar, Union

from pydantic import BaseModel, field_serializer, model_validator
from typing_extensions import Self

from .base_models import CalcType, Files, Model
from .structure import Structure
from .utils import deprecated_class

__all__ = [
    "FileSpec",
    "CalcSpec",
    "CompositeCalcSpec",
    "CoreSpec",
    "Specs",
    "SpecType",
    "StructuredSpecs",
    "SubCalcSpec",
    "ProgramInput",
    "ProgramArgs",
    "ProgramArgsSub",
    "DualProgramInput",
    "FileInput",
]


class FileSpec(Files):
    """File and command line argument inputs for a calculation.

    Attributes:
        files Files: A dict mapping filename to str or bytes data.
        cmdline_args: A list of command line arguments to be passed to the program.
        extras Dict[str, Any]: Additional information to bundle with the object. Use for
            schema development and scratch space.
    """

    cmdline_args: list[str] = []

    @classmethod
    def from_directory(cls, directory: Path | str, **kwargs) -> Self:
        """Create a new FileSpec and collect all files in the directory."""
        obj = cls(**kwargs)
        directory = Path(directory)
        obj.add_files(directory)
        return obj


class _KeywordsMixin(BaseModel):
    """Mixin for keywords attribute.

    Attributes:
        Keywords: dict[str, Any]: A dict of keywords to be passed to the program
            excluding model and calctype. Defaults to an empty dict.
    """

    keywords: dict[str, Any] = {}


class _StructureKeywordsMixin(_KeywordsMixin):
    """
    Attributes:
        structure: The structure to be used in the calculation.
    """

    structure: Structure

    def __init__(self, **data: Any):
        """Backwards compatibility for 'molecule' attribute."""

        # TODO: Remove in future versions.
        if "molecule" in data:
            warnings.warn(
                "Use of 'molecule' attribute is deprecated. Use 'structure' instead.",
                FutureWarning,
                stacklevel=2,
            )
            data["structure"] = data.pop("molecule")
        super().__init__(**data)

    @property
    def molecule(self) -> Structure:
        """Backwards compatibility for 'molecule' attribute."""
        warnings.warn(
            "Use of 'molecule' attribute is deprecated. Use 'structure' instead.",
            FutureWarning,
            stacklevel=2,
        )
        return self.structure


class CoreSpec(FileSpec, _KeywordsMixin):
    """Core arguments for a calculation without a calctype or structure specification.

    This class is used by `CompositeCalcSpec` or multi-step calculations to
    specify `subprogram_spec` or basic program arguments for a multistep algorithm in
    BigChem. It is not intended to be used directly for single-step calculations since
    it lacks a `calctype` and `structure`.


    Attributes:
        model Model: The model for the quantum chemistry calculation.
        keywords Dict[str, Any]: A dict of keywords to be passed to the program
            excluding model and calctype. Defaults to an empty dict.
        files Files: Files to be passed to the QC program.
        extras Dict[str, Any]: Additional information to bundle with the object. Use
            for schema development and scratch space.
    """

    model: Model


class SubCalcSpec(FileSpec, _KeywordsMixin):
    """Generic arguments for a calculation that also calls a sub-calculation.

    This class is needed for multi-step calculations where the calctype and structure
    are specified only once for the entire calculation, e.g., multistep_opt in BigChem.

    Attributes:
        model: The model for the quantum chemistry calculation
        keywords: A dict of keywords to be passed to the program excluding model and
            calctype. Defaults to an empty dict.
        files: Files to be passed to the QC program.
        subprogram: The name of the subprogram to use.
        subprogram_spec: The CoreSpec for the subprogram.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    model: Model | None = None
    subprogram: str
    subprogram_spec: CoreSpec

    @model_validator(mode="before")
    @classmethod
    def _backcompat(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Backwards compatibility for 'subprogram_args' attribute."""
        if (
            isinstance(payload, dict)
            and "subprogram_args" in payload
            and "subprogram_spec" not in payload
        ):
            payload = dict(payload)
            payload["subprogram_spec"] = payload.pop("subprogram_args")
            warnings.warn(
                "'subprogram_args' has been renamed to 'subprogram_spec' (CoreSpec).",
                FutureWarning,
                stacklevel=2,
            )
        return payload

    @property
    def subprogram_args(self) -> CoreSpec:
        """Backwards compatibility for 'subprogram_args' attribute."""
        warnings.warn(
            "'subprogram_args' has been renamed to 'subprogram_spec' (CoreSpec).",
            FutureWarning,
            stacklevel=2,
        )
        return self.subprogram_spec


class CalcSpec(CoreSpec, _StructureKeywordsMixin):
    """Specification for a quantum chemistry calculation. This is the most common input type.

    Attributes:
        calctype CalcType: The type of calculation to perform.
        model Model: The model for the quantum chemistry calculation.
        keywords Dict[str, Any]: A dict of keywords to be passed to the program
            excluding model and calctype. Defaults to an empty dict.
        structure Structure: The structure to be used in the calculation.
        files Files: Files to be passed to the QC program.
        extras Dict[str, Any]: Additional information to bundle with the object. Use
            for schema development and scratch space.

    Example:
        ```python
        from qcio.models import CalcSpec, Structure

        struct = Structure.open("path/to/structure.xyz")

        prog_inp = CalcSpec(
            calctype = "energy",
            structure = struct,
            model = {"method": "hf", "basis": "6-31G"},
            keywords = {"maxsteps": "250"},  # Optional
            files = {"file1": b"binary data"}  # Optional
        )
        ```
    """

    calctype: CalcType

    @field_serializer("calctype")
    def _serialize_calctype(self, calctype: CalcType, _info) -> str:
        """Serialize CalcType to string"""
        return calctype.value


class CompositeCalcSpec(SubCalcSpec, CalcSpec):
    """Input for a two program calculation.

    Attributes:
        calctype CalcType: The type of calculation to perform.
        model Model: The model for the quantum chemistry calculation.
        keywords Dict[str, Any]: A dict of keywords to be passed to the program
            excluding model and calctype. Defaults to an empty dict.
        structure Structure: The structure to be used in the calculation.
        files Files: Files to be passed to the QC program.
        subprogram: The name of the subprogram to use.
        subprogram_spec CoreSpec: The CoreSpec for the subprogram.
        extras Dict[str, Any]: Additional information to bundle with the object. Use
            for schema development and scratch space.

    Example:
        ```python
        from qcio.models import CompositeCalcSpec, Structure

        struct = Structure.open("path/to/structure.xyz")

        prog_inp = CompositeCalcSpec(
            calctype = "optimization",
            structure = struct,
            keywords = {"maxiter": "250"},  # Optional
            subprogram = "orca",
            subprogram_spec = CoreSpec(
                model = {"method": "wb97x-d3", "basis": "def2-SVP"},
                keywords = {"convthre": "1e-6"},  # Optional
            )
        )
        ```
    """


Specs = Union[FileSpec, CalcSpec, CompositeCalcSpec]
SpecType = TypeVar("SpecType", bound=Specs)
StructuredSpecs = Union[CalcSpec, CompositeCalcSpec]


@deprecated_class("CalcSpec")
class ProgramInput(CalcSpec):
    """Deprecated alias for CalcSpec.

    This class is deprecated and will be removed in a future release. Please use
    `CalcSpec` instead.
    """

    pass


@deprecated_class("CoreSpec")
class ProgramArgs(CoreSpec):
    """Deprecated alias for CoreSpec.

    This class is deprecated and will be removed in a future release. Please use
    `CoreSpec` instead.
    """

    pass


@deprecated_class("SubCalcSpec")
class ProgramArgsSub(SubCalcSpec):
    """Deprecated alias for SubCalcSpec.

    This class is deprecated and will be removed in a future release. Please use
    `SubCalcSpec` instead.
    """

    pass


@deprecated_class("CompositeCalcSpec")
class DualProgramInput(CompositeCalcSpec):
    """Deprecated alias for CompositeCalcSpec.

    This class is deprecated and will be removed in a future release. Please use
    `CompositeCalcSpec` instead.
    """

    pass


@deprecated_class("FileSpec")
class FileInput(FileSpec):
    """Deprecated alias for FileSpec.

    This class is deprecated and will be removed in a future release. Please use
    `FileSpec` instead.
    """

    pass
