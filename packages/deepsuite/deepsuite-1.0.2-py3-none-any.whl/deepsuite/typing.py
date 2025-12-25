"""Type definitions for unified NumPy and PyTorch array handling."""

from typing import Union

import numpy as np
from numpy.typing import NDArray
import torch

#: A unified type for either a NumPy array (float32) or a PyTorch tensor.
#:
#: Useful for writing functions that accept or return either framework's data format
#: without sacrificing type safety or requiring duplicate logic.
#:
#: Examples:
#:
#:     def normalize(x: ArrayOrTensor) -> ArrayOrTensor:
#:         ...
ArrayOrTensor = Union[NDArray[np.float32], torch.Tensor]
