"""Bounding box loss functions for object detection.

This module provides various loss functions for bounding box regression, including
IoU-based losses and Distribution Focal Loss (DFL).

Example:
    .. code-block:: python

        import torch
        from deepsuite.loss.bbox import BboxLoss

        criterion = BboxLoss(reg_max=16)
        iou_loss, dfl_loss = criterion(
            pred_dist,
            pred_bboxes,
            anchor_points,
            target_bboxes,
            target_scores,
            target_scores_sum,
            fg_mask,
        )

Classes:
    BboxLoss: Base loss combining IoU and DFL for box regression.
    RotatedBboxLoss: Loss for rotated bounding boxes.
    AnkerloserBboxLoss: Anchor-free loss with optional logarithmic scaling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import nn
import torch.nn.functional as F  # noqa: N812

from deepsuite.loss.dfl import DFLoss
from deepsuite.metric.bbox_iou import bbox_iou, rotated_bbox_iou
from deepsuite.metric.probiou import probiou
from deepsuite.utils.bbox import bbox2dist
from deepsuite.utils.xy import xywh2xyxy

if TYPE_CHECKING:
    from torch import Tensor


class BboxLoss(nn.Module):
    """IoU and Distribution Focal Loss for bounding box regression.

    Computes Intersection over Union (IoU) loss and optional Distribution Focal
    Loss (DFL) for training detection models.

    Attributes:
        dfl_loss: Instance of :class:`DFLoss` when `reg_max` > 1, otherwise ``None``.

    Example:
        .. code-block:: python

            bbox_loss = BboxLoss(reg_max=16)
            iou_loss, dfl_loss = bbox_loss(
                pred_dist,
                pred_bboxes,
                anchor_points,
                target_bboxes,
                target_scores,
                target_scores_sum,
                fg_mask,
            )
    """

    def __init__(self, reg_max: int = 16) -> None:
        """Initialize the loss.

        Args:
            reg_max: Maximum regularization (number of DFL bins).
        """
        super().__init__()
        self.dfl_loss = DFLoss(reg_max) if reg_max > 1 else None

    def forward(
        self,
        pred_dist: Tensor,
        pred_bboxes: Tensor,
        anchor_points: Tensor,
        target_bboxes: Tensor,
        target_scores: Tensor,
        target_scores_sum: float,
        fg_mask: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Compute IoU loss and DFL loss.

        Args:
            pred_dist: Predicted distances (batch, anchors, reg_max).
            pred_bboxes: Predicted boxes (batch, anchors, 4).
            anchor_points: Anchor points (anchors, 2).
            target_bboxes: Target boxes (batch, targets, 4).
            target_scores: Target scores (batch, targets, num_classes).
            target_scores_sum: Sum of target scores for normalization.
            fg_mask: Foreground mask (batch, anchors).

        Returns:
            Tuple of scalar tensors: (IoU loss, DFL loss).
        """
        if fg_mask.sum() == 0:
            return torch.tensor(0.0, device=pred_dist.device), torch.tensor(
                0.0, device=pred_dist.device
            )

        weight = target_scores.sum(-1)[fg_mask].unsqueeze(-1)
        iou = bbox_iou(pred_bboxes[fg_mask], target_bboxes[fg_mask], xywh=False, CIoU=True)
        loss_iou = ((1.0 - iou) * weight).sum() / max(target_scores_sum, 1e-6)

        # DFL loss
        if self.dfl_loss:
            target_ltrb = bbox2dist(anchor_points, target_bboxes, self.dfl_loss.reg_max - 1)
            loss_dfl = (
                self.dfl_loss(
                    pred_dist[fg_mask].view(-1, self.dfl_loss.reg_max), target_ltrb[fg_mask]
                )
                * weight
            )
            loss_dfl = loss_dfl.sum() / max(target_scores_sum, 1e-6)
        else:
            loss_dfl = torch.tensor(0.0, device=pred_dist.device)

        return loss_iou, loss_dfl


