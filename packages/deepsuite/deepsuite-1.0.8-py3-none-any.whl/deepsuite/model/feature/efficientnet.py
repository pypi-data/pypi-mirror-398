"""Efficientnet module."""

from collections.abc import Sequence
import math

import torch
from torch import nn

from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.conv import BaseConv2dBlock, SEBlock


# MBConv Block
class MBConvBlock(nn.Module):
    """Mobile Inverted Residual Bottleneck Block.

    This block is used in EfficientNet and consists of an expansion phase, depthwise convolution,
    squeeze and excitation, and output phase. Nutzt BaseConv2dBlock für vereinheitlichte Conv-Operationen.

    Attributes:
        use_residual (bool): Whether to use residual connections.
        block (nn.Sequential): The sequential block containing the layers.
    """

    def __init__(
        self, in_channels, out_channels, expand_ratio, kernel_size, stride, se_ratio
    ) -> None:
        """Initialize the MBConvBlock.

        Args:
            in_channels (int): Number of input channels.
            out_channels (int): Number of output channels.
            expand_ratio (float): Expansion ratio for the hidden dimension.
            kernel_size (int): Size of the convolutional kernel.
            stride (int): Stride for the convolution.
            se_ratio (float): Squeeze and excitation ratio.
        """
        super().__init__()
        self.stride = stride
        hidden_dim = in_channels * expand_ratio
        self.use_residual = self.stride == 1 and in_channels == out_channels

        layers = []

        # Expansion phase (nur wenn expand_ratio != 1)
        if expand_ratio != 1:
            layers.append(
                BaseConv2dBlock(
                    in_channels=in_channels,
                    out_channels=hidden_dim,
                    kernel_size=1,
                    stride=1,
                    padding=0,
                    bias=False,
                    use_bn=True,
                    activation=nn.SiLU,
                )
            )

        # Depthwise convolution phase
        layers.append(
            BaseConv2dBlock(
                in_channels=hidden_dim,
                out_channels=hidden_dim,
                kernel_size=kernel_size,
                stride=stride,
                padding=kernel_size // 2,
                groups=hidden_dim,  # Depthwise
                bias=False,
                use_bn=True,
                activation=nn.SiLU,
            )
        )

        # Squeeze and Excitation phase
        if se_ratio is not None:
            layers.append(SEBlock(hidden_dim, reduction=int(1 / se_ratio)))

        # Output phase (Pointwise convolution ohne Aktivierung)
        layers.append(
            BaseConv2dBlock(
                in_channels=hidden_dim,
                out_channels=out_channels,
                kernel_size=1,
                stride=1,
                padding=0,
                bias=False,
                use_bn=True,
                activation=None,  # Keine Aktivierung am Ende
            )
        )

        self.block = nn.Sequential(*layers)

    def forward(self, x):
        """Forward pass through the MBConvBlock.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        if self.use_residual:
            return x + self.block(x)
        return self.block(x)


# EfficientNet als Backbone (Feature Extractor)
class EfficientNetBackbone(BackboneAdapter):
    """EfficientNet model for image classification.

    This class implements the EfficientNet architecture with configurable parameters.

    Attributes:
        image_size (tuple): The input image size.
        stem (nn.Sequential): The stem layers.
        blocks (nn.Sequential): The MBConv blocks.
        head (nn.Sequential): The head layers.
        avgpool (nn.AdaptiveAvgPool2d): The adaptive average pooling layer.
        dropout (nn.Dropout): The dropout layer.
        stage_indices (tuple): stage information
    """

    def __init__(
        self,
        resolution_coefficient: float,
        width_coefficient: float,
        depth_coefficient: float,
        input_channels: int = 3,
        dropout_rate: float = 0.2,
        stage_indices: Sequence[int] = (3, 4, 5),
        version: str = "b0",
    ) -> None:
        """Initialize the EfficientNet model.

        Args:
            resolution_coefficient (float): Coefficient for scaling the input resolution.
            width_coefficient (float): Coefficient for scaling the width (number of channels).
            depth_coefficient (float): Coefficient for scaling the depth (number of layers).
            input_channels (int): Number of input channels. Default is 3.
            dropout_rate (float): Dropout rate. Default is 0.2.

        stage_indices (tuple): stage information
        """
        super().__init__()
        self.set_stage_indices(stage_indices)

        # Calculate the dynamic image size based on the resolution_coefficient
        self.image_size = self.calculate_image_size(resolution_coefficient)

        self.block_args = self.get_block_args(version)

        # Stem
        out_channels = self.round_filters(32, width_coefficient)
        self.stem = nn.Sequential(
            BaseConv2dBlock(
                in_channels=input_channels,
                out_channels=out_channels,
                kernel_size=3,
                stride=2,
                padding=1,
                bias=False,
                use_bn=True,
                activation=nn.SiLU,
            )
        )
        in_channels = out_channels

        # Blocks
        self.blocks = nn.Sequential()
        for idx, (expand_ratio, channels, repeats, kernel_size, stride, se_ratio) in enumerate(
            self.block_args
        ):
            out_channels = self.round_filters(channels, width_coefficient)
            repeats = self.round_repeats(repeats, depth_coefficient)
            for i in range(repeats):
                self.blocks.add_module(
                    f"mbconv{idx + 1}_block{i + 1}",
                    MBConvBlock(
                        in_channels,
                        out_channels,
                        expand_ratio,
                        kernel_size,
                        stride if i == 0 else 1,
                        se_ratio,
                    ),
                )
                in_channels = out_channels

        # Head
        out_channels = self.round_filters(1280, width_coefficient)
        self.head = nn.Sequential(
            BaseConv2dBlock(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=1,
                stride=1,
                padding=0,
                bias=False,
                use_bn=True,
                activation=nn.SiLU,
            )
        )

        # Final linear layer
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(dropout_rate)

        self.out_channels = out_channels

    def forward(
        self, x: torch.Tensor, return_stages: bool = False, return_pooled: bool = True
    ) -> torch.Tensor:
        """Forward pass through the EfficientNet model.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x = self.stem(x)

        features = []
        for i, (_, block) in enumerate(self.blocks.named_children()):
            x = block(x)
            if return_stages and i in self.stage_indices:
                features.append(x)

        x = self.head(x)

        if return_pooled:
            return x

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)

        return features if return_stages else x

    def _round_filters(self, filters, width_coefficient, divisor=8):
        filters *= width_coefficient
        new_filters = max(divisor, int(filters + divisor / 2) // divisor * divisor)
        if new_filters < 0.9 * filters:
            new_filters += divisor
        return int(new_filters)

    def _round_repeats(self, repeats, depth_coefficient):
        return math.ceil(repeats * depth_coefficient)

    def get_block_args(self, version: str = "b0") -> list[tuple[int, int, int, int, int, float]]:
        base_blockargs = (
            (1, 16, 1, 3, 1, 0.25),
            (6, 24, 2, 3, 2, 0.25),
            (6, 40, 2, 5, 2, 0.25),
            (6, 80, 3, 3, 2, 0.25),
            (6, 112, 3, 5, 1, 0.25),
            (6, 192, 4, 5, 2, 0.25),
            (6, 320, 1, 3, 1, 0.25),
        )

        model_scales = {
            "b0": (1.0, 1.0),
            "b1": (1.0, 1.1),
            "b2": (1.1, 1.2),
            "b3": (1.2, 1.4),
            "b4": (1.4, 1.8),
            "b5": (1.6, 2.2),
            "b6": (1.8, 2.6),
            "b7": (2.0, 3.1),
        }

        if version not in model_scales:
            raise ValueError(f"Unknown EfficientNet version '{version}'")

        width_coef, depth_coef = model_scales.get(version, "b0")
        args = []

        for expand_ratio, channels, repeats, kernel_size, stride, se_ratio in base_blockargs:
            out_channels = self._round_filters(channels, width_coef)
            num_repeats = self._round_repeats(repeats, depth_coef)
            args.append((expand_ratio, out_channels, num_repeats, kernel_size, stride, se_ratio))

        return args
