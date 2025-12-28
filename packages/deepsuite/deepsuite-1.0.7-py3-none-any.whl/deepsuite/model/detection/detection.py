"""Detection model with flexible channel sizes and layer numbers.

This class implements a detection model using a CSPDarknet backbone, FPN neck, and a detection head.

Attributes:
    backbone (CSPDarknet): The backbone network.
    neck (FPN): The feature pyramid network.
    head (DetectionHead): The detection head.

Example:
    >>> model = DetectionModel()
    >>> model
    DetectionModel(
        (backbone): CSPDarknet(
            (conv1): ConvBlock(
                (conv): Conv2d(3, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), bias=False)
                (bn): BatchNorm2d(32, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
                (act): SiLU()
            )
            (conv2): ConvBlock(
                (conv): Conv2d(32, 64, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
                (bn): BatchNorm2d(64, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
                (act): SiLU()
            )

            ...

           (conv3): ConvBlock(
                (conv): Conv2d(512, 1024, kernel_size=(1, 1), stride=(1, 1), bias=False)
                (bn): BatchNorm2d(1024, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
                (act): SiLU()
            )
        )

        (neck): FPN(

            ...

            (lateral_convs): ModuleList(

                ...

                (0): ConvBlock(
                    (conv): Conv2d(256, 256, kernel_size=(1, 1), stride=(1, 1), bias=False)
                    (bn): BatchNorm2d(256, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
                    (act): SiLU()
                )
            )

            ...

            (output_convs): ModuleList(
                (0): ConvBlock(
                    (conv): Conv2d(256, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), bias=False)
                    (bn): BatchNorm2d(256, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
                    (act): SiLU()
                )
            )
        )

        (head): DetectionHead(
            (conv): Conv2d(256, 255, kernel_size=(1, 1), stride=(1, 1))
        )

    )
"""

from collections.abc import Sequence

import torch
from torch import nn

from deepsuite.model.detection.head import DetectionHead
from deepsuite.model.feature.darknet import CSPDarknetBackbone
from deepsuite.model.feature.fpn import FPN


class DetectionModel(nn.Module):
    """Detection model with flexible channel sizes and layer numbers.

    This class implements a detection model using a CSPDarknet backbone, FPN neck, and a detection head.

    Attributes:
        backbone (CSPDarknet): The backbone network.
        neck (FPN): The feature pyramid network.
        head (DetectionHead): The detection head.
    """

    def __init__(
        self,
        in_channels: int = 3,
        backbone_channels: Sequence[int] | None = None,
        backbone_blocks: Sequence[int] | None = None,
        fpn_out_channels: int = 256,
        num_classes: int = 1,
        num_anchors: int = 3,
    ) -> None:
        """Initialize the DetectionModel.

        Args:
            in_channels (int): Number of input channels. Default is 3.
            backbone_channels (list): List of channel sizes for the backbone. Default is [32, 64, 128, 256, 512, 1024].
            backbone_blocks (list): List of block numbers for the backbone. Default is [1, 2, 8, 8, 4].
            fpn_out_channels (int): Number of output channels for the FPN. Default is 256.
            num_classes (int): Number of classes. Default is 1.
            num_anchors (int): Number of anchors. Default is 3.
        """
        super().__init__()
        if backbone_channels is None:
            backbone_channels = (32, 64, 128, 256, 512, 1024)

        if backbone_blocks is None:
            backbone_blocks = (1, 2, 8, 8, 4)

        self.backbone = CSPDarknetBackbone(
            in_channels=in_channels,
            channels_list=backbone_channels,
            num_blocks_list=backbone_blocks,
            stage_indices=(2, 3, 4),
        )
        self.neck = FPN(in_channels_list=self.backbone.out_channels, out_channels=fpn_out_channels)
        self.head = DetectionHead(fpn_out_channels, num_classes, num_anchors)

    def forward(self, x: torch.Tensor) -> list:
        """Forward pass through the DetectionModel.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            list: List of output tensors from the detection head.
        """
        # Backbone
        features = self.backbone(x)

        # Feature pyramid
        fpn_features = self.neck(features)

        # Head
        return [self.head(feature) for feature in fpn_features]
