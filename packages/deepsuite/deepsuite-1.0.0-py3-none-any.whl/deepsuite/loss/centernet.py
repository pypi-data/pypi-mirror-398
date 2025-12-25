"""Centernet module."""

from torch import Tensor
from torch.nn import Module

from deepsuite.loss.bbox import AnkerloserBboxLoss
from deepsuite.loss.heat import KeypointHeatmapLoss


class CenterNetLoss(Module):
    def __init__(self, heatmap_weight=1.0, bbox_weight=1.0) -> None:
        super().__init__()
        self.heatmap_loss = KeypointHeatmapLoss()
        self.bbox_loss = AnkerloserBboxLoss()

        self.heatmap_weight = heatmap_weight
        self.bbox_weight = bbox_weight

    def forward(self, preds: dict, targets: dict) -> Tensor:
        """preds: dict with keys ['tl_heat', 'br_heat', 'ct_heat', 'bbox']
        targets: dict with same keys and 'bbox_mask'
        """
        loss = 0.0
        loss += self.heatmap_weight * self.heatmap_loss(preds, targets)
        if "bbox" in preds:
            loss += self.bbox_weight * self.bbox_loss(
                preds["bbox"], targets["bbox"], targets["bbox_mask"]
            )
        return loss
