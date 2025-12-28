"""Classification Loss.

This module provides the classification loss for training classification tasks.

Example:
    .. code-block:: python

        import torch
        from deepsuite.loss import ClassificationLoss

        criterion = ClassificationLoss()
        preds = torch.randn(2, 10)
        batch = {"cls": torch.randint(0, 10, (2,))}
        loss, loss_items = criterion(preds, batch)
        print(loss, loss_items)

References:
    https://pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html
"""

from collections.abc import Mapping

import torch
from torch.nn import functional as F


class ClassificationLoss:
    """Criterion class for computing training losses for classification tasks."""

    def __call__(
        self,
        preds: torch.Tensor | list[torch.Tensor] | tuple[torch.Tensor, ...],
        batch: Mapping[str, torch.Tensor],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute the classification loss between predictions and true labels.

        Args:
            preds (torch.Tensor): The predicted logits or probabilities.
            batch (Mapping[str, torch.Tensor]): Dict containing the true labels under key "cls".

        Returns:
            tuple[Tensor, Tensor]: Loss and detached loss items.
        """
        if isinstance(preds, (list, tuple)):
            preds = preds[1] if len(preds) > 1 else preds[0]
        loss = F.cross_entropy(preds, batch["cls"], reduction="mean")
        loss_items = loss.detach()
        return loss, loss_items
