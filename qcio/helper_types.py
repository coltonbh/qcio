from pathlib import Path
from typing import List, Union

import numpy as np
from pydantic import PlainSerializer
from typing_extensions import Annotated

StrOrPath = Annotated[Union[str, Path], PlainSerializer(lambda x: str(x))]

# May be energy (float), gradient or hessian (List[List[float]])
SPReturnResult = Union[float, List[List[float]]]

# Type for any values that can be coerced to 2D numpy array
ArrayLike2D = Annotated[
    Union[List[List[float]], List[float], np.ndarray],
    PlainSerializer(lambda x: np.array(x).tolist()),
]

# Type for any values that can be coerced to 3D numpy array
ArrayLike3D = Annotated[
    Union[List[List[List[float]]], List[List[float]], np.ndarray],
    PlainSerializer(lambda x: np.array(x).tolist()),
]
