"""Focal module."""

r"""This module contains the FocalLoss class which is a wrapper around the binary cross entropy loss function.

..math::
    loss = -\alpha_{t} (1 - p_{t})^{\\gamma} \\log(p_{t})

Example:
    >>> import torch
    >>> from deepsuite.loss import FocalLoss
    >>> criterion = FocalLoss()
    >>> preds = torch.randn(2, 1)
    >>> labels = torch.randint(0, 2, (2, 1))
    >>> loss = criterion(preds, labels)
    >>> loss
    tensor(0.0000)
    >>> loss_items
    tensor(0.0000)

Attributes:
    FocalLoss: The class for computing the Focal Loss.

Methods:
    forward: Compute the Focal Loss between predictions and true labels.

References:
    https://arxiv.org/abs/1708.02002

"""


from typing import cast

from loguru import logger
import torch
from torch import Tensor, nn
from torch.nn import functional as f


class FocalLoss(nn.Module):
    def __init__(
        self,
        alpha: Tensor | float = 0.0,
        gamma: float = 1.5,
        reduction: str = "mean",
        ignore_index: int = -100,
        debug: bool = False,
    ) -> None:
        if reduction not in ("mean", "sum", "none"):
            raise ValueError('Reduction must be one of: "mean", "sum", "none".')

        if alpha is not None and not isinstance(alpha, Tensor | float):
            raise ValueError("alpha must be a Tensor or None.")

        if not isinstance(gamma, float | int) or gamma < 0:
            raise ValueError("gamma must be a non-negative float or int.")

        if not isinstance(ignore_index, int):
            raise ValueError("ignore_index must be an integer.")

        super().__init__()
        self._alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        self.ignore_index = ignore_index
        self.debug = debug
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def alpha(self):
        return (
            self._alpha.to(self._device)
            if isinstance(self._alpha, Tensor)
            else torch.tensor(self._alpha, device=self._device)
        )

    @alpha.setter
    def alpha(self, value) -> None:
        self._alpha = value

    def forward(self, pred: Tensor, label: Tensor) -> Tensor:
        """Calculate the Focal Loss between predictions and true labels.

        Args:
            pred (torch.Tensor): The predicted logits.
            label (torch.Tensor): The true labels.

        Returns:
            torch.Tensor: Computed Focal Loss.
        """
        loss = f.binary_cross_entropy_with_logits(pred, label, reduction="none")

        pred_prob = pred.sigmoid()  # prob from logits
        p_t = label * pred_prob + (1 - label) * (1 - pred_prob)
        modulating_factor = (1.0 - p_t) ** self.gamma
        loss *= modulating_factor

        if self.alpha > 0:
            alpha_factor = label * self.alpha + (1 - label) * (1 - self.alpha)
            loss *= alpha_factor

        return loss.mean(1).sum()


class BinaryFocalLoss(FocalLoss):
    """Compute the Focal Loss for binary classification.

    This implementation uses `binary_cross_entropy_with_logits` internally,
    and supports both logits and one-hot targets (0 or 1).

    Equation:
        loss = -alpha_t * (1 - p_t) ** gamma * log(p_t)

    References:
        https://arxiv.org/abs/1708.02002
    """

    def __init__(
        self, alpha: float = 0.25, gamma: float = 2.0, reduction: str = "mean", debug: bool = False
    ) -> None:
        """Initialize the BinaryFocalLoss class.

        Args:
            alpha (float): Weighting factor for the class. Defaults to 0.25.
            gamma (float): Focusing parameter. Defaults to 2.0.
            reduction (str): Specifies the reduction to apply to the output: 'mean', 'sum', or 'none'. Defaults to 'mean'.
        """
        super().__init__(alpha=alpha, gamma=gamma, reduction=reduction, debug=debug)

    def forward(self, x: Tensor, target: Tensor) -> Tensor:
        """Compute the Binary Focal Loss between predictions and true labels.

        Args:
            x (Tensor): The predicted logits.
            target (Tensor): The true labels (0 or 1).

        Returns:
            Tensor: Computed Binary Focal Loss.
        """
        # Compute binary cross entropy loss without reduction
        bce_loss = f.binary_cross_entropy_with_logits(x, target, reduction="none")

        # Apply sigmoid to get probabilities
        prob = torch.sigmoid(x)

        # Compute p_t: probability of the true class
        p_t = prob * target + (1 - prob) * (1 - target)

        # Compute alpha_t: weighting factor for the true class
        alpha_t = self.alpha * target + (1 - self.alpha) * (1 - target)

        # Compute the focal term: (1 - p_t) ** gamma
        focal_term = (1 - p_t) ** self.gamma

        # Compute the final loss
        loss = alpha_t * focal_term * bce_loss

        # Apply reduction
        if self.reduction == "mean":
            return cast("Tensor", loss.mean())

        if self.reduction == "sum":
            return cast("Tensor", loss.sum())

        return cast("Tensor", loss)


