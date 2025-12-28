"""Bottleneck module."""

import torch
from torch import nn


class Bottleneck(nn.Module):
    def __init__(
        self,
        in_channels: int,
        intermediate_channels: int,
        expansion: int,
        is_bottleneck: bool,
        stride: int,
    ) -> None:
        """Creates a Bottleneck with conv 1x1->3x3->1x1 layers.

        Note:
          1. Addition of feature maps occur at just before the final ReLU with the input feature maps
          2. if input size is different from output, select projected mapping or else identity mapping.
          3. if is_Bottleneck=False (3x3->3x3) are used else (1x1->3x3->1x1). Bottleneck is required for resnet-50/101/152
        Args:
            in_channels (int) : input channels to the Bottleneck
            intermediate_channels (int) : number of channels to 3x3 conv
            expansion (int) : factor by which the input #channels are increased
            stride (int) : stride applied in the 3x3 conv. 2 for first Bottleneck of the block and 1 for remaining

        Attributes:
            Layer consisting of conv->batchnorm->relu

        """
        super().__init__()

        self.expansion = expansion
        self.in_channels = in_channels
        self.intermediate_channels = intermediate_channels
        self.is_bottleneck = is_bottleneck

        # i.e. if dim(x) == dim(F) => Identity function
        if self.in_channels == self.intermediate_channels * self.expansion:
            self.identity = True
        else:
            self.identity = False
            projection_layer = []
            projection_layer.append(
                nn.Conv2d(
                    in_channels=self.in_channels,
                    out_channels=self.intermediate_channels * self.expansion,
                    kernel_size=1,
                    stride=stride,
                    padding=0,
                    bias=False,
                )
            )
            self.projection = nn.Sequential(
                *projection_layer, nn.BatchNorm2d(int(self.intermediate_channels * self.expansion))
            )

        # commonly used relu
        self.relu = nn.ReLU()

        # is_Bottleneck = True for all ResNet 50+
        if self.is_bottleneck:
            # bottleneck
            # 1x1
            self.conv1_1x1 = nn.Conv2d(
                in_channels=self.in_channels,
                out_channels=self.intermediate_channels,
                kernel_size=1,
                stride=1,
                padding=0,
                bias=False,
            )
            self.batchnorm1 = nn.BatchNorm2d(self.intermediate_channels)

            # 3x3
            self.conv2_3x3 = nn.Conv2d(
                in_channels=self.intermediate_channels,
                out_channels=self.intermediate_channels,
                kernel_size=3,
                stride=stride,
                padding=1,
                bias=False,
            )
            self.batchnorm2 = nn.BatchNorm2d(self.intermediate_channels)

            # 1x1
            self.conv3_1x1 = nn.Conv2d(
                in_channels=self.intermediate_channels,
                out_channels=self.intermediate_channels * self.expansion,
                kernel_size=1,
                stride=1,
                padding=0,
                bias=False,
            )
            self.batchnorm3 = nn.BatchNorm2d(self.intermediate_channels * self.expansion)

        else:
            # basicblock
            # 3x3
            self.conv1_3x3 = nn.Conv2d(
                in_channels=self.in_channels,
                out_channels=self.intermediate_channels,
                kernel_size=3,
                stride=stride,
                padding=1,
                bias=False,
            )
            self.batchnorm1 = nn.BatchNorm2d(self.intermediate_channels)

            # 3x3
            self.conv2_3x3 = nn.Conv2d(
                in_channels=self.intermediate_channels,
                out_channels=self.intermediate_channels,
                kernel_size=3,
                stride=1,
                padding=1,
                bias=False,
            )
            self.batchnorm2 = nn.BatchNorm2d(self.intermediate_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # input stored to be added before the final relu
        in_x = x

        if self.is_bottleneck:
            # conv1x1->BN->relu
            x = self.relu(self.batchnorm1(self.conv1_1x1(x)))

            # conv3x3->BN->relu
            x = self.relu(self.batchnorm2(self.conv2_3x3(x)))

            # conv1x1->BN
            x = self.batchnorm3(self.conv3_1x1(x))

        else:
            # conv3x3->BN->relu
            x = self.relu(self.batchnorm1(self.conv1_3x3(x)))

            # conv3x3->BN
            x = self.batchnorm2(self.conv2_3x3(x))

        # identity or projected mapping
        if self.identity:
            x += in_x
        else:
            x += self.projection(in_x)

        # final relu
        return self.relu(x)
