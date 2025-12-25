"""Classification Loss.
-------------------
This module contains the classification loss class for computing training losses for classification tasks.

Example:
>>> import torch
>>> from deepsuite.loss import ClassificationLoss
>>> criterion = ClassificationLoss()
>>> preds = torch.randn(2, 10)
>>> batch = {"cls": torch.randint(0, 10, (2,))}
>>> loss, loss_items = criterion(preds, batch)
>>> loss
tensor(2.4175)
>>> loss_items
tensor(2.4175)

Attributes:
ClassificationLoss: The class for computing classification losses.

Methods:
__call__: Compute the classification loss between predictions and true labels.

References:
https://pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html
"""

import torch
from torch.nn import functional as F


class ClassificationLoss:
    """Criterion class for computing training losses for classification tasks."""

    def __call__(self, preds: torch.Tensor, batch: dict) -> tuple:
        """Compute the classification loss between predictions and true labels.

        Args:
            preds (torch.Tensor): The predicted logits or probabilities.
            batch (dict): A dictionary containing the true labels under the key "cls".

        Returns:
            tuple: A tuple containing the classification loss and the detached loss items.
        """
        preds = preds[1] if isinstance(preds, list | tuple) else preds
        loss = F.cross_entropy(preds, batch["cls"], reduction="mean")
        loss_items = loss.detach()
        return loss, loss_items
