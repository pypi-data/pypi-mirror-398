"""Bounding box regression heads for object detection.

Provides convolutional heads for predicting bounding box parameters with
optional selective ReLU activation on specific channels. Supports both
rotation-free and rotation-aware bounding box representations.
"""

import torch
from torch import nn


class GeneralBBoxHead(nn.Module):
    """General bounding box regression head with selective channel activation.

    A convolutional head that predicts bounding box parameters with optional
    ReLU activation applied only to specific output channels (typically width
    and height to ensure positive values).

    Args:
        in_channels: Number of input feature channels.
        out_channels: Number of output channels for box parameters. Defaults to 4.
        relu_dims: Tuple of channel indices to apply ReLU activation.
            Typically (2, 3) for width and height channels. Defaults to (2, 3).

    Attributes:
        conv: 3x3 convolutional layer for box parameter prediction.
        relu_dims: Indices of output channels that require ReLU activation.

    Raises:
        AssertionError: If any relu_dims index is outside valid range [0, out_channels).

    Examples:
        >>> head = GeneralBBoxHead(in_channels=256, out_channels=4)
        >>> features = torch.randn(2, 256, 32, 32)
        >>> boxes = head(features)
        >>> boxes.shape
        torch.Size([2, 4, 32, 32])
    """

    def __init__(
        self, in_channels: int, out_channels: int = 4, relu_dims: tuple[int] | None = (2, 3)
    ) -> None:
        """Initialize the general bounding box head.

        Args:
            in_channels: Number of input feature channels.
            out_channels: Number of output box parameter channels.
            relu_dims: Channel indices for ReLU activation (e.g., width/height).

        Raises:
            AssertionError: If relu_dims contains out-of-bounds indices.
        """
        assert all(0 <= i < out_channels for i in relu_dims), "ReLU channel index out of bounds"
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.relu_dims = relu_dims

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Predict bounding box parameters from feature maps.

        Args:
            x: Input features of shape (batch_size, in_channels, height, width).

        Returns:
            Bounding box parameters of shape (batch_size, out_channels, height, width).
            Channels specified in relu_dims are constrained to non-negative values.

        Note:
            ReLU is applied only to specified channels to ensure positive values
            for width and height while allowing negative offsets for center coordinates.
        """
        out = self.conv(x)
        if self.relu_dims:
            out[:, list(self.relu_dims)] = torch.relu(out[:, list(self.relu_dims)])
        return out


class RotationFreeBBoxHead(GeneralBBoxHead):
    """Rotation-free bounding box head for axis-aligned boxes.

    Predicts 4-channel output representing axis-aligned bounding boxes:
    (center_x, center_y, width, height) for anchor-free detection.

    Args:
        in_channels: Number of input feature channels.
        relu_dims: Channel indices for ReLU (typically (2, 3) for width/height).
            Defaults to (2, 3).

    Note:
        Output format is (Cx, Cy, W, H) where:
            - Cx, Cy: Center coordinates (can be negative offsets)
            - W, H: Width and height (positive values enforced via ReLU)

    Examples:
        >>> head = RotationFreeBBoxHead(in_channels=256)
        >>> features = torch.randn(2, 256, 40, 40)
        >>> boxes = head(features)
        >>> boxes.shape
        torch.Size([2, 4, 40, 40])
    """

    def __init__(self, in_channels: int, relu_dims: tuple[int] | None = (2, 3)) -> None:
        """Initialize rotation-free bounding box head.

        Args:
            in_channels: Number of input feature channels.
            relu_dims: Channel indices for ReLU activation.
        """
        super().__init__(in_channels=in_channels, out_channels=4, relu_dims=relu_dims)


class BBoxHead(GeneralBBoxHead):
    """Rotation-aware bounding box head for oriented object detection.

    Predicts 5-channel output representing oriented bounding boxes:
    (center_x, center_y, width, height, theta) for anchor-free detection
    with rotation support.

    Args:
        in_channels: Number of input feature channels.
        relu_dims: Channel indices for ReLU (typically (2, 3) for width/height).
            Defaults to (2, 3).

    Note:
        Output format is (Cx, Cy, W, H, θ) where:
            - Cx, Cy: Center coordinates (can be negative offsets)
            - W, H: Width and height (positive values enforced via ReLU)
            - θ: Rotation angle in radians (no activation)

    Examples:
        >>> head = BBoxHead(in_channels=256)
        >>> features = torch.randn(2, 256, 40, 40)
        >>> boxes = head(features)
        >>> boxes.shape
        torch.Size([2, 5, 40, 40])
    """

    def __init__(self, in_channels: int, relu_dims: tuple[int] | None = (2, 3)) -> None:
        """Initialize rotation-aware bounding box head.

        Args:
            in_channels: Number of input feature channels.
            relu_dims: Channel indices for ReLU activation.
        """
        super().__init__(in_channels=in_channels, out_channels=5, relu_dims=relu_dims)
