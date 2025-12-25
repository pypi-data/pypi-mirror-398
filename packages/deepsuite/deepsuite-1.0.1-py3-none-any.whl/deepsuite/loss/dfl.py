"""Distribution Focal Loss (DFL) for object detection models.

This module implements Distribution Focal Loss (DFL) from the paper
"Generalized Focal Loss for Dense Object Detection" (Li et al., 2020).

The DFL function interpolates between two adjacent bins based on the continuous
target value and computes the Cross-Entropy Loss with weighted interpolation.

References:
    Li, X., Wang, W., Wu, L., Chen, S., Hu, X., Li, J., Tang, Y., & Liu, S. (2020).
    Generalized Focal Loss: Learning to Locate Objects with Estimated Uncertainty.
    https://ieeexplore.ieee.org/document/9792391

Example:
    ```python
    import torch
    from deepsuite.loss.dfl import DFLoss

    criterion = DFLoss(reg_max=16)

    # Predicted distribution over 16 bins (batch=2)
    pred_dist = torch.randn(2, 16, requires_grad=True)

    # Continuous target values (can be between 0 and 16)
    target = torch.tensor([3.2, 7.8])

    loss = criterion(pred_dist, target)
    print(f"DFL Loss: {loss.item()}")
    ```
"""

from __future__ import annotations

from torch import Tensor, nn
import torch.nn.functional as F


class DFLoss(nn.Module):
    """Distribution Focal Loss for continuous regression targets.

    This class implements Distribution Focal Loss (DFL), which models continuous
    regression targets (e.g., bounding box offsets) as discrete distributions over
    multiple bins. It computes the Cross-Entropy Loss between two adjacent bins
    with interpolated weights.

    Attributes:
        reg_max: Maximum number of bins for discretization.
                 Target values are clamped to [0, reg_max-1].

    Example:
        ```python
        # Initialize DFL with 16 bins (standard for YOLOv8)
        dfl = DFLoss(reg_max=16)

        # Batch-wise predictions and targets
        pred_dist = torch.randn(32, 16)  # 32 samples, 16 bins
        target = torch.rand(32) * 15  # target values in [0, 15]

        loss = dfl(pred_dist, target)
        ```
    """

    def __init__(self, reg_max: int = 16) -> None:
        """Initialize Distribution Focal Loss.

        Args:
            reg_max: Maximum number of bins for distribution. Default is 16,
                     which is typical for bounding box regression.
        """
        super().__init__()
        self.reg_max = reg_max

    def forward(self, pred_dist: Tensor, target: Tensor) -> Tensor:
        """Compute Distribution Focal Loss.

        Discretizes continuous target values into two adjacent bin indices
        and computes the weighted Cross-Entropy Loss between them.

        Mathematical Formulation:
            - Clamp target to [0, reg_max - 1 - 0.01]
            - Identify left_bin (tl) and right_bin (tr = tl + 1)
            - Compute interpolation weights: wl = tr - target, wr = 1 - wl
            - Loss = wl * CE(pred, tl) + wr * CE(pred, tr)

        Args:
            pred_dist: Predicted distributions over bins. Shape (batch, reg_max).
                       Should be unnormalized logits (before softmax).
            target: Continuous target values. Shape (batch,).
                    Values should typically be in range [0, reg_max-1].

        Returns:
            Tensor: Averaged DFL loss per sample. Shape (batch, 1).

        Example:
            ```python
            pred = torch.randn(8, 16)
            target = torch.tensor([1.5, 3.2, 5.0, 7.8, 2.1, 4.3, 6.9, 8.5])
            loss = dfl_loss(pred, target)  # Shape (8, 1)
            mean_loss = loss.mean()
            ```
        """
        # Clamp target values to [0, reg_max - 1 - 0.01]
        # Small constant 0.01 prevents numerical issues at boundaries
        target = target.clamp_(0, self.reg_max - 1 - 0.01)

        # Identify two adjacent bin indices
        tl = target.long()  # Left (lower) bin index
        tr = tl + 1  # Right (upper) bin index

        # Compute interpolation weights based on closeness to each bin
        wl = tr - target  # Weight for left bin
        wr = 1 - wl  # Weight for right bin (= target - tl)

        # Compute Cross-Entropy Loss for both bins with respective target bins
        # Use this trick to compute two Cross-Entropy Losses:
        # - Cross-Entropy against tl with weight wl
        # - Cross-Entropy against tr with weight wr
        left_loss = F.cross_entropy(pred_dist, tl.view(-1), reduction="none").view(tl.shape)
        right_loss = F.cross_entropy(pred_dist, tr.view(-1), reduction="none").view(tl.shape)

        # Combine losses with interpolation weights
        return (left_loss * wl + right_loss * wr).mean(-1, keepdim=True)
