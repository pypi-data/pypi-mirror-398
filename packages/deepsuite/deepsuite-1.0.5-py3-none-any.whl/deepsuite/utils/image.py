"""Image module."""

import torch


def crop_mask(masks: torch.Tensor, boxes: torch.Tensor) -> torch.Tensor:
    """Crop masks to bounding boxes.

    Args:
        masks: Tensor of shape ``(n, h, w)`` containing binary masks.
        boxes: Tensor of shape ``(n, 4)`` with bbox coordinates in relative point form.

    Returns:
        torch.Tensor: Cropped masks of shape ``(n, h, w)``.
    """
    _, h, w = masks.shape
    x1, y1, x2, y2 = torch.chunk(boxes[:, :, None], 4, 1)  # x1 shape(n,1,1)
    r = torch.arange(w, device=masks.device, dtype=x1.dtype)[None, None, :]  # rows shape(1,1,w)
    c = torch.arange(h, device=masks.device, dtype=x1.dtype)[None, :, None]  # cols shape(1,h,1)

    return masks * ((r >= x1) * (r < x2) * (c >= y1) * (c < y2))
