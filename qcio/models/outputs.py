"""End user output objects from a calculation."""
from typing import Literal, Optional, Union

from qcio.helper_types import ArrayLike2D

from .inputs import DualProgramInput, FileInput, ProgramInput
from .molecule import Molecule
from .outputs_base import OutputBase, SuccessfulOutputBase
from .results import OptimizationResults, SinglePointResults

__all__ = ["FileOutput", "SinglePointOutput", "OptimizationOutput", "ProgramFailure"]


class FileOutput(SuccessfulOutputBase):
    """Generic output class for pure file based I/O.

    Attributes:
        input_data: The FileInput object used for the computation.
        files: A dict mapping filename to str or bytes data.
        success: A boolean indicator that the operation succeeded (always True)
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the results.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.

    """

    input_data: FileInput


class SinglePointOutput(SuccessfulOutputBase):
    """Output from a successful single point calculation.

    Attributes:
        input_data: The SinglePointInput object for the computation.
        success: Always True for a successful computation.
        results: The results computed by the program.
        files: A dict mapping filename to str or bytes data.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the results.
        extras: Additional information to bundle with the object. Use for schema
            development and scratch space.
    """

    input_data: ProgramInput
    results: SinglePointResults

    @property
    def return_result(self) -> Union[float, ArrayLike2D]:
        """Return the result of the calculation.

        Returns:
            The explicitly requested result of the calculation, i.e., the energy,
                gradient, or hessian.
        """
        return getattr(self.results, self.input_data.calctype.value)


class OptimizationOutput(SuccessfulOutputBase):
    """Output from a successful optimization.

    Attributes:
        input_data: The OptimizationInput object for the computation.
        results: The results computed by the program.
    """

    input_data: Union[DualProgramInput, ProgramInput]
    results: OptimizationResults

    @property
    def final_molecule(self) -> Molecule:
        """Return the final molecule in the optimization."""
        return self.results.molecules[-1]


class ProgramFailure(OutputBase):
    """A object containing details about a failed calculation.

    Attributes:
        input_data: The input object for the computation.
        success: Always False for a Failed output.
        traceback: String representation of the traceback of the exception that caused
            the failure.
        results: Any compted data that was able to be extracted before program failed.
        stdout: The primary logging output of the program. Contains a union of stdout
            and stderr.
        provenance: An object containing the provenance information for the output.
    """

    input_data: Union[DualProgramInput, ProgramInput, FileInput]
    success: Literal[False] = False
    traceback: Optional[str] = None

    @property
    def ptraceback(self) -> None:
        """Print the traceback text"""
        print(self.traceback)
