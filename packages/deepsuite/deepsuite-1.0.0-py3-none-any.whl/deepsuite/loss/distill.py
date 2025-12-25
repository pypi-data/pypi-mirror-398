"""Distill module."""

import torch
import torch.nn.functional as f


class Distill(torch.nn.Module):
    def __init__(self, t: float = 2.0, reduction: str = "batchmean") -> None:
        """KL-Distillation Loss nach Hinton et al.

        Args:
            t: Temperatur (default=2.0)
            reduction: Reduktionstyp für KL-Divergenz
        """
        super().__init__()
        self.temperature = t
        self.reduction = reduction

    def forward(self, student_logits, teacher_logits):
        return f.kl_div(
            f.log_softmax(student_logits / self.temperature, dim=1),
            f.softmax(teacher_logits / self.temperature, dim=1),
            reduction=self.reduction,
        ) * pow(self.temperature, 2)
