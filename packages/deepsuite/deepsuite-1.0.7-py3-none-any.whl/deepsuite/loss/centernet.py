"""CenterNet loss wrapper combining heatmap and bbox losses."""

from collections.abc import Mapping

import torch
from torch import Tensor
from torch.nn import Module

from deepsuite.loss.bbox import AnkerloserBboxLoss
from deepsuite.loss.heat import KeypointHeatmapLoss


class CenterNetLoss(Module):
    def __init__(self, heatmap_weight: float = 1.0, bbox_weight: float = 1.0) -> None:
        super().__init__()
        self.heatmap_loss = KeypointHeatmapLoss()
        self.bbox_loss = AnkerloserBboxLoss()

        self.heatmap_weight = heatmap_weight
        self.bbox_weight = bbox_weight

    def forward(self, preds: Mapping[str, Tensor], targets: Mapping[str, Tensor]) -> Tensor:
        """Compute CenterNet loss.

        Args:
            preds: Dict with keys ['tl_heat', 'br_heat', 'ct_heat', 'bbox'].
            targets: Dict with same keys and 'bbox_mask'.
        """
        loss: Tensor = torch.tensor(0.0, device=next(iter(preds.values())).device)
        loss = loss + self.heatmap_weight * self.heatmap_loss(preds, targets)
        if "bbox" in preds:
            loss = loss + self.bbox_weight * self.bbox_loss(
                preds["bbox"], targets["bbox"], targets["bbox_mask"]
            )
        return loss
