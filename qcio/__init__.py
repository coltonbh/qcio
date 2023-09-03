# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

from .models import *  # noqa: F403

__version__ = metadata.version(__name__)

__all__ = [  # noqa: F405
    # Core Models
    "Molecule",
    "Files",
    "OutputBase",
    "Files",
    "FileInput",
    "FileOutput",
    "Provenance",
    "Model",
    "CalcType",
    "ProgramInput",
    "SinglePointResults",
    "SinglePointOutput",
    "Wavefunction",
    "ProgramFailure",
    "ProgramArgs",
    "QCProgramArgs",
    "DualProgramArgs",
]
