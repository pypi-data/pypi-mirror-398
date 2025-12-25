"""Centernet module."""

import torch

from deepsuite.lightning_base.module import BaseModule
from deepsuite.loss import get_loss
from deepsuite.metric.detection import DetectionMetrics
from deepsuite.model.detection.centernet import CenterNetDecoder, CenterNetModel


class CenterNetModule(BaseModule):
    def __init__(
        self,
        backbone,
        in_channels_list,
        num_classes=1,
        lr=1e-3,
        decoder_topk=100,
        loss_fn=None,
    ) -> None:
        loss_fn = loss_fn or get_loss("centernet")

        super().__init__(loss_fn=loss_fn)

        self.save_hyperparameters()

        self.model = CenterNetModel(
            backbone=backbone, in_channels_list=in_channels_list, num_classes=num_classes
        )
        self.decoder = CenterNetDecoder(topk=decoder_topk)

        self.loss_fn = loss_fn
        self.metrics = DetectionMetrics(num_classes=num_classes)

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, targets = batch
        outputs = self(x)
        loss = self.loss_fn(outputs, targets)

        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, targets = batch
        outputs = self(x)
        loss = self.loss_fn(outputs, targets)

        pred_boxes = self.decoder(outputs, img_size=x.shape[2:])
        if isinstance(targets, dict):
            gt_boxes = targets["boxes"]
        else:
            gt_boxes = [t for t in targets]

        self.metrics.update(pred_boxes, gt_boxes)
        self.log("val/loss", loss, prog_bar=True)
        return loss

    def on_validation_epoch_end(self):
        results = self.metrics.compute()
        for key, val in results.items():
            self.log(f"val/{key}", val, prog_bar=True)
            print(f"[val] {key}: {val:.4f}")
        self.metrics.reset()

    def configure_optimizers(self):
        optimizer = self.optimizer(self.parameters(), lr=self.hparams.lr)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", patience=3, factor=0.5
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "monitor": "val/loss",  # important for ReduceLROnPlateau
                "interval": "epoch",
                "frequency": 1,
            },
        }
