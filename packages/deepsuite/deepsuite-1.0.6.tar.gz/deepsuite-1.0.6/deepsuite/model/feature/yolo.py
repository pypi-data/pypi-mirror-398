"""Yolo module."""

from collections.abc import Sequence
from typing import Any

import torch
from torch.nn import Module

from deepsuite.lightning_base.module import BaseModule
from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.detection.yolo import YOLO


# End-to-End PyTorch-Lightning Modell
class Yolo(BaseModule):
    """Yolo Object Detection Model with EfficientNet Backbone, FPN Neck, and BBox and Classification Heads.

    Args:
        backbone (nn.Module): EfficientNet Backbone
        classification_model (nn.Module): Classification Model for direct classification
        reg_max (int): Maximum number of anchor boxes
        num_classes (int): Number of classes
        use_rotated_loss (bool): Whether to use rotated bounding box loss
        search_space (dict): Search space for hyperparameter optimization
        log_every_n_steps (int): Log metrics every n steps
        use_mlflow (bool): Whether to use MLflow for logging
        metrics (list): List of metrics to log

    Attributes:
        backbone (EfficientNetBackbone): EfficientNetBackbone
        neck (FPN): Feature Pyramid Network
        bbox_head (BBoxHead): Bounding Box Head
        classification_head (nn.Module): Classification Head
        bbox_loss (BboxLoss): Bounding Box Loss

    Examples:
        >>> efficientnet_model = EfficientNet(...)  # Your implementation of EfficientNet
        >>> mobilenet_model = MobileNetV3(...)  # Use MobileNet as classification head
        >>> model = ObjectDetection(efficientnet_model, mobilenet_model, num_classes
    """

    def __init__(
        self,
        classification_model: Module,
        backbone: BackboneAdapter,
        reg_max: int = 16,
        use_rotated_loss: bool = False,
        metrics: list[str] | None = None,
        stage_indices: Sequence[int] = (3, 4, 5),
        num_classes: int = 15_000,
        search_space: dict[str, Any] | None = None,
        log_every_n_steps: int = 50,
        use_mlflow: bool = False,
    ) -> None:
        """Initializes Yolo.

        Args:
            backbone (nn.Module): Feature extractor Backbone
            classification_model (nn.Module): Classification Model for direct classification
            reg_max (int): Maximum number of anchor boxes
            num_classes (int): Number of classes
            use_rotated_loss (bool): Whether to use rotated bounding box loss
            search_space (dict): Search space for hyperparameter optimization
            log_every_n_steps (int): Log metrics every n steps
            use_mlflow (bool): Whether to use MLflow for logging
            metrics (list): List of metrics to log
            stage_indices (Sequence[int]): Indizes der Feature Maps aus dem Backbone, die für die FPN verwendet werden.
        """
        if metrics is None:
            metrics = ["accuracy", "precision", "recall"]
        super().__init__(
            search_space=search_space,
            log_every_n_steps=log_every_n_steps,
            use_mlflow=use_mlflow,
            loss_fn=torch.nn.functional.cross_entropy,
            optimizer=torch.optim.Adam,
            num_classes=num_classes,
            metrics=metrics,
        )

        self.model = YOLO(
            classification_model=classification_model,
            backbone=backbone,
            reg_max=reg_max,
            use_rotated_loss=use_rotated_loss,
            stage_indices=stage_indices,
        )

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.model(args[0])

    def training_step(self, batch: Any, batch_idx: int) -> Any:
        """Training step for the model.

        Args:
            batch (Any): Input batch
            batch_idx (int): Batch index

        Returns:
            torch.Tensor: Loss

        Examples:
            >>> model = ObjectDetection(...)
            >>> model.training_step(batch, batch_idx)
        """
        images, targets = batch
        bbox_pred, class_pred = self(images)

        # Ankerlose Loss-Funktion verwenden
        bbox_loss = self.model.bbox_loss(bbox_pred, targets["target_bboxes"])

        # Klassifikationsloss
        class_loss = self.loss_fn(class_pred, targets["labels"])

        loss = bbox_loss + class_loss

        self.log("train/loss", loss, prog_bar=True, on_step=True, on_epoch=True, logger=True)

        return loss

    def validation_step(self, batch: Any, batch_idx: int) -> Any:
        images, targets = batch
        bbox_pred, class_pred = self(images)

        loss_iou, loss_dfl = self.model.bbox_loss(
            bbox_pred,
            targets["bboxes"],
            targets["anchor_points"],
            targets["target_bboxes"],
            targets["target_scores"],
            targets["target_scores_sum"],
            targets["fg_mask"],
        )
        bbox_loss_val = loss_iou + loss_dfl

        class_loss = self.loss_fn(class_pred, targets["labels"])
        loss = bbox_loss_val + class_loss

        self.log("val/loss", loss, prog_bar=True, on_epoch=True, logger=True)

        for name, metric in self.active_metrics.items():
            self.log(
                f"val/{name}", metric(class_pred, targets["labels"]), prog_bar=True, on_epoch=True
            )

        return loss

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.Adam(self.parameters(), lr=1e-4)

    def on_train_epoch_end(self) -> None:
        for metric in self.active_metrics.values():
            metric.reset()

    def on_validation_epoch_end(self) -> None:
        for metric in self.active_metrics.values():
            metric.reset()
