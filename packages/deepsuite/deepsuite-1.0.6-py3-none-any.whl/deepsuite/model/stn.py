from __future__ import annotations

import math

import torch
from torch import nn
import torch.nn.functional as F


class RotationOnlySTN(nn.Module):
    def __init__(self, in_channels: int, max_deg: float = 15.0) -> None:
        super().__init__()
        self.max_rad = math.radians(max_deg)
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_channels, 128),
            nn.ReLU(True),
            nn.Linear(128, 1),
        )
        # start near 0 rotation
        nn.init.zeros_(self.fc[-1].weight)
        nn.init.zeros_(self.fc[-1].bias)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _B, _C, _H, _W = x.shape
        angle = torch.tanh(self.fc(x)) * self.max_rad  # (B,1)
        cos, sin = torch.cos(angle), torch.sin(angle)
        zeros = torch.zeros_like(cos)
        theta = torch.cat(
            [torch.cat([cos, -sin, zeros], dim=1), torch.cat([sin, cos, zeros], dim=1)], dim=1
        ).view(-1, 2, 3)
        grid = F.affine_grid(theta, size=x.size(), align_corners=False)
        x_trans = F.grid_sample(x, grid, align_corners=False)
        return x_trans, angle.squeeze(1)


class AffineSTN(nn.Module):
    """Full affine STN (rotation/scale/shear/translation). Useful for arbitrarily rotated tattoos."""

    def __init__(self, in_channels: int) -> None:
        super().__init__()
        self.reg = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_channels, 128),
            nn.ReLU(True),
            nn.Linear(128, 6),
        )
        # initialize to identity
        nn.init.zeros_(self.reg[-1].weight)
        nn.init.constant_(self.reg[-1].bias, 0.0)
        with torch.no_grad():
            self.reg[-1].bias.copy_(torch.tensor([1, 0, 0, 0, 1, 0], dtype=torch.float))

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        theta = self.reg(x).view(-1, 2, 3)
        grid = F.affine_grid(theta, size=x.size(), align_corners=False)
        x_trans = F.grid_sample(x, grid, align_corners=False)
        return x_trans, theta
