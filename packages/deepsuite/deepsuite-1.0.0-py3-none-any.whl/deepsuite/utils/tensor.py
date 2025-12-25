"""Tensor module."""

import numpy as np
import torch

from deepsuite.typing import ArrayOrTensor


def empty_like(x: ArrayOrTensor) -> ArrayOrTensor:
    """Create an empty tensor or array with the same shape as the input.

    This function returns a new uninitialized tensor or array with the same shape
    as `x` and a float32 data type. The returned object will be a `torch.Tensor`
    if `x` is a tensor, or a `numpy.ndarray` if `x` is a NumPy array.

    Args:
        x (NDArray[Any] | torch.Tensor): Input tensor or array whose shape will be copied.

    Returns:
        NDArray[Any] | torch.Tensor: An uninitialized tensor or array with float32 dtype.
    """
    return (
        torch.empty_like(x, dtype=torch.float32)
        if isinstance(x, torch.Tensor)
        else np.empty_like(x, dtype=np.float32)
    )
