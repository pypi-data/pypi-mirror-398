"""Box module."""

import torch
from torch import nn


class GeneralBBoxHead(nn.Module):
    def __init__(
        self, in_channels: int, out_channels: int = 4, relu_dims: tuple[int] | None = (2, 3)
    ):
        assert all(0 <= i < out_channels for i in relu_dims), "ReLU channel index out of bounds"
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.relu_dims = relu_dims  # Welche Kanäle ReLU brauchen

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv(x)
        if self.relu_dims:
            out[:, list(self.relu_dims)] = torch.relu(out[:, list(self.relu_dims)])
        return out


class RotationFreeBBoxHead(GeneralBBoxHead):
    def __init__(self, in_channels: int, relu_dims: tuple[int] | None = (2, 3)):
        super().__init__(
            in_channels=in_channels, out_channels=4, relu_dims=relu_dims
        )  # 4 = (Cx, Cy, W, H) für eine ankerlose Box pro Feature-Map-Zelle


# Bounding Box Head (Regressor)
class BBoxHead(GeneralBBoxHead):
    def __init__(self, in_channels: int, relu_dims: tuple[int] | None = (2, 3)):
        super().__init__(
            in_channels=in_channels, out_channels=5, relu_dims=relu_dims
        )  # 5 = (Cx, Cy, W, H, θ) für eine ankerlose Box pro Feature-Map-Zelle
