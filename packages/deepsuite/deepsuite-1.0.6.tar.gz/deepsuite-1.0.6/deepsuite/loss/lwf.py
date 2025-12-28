"""Learning without Forgetting (LwF) loss wrapper."""

from collections.abc import Callable
from typing import cast

import torch
import torch.nn.functional as f

from deepsuite.loss.distill import Distill


# learning without forgetting
class LwF(torch.nn.Module):
    def __init__(
        self,
        t: float = 2.0,
        alpha: float = 0.5,
        loss: type[torch.nn.Module] = Distill,
        new_class_loss: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] = f.cross_entropy,
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.loss = loss(t)  # <- jetzt instanziieren
        self.new_class_loss = new_class_loss

    def forward(
        self, old_logits: torch.Tensor, new_logits: torch.Tensor, targets: torch.Tensor
    ) -> torch.Tensor:
        ce_loss = self.new_class_loss(new_logits, targets)
        distill_loss = self.loss(new_logits, old_logits)
        return cast(
            "torch.Tensor",
            (self.alpha * distill_loss + (1 - self.alpha) * ce_loss).to(new_logits.dtype),
        )
