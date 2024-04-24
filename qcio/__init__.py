# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

from .models import *  # noqa: F403
from .utils import json_dumps

__version__ = metadata.version(__name__)

__all__ = [  # noqa: F405
    # Core Models
    "CalcType",
    "Model",
    "Provenance",
    "Molecule",
    "Files",
    "FileInput",
    "ProgramInput",
    "ProgramOutput",
    "DualProgramInput",
    "NoResults",
    "SinglePointResults",
    "OptimizationResults",
    "SinglePointOutput",
    "Wavefunction",
    "ProgramArgs",
    "ProgramArgsSub",
    "json_dumps",
]
