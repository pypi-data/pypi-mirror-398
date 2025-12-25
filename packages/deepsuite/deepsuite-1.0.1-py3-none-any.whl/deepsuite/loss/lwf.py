"""Lwf module."""

import torch
import torch.nn.functional as f

from deepsuite.loss.distill import Distill


# learning without forgetting
class LwF(torch.nn.Module):
    def __init__(
        self,
        t=2,
        alpha=0.5,
        loss: torch.nn.Module = Distill,
        new_class_loss: torch.nn.Module = f.cross_entropy,
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.loss = loss(t)  # <- jetzt instanziieren
        self.new_class_loss = new_class_loss

    def forward(self, old_logits, new_logits, targets):
        ce_loss = self.new_class_loss(new_logits, targets)

        return self.alpha * self.loss(new_logits, old_logits) + (1 - self.alpha) * ce_loss
