from pathlib import Path
from typing import Union

import numpy as np
from pydantic import PlainSerializer, SkipValidation
from typing_extensions import Annotated

StrOrPath = Annotated[Union[str, Path], PlainSerializer(lambda x: str(x))]

# Skipping validation allows non numpy arrays to be passed and then coerced by
# validators to numpy arrays.
SerializableNDArray = Annotated[
    SkipValidation[np.ndarray], PlainSerializer(lambda x: np.array(x).tolist())
]
