from pathlib import Path
from typing import List, Union

import numpy as np

StrOrPath = Union[str, Path]

# May be energy (float), gradient or hessian (List[List[float]])
SPReturnResult = Union[float, List[List[float]]]

# Type for any values that can be coerced to 2D numpy array
ArrayLike2D = Union[List[List[float]], List[float], np.ndarray]
