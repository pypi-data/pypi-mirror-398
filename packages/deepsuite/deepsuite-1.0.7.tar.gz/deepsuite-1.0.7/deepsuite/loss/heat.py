"""Heatmap Loss module for keypoints."""

from collections.abc import Mapping

import torch
from torch import Tensor

from deepsuite.loss.focal import BinaryFocalLoss


class KeypointHeatmapLoss(BinaryFocalLoss):  # type: ignore[misc]
    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean",
        weights: dict[str, float] | None = None,
    ) -> None:
        super().__init__(alpha=alpha, gamma=gamma, reduction=reduction)
        self.weights = weights or {"tl_heat": 1.0, "br_heat": 1.0, "ct_heat": 1.0}

    def forward(self, pred: Mapping[str, Tensor], target: Mapping[str, Tensor]) -> Tensor:
        """Compute weighted focal heatmap loss for multiple keypoint maps.

        Args:
            pred: Dict with 'tl_heat', 'br_heat', 'ct_heat' logits (B, C, H, W).
            target: Dict with same keys and binary target heatmaps.
        """
        total_loss: Tensor = torch.tensor(0.0, device=next(iter(pred.values())).device)
        for key in ["tl_heat", "br_heat", "ct_heat"]:
            total_loss = total_loss + self.weights[key] * super().forward(pred[key], target[key])
        return total_loss
