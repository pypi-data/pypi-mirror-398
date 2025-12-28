"""Varifocal Loss for quality-aware object detection.

This module implements Varifocal Loss (VFL) from the paper
"Varifocal Loss for Dense Object Detection" (Zhang et al., 2021).

Varifocal Loss combines classification loss with quality metrics corresponding
to the model's confidence. This enables focused training on high-quality
positive samples with high confidence probability.

References:
    Zhang, H., Wang, Y., Dayoub, F., & Sundaresan, N. (2021).
    Varifocal Loss for Dense Object Detection.
    https://arxiv.org/abs/2008.13367

Example:
    .. code-block:: python

        import torch
        from deepsuite.loss.varifocal import VarifocalLoss

        criterion = VarifocalLoss()

        # Predicted scores (logits) for the class
        pred_score = torch.randn(16, 80, requires_grad=True)  # 16 anchors, 80 classes

        # Target scores (continuous values between 0 and 1)
        gt_score = torch.rand(16, 80)

        # Class labels (binary: 0 or 1)
        label = (gt_score > 0.5).float()

        loss = criterion(pred_score, gt_score, label)
        print(f"Varifocal Loss: {loss.item()}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from torch import nn
import torch.nn.functional as F

from deepsuite.utils.autocast import autocast

if TYPE_CHECKING:
    import torch


class VarifocalLoss(nn.Module):
    """Varifocal Loss with quality-awareness for object detection.

    Varifocal Loss combines focus mechanisms with continuous quality scores.
    It weights each sample based on prediction confidence and target quality score,
    achieving focused training on high-quality positive samples.

    Unlike standard Focal Loss, this not only considers prediction probability
    but also a continuous quality score of the target dataset.

    Example:
        .. code-block:: python

            vfl = VarifocalLoss()

            # Batch of 32 samples with 80 classes
            pred_score = torch.randn(32, 80, requires_grad=True)
            gt_score = torch.rand(32, 80)  # Target quality scores
            label = (gt_score > 0.5).float()  # Binary labels

            loss = vfl(pred_score, gt_score, label)
            print(f("Loss: {loss.item()}"))
    """

    def __init__(self) -> None:
        """Initialize the Varifocal Loss class.

        No configurable parameters necessary.
        Hyperparameters alpha and gamma are fixed in the forward method.
        """
        super().__init__()

    def forward(
        self,
        pred_score: torch.Tensor,
        gt_score: torch.Tensor,
        label: torch.Tensor,
        alpha: float = 0.75,
        gamma: float = 2.0,
    ) -> torch.Tensor:
        """Compute Varifocal Loss.

        Loss is computed as weighted Binary Cross Entropy:
            loss = BCEWithLogits(pred_score, gt_score, weight=weight)

        where weight is defined as:
            weight = alpha * sigmoid(pred)^gamma * (1 - label) + gt_score * label

        This focuses training on:
            - Negative samples: Higher weight as model becomes more confident
            - Positive samples: Weighted by gt_score (quality metric)

        Args:
            pred_score: Predicted scores (logits) before sigmoid activation.
                       Shape: (batch_size, num_classes) or compatible batch form.
            gt_score: Target quality scores (continuous values between 0 and 1).
                     Shape: must be compatible with pred_score.
            label: Binary class labels (0 or 1) to distinguish positive/negative samples.
                  Shape: must be compatible with pred_score.
            alpha: Focus weighting factor for negative samples. Default: 0.75.
                   Higher values amplify focus on hard-to-classify negative samples.
            gamma: Focus exponent for prediction confidence. Default: 2.0.
                   Higher values amplify focus exponentially.

        Returns:
            torch.Tensor: Scalar loss (averaged over all samples and classes).

        Example:
            .. code-block:: python

                pred = torch.randn(8, 10)  # 8 samples, 10 classes
                gt = torch.rand(8, 10) * 0.5 + 0.25  # Scores between 0.25 and 0.75
                labels = torch.randint(0, 2, (8, 10)).float()

                vfl = VarifocalLoss()
                loss = vfl(pred, gt, labels, alpha=0.75, gamma=2.0)
                print(f"Loss: {loss.item()}")
        """
        # Compute focus weight based on prediction confidence and quality score
        # - Negative samples (label=0): Weight increases with sigmoid(pred)^gamma
        # - Positive samples (label=1): Weight is gt_score (quality metric)
        weight = alpha * pred_score.sigmoid().pow(gamma) * (1 - label) + gt_score * label

        # Compute Binary Cross Entropy Loss with autocast for numerical stability
        # Autocast disables half-precision (float16) for numerically stable computation
        with autocast(enable=False):
            loss = (
                (
                    F.binary_cross_entropy_with_logits(
                        pred_score.float(), gt_score.float(), reduction="none"
                    )
                    * weight
                )
                .mean(1)
                .sum()
            )
        return cast("torch.Tensor", loss)
