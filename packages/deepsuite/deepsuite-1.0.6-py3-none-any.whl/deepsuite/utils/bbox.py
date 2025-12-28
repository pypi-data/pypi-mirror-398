"""Bounding box coordinate transformation utilities.

Provides functions for converting between different bounding box representations:
- Distance-based (ltrb: left, top, right, bottom distances from anchor)
- Center-based (xywh: center x, center y, width, height)
- Corner-based (xyxy: x1, y1, x2, y2 coordinates)
"""

import torch


def dist2bbox(
    distance: torch.Tensor,
    anchor_points: torch.Tensor,
    xywh: bool = True,
    dim: int = -1,
) -> torch.Tensor:
    """Transform distance predictions to bounding boxes.

    Converts distance-based box encoding (left, top, right, bottom distances
    from anchor points) to either center-based (xywh) or corner-based (xyxy)
    bounding box format.

    Args:
        distance: Distance predictions of shape (..., 4) containing
            (left, top, right, bottom) distances from anchor points.
        anchor_points: Anchor point coordinates of shape (..., 2) containing
            (x, y) center positions.
        xywh: If True, return boxes in (cx, cy, w, h) format.
            If False, return boxes in (x1, y1, x2, y2) format. Defaults to True.
        dim: Dimension along which to split and concatenate distance components.
            Defaults to -1.

    Returns:
        Bounding boxes with same dtype and device as inputs:
            - If xywh=True: shape (..., 4) as (center_x, center_y, width, height)
            - If xywh=False: shape (..., 4) as (x1, y1, x2, y2)

    Note:
        The distance tensor is expected to have 4 channels in the specified dimension:
        [left_dist, top_dist, right_dist, bottom_dist]. These are converted to
        corner coordinates before optional conversion to center format.

    Examples:
        >>> anchor_points = torch.tensor([[10.0, 10.0], [20.0, 20.0]])
        >>> distances = torch.tensor([[2.0, 3.0, 2.0, 3.0], [1.0, 1.0, 1.0, 1.0]])
        >>> boxes_xywh = dist2bbox(distances, anchor_points, xywh=True)
        >>> boxes_xywh
        tensor([[10., 10.,  4.,  6.],
                [20., 20.,  2.,  2.]])
        >>> boxes_xyxy = dist2bbox(distances, anchor_points, xywh=False)
        >>> boxes_xyxy
        tensor([[ 8.,  7., 12., 13.],
                [19., 19., 21., 21.]])
    """
    lt, rb = distance.chunk(2, dim)
    x1y1 = anchor_points - lt
    x2y2 = anchor_points + rb
    if xywh:
        c_xy = (x1y1 + x2y2) / 2
        wh = x2y2 - x1y1
        return torch.cat((c_xy, wh), dim)  # xywh bbox
    return torch.cat((x1y1, x2y2), dim)  # xyxy bbox


def bbox2dist(
    anchor_points: torch.Tensor,
    bbox: torch.Tensor,
    reg_max: int,
) -> torch.Tensor:
    """Transform bounding boxes to distance predictions.

    Converts corner-based bounding boxes (xyxy format) to distance-based
    encoding (left, top, right, bottom distances from anchor points).
    Commonly used in anchor-free detection for training targets.

    Args:
        anchor_points: Anchor point coordinates of shape (..., 2) containing
            (x, y) center positions.
        bbox: Bounding boxes in corner format of shape (..., 4) as
            (x1, y1, x2, y2) coordinates.
        reg_max: Maximum regression distance value for clamping.
            Distances are clamped to [0, reg_max - 0.01].

    Returns:
        Distance encodings of shape (..., 4) as (left, top, right, bottom)
        distances from anchor points, clamped to valid range.

    Note:
        The small offset (0.01) in clamping prevents numerical issues when
        distances exactly equal reg_max. This is particularly important for
        distribution focal loss (DFL) implementations.

    Examples:
        >>> anchor_points = torch.tensor([[10.0, 10.0]])
        >>> bbox = torch.tensor([[8.0, 7.0, 12.0, 13.0]])
        >>> distances = bbox2dist(anchor_points, bbox, reg_max=16)
        >>> distances
        tensor([[2., 3., 2., 3.]])
    """
    x1y1, x2y2 = bbox.chunk(2, -1)
    return torch.cat((anchor_points - x1y1, x2y2 - anchor_points), -1).clamp_(0, reg_max - 0.01)
