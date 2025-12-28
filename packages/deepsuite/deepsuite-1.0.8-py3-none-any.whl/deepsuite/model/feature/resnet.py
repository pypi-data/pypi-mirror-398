"""Resnet module."""

import torch
from torch import nn

from deepsuite.layers.bottleneck import Bottleneck
from deepsuite.model.backend_adapter import BackboneAdapter


class ResNetBackbone(BackboneAdapter):
    model_parameters = {
        "resnet18": ([64, 128, 256, 512], [2, 2, 2, 2], 1, False),
        "resnet34": ([64, 128, 256, 512], [3, 4, 6, 3], 1, False),
        "resnet50": ([64, 128, 256, 512], [3, 4, 6, 3], 4, True),
        "resnet101": ([64, 128, 256, 512], [3, 4, 23, 3], 4, True),
        "resnet152": ([64, 128, 256, 512], [3, 8, 36, 3], 4, True),
    }

    def __init__(self, resnet_variant: str, in_channels: int, stage_indices=(3, 6, 11)) -> None:
        assert (
            resnet_variant in self.model_parameters
        ), f"{resnet_variant} not in {self.model_parameters.keys()}"

        super().__init__()
        self.set_stage_indices(stage_indices)

        self.channels_list, self.repeatition_list, self.expansion, self.is_bottleneck = (
            self.model_parameters[resnet_variant]
        )

        self.conv1 = nn.Conv2d(
            in_channels=in_channels, out_channels=64, kernel_size=7, stride=2, padding=3, bias=False
        )
        self.batchnorm1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()

        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.block1 = self._make_blocks(
            64,
            self.channels_list[0],
            self.repeatition_list[0],
            self.expansion,
            self.is_Bottleneck,
            stride=1,
        )

        self.block2 = self._make_blocks(
            self.channels_list[0] * self.expansion,
            self.channels_list[1],
            self.repeatition_list[1],
            self.expansion,
            self.is_bottleneck,
            stride=2,
        )
        self.block3 = self._make_blocks(
            self.channels_list[1] * self.expansion,
            self.channels_list[2],
            self.repeatition_list[2],
            self.expansion,
            self.is_bottleneck,
            stride=2,
        )
        self.block4 = self._make_blocks(
            self.channels_list[2] * self.expansion,
            self.channels_list[3],
            self.repeatition_list[3],
            self.expansion,
            self.is_bottleneck,
            stride=2,
        )

    def forward(self, x: torch.Tensor, return_stages=False, return_pooled=True):
        x = self.relu(self.batchnorm1(self.conv1(x)))
        x = self.maxpool(x)

        features = []

        x = self.block1(x)
        if return_stages and 0 in self.stage_indices:
            features.append(x)

        x = self.block2(x)
        if return_stages and 1 in self.stage_indices:
            features.append(x)

        x = self.block3(x)
        if return_stages and 2 in self.stage_indices:
            features.append(x)

        x = self.block4(x)
        if return_stages and 3 in self.stage_indices:
            features.append(x)

        return features if return_stages else x

    def _make_blocks(
        self, in_channels, intermediate_channels, num_repeat, expansion, is_bottleneck, stride
    ):
        """Args:
            in_channels : #channels of the Bottleneck input
            intermediate_channels : #channels of the 3x3 in the Bottleneck
            num_repeat : #Bottlenecks in the block
            expansion : factor by which intermediate_channels are multiplied to create the output channels
            is_bottleneck : status if Bottleneck in required
            stride : stride to be used in the first Bottleneck conv 3x3.

        Attributes:
            Sequence of Bottleneck layers

        """
        layers = []

        layers.append(
            Bottleneck(in_channels, intermediate_channels, expansion, is_bottleneck, stride=stride)
        )
        for _ in range(1, num_repeat):
            layers.append(
                Bottleneck(
                    intermediate_channels * expansion,
                    intermediate_channels,
                    expansion,
                    is_bottleneck,
                    stride=1,
                )
            )

        return nn.Sequential(*layers)
