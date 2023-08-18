"""End user input models for qcio"""
from pathlib import Path
from typing import List, Union

from typing_extensions import Self

from .inputs_base import DualProgramArgs, InputBase, QCProgramArgs, StructuredInputBase
from .molecule import Molecule

__all__ = [
    "FileInput",
    "ProgramInput",
    "DualProgramInput",
]


class FileInput(InputBase):
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


class ProgramInput(StructuredInputBase, QCProgramArgs):
    """Input for a single point calculation.

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


class DualProgramInput(StructuredInputBase, DualProgramArgs):
    """Input for a two program calculation.

    Attributes:
        calctype: The type of calculation to be performed.
        keywords: Dict of keywords to be passed to the program. Defaults to empty dict.
        molecule: The molecule to be used in the calculation.
        files: A dict mapping filename to str or bytes data.
        subprogram_args: The input arguments for the subprogram.
        subprogram: The name of the subprogram to be used.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """


if __name__ == "__main__":
    # Test geometry optimization input
    from qcio import CalcType, Model

    opt_inp = DualProgramInput(
        calctype=CalcType.optimization,
        keywords={"maxiter": 100},
        molecule=Molecule(
            symbols=["C", "C", "H", "H", "H", "H"],
            geometry=[
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 1.2],
                [0.0, 1.2, 0.0],
                [0.0, -1.2, 0.0],
                [1.2, 0.0, 0.0],
                [-1.2, 0.0, 0.0],
            ],
        ),
        subprogram_args=QCProgramArgs(
            keywords={"purify": "no"},
            model=Model(**{"method": "b3lyp", "basis": "6-31g"}),
        ),
        subprogram="terachem",
    )
