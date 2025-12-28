"""Keypoint module."""

r"""This module contains the KeypointLoss class for computing training losses.

..math::
     loss = \frac{1}{N} \\sum_{i=1}^{N} \frac{1}{M} \\sum_{j=1}^{M} \frac{1}{2 \\sigma^2} \\left\\| \\hat{y}_{ij} - y_{ij} \right\\|^2

Example:
    >>> import torch
    >>> from deepsuite.loss import KeypointLoss
    >>> criterion = KeypointLoss()
    >>> preds = torch.randn(2, 1)
    >>> labels = torch.randint(0, 2, (2, 1))
    >>> loss = criterion(preds, labels)
    >>> loss
    tensor(0.0000)
    >>> loss_items
    tensor(0.0000)

Attributes:
    KeypointLoss: The class for computing the Keypoint Loss.

Methods:
    forward: Compute the Keypoint Loss between predictions and true labels.

References:
    https://arxiv.org/abs/1708.02002

"""

import torch
from torch import nn


class KeypointLoss(nn.Module):
    """Criterion class for computing training losses.

    This class implements the keypoint loss for keypoint detection tasks.

    Attributes:
        sigmas (torch.Tensor): Standard deviations for keypoint coordinates.
    """

    def __init__(self, sigmas: torch.Tensor) -> None:
        """Initialize the KeypointLoss class.

        Args:
            sigmas (torch.Tensor): Standard deviations for keypoint coordinates.
        """
        super().__init__()
        self.sigmas = sigmas

    def forward(
        self, pred_kpts: torch.Tensor, gt_kpts: torch.Tensor, kpt_mask: torch.Tensor, area: float
    ) -> torch.Tensor:
        """Calculates keypoint loss factor and Euclidean distance loss for predicted and actual keypoints.

        Args:
            pred_kpts (torch.Tensor): Predicted keypoints.
            gt_kpts (torch.Tensor): Ground truth keypoints.
            kpt_mask (torch.Tensor): Mask for valid keypoints.
            area (float): Area of the bounding box.

        Returns:
            torch.Tensor: Computed keypoint loss.
        """
        d = (pred_kpts[..., 0] - gt_kpts[..., 0]).pow(2) + (
            pred_kpts[..., 1] - gt_kpts[..., 1]
        ).pow(2)
        kpt_loss_factor = kpt_mask.shape[1] / (torch.sum(kpt_mask != 0, dim=1) + 1e-9)
        e = d / ((2 * self.sigmas).pow(2) * (area + 1e-9) * 2)
        from typing import cast

        return cast(
            "torch.Tensor", (kpt_loss_factor.view(-1, 1) * ((1 - torch.exp(-e)) * kpt_mask)).mean()
        )
