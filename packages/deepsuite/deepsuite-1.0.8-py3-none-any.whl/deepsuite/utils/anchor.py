"""Anchor point generation utilities for anchor-free object detection.

Provides functions to generate anchor points and stride tensors from feature
maps at multiple scales. Commonly used in YOLO and other anchor-free detectors.
"""

import torch


def make_anchors(
    feats: list[torch.Tensor] | list[tuple[int, int]],
    strides: list[int],
    grid_cell_offset: float = 0.5,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Generate anchor points and stride tensors from feature maps.

    Creates a grid of anchor points for each feature map scale, with each point
    representing the center of a grid cell. Also generates corresponding stride
    values indicating the downsampling factor at each scale.

    Args:
        feats: Feature maps or their shapes. Can be either:
            - List of tensors with shape (B, C, H, W)
            - List of (H, W) tuples specifying spatial dimensions
        strides: Downsampling stride for each feature level (e.g., [8, 16, 32]).
            Must have same length as feats.
        grid_cell_offset: Offset to add to grid coordinates, typically 0.5 to
            center anchors within grid cells. Defaults to 0.5.

    Returns:
        A tuple containing:
            - anchor_points: Concatenated anchor coordinates of shape (N, 2)
                where N = sum(H_i * W_i) for all feature levels.
                Each row is (x, y) in the original image coordinate space.
            - stride_tensor: Corresponding stride values of shape (N, 1)
                indicating the feature map stride for each anchor point.

    Raises:
        AssertionError: If feats is None or empty.
        ValueError: If feats and strides have different lengths.

    Note:
        - Anchor points are offset by grid_cell_offset (default 0.5) to represent
          grid cell centers rather than top-left corners.
        - Output dtype and device match the first feature map.
        - Stride tensor is useful for normalizing regression targets.

    Examples:
        >>> # Using feature map tensors
        >>> feat1 = torch.randn(2, 256, 80, 80)  # stride 8
        >>> feat2 = torch.randn(2, 256, 40, 40)  # stride 16
        >>> feat3 = torch.randn(2, 256, 20, 20)  # stride 32
        >>> anchors, strides = make_anchors([feat1, feat2, feat3], [8, 16, 32])
        >>> anchors.shape
        torch.Size([8400, 2])  # 80*80 + 40*40 + 20*20 = 8400
        >>> strides.shape
        torch.Size([8400, 1])
        >>> # First few anchors are from 80x80 feature map with stride 8
        >>> anchors[:3]
        tensor([[0.5, 0.5],
                [1.5, 0.5],
                [2.5, 0.5]])
        >>> strides[:3]
        tensor([[8.],
                [8.],
                [8.]])

        >>> # Using shape tuples
        >>> anchors, strides = make_anchors([(80, 80), (40, 40)], [8, 16])
        >>> anchors.shape
        torch.Size([8000, 2])  # 80*80 + 40*40 = 8000
    """
    anchor_points, stride_tensor = [], []
    assert feats is not None
    dtype, device = feats[0].dtype, feats[0].device
    for i, stride in enumerate(strides):
        h, w = (
            feats[i].shape[2:] if isinstance(feats, list) else (int(feats[i][0]), int(feats[i][1]))
        )
        sx = torch.arange(end=w, device=device, dtype=dtype) + grid_cell_offset
        sy = torch.arange(end=h, device=device, dtype=dtype) + grid_cell_offset
        sy, sx = torch.meshgrid(sy, sx, indexing="ij")
        anchor_points.append(torch.stack((sx, sy), -1).view(-1, 2))
        stride_tensor.append(torch.full((h * w, 1), stride, dtype=dtype, device=device))
    return torch.cat(anchor_points), torch.cat(stride_tensor)
