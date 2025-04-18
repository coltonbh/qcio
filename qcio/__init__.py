# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

from .models import *  # noqa: F403
from .models.utils import rmsd, to_multi_xyz
from .utils import align, json_dumps

__version__ = metadata.version(__name__)


__all__ = [  # noqa: F405
    # Core Models
    "CalcType",
    "Model",
    "Provenance",
    "Structure",
    "Molecule",
    "Files",
    "FileInput",
    "ProgramInput",
    "ProgramOutput",
    "DualProgramInput",
    "SinglePointResults",
    "OptimizationResults",
    "Wavefunction",
    "ProgramArgs",
    "ProgramArgsSub",
    "json_dumps",
    "rmsd",
    "align",
    "to_multi_xyz",
    "LengthUnit",
]
