"""Heatmap and offset prediction heads for keypoint-based detection.

Provides convolutional heads for predicting object center heatmaps and
sub-pixel offset maps, commonly used in CenterNet-style detectors and
keypoint estimation networks.
"""

import torch
from torch import nn


class HeatmapHead(nn.Module):
    """Heatmap prediction head with sigmoid activation.

    Predicts per-class heatmaps indicating object center locations or keypoint
    presence probabilities. Uses a two-stage convolution with intermediate
    feature refinement and sigmoid activation for probability output.

    Args:
        in_channels: Number of input feature channels.
        num_classes: Number of object classes or keypoint types to detect.

    Attributes:
        conv: Sequential convolutional layers consisting of:
            - 3x3 conv with batch normalization and ReLU
            - 1x1 conv for final class prediction

    Examples:
        >>> head = HeatmapHead(in_channels=256, num_classes=80)
        >>> features = torch.randn(2, 256, 128, 128)
        >>> heatmap = head(features)
        >>> heatmap.shape
        torch.Size([2, 80, 128, 128])
        >>> assert (heatmap >= 0).all() and (heatmap <= 1).all()
    """

    def __init__(self, in_channels: int, num_classes: int) -> None:
        """Initialize the heatmap head.

        Args:
            in_channels: Number of input feature map channels.
            num_classes: Number of output heatmap channels (one per class).
        """
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, num_classes, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Predict class heatmaps from feature maps.

        Args:
            x: Input features of shape (batch_size, in_channels, height, width).

        Returns:
            Heatmap probabilities of shape (batch_size, num_classes, height, width).
            Values are in range [0, 1] after sigmoid activation, representing the
            probability of each class being present at each spatial location.
        """
        return self.conv(x).sigmoid()


class OffsetHead(nn.Module):
    """Sub-pixel offset prediction head for precise localization.

    Predicts 2D offset vectors for refining discretized heatmap locations to
    sub-pixel precision. Commonly used alongside heatmap heads in CenterNet-style
    detectors to compensate for downsampling quantization errors.

    Args:
        in_channels: Number of input feature channels.

    Attributes:
        conv: Sequential convolutional layers consisting of:
            - 3x3 conv with batch normalization and ReLU
            - 1x1 conv producing 2-channel offset output

    Note:
        Output offsets are typically in range [-0.5, 0.5] representing fractional
        pixel displacements in x and y directions.

    Examples:
        >>> head = OffsetHead(in_channels=256)
        >>> features = torch.randn(2, 256, 128, 128)
        >>> offsets = head(features)
        >>> offsets.shape
        torch.Size([2, 2, 128, 128])
    """

    def __init__(self, in_channels: int) -> None:
        """Initialize the offset head.

        Args:
            in_channels: Number of input feature map channels.
        """
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 2, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Predict offset maps from feature maps.

        Args:
            x: Input features of shape (batch_size, in_channels, height, width).

        Returns:
            Offset vectors of shape (batch_size, 2, height, width) where:
                - Channel 0: x-direction offset
                - Channel 1: y-direction offset
        """
        return self.conv(x)
