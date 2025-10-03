"""Input models for quantum chemistry calculations."""

import warnings
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, field_serializer
from typing_extensions import Self, TypeVar

from .base_models import CalcType, Files, Model
from .structure import Structure
from .utils import deprecated_class

__all__ = [
    "FileInput",
    "CalcInput",
    "CompositeCalcInput",
    "CalcArgs",
    "Inputs",
    "InputType",
    "StructuredInputs",
    "SubCalcArgs",
    "ProgramInput",
    "ProgramArgs",
    "ProgramArgsSub",
    "DualProgramInput",
]


class FileInput(Files):
    """File and command line argument inputs for a calculation.

    Attributes:
        files Files: A dict mapping filename to str or bytes data.
        cmdline_args: A list of command line arguments to be passed to the program.
        extras Dict[str, Any]: Additional information to bundle with the object. Use for
            schema development and scratch space.
    """

    cmdline_args: list[str] = []

    @classmethod
    def from_directory(cls, directory: Union[Path, str], **kwargs) -> Self:
        """Create a new FileInput and collect all files in the directory."""
        obj = cls(**kwargs)
        directory = Path(directory)
        obj.add_files(directory)
        return obj


class _KeywordsMixin(BaseModel):
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


class CalcArgs(FileInput, _KeywordsMixin):
    """Generic arguments for a calculation without a calctype or structure specification.

    This class is used by `CompositeCalcInput` or multi-step calculations to
    specify `subprogram_args` or a basic program arguments multistep algorithm in
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


class SubCalcArgs(FileInput, _KeywordsMixin):
    """Generic arguments for a calculation that also calls a sub-calculation.

    This class is needed for multi-step calculations where the calctype and structure
    are specified only once for the entire calculation, e.g., multistep_opt in BigChem.

    Attributes:
        keywords: A dict of keywords to be passed to the program excluding model and
            calctype. Defaults to an empty dict.
        files: Files to be passed to the QC program.
        model: The model for the quantum chemistry calculation
        subprogram: The name of the subprogram to use.
        subprogram_args: The ProgramArgs for the subprogram.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    model: Optional[Model] = None
    subprogram: str
    subprogram_args: CalcArgs


class CalcInput(CalcArgs, _StructureKeywordsMixin):
    """Input for a single quantum chemistry program. This is the most common input type.

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
        from qcio.models import CalcInput, Structure

        struct = Structure.open("path/to/structure.xyz")

        prog_inp = CalcInput(
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


class CompositeCalcInput(SubCalcArgs, CalcInput):
    """Input for a two program calculation.

    Attributes:
        calctype CalcType: The type of calculation to perform.
        model Model: The model for the quantum chemistry calculation.
        keywords Dict[str, Any]: A dict of keywords to be passed to the program
            excluding model and calctype. Defaults to an empty dict.
        structure Structure: The structure to be used in the calculation.
        files Files: Files to be passed to the QC program.
        subprogram: The name of the subprogram to use.
        subprogram_args ProgramArgs: The ProgramArgs for the subprogram.
        extras Dict[str, Any]: Additional information to bundle with the object. Use
            for schema development and scratch space.

    Example:
        ```python
        from qcio.models import CompositeCalcInput, Structure

        struct = Structure.open("path/to/structure.xyz")

        prog_inp = CompositeCalcInput(
            calctype = "optimization",
            structure = struct,
            keywords = {"maxiter": "250"},  # Optional
            subprogram = "orca",
            subprogram_args = ProgramArgs(
                model = {"method": "wb97x-d3", "basis": "def2-SVP"},
                keywords = {"convthre": "1e-6"},  # Optional
            )
        )
        ```
    """


Inputs = Union[FileInput, CalcInput, CompositeCalcInput]
InputType = TypeVar("InputType", bound=Inputs)
StructuredInputs = Union[CalcInput, CompositeCalcInput]


@deprecated_class("CalcInput")
class ProgramInput(CalcInput):
    """Deprecated alias for CalcInput.

    This class is deprecated and will be removed in a future release. Please use
    `CalcInput` instead.
    """

    pass


@deprecated_class("ProgramArgs")
class ProgramArgs(CalcArgs):
    """Deprecated alias for CalcArgs.

    This class is deprecated and will be removed in a future release. Please use
    `CalcArgs` instead.
    """

    pass


@deprecated_class("SubCalcArgs")
class ProgramArgsSub(SubCalcArgs):
    """Deprecated alias for SubCalcArgs.

    This class is deprecated and will be removed in a future release. Please use
    `SubCalcArgs` instead.
    """

    pass


@deprecated_class("CompositeCalcInput")
class DualProgramInput(CompositeCalcInput):
    """Deprecated alias for CompositeCalcInput.

    This class is deprecated and will be removed in a future release. Please use
    `CompositeCalcInput` instead.
    """

    pass
