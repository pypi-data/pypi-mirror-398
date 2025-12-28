"""Classification head module for converting feature maps to class logits.

This module provides a classification head that applies global average pooling
followed by a fully connected layer to produce class predictions from feature maps.
Commonly used as the final layer in image classification networks.
"""

import torch
from torch import nn


class ClassificationHead(nn.Module):
    """Classification head with global pooling and fully connected layer.

    Converts multi-channel feature maps into class logits by applying global
    average pooling followed by a linear transformation. Compatible with any
    backbone that outputs feature maps.

    Args:
        in_channels: Number of input feature map channels.
        num_classes: Number of output classes for classification.

    Attributes:
        pool: Adaptive average pooling layer that reduces spatial dimensions to 1x1.
        fc: Fully connected layer that maps pooled features to class logits.

    Examples:
        >>> head = ClassificationHead(in_channels=2048, num_classes=1000)
        >>> features = torch.randn(8, 2048, 7, 7)
        >>> logits = head(features)
        >>> logits.shape
        torch.Size([8, 1000])
    """

    def __init__(self, in_channels: int, num_classes: int) -> None:
        """Initialize the classification head.

        Args:
            in_channels: Number of input feature map channels.
            num_classes: Number of output classes.
        """
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(in_channels, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the classification head.

        Args:
            x: Input feature maps of shape (batch_size, in_channels, height, width).

        Returns:
            Class logits of shape (batch_size, num_classes).

        Raises:
            RuntimeError: If input tensor has incorrect dimensions (expected 4D).
        """
        x = self.pool(x)
        x = torch.flatten(x, 1)
        return self.fc(x)
