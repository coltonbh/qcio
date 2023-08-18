# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

from .models import *  # noqa: F403

__version__ = metadata.version(__name__)

__all__ = [  # noqa: F405
    # Core Models
    "Files",
    "ComputedPropsBase",
    "OutputBase",
    "Files",
    "FileInput",
    "FileResult",
    "FileFailure",
    "Provenance",
    "Model",
    "CalcType",
    "ProgramInput",
    "SinglePointResults",
    "SinglePointOutput",
    "SinglePointFailure",
    "SinglePointComputedProps",
    "Wavefunction",
    "ProgramFailure",
    "ProgramArgs",
    "QCProgramArgs",
    "DualProgramArgs",
]
