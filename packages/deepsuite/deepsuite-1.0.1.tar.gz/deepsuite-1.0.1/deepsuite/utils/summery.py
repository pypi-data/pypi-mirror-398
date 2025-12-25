"""Summery module."""

import torch
from torch import nn
from torchsummary import summary


def print_model_summary(model: nn.Module, input_size=(1, 3, 416, 416)):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    summary(model, input_size=input_size[1:])
