"""Mobile module."""

import torch
from torch import nn

from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.conv import ConvBlock, DepthwiseSeparableConv
from deepsuite.model.residual import InverseResidualBlock


class MobileNetV1Backbone(BackboneAdapter):
    def __init__(self, width_multiplier=1.0, stage_indices=(3, 6, 11)) -> None:
        super().__init__()
        self.set_stage_indices(stage_indices)

        def c(channels):
            return int(channels * width_multiplier)

        self.conv1 = nn.Conv2d(3, c(32), kernel_size=3, stride=2, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(c(32))
        self.relu = nn.ReLU(inplace=True)

        self.layers = nn.ModuleList(
            [
                DepthwiseSeparableConv(c(32), c(64), stride=1),  # 0
                DepthwiseSeparableConv(c(64), c(128), stride=2),  # 1
                DepthwiseSeparableConv(c(128), c(128), stride=1),  # 2
                DepthwiseSeparableConv(c(128), c(256), stride=2),  # 3
                DepthwiseSeparableConv(c(256), c(256), stride=1),  # 4
                DepthwiseSeparableConv(c(256), c(512), stride=2),  # 5
                *[DepthwiseSeparableConv(c(512), c(512), stride=1) for _ in range(5)],  # 6–10
                DepthwiseSeparableConv(c(512), c(1024), stride=2),  # 11
                DepthwiseSeparableConv(c(1024), c(1024), stride=1),  # 12
            ]
        )

    def forward(self, x, return_stages=False, return_pooled=True):
        x = self.relu(self.bn1(self.conv1(x)))
        features = []
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if return_stages and i in self.stage_indices:
                features.append(x)
        return features if return_stages else x


class MobileNetV2Backbone(BackboneAdapter):
    def __init__(self, stage_indices=(3, 6, 13), dropout=0.2) -> None:
        super().__init__()
        self.set_stage_indices(stage_indices)

        self.seq = nn.Sequential(ConvBlock(3, 32, (3, 3), stride=2, padding=1))

        config = (
            (32, 1, 16, 1, 1),
            (16, 6, 24, 2, 2),
            (24, 6, 32, 3, 2),
            (32, 6, 64, 4, 2),
            (64, 6, 96, 3, 1),
            (96, 6, 160, 3, 2),
            (160, 6, 320, 1, 1),
        )

        self.model = nn.ModuleList()
        for in_channels, expansion_factor, out_channels, repeat, stride in config:
            for i in range(repeat):
                self.model.append(
                    InverseResidualBlock(
                        in_channels=in_channels,
                        out_channels=out_channels,
                        expansion_factor=expansion_factor,
                        stride=stride if i == 0 else 1,
                        activation=nn.ReLU6(),
                    )
                )
                in_channels = out_channels

        self.conv1 = ConvBlock(in_channels, 1280, kernel_size=(1, 1))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, return_stages=False, return_pooled=False):
        x = self.seq(x)
        features = []

        for i, block in enumerate(self.model):
            x = block(x)
            if return_stages and i in self.stage_indices:
                features.append(x)

        x = self.conv1(x)

        if return_pooled:
            x = nn.functional.adaptive_avg_pool2d(x, 1)
            x = torch.flatten(x, 1)
            x = self.dropout(x)

        return features if return_stages else x


class MobileNetV3Backbone(BackboneAdapter):
    def __init__(
        self, config: str = "large", stage_indices: tuple = (3, 6, 11), dropout: float = 0.8
    ) -> None:
        super().__init__()
        self.set_stage_indices(stage_indices)

        re = nn.ReLU
        hs = nn.Hardswish

        self.model = nn.ModuleList([ConvBlock(3, 16, (3, 3), stride=2, padding=1, activation=hs)])

        configs_dict = {
            "small": (
                (16, 3, 16, 16, True, re, 2),
                (16, 3, 72, 24, False, re, 2),
                (24, 3, 88, 24, False, re, 1),
                (24, 5, 96, 40, True, hs, 2),
                (40, 5, 240, 40, True, hs, 1),
                (40, 5, 240, 40, True, hs, 1),
                (40, 5, 120, 48, True, hs, 1),
                (48, 5, 144, 48, True, hs, 1),
                (48, 5, 288, 96, True, hs, 2),
                (96, 5, 576, 96, True, hs, 1),
                (96, 5, 576, 96, True, hs, 1),
            ),
            "large": (
                (16, 3, 16, 16, False, re, 1),
                (16, 3, 64, 24, False, re, 2),
                (24, 3, 72, 24, False, re, 1),
                (24, 5, 72, 40, True, re, 2),
                (40, 5, 120, 40, True, re, 1),
                (40, 5, 120, 40, True, re, 1),
                (40, 3, 240, 80, False, hs, 2),
                (80, 3, 200, 80, False, hs, 1),
                (80, 3, 184, 80, False, hs, 1),
                (80, 3, 184, 80, False, hs, 1),
                (80, 3, 480, 112, True, hs, 1),
                (112, 3, 672, 112, True, hs, 1),
                (112, 5, 672, 160, True, hs, 2),
                (160, 5, 960, 160, True, hs, 1),
                (160, 5, 960, 160, True, hs, 1),
            ),
        }

        out_channels = 16
        for in_channels, k, exp_size, out_channels, se, act, stride in configs_dict[config]:
            self.model.append(
                InverseResidualBlock(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=k,
                    expansion_factor=exp_size,
                    stride=stride,
                    squeeze_exitation=se,
                    activation=act,
                )
            )

        hidden_channels = 576 if config == "small" else 960
        _out_channel = 1024 if config == "small" else 1280

        self.model.append(
            ConvBlock(out_channels, hidden_channels, (1, 1), bias=False, activation=hs)
        )
        self.head = nn.Sequential(
            nn.Conv2d(hidden_channels, _out_channel, (1, 1)), nn.Hardswish(), nn.Dropout(dropout)
        )

    def forward(self, x, return_stages=False, return_pooled=False):
        features = []
        for i, layer in enumerate(self.model):
            x = layer(x)
            if return_stages and i in self.stage_indices:
                features.append(x)

        x = self.head(x)

        if return_pooled:
            x = nn.functional.adaptive_avg_pool2d(x, 1)
            x = torch.flatten(x, 1)

        return features if return_stages else x
