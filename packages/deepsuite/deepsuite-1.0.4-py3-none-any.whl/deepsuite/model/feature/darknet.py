"""Darknet module."""

import torch
from torch import nn

from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.conv import ConvBlock


class CSPBlock(nn.Module):
    """A CSP (Cross-Stage-Partial) Block.

    This block is used in the CSPDarknet architecture and consists of several convolutional layers.

    Attributes:
        conv1 (ConvBlock): First convolutional block.
        conv2 (ConvBlock): Second convolutional block.
        blocks (nn.Sequential): Sequential block containing multiple convolutional layers.
        conv3 (ConvBlock): Third convolutional block.
    """

    def __init__(self, in_channels, out_channels, num_blocks) -> None:
        """Initialize the CSPBlock.

        Args:
            in_channels (int): Number of input channels.
            out_channels (int): Number of output channels.
            num_blocks (int): Number of convolutional blocks.
        """
        super().__init__()
        self.conv1 = ConvBlock(in_channels, out_channels // 2, kernel_size=1)
        self.conv2 = ConvBlock(in_channels, out_channels // 2, kernel_size=1)
        self.blocks = nn.Sequential(
            *[
                ConvBlock(out_channels // 2, out_channels // 2, kernel_size=3, padding=1)
                for _ in range(num_blocks)
            ]
        )
        self.conv3 = ConvBlock(out_channels, out_channels, kernel_size=1)

    def forward(self, x):
        """Forward pass through the CSPBlock.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x1 = self.conv1(x)
        x2 = self.conv2(x)
        x2 = self.blocks(x2)
        x = torch.cat([x1, x2], dim=1)
        return self.conv3(x)


class CSPDarknetBackbone(BackboneAdapter):
    def __init__(
        self,
        in_channels=3,
        channels_list=None,
        num_blocks_list=None,
        stage_indices=(2, 4, 6),  # CSPBlock-Schichten (nach Conv, CSP, Conv, CSP, ...)
    ):
        super().__init__()
        self.set_stage_indices(stage_indices)

        if channels_list is None:
            channels_list = [32, 64, 128, 256, 512, 1024]
        if num_blocks_list is None:
            num_blocks_list = [1, 2, 8, 8, 4]

        assert len(channels_list) == len(num_blocks_list) + 1, (
            "channels_list and num_blocks_list must be compatible."
        )

        self.layers = nn.ModuleList()
        in_ch = in_channels
        for out_ch, num_blocks in zip(channels_list, num_blocks_list):
            self.layers.append(
                ConvBlock(in_ch, out_ch, kernel_size=3, stride=2, padding=1)
            )  # index += 1
            self.layers.append(CSPBlock(out_ch, out_ch, num_blocks))  # index += 1
            in_ch = out_ch

    def forward(self, x, return_stages=False, return_pooled=False):
        features = []
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if return_stages and i in self.stage_indices:
                features.append(x)

        return features if return_stages else x

    @property
    def out_channels(self):
        return self._output_channels
