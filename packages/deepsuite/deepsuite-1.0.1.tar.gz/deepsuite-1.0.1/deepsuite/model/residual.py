"""Residual module."""

import torch
from torch import nn

from deepsuite.model.conv import ConvBlock, SEBlock


class InverseResidualBlock(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        expansion_factor: int = 6,
        stride: int = 1,
        squeeze_exitation: bool = False,
        activation=None,
    ) -> None:
        """Constructs a inverse residual block with depthwise seperable convolution.

        Args:
            in_channels (int): input channels
            out_channels (int): output channels
            expansion_factor (int, optional): Calculating the input & output channel for depthwise convolution by multiplying the expansion factor with input channels. Defaults to 6.
            stride (int, optional): stride paramemeter for depthwise convolution. Defaults to 1.
        """
        super().__init__()

        self.squeeze_exitation = squeeze_exitation

        hidden_channels = in_channels * expansion_factor
        self.residual = in_channels == out_channels and stride == 1

        self.activation = activation if activation else nn.Hardswish()

        self.conv1 = (
            ConvBlock(in_channels, hidden_channels, (1, 1), activation=self.activation)
            if in_channels != hidden_channels
            else nn.Identity()
        )

        self.depthwise_conv = ConvBlock(
            hidden_channels,
            hidden_channels,
            (kernel_size, kernel_size),
            stride=stride,
            padding=kernel_size // 2,
            groups=hidden_channels,
            activation=self.activation,
        )
        if self.squeeze_exitation:
            self.se = SEBlock(hidden_channels)

        self.conv2 = ConvBlock(hidden_channels, out_channels, (1, 1), bias=False)
        self.norm = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        """Perform forward pass."""
        identity = x

        x = self.conv1(x)
        x = self.depthwise_conv(x)

        if self.squeeze_exitation:
            x = self.se(x)

        x = self.conv2(x)
        x = self.norm(x)

        if self.residual:
            x = torch.add(x, identity)

        return x