class RotatedBboxLoss(BboxLoss):
    """Loss function for rotated bounding boxes."""

    def forward(
        self,
        pred_dist: Tensor,
        pred_bboxes: Tensor,
        anchor_points: Tensor,
        target_bboxes: Tensor,
        target_scores: Tensor,
        target_scores_sum: float,
        fg_mask: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Compute the IoU loss and DFL loss for rotated bounding boxes."""
        if fg_mask.sum() == 0:
            return torch.tensor(0.0, device=pred_dist.device), torch.tensor(
                0.0, device=pred_dist.device
            )

        weight = target_scores.sum(-1)[fg_mask].unsqueeze(-1)
        iou = probiou(pred_bboxes[fg_mask], target_bboxes[fg_mask])
        loss_iou = ((1.0 - iou) * weight).sum() / max(target_scores_sum, 1e-6)

        # DFL loss
        if self.dfl_loss:
            target_ltrb = bbox2dist(
                anchor_points, xywh2xyxy(target_bboxes[..., :4]), self.dfl_loss.reg_max - 1
            )
            loss_dfl = (
                self.dfl_loss(
                    pred_dist[fg_mask].view(-1, self.dfl_loss.reg_max), target_ltrb[fg_mask]
                )
                * weight
            )
            loss_dfl = loss_dfl.sum() / max(target_scores_sum, 1e-6)
        else:
            loss_dfl = torch.tensor(0.0, device=pred_dist.device)

        return loss_iou, loss_dfl


class AnkerloserBboxLoss(nn.Module):
    """Anchor-free bounding box loss with optional logarithmic scaling."""

    def __init__(
        self, log_reg: bool = False, use_rotated_iou: bool = True, reduction: str = "mean"
    ) -> None:
        super().__init__()
        self.log_reg = log_reg
        self.use_rotated_iou = use_rotated_iou
        self.reduction = reduction

    def forward(
        self,
        bbox_pred: Tensor,
        target_bboxes: Tensor,
        weights: tuple[float, float, float] = (0.4, 0.2, 0.4),
    ) -> Tensor:
        """Compute the combined loss for anchor-free bounding box regression."""
        # weights is typed as a 3-tuple; normalization by length is unnecessary here.

        has_theta = bbox_pred.shape[-1] > 4
        use_rot_iou = self.use_rotated_iou and has_theta
        # If rotation IoU is requested but boxes have no angle, silently fall back.
        loss_theta: Tensor
        if not has_theta:
            loss_theta = torch.tensor(0.0, device=bbox_pred.device)
        else:
            # will be computed below in the dedicated block
            loss_theta = torch.tensor(0.0, device=bbox_pred.device)

        # Falls die Summe der Gewichte nicht 1.0 ist, normalisieren
        weight_sum = sum(weights)
        norm_weights = [float(w / weight_sum) for w in weights] if weight_sum != 1.0 else weights

        # 📌 **1. L1-Regressionsverlust für W, H & θ**
        if self.log_reg:
            loss_wh = F.smooth_l1_loss(
                torch.log1p(bbox_pred[..., 2:4]),
                torch.log1p(target_bboxes[..., 2:4]),
                reduction=self.reduction,
            )
        else:
            loss_wh = F.smooth_l1_loss(
                bbox_pred[..., 2:4], target_bboxes[..., 2:4], reduction=self.reduction
            )

        # 🔄 **L1-Verlust für die Rotation (θ)**
        if has_theta:  # rotation present
            loss_theta = F.smooth_l1_loss(
                bbox_pred[..., 4], target_bboxes[..., 4], reduction=self.reduction
            )

        # 📌 **2. IoU-Verlust für Rotation oder Standard-IoU**
        loss_iou = (
            1 - rotated_bbox_iou(bbox_pred, target_bboxes)
            if use_rot_iou
            else 1 - bbox_iou(bbox_pred, target_bboxes, xywh=True)
        )
        loss_iou = loss_iou.mean()

        # 📌 **3. Gesamtverlust mit normalisierten Gewichtungen**
        loss: Tensor = (
            norm_weights[0] * loss_wh + norm_weights[1] * loss_theta + norm_weights[2] * loss_iou
        )

        return loss
