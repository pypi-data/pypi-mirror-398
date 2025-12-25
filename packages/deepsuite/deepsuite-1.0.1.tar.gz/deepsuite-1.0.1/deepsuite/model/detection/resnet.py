"""ResNet-based classification and detection models.

This module contains ResNet variants (18, 34, 50, 101, etc.) as
feature backbones for different tasks:
- Image Classification: ResNet as complete classification model
- Object Detection: ResNet backbone for YOLO, RetinaNet, etc.

ResNet architecture is based on the Residual Learning assumption that deep
networks are easier to train when they have residual connections.

Reference:
    He, K., Zhang, X., Ren, S., & Sun, J. (2015).
    Deep Residual Learning for Image Recognition.
    https://arxiv.org/abs/1512.03385

Example:
    ```python
    import torch
    from deepsuite.model.detection.resnet import ResNet

    # ResNet50 for classification with 1000 classes
    model = ResNet(
        resnet_variant=[[64, 128, 256, 512], [3, 4, 6, 3], 4, True],
        in_channels=3,
        num_classes=1000
    )
    x = torch.randn(2, 3, 224, 224)
    output = model(x)  # Shape (2, 1000)
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.model.feature.resnet import ResNetBackbone

if TYPE_CHECKING:
    from torch import Tensor


class ResNet(ResNetBackbone):
    """ResNet classification model with complete classification pipeline.

    This class extends ResNetBackbone (feature extractor) with:
    - Adaptive Average Pooling for global aggregation
    - Fully Connected Layer for classification

    It can be used directly for image classification or as a backbone for
    detection models (see `return_stages` parameter in backbone).

    Attributes:
        average_pool: Adaptive Average Pooling Layer.
        fc1: Fully Connected Layer for classification.
        expansion: Expansion factor of bottleneck blocks (e.g., 4 for ResNet50+).

    Example:
        ```python
        import torch
        from deepsuite.model.detection.resnet import ResNet

        # ResNet50 (variant=[64,128,256,512], [3,4,6,3], 4, True)
        model = ResNet(
            resnet_variant=[[64, 128, 256, 512], [3, 4, 6, 3], 4, True],
            in_channels=3,
            num_classes=1000,
            stage_indices=(3, 4, 5)
        )

        # Forward pass
        x = torch.randn(1, 3, 224, 224)
        logits = model(x)  # Shape (1, 1000)

        # Extract intermediate features for detection
        features = model(x, return_stages=True, return_pooled=True)
        ```
    """

    def __init__(
        self,
        resnet_variant: list[Any],
        in_channels: int,
        num_classes: int,
        stage_indices: tuple[int, ...] = (3, 4, 5),
    ) -> None:
        """Initialize ResNet classification model.

        Args:
            resnet_variant: List with [channels, repeats, expansion, use_bottleneck].
                           Example: [[64, 128, 256, 512], [3, 4, 6, 3], 4, True]
                           defines a ResNet50 architecture.
            in_channels: Number of input channels (typically 3 for RGB).
            num_classes: Number of classification classes in output.
            stage_indices: Indices of backbone stages used for feature extraction.
                          Default: (3, 4, 5) for 3 stages.

        Example:
            ```python
            # ResNet18
            model18 = ResNet(
                resnet_variant=[[64, 128, 256, 512], [2, 2, 2, 2], 1, False],
                in_channels=3,
                num_classes=1000
            )

            # ResNet50
            model50 = ResNet(
                resnet_variant=[[64, 128, 256, 512], [3, 4, 6, 3], 4, True],
                in_channels=3,
                num_classes=1000
            )
            ```
        """
        super().__init__(
            resnet_variant=resnet_variant,
            in_channels=in_channels,
            stage_indices=stage_indices,
        )

        self.average_pool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Linear(self.channels_list[3] * self.expansion, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through ResNet classification model.

        Args:
            x: Input tensor. Shape: (batch, in_channels, height, width).
               Typically: (batch, 3, 224, 224) for ImageNet.

        Returns:
            torch.Tensor: Classification logits. Shape: (batch, num_classes).
                         Not normalized with softmax yet.

        Example:
            ```python
            model = ResNet(...)
            x = torch.randn(8, 3, 224, 224)
            logits = model(x)  # Shape (8, 1000)
            probs = torch.softmax(logits, dim=1)  # Normalize for probabilities
            ```
        """
        # Extract features with backbone
        x = super().forward(x, return_stages=False, return_pooled=False)

        # Global average pooling
        x = self.average_pool(x)

        # Flatten for fully connected layer
        x = torch.flatten(x, start_dim=1)

        # Classification
        x = self.fc1(x)

        return x
