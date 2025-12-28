"""Summery module."""

import torch
from torch import nn
from torchsummary import summary


def print_model_summary(
    model: nn.Module,
    input_size: tuple[int, int, int, int] = (1, 3, 416, 416),
) -> None:
    """Print a concise model summary using ``torchsummary``.

    Args:
        model: The model to summarize.
        input_size: Full input size; channel-first. Batch dimension is ignored.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    summary(model, input_size=input_size[1:])
