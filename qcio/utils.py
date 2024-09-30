import json
from typing import List, Union

import numpy as np
from pydantic import BaseModel

from .models import Structure  # FileOutput,

# Helper Structures
water = Structure(
    symbols=["O", "H", "H"],
    geometry=np.array(
        [
            [0.0253397, 0.01939466, -0.00696322],
            [0.22889176, 1.84438441, 0.16251426],
            [1.41760224, -0.62610794, -1.02954938],
        ]
    ),
    charge=0,
    multiplicity=1,
    connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
    identifiers={"name": "water"},
)


def json_dumps(obj: Union[BaseModel, List[BaseModel]]) -> str:
    """Serialization helper for lists of pydantic objects."""
    if isinstance(obj, list):
        return json.dumps([o.model_dump() for o in obj])
    return obj.model_dump_json()