class MulticlassFocalLoss(FocalLoss):
    """Wraps focal loss around existing loss function.

    This class implements the Focal Loss as proposed in the paper "Focal Loss for Dense Object Detection".

    Attributes:
        None

    Note:
        This implementation supports multi-class classification.
        For binary classification, consider using BinaryFocalLoss instead.
    """

    def __init__(
        self,
        alpha: Tensor | None = None,
        gamma: float = 1.5,
        reduction: str = "mean",
        ignore_index: int = -100,
        epsilon: float = 1e-8,
        debug: bool = False,
    ) -> None:
        """Initialize the FocalLoss class.

        Args:
            alpha (Tensor, optional): Weights for each class. Defaults to None.
            gamma (float, optional): A constant, as described in the paper.
                Defaults to 1.5.
            reduction (str, optional): 'mean', 'sum' or 'none'.
                Defaults to 'mean'.
            ignore_index (int, optional): class label to ignore.
                Defaults to -100.
        """
        super().__init__(
            alpha=alpha if alpha else 0.0,
            gamma=gamma,
            reduction=reduction,
            ignore_index=ignore_index,
            debug=debug,
        )

        self.epsilon = epsilon

    def __repr__(self) -> str:
        arg_keys = ["alpha", "gamma", "ignore_index", "reduction"]
        arg_vals = [self.__dict__[k] for k in arg_keys]
        arg_strs = [f"{k}={v!r}" for k, v in zip(arg_keys, arg_vals, strict=False)]
        arg_str = ", ".join(arg_strs)
        return f"{type(self).__name__}({arg_str})"

    def forward(self, pred: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
        """Calculate the Focal Loss between predictions and true labels.

        Args:
            pred (torch.Tensor): The predicted logits.
            label (torch.Tensor): The true labels.

        Returns:
            torch.Tensor: Computed Focal Loss.
        """
        pred_dim = pred.ndim
        if pred_dim > 2:
            # (N, C, d1, d2, ..., dK) --> (N * d1 * ... * dK, C)
            c = pred.shape[1]
            pred = pred.permute(0, *range(2, pred_dim), 1).reshape(-1, c)
            # (N, d1, d2, ..., dK) --> (N * d1 * ... * dK,)
            label = label.view(-1)

        unignored_mask = label != self.ignore_index
        label = label[unignored_mask]
        if len(label) == 0:
            return torch.tensor(0.0, dtype=pred.dtype, device=pred.device)
        pred = pred[unignored_mask]

        # compute weighted cross entropy term: -alpha * log(pt)
        log_p = f.log_softmax(pred, dim=-1)

        # get true class column from each row
        # in extremfällen kann es hier zu -inf kommen, das muss abgesichert werden
        log_pt = torch.gather(log_p, dim=1, index=label.unsqueeze(1)).squeeze(1)

        # compute focal term: (1 - pt)^gamma
        pt = torch.clamp(log_pt.exp(), min=self.epsilon, max=1.0 - self.epsilon)
        focal_term = (1 - pt) ** self.gamma

        # the full loss: -alpha * ((1 - pt)^gamma) * log(pt)
        loss = focal_term * (-log_pt)

        if self.reduction == "mean":
            loss = loss.mean()

        elif self.reduction == "sum":
            loss = loss.sum()

        if self.debug:
            logger.debug(
                f"pt mean: {pt.mean().item():.4f}, focal term mean: {focal_term.mean().item():.4f}"
            )

        return cast("torch.Tensor", loss)
