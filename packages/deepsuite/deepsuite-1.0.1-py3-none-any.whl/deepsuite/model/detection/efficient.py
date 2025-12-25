"""EfficientNet family for scalable image classification and detection.

This module contains EfficientNet (B0-B7) - a family of models that use
Compound Scaling to jointly optimize width, depth, and resolution.

EfficientNet achieves state-of-the-art accuracy with significantly lower
memory and computational overhead than previous models.

The scaling coefficients (width, depth, resolution) enable easy adaptation
to various hardware constraints:
- **Small coefficients** (B0, B1): Mobile devices, edge computing
- **Large coefficients** (B6, B7): Servers, GPU clusters

References:
    Tan, M., & Le, Q. V. (2019).
    EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks.
    https://arxiv.org/abs/1905.11946

Example:
    ```python
    import torch
    from deepsuite.model.detection.efficient import EfficientNet

    # EfficientNet-B0 (mobile optimized)
    model_b0 = EfficientNet(
        resolution_coefficient=1.0,
        width_coefficient=1.0,
        depth_coefficient=1.0,
        num_classes=1000,
        version='b0'
    )

    # EfficientNet-B4 (better accuracy)
    model_b4 = EfficientNet(
        resolution_coefficient=1.38,
        width_coefficient=1.4,
        depth_coefficient=1.8,
        num_classes=1000,
        version='b4'
    )

    x = torch.randn(2, 3, 224, 224)
    logits = model_b0(x)  # Shape (2, 1000)
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.model.feature.efficientnet import EfficientNetBackbone

if TYPE_CHECKING:
    from torch import Tensor


class EfficientNet(EfficientNetBackbone):
    """EfficientNet classification model with Compound Scaling.

    EfficientNet uses Compound Scaling to jointly optimize width (channels),
    depth (layers), and resolution (input size) together, resulting in significantly
    better efficiency than simple depth or width scaling alone.

    The EfficientNet family B0 through B7 spans a spectrum:
    - B0: 5.3M parameters, 390M FLOPs (Mobile)
    - B4: 19M parameters, 4.2B FLOPs (Medium)
    - B7: 66M parameters, 37B FLOPs (Large, Server)

    Attributes:
        fc: Fully Connected Layer for classification.

    Example:
        ```python
        import torch
        from deepsuite.model.detection.efficient import EfficientNet

        # EfficientNet-B3
        model = EfficientNet(
            resolution_coefficient=1.2,
            width_coefficient=1.2,
            depth_coefficient=1.4,
            num_classes=1000,
            version='b3'
        )

        x = torch.randn(8, 3, 300, 300)  # B3 uses higher resolution
        logits = model(x)  # Shape (8, 1000)
        ```
    """

    def __init__(
        self,
        resolution_coefficient: float,
        width_coefficient: float,
        depth_coefficient: float,
        input_channels: int = 3,
        dropout_rate: float = 0.2,
        num_classes: int = 1000,
        version: str = "b0",
    ) -> None:
        """Initialize the EfficientNet model.

        Args:
            resolution_coefficient: Scaling factor for input resolution.
                                   Standard ImageNet: 224x224.
                                   Example: 1.0 = 224x224, 1.5 = 336x336.
            width_coefficient: Scaling factor for channel width.
                              1.0 = standard, 1.2 = 20% more channels.
            depth_coefficient: Scaling factor for network depth.
                              1.0 = standard, 1.5 = 50% more layers.
            input_channels: Number of input channels. Default: 3 (RGB).
            dropout_rate: Dropout rate before FC layer. Default: 0.2.
            num_classes: Number of classification classes. Default: 1000 (ImageNet).
            version: EfficientNet version ('b0' to 'b7'). Default: 'b0'.
                    - 'b0': 1.0, 1.0, 1.0 (Standard baseline)
                    - 'b1': 1.1, 1.0, 1.1
                    - 'b4': 1.38, 1.4, 1.8 (recommended for good balance)
                    - 'b7': 1.98, 2.0, 3.1 (largest, requires GPU)

        Example:
            ```python
            # EfficientNet-B0 for mobile devices
            model_mobile = EfficientNet(
                resolution_coefficient=1.0,
                width_coefficient=1.0,
                depth_coefficient=1.0,
                num_classes=1000,
                version='b0'
            )

            # EfficientNet-B4 for better balance
            model_balanced = EfficientNet(
                resolution_coefficient=1.38,
                width_coefficient=1.4,
                depth_coefficient=1.8,
                num_classes=1000,
                version='b4'
            )
            ```
        """
        super().__init__(
            resolution_coefficient=resolution_coefficient,
            width_coefficient=width_coefficient,
            depth_coefficient=depth_coefficient,
            input_channels=input_channels,
            dropout_rate=dropout_rate,
            version=version,
        )

        self.fc = nn.Linear(self.out_channels, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the EfficientNet model.

        Args:
            x: Input tensor. Shape: (batch, 3, height, width).
               Height and width depend on resolution_coefficient:
               - B0: (batch, 3, 224, 224)
               - B3: (batch, 3, 300, 300)
               - B7: (batch, 3, 600, 600)

        Returns:
            torch.Tensor: Classification logits. Shape: (batch, num_classes).

        Example:
            ```python
            model = EfficientNet(
                resolution_coefficient=1.0,
                width_coefficient=1.0,
                depth_coefficient=1.0,
                num_classes=1000
            )
            x = torch.randn(8, 3, 224, 224)
            logits = model(x)  # Shape (8, 1000)
            probs = torch.softmax(logits, dim=1)
            ```
        """
        x = super().forward(x, return_pooled=False, return_stages=False)
        x = self.fc(x)
        return x
