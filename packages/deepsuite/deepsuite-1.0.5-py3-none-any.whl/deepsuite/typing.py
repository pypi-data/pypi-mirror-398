"""Type definitions for unified NumPy and PyTorch array handling."""

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
ArrayOrTensor = NDArray[np.float32] | torch.Tensor
