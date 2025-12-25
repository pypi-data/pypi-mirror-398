"""YOLO object detection model for end-to-end object detection.

This module implements YOLO (You Only Look Once) with modular backbone,
FPN neck, and BBox/Classification heads for end-to-end object detection.

Example:
    ```python
    import torch
    from deepsuite.model.detection.yolo import YOLO
    from deepsuite.model.backbone import ResNet50Backbone

    backbone = ResNet50Backbone()
    model = YOLO(
        classification_model=classification_model,
        backbone=backbone,
        reg_max=16,
        use_rotated_loss=False
    )
    x = torch.randn(2, 3, 640, 640)
    output = model(x)
    ```

Classes:
    YOLO: Complete YOLO detection model.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch
from torch import nn

from deepsuite.heads.box import BBoxHead
from deepsuite.loss.bbox import BboxLoss, RotatedBboxLoss
from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.feature.fpn import FPN


class YOLO(nn.Module):
    """YOLO Objektdektektions-Modell mit FPN Neck.

    Kombiniert einen konfigurierbaren Backbone, Feature Pyramid Network (FPN),
    BBox und Classification Heads für Objektdetektion.

    Attributes:
        backbone: Feature-Extraktions-Backbone.
        neck: Feature Pyramid Network für Multi-Scale Features.
        bbox_head: Bounding Box Vorhersage Head.
        classification_head: Klassifikations Head.
        bbox_loss: Loss-Funktion für BBox Regression (IoU + DFL).
        extra_heads: Zusätzliche optionale Heads.

    Beispiel:
        ```python
        model = YOLO(
            classification_model=cls_model,
            backbone=backbone,
            reg_max=16,
            use_rotated_loss=False,
            stage_indices=(3, 4, 5)
        )
        output = model(x)  # Returns dict with 'bbox' and 'cls' predictions
        ```
    """

    def __init__(
        self,
        classification_model: nn.Module,
        backbone: BackboneAdapter,
        reg_max: int = 16,
        use_rotated_loss: bool = False,
        stage_indices: Sequence[int] = (3, 4, 5),
        extra_heads: dict[str, nn.Module] | None = None,
    ) -> None:
        """Initialisiert das YOLO-Modell mit konfigurierbarem Backbone und Heads.

        Args:
            classification_model: Klassifikations-Modul für Klassen-Vorhersagen.
            backbone: Feature-Extraktions-Backbone (z. B. ResNet, EfficientNet).
            reg_max: Maximale Anzahl Bins für Distribution Focal Loss.
            use_rotated_loss: Falls True, verwende RotatedBboxLoss für rotierte BBoxen.
            stage_indices: Indices der Backbone-Stages für FPN-Input.
            extra_heads: Optionale zusätzliche Heads als Dictionary.
        """
        super().__init__()

        # Setze Backbone
        self.backbone = backbone
        self.backbone.set_stage_indices(stage_indices)

        # Setze Feature Pyramid Network
        channels = self.get_backbone_out_channels(backbone)
        self.neck = FPN(channels, 256)

        # Baue Heads
        self.bbox_head = BBoxHead(256)  # BBox Vorhersage
        self.classification_head = classification_model  # Klassifikation

        # Wähle passende BBox-Loss basierend auf Rotiertheit
        self.bbox_loss: BboxLoss | RotatedBboxLoss = (
            RotatedBboxLoss(reg_max=reg_max) if use_rotated_loss else BboxLoss(reg_max=reg_max)
        )

        self.extra_heads = nn.ModuleDict(extra_heads or {})

    def forward(self, *args: Any, **kwargs: Any) -> dict[str, torch.Tensor]:
        """Forward Pass durch das Dektektions-Modell.

        Args:
            *args: Positionsargumente, args[0] ist der Input-Tensor.
            **kwargs: Benannte Argumente (z.B. Rückgabe von Zwischenschritten).

        Returns:
            dict[str, torch.Tensor]: Dictionary mit 'bbox' und 'cls' Vorhersagen.

        Beispiel:
            ```python
            x = torch.randn(2, 3, 640, 640)
            output = model(x)
            # output['bbox']: Shape (2, num_anchors, 4)
            # output['cls']: Shape (2, num_anchors, num_classes)
            ```

        Raises:
            AssertionError: Falls Backbone nicht die richtige Anzahl Features zurückgibt.
        """
        x = args[0]

        features = self.backbone(x, return_stages=True)

        assert len(features) == len(self.neck.lateral_convs), (
            f"Backbone gab {len(features)} Features zurück, "
            f"aber FPN erwartet {len(self.neck.lateral_convs)}."
        )

        pyramid_feats = self.neck(features)

        outputs = {
            "bbox": self.bbox_head(pyramid_feats[-1]),
            "class": self.classification_head(pyramid_feats[-1]),
        }

        for name, head in self.extra_heads.items():
            outputs[name] = head(pyramid_feats[-1])

        return outputs

    @staticmethod
    def get_backbone_out_channels(backbone: nn.Module, x: torch.Tensor | None = None) -> list[int]:
        with torch.no_grad():
            x = torch.randn(1, 3, 224, 224) if x is None else x
            features = backbone(x, return_stages=True)
            return [f.shape[1] for f in features]

    @staticmethod
    def crop_from_rotated_boxes(
        images: torch.Tensor, boxes: torch.Tensor, size: tuple[int, int] = (224, 224)
    ) -> dict[str, Any]:
        device = images.device
        _b, _c, _h, _w = images.shape
        crops = []
        crop_indices = []
        xyxy_boxes = []

        for batch_idx, (img, img_boxes) in enumerate(zip(images, boxes)):
            for box_idx, box in enumerate(img_boxes):
                cx, cy, w, h, angle = box.tolist()

                scale_x = w / _w
                scale_y = h / _h
                tx = (2 * cx / _w) - 1
                ty = (2 * cy / _h) - 1

                theta = torch.tensor(
                    [
                        [scale_x * torch.cos(angle), -scale_y * torch.sin(angle), tx],
                        [scale_x * torch.sin(angle), scale_y * torch.cos(angle), ty],
                    ],
                    device=device,
                ).unsqueeze(0)

                grid = torch.nn.functional.affine_grid(
                    theta, size=[1, _c, *size], align_corners=False
                )
                crop = torch.nn.functional.grid_sample(img.unsqueeze(0), grid, align_corners=False)
                crops.append(crop)
                crop_indices.append((batch_idx, box_idx))

                x1 = max(int(cx - w / 2), 0)
                y1 = max(int(cy - h / 2), 0)
                x2 = min(int(cx + w / 2), img.shape[2])
                y2 = min(int(cy + h / 2), img.shape[1])
                xyxy_boxes.append((batch_idx, box_idx, x1, y1, x2, y2))

        return {
            "crops": torch.cat(crops, dim=0),
            "indices": crop_indices,
            "boxes_xyxy": xyxy_boxes,
        }

    @staticmethod
    def crop_from_boxes(
        images: torch.Tensor, boxes: torch.Tensor, size: tuple[int, int] = (224, 224)
    ) -> dict[str, Any]:
        crops = []
        crop_indices = []
        xyxy_boxes = []

        for batch_idx, (img, img_boxes) in enumerate(zip(images, boxes)):
            for box_idx, box in enumerate(img_boxes):
                cx, cy, w, h, _ = box.tolist()

                x1 = max(int(cx - w / 2), 0)
                y1 = max(int(cy - h / 2), 0)
                x2 = min(int(cx + w / 2), img.shape[2])
                y2 = min(int(cy + h / 2), img.shape[1])

                crop = img[:, y1:y2, x1:x2]
                crop = torch.nn.functional.interpolate(
                    crop.unsqueeze(0), size=size, mode="bilinear", align_corners=False
                )
                crops.append(crop)
                crop_indices.append((batch_idx, box_idx))
                xyxy_boxes.append((batch_idx, box_idx, x1, y1, x2, y2))

        return {
            "crops": torch.cat(crops, dim=0),
            "indices": crop_indices,
            "boxes_xyxy": xyxy_boxes,
        }
