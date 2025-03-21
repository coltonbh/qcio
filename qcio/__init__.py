# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
import sys
from importlib import metadata

from .models import *  # noqa: F403
from .models.utils import to_multi_xyz
from .utils import json_dumps

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
    "SinglePointOutput",
    "Wavefunction",
    "ProgramArgs",
    "ProgramArgsSub",
    "json_dumps",
    "to_multi_xyz",
    "LengthUnit",
]


def load_plugins():
    if sys.version_info >= (3, 10):
        # New syntax (Python 3.10+)
        eps = metadata.entry_points(group="qcio.plugins")
    else:
        # Older syntax (Python 3.9)
        eps = metadata.entry_points().get("qcio.plugins", [])

    for entry_point in eps:
        entry_point.load()()


# Automatically load plugins at import-time
load_plugins()
