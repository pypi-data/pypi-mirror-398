"""Xy module."""

from typing import cast

import numpy as np
from numpy.typing import NDArray
import torch

from deepsuite.typing import ArrayOrTensor
from deepsuite.utils.tensor import empty_like


def xywh2xyxy(x: ArrayOrTensor) -> ArrayOrTensor:
    """Convert bounding boxes from (x, y, width, height) to (x1, y1, x2, y2) format.

    (x, y) is the center of the box, (x1, y1) is the top-left, and (x2, y2) is the bottom-right.

    Args:
        x (np.ndarray | torch.Tensor): Bounding boxes in (x, y, w, h) format. Last dim must be 4.

    Returns:
        np.ndarray | torch.Tensor: Bounding boxes in (x1, y1, x2, y2) format.
    """
    assert x.shape[-1] == 4, f"Expected input shape [..., 4], got {x.shape}"
    y = empty_like(x)

    if isinstance(x, torch.Tensor):
        xy = x[..., :2]
        wh = x[..., 2:] / 2
        y[..., :2] = xy - wh
        y[..., 2:] = xy + wh
    else:
        xy_np = x[..., :2].astype(np.float32)
        wh_np = (x[..., 2:] / 2).astype(np.float32)
        y_np = cast("NDArray[np.float32]", y)
        y_np[..., :2] = xy_np - wh_np
        y_np[..., 2:] = xy_np + wh_np
        y = y_np

    return y


def xyxy2xywh(x: ArrayOrTensor) -> ArrayOrTensor:
    """Convert bounding boxes from (x1, y1, x2, y2) to (x, y, width, height) format.

    (x1, y1) is the top-left corner, (x2, y2) the bottom-right. (x, y) is the box center.

    Args:
        x (np.ndarray | torch.Tensor): Bounding boxes in (x1, y1, x2, y2) format.
            Last dim must be 4.

    Returns:
        np.ndarray | torch.Tensor: Bounding boxes in (x, y, w, h) format.
    """
    assert x.shape[-1] == 4, f"Expected input shape [..., 4], got {x.shape}"
    y = empty_like(x)

    if isinstance(x, torch.Tensor):
        y[..., 0] = (x[..., 0] + x[..., 2]) / 2
        y[..., 1] = (x[..., 1] + x[..., 3]) / 2
        y[..., 2] = x[..., 2] - x[..., 0]
        y[..., 3] = x[..., 3] - x[..., 1]
    else:
        x = x.astype(np.float32)
        y_np = cast("NDArray[np.float32]", y)
        y_np[..., 0] = (x[..., 0] + x[..., 2]) / 2
        y_np[..., 1] = (x[..., 1] + x[..., 3]) / 2
        y_np[..., 2] = x[..., 2] - x[..., 0]
        y_np[..., 3] = x[..., 3] - x[..., 1]
        y = y_np

    return y
