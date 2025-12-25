"""Backend Adapter module."""

from collections.abc import Sequence
import math

from torch import Tensor, nn


class BackboneAdapter(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self._stage_indices: Sequence[int] = []

    def set_stage_indices(self, indices: Sequence[int]):
        self._stage_indices = indices

    @property
    def stage_indices(self):
        return self._stage_indices

    @staticmethod
    def round_filters(filters, width_coefficient, divisor=8):
        """Round the number of filters based on the width coefficient.

        Args:
            filters (int): Number of filters.
            width_coefficient (float): Width coefficient.
            divisor (int): Divisor for rounding. Default is 8.

        Returns:
            int: Rounded number of filters.
        """
        filters *= width_coefficient
        new_filters = max(divisor, int(filters + divisor / 2) // divisor * divisor)
        if new_filters < 0.9 * filters:
            new_filters += divisor
        return int(new_filters)

    @staticmethod
    def round_repeats(repeats, depth_coefficient):
        """Round the number of repeats based on the depth coefficient.

        Args:
            repeats (int): Number of repeats.
            depth_coefficient (float): Depth coefficient.

        Returns:
            int: Rounded number of repeats.
        """
        return int(math.ceil(depth_coefficient * repeats))

    @staticmethod
    def calculate_image_size(resolution_coefficient, base_size=224):
        """Calculate the input image size based on the resolution coefficient.

        Args:
            resolution_coefficient (float): Resolution coefficient.
            base_size (int): Base size of the image. Default is 224.

        Returns:
            tuple: Calculated image size.
        """
        # Scale the base resolution with the resolution_coefficient
        scaled_size = base_size * resolution_coefficient
        # Round to the nearest multiple of 8
        new_size = int(math.ceil(scaled_size / 8) * 8)
        return (new_size, new_size)

    def extract_embedding(self, x: Tensor) -> Tensor:
        """Returns a single embedding tensor (z. B. für Logging), standardmäßig letzte Stage."""
        features = self.forward(x, return_stages=True)
        return features[-1].mean(dim=[2, 3])  # Spatial mean pooling → [B, C]
