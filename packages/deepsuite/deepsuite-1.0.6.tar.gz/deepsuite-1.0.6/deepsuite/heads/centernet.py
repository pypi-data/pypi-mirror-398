"""Centernet module."""

from torch.nn import Module, ModuleList

from deepsuite.heads.box import RotationFreeBBoxHead
from deepsuite.heads.heatmap import HeatmapHead, OffsetHead


class CenterNetHead(Module):
    def __init__(
        self, in_channels: int, num_classes: int = 1, use_bbox_regression: bool = False
    ) -> None:
        super().__init__()

        # Heatmaps
        self.tl_heat = HeatmapHead(in_channels, num_classes)
        self.br_heat = HeatmapHead(in_channels, num_classes)
        self.ct_heat = HeatmapHead(in_channels, num_classes)

        # Offsets
        self.tl_off = OffsetHead(in_channels)
        self.br_off = OffsetHead(in_channels)
        self.ct_off = OffsetHead(in_channels)

        self.use_bbox_regression = use_bbox_regression
        if self.use_bbox_regression:
            self.bbox_reg = RotationFreeBBoxHead(in_channels)

    def forward(self, x):
        out = {
            "tl_heat": self.tl_heat(x),
            "br_heat": self.br_heat(x),
            "ct_heat": self.ct_heat(x),
            "tl_off": self.tl_off(x),
            "br_off": self.br_off(x),
            "ct_off": self.ct_off(x),
        }
        if self.use_bbox_regression:
            out["bbox"] = self.bbox_reg(x)  # (B, 4, H, W)
        return out


class MultiScaleCenterNetHead(Module):
    def __init__(self, in_channels_list, num_classes=1) -> None:
        super().__init__()
        self.heads = ModuleList([CenterNetHead(ch, num_classes) for ch in in_channels_list])

    def forward(self, features):  # list of FPN outputs
        return [head(f) for head, f in zip(self.heads, features, strict=False)]
