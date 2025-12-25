"""Heat module."""

from torch import Tensor

from deepsuite.loss.focal import BinaryFocalLoss


class KeypointHeatmapLoss(BinaryFocalLoss):
    def __init__(
        self, alpha=0.25, gamma=2.0, reduction="mean", weights: dict | None = None
    ) -> None:
        super().__init__(alpha=alpha, gamma=gamma, reduction=reduction)
        self.weights = weights or {"tl_heat": 1.0, "br_heat": 1.0, "ct_heat": 1.0}

    def forward(self, pred: dict, target: dict) -> Tensor:
        """Args:
        pred: dict with 'tl_heat', 'br_heat', 'ct_heat' logits (B, C, H, W)
        target: dict with same keys and binary target heatmaps
        """
        total_loss = 0.0
        for key in ["tl_heat", "br_heat", "ct_heat"]:
            total_loss += self.weights[key] * super().forward(pred[key], target[key])
        return total_loss
