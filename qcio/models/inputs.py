"""Input models for quantum chemistry calculations."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, field_serializer
from typing_extensions import Self, TypeVar

from .base_models import CalcType, Files, Model
from .molecule import Molecule

__all__ = [
    "FileInput",
    "ProgramInput",
    "DualProgramInput",
    "ProgramArgs",
    "Inputs",
    "InputType",
    "StructuredInputs",
    "ProgramArgsSub",
]


class FileInput(Files):
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


class _KeywordsMixin(BaseModel):
    keywords: Dict[str, Any] = {}


class _MoleculeKeywordsMixin(_KeywordsMixin):
    molecule: Molecule


class ProgramArgs(FileInput, _KeywordsMixin):
    """Generic arguments for a program without a calctype or molecule specification.

    This class is needed for multi-step calculations where the calctype and molecule
    are specified only once for the entire calculation, e.g., multistep_opt in BigChem.

    Attributes:
        model: The model for the quantum chemistry calculation.
        keywords: A dict of keywords to be passed to the program excluding model and
            calctype. Defaults to an empty dict.
        files: Files to be passed to the QC program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    model: Model


class ProgramArgsSub(FileInput, _KeywordsMixin):
    """Generic arguments for a program that also calls a subprogram.

    This class is needed for multi-step calculations where the calctype and molecule
    are specified only once for the entire calculation, e.g., multistep_opt in BigChem.

    Attributes:
        keywords: A dict of keywords to be passed to the program excluding model and
            calctype. Defaults to an empty dict.
        files: Files to be passed to the QC program.
        subprogram: The name of the subprogram to use.
        subprogram_args: The ProgramArgs for the subprogram.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    model: Optional[Model] = None
    subprogram: str
    subprogram_args: ProgramArgs


class ProgramInput(ProgramArgs, _MoleculeKeywordsMixin):
    """Input for a single quantum chemistry program.

    Attributes:
        calctype: The type of calculation to perform.
        model: The model for the quantum chemistry calculation.
        keywords: A dict of keywords to be passed to the program excluding model and
            calctype. Defaults to an empty dict.
        molecule: The molecule to be used in the calculation.
        files: Files to be passed to the QC program.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    calctype: CalcType

    @field_serializer("calctype")
    def serialize_calctype(self, calctype: CalcType, _info) -> str:
        """Serialize CalcType to string"""
        return calctype.value


class DualProgramInput(ProgramArgsSub, ProgramInput):
    """Input for a two program calculation.

    Attributes:
        calctype: The type of calculation to be performed.
        molecule: The molecule to be used in the calculation.
        keywords: Dict of keywords to be passed to the program. Defaults to empty dict.
        files: A dict mapping filename to str or bytes data.
        subprogram: The name of the subprogram to use.
        subprogram_args: The program input for the subprogram.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    pass


Inputs = Union[FileInput, ProgramInput, DualProgramInput]
InputType = TypeVar("InputType", bound=Inputs)
StructuredInputs = Union[ProgramInput, DualProgramInput]
