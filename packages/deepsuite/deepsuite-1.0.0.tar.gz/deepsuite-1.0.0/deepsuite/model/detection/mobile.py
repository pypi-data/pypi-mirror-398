"""MobileNet architectures for efficient mobile inference.

This module contains MobileNetV1, V2, and V3 - models optimized for
mobile and embedded devices with minimal latency and memory consumption.

The MobileNet family uses Depthwise-Separable Convolutions to drastically reduce
complexity while maintaining accuracy.

References:
    - MobileNetV1: Howard, A. G., et al. (2017).
      MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications.
      https://arxiv.org/abs/1704.04861

    - MobileNetV2: Sandler, M., et al. (2018).
      MobileNetV2: Inverted Residuals and Linear Bottlenecks.
      https://arxiv.org/abs/1801.04381

    - MobileNetV3: Howard, A., et al. (2019).
      Searching for MobileNetV3.
      https://arxiv.org/abs/1905.02175

Example:
    ```python
    import torch
    from deepsuite.model.detection.mobile import MobileNetV3

    model = MobileNetV3(n_classes=1000, config='large')
    x = torch.randn(2, 3, 224, 224)
    output = model(x)  # Shape (2, 1000)
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.model.feature.mobile import (
    MobileNetV1Backbone,
    MobileNetV2Backbone,
    MobileNetV3Backbone,
)

if TYPE_CHECKING:
    from torch import Tensor


class MobileNetV1(MobileNetV1Backbone):
    """MobileNetV1 for image classification with minimal complexity.

    MobileNetV1 uses Depthwise-Separable Convolutions to achieve 8-9x fewer
    parameters and 5-14x fewer operations than standard CNNs.

    This makes the model ideal for mobile and embedded devices with
    limited resources (e.g., smartphones, IoT devices).

    Attributes:
        avgpool: Adaptive Average Pooling for dimension reduction.
        flatten: Flattening layer before FC layer.
        fc: Fully Connected classification layer.

    Example:
        ```python
        import torch
        from deepsuite.model.detection.mobile import MobileNetV1

        model = MobileNetV1(num_classes=1000, width_multiplier=1.0)
        x = torch.randn(2, 3, 224, 224)
        logits = model(x)  # Shape (2, 1000)
        ```
    """

    def __init__(
        self,
        num_classes: int = 1000,
        width_multiplier: float = 1.0,
        stage_indices: tuple[int, ...] = (3, 6, 11),
    ) -> None:
        """Initialize MobileNetV1.

        Args:
            num_classes: Number of classification classes. Default: 1000.
            width_multiplier: Channel scaling factor (0.25, 0.5, 1.0, etc.).
                             1.0 = standard width, 0.5 = half width.
                             Default: 1.0.
            stage_indices: Indices of backbone stages for feature extraction.
                          Default: (3, 6, 11).

        Example:
            ```python
            # Standard MobileNetV1
            model = MobileNetV1(num_classes=1000, width_multiplier=1.0)

            # Compact version with half width
            compact = MobileNetV1(num_classes=1000, width_multiplier=0.5)
            ```
        """
        super().__init__(width_multiplier=width_multiplier, stage_indices=stage_indices)
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(int(1024 * width_multiplier), num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through MobileNetV1.

        Args:
            x: Input tensor. Shape: (batch, 3, height, width).
               Standard: (batch, 3, 224, 224).

        Returns:
            torch.Tensor: Classification logits. Shape: (batch, num_classes).

        Example:
            ```python
            model = MobileNetV1()
            x = torch.randn(8, 3, 224, 224)
            logits = model(x)  # Shape (8, 1000)
            ```
        """
        x = super().forward(x, return_stages=False, return_pooled=False)
        x = self.avgpool(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x


class MobileNetV2(MobileNetV2Backbone):
    """MobileNetV2 with Inverted Residual Bottlenecks for improved efficiency.

    MobileNetV2 introduces Inverted Residual blocks that:
    - Use Linear activations (instead of ReLU) at output
    - Expand width before depthwise convolution
    - Include skip connections for residual learning

    This improves efficiency and accuracy over V1 with similar or lower
    memory/computation overhead.

    Attributes:
        pool: Adaptive Average Pooling Layer.
        flatten: Flattening Layer.
        dropout: Dropout for regularization.
        fc: Fully Connected classification layer.

    Example:
        ```python
        import torch
        from deepsuite.model.detection.mobile import MobileNetV2

        model = MobileNetV2(n_classes=1000)
        x = torch.randn(2, 3, 224, 224)
        logits = model(x)  # Shape (2, 1000)
        ```
    """

    def __init__(
        self,
        n_classes: int = 1000,
        dropout: float = 0.2,
        stage_indices: tuple[int, ...] = (3, 6, 13),
    ) -> None:
        """Initialize MobileNetV2.

        Args:
            n_classes: Number of classification classes. Default: 1000.
            dropout: Dropout rate before FC layer for regularization.
                    Default: 0.2.
            stage_indices: Indices of backbone stages. Default: (3, 6, 13).

        Example:
            ```python
            model = MobileNetV2(n_classes=1000, dropout=0.2)
            ```
        """
        super().__init__(stage_indices=stage_indices, dropout=dropout)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(1280, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through MobileNetV2.

        Args:
            x: Input tensor. Shape: (batch, 3, height, width).
               Standard: (batch, 3, 224, 224).

        Returns:
            torch.Tensor: Classification logits. Shape: (batch, n_classes).

        Example:
            ```python
            model = MobileNetV2()
            x = torch.randn(8, 3, 224, 224)
            logits = model(x)  # Shape (8, 1000)
            ```
        """
        x = super().forward(x, return_stages=False, return_pooled=False)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.dropout(x)
        x = self.fc(x)
        return x


class MobileNetV3(MobileNetV3Backbone):
    """MobileNetV3 with Hardware-Aware Neural Architecture Search and Attention.

    MobileNetV3 uses Neural Architecture Search (NAS) to automatically find
    optimal architectures balanced between latency, memory, and accuracy.

    Key Features:
    - Squeeze-and-Excitation (SE) Blocks for channel-wise attention
    - Updated Depthwise-Separable Convolutions
    - Hard Swish and Hard Sigmoid activations for faster inference

    Two Variants:
    - **Large**: Higher accuracy, suitable for devices with more resources
    - **Small**: Minimal footprint, optimized for ultra-mobile devices

    Attributes:
        pool: Adaptive Average Pooling Layer.
        flatten: Flattening Layer.
        fc: Fully Connected Classification Layer.

    Example:
        ```python
        import torch
        from deepsuite.model.detection.mobile import MobileNetV3

        # Large variant for higher accuracy
        model_large = MobileNetV3(n_classes=1000, config='large')

        # Small variant for minimal footprint
        model_small = MobileNetV3(n_classes=1000, config='small')

        x = torch.randn(2, 3, 224, 224)
        logits = model_large(x)  # Shape (2, 1000)
        ```
    """

    def __init__(
        self,
        n_classes: int = 1000,
        config: str = "large",
        dropout: float = 0.8,
        stage_indices: tuple[int, ...] = (3, 6, 11),
    ) -> None:
        """Initialize MobileNetV3.

        Args:
            n_classes: Number of classification classes. Default: 1000.
            config: Architecture variant: 'large' or 'small'. Default: 'large'.
                   - 'large': ~5.4M parameters, higher accuracy (~75% Top-1 ImageNet)
                   - 'small': ~2.5M parameters, very fast, good accuracy (~67% Top-1)
            dropout: Dropout rate before FC layer. Default: 0.8.
            stage_indices: Indices of backbone stages. Default: (3, 6, 11).

        Example:
            ```python
            # Standard MobileNetV3-Large
            model = MobileNetV3(n_classes=1000, config='large', dropout=0.8)

            # Compact MobileNetV3-Small version
            compact = MobileNetV3(n_classes=1000, config='small', dropout=0.5)
            ```

        Raises:
            ValueError: If config is not 'large' or 'small'.
        """
        if config not in ("large", "small"):
            msg = f"config must be 'large' or 'small', got: {config}"
            raise ValueError(msg)

        super().__init__(config=config, stage_indices=stage_indices, dropout=dropout)

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.flatten = nn.Flatten()

        # Different output channels for Large vs Small
        output_channels = 1280 if config == "large" else 1024
        self.fc = nn.Linear(output_channels, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through MobileNetV3.

        Args:
            x: Input tensor. Shape: (batch, 3, height, width).
               Standard: (batch, 3, 224, 224).

        Returns:
            torch.Tensor: Classification logits. Shape: (batch, n_classes).

        Example:
            ```python
            model = MobileNetV3(n_classes=1000, config='large')
            x = torch.randn(8, 3, 224, 224)
            logits = model(x)  # Shape (8, 1000)
            probs = torch.softmax(logits, dim=1)  # Normalize probabilities
            ```
        """
        x = super().forward(x, return_stages=False, return_pooled=False)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x
