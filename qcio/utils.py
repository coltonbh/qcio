import json
from typing import List, Optional, Union

from pydantic import BaseModel

from .models import (
    CalcType,
    FileOutput,
    Molecule,
    OptimizationOutput,
    SinglePointOutput,
)

# Helper Molecules
water = Molecule(
    symbols=["O", "H", "H"],
    geometry=[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0, 1.0, 0.0],
    charge=0,
    multiplicity=1,
    connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
)


def calctype_to_output(calctype: Optional[CalcType]):
    """Return the output object for the given calculation type."""
    calctype_to_output = {
        None: FileOutput,  # Covers FileInput case
        CalcType.energy: SinglePointOutput,
        CalcType.gradient: SinglePointOutput,
        CalcType.hessian: SinglePointOutput,
        CalcType.optimization: OptimizationOutput,
        CalcType.transition_state: OptimizationOutput,
    }
    return calctype_to_output[calctype]


def json_dumps(obj: Union[BaseModel, List[BaseModel]]) -> str:
    """Serialization helper for lists of pydantic objects."""
    if isinstance(obj, list):
        return json.dumps([o.model_dump() for o in obj])
    return obj.model_dump_json()
