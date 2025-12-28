"""Camera resolution presets for ConfigurableHourglassAutoencoder.

This module provides pre-configured model settings for common camera
resolutions and image sizes, allowing easy model creation without
manual tuning.

Example:
    >>> from deepsuite.model.autoencoder_configs import camera_configs
    >>> config = camera_configs["5mp"]
    >>> model = ConfigurableHourglassAutoencoder(**config)
"""

from __future__ import annotations

from typing import Any

camera_configs: dict[str, dict[str, Any]] = {
    # Mobile/VGA resolutions
    "vga": {
        "input_shape": (3, 480, 640),
        "num_layers": 3,
        "bottleneck_channels": 64,
        "base_channels": 32,
    },
    "qvga": {
        "input_shape": (3, 240, 320),
        "num_layers": 2,
        "bottleneck_channels": 32,
        "base_channels": 16,
    },
    # HD resolutions
    "hd": {
        "input_shape": (3, 720, 1280),
        "num_layers": 4,
        "bottleneck_channels": 128,
        "base_channels": 32,
    },
    "fullhd": {
        "input_shape": (3, 1080, 1920),
        "num_layers": 4,
        "bottleneck_channels": 128,
        "base_channels": 32,
    },
    # Megapixel resolutions
    "2mp": {
        "input_shape": (3, 1536, 2048),
        "num_layers": 5,
        "bottleneck_channels": 256,
        "base_channels": 32,
    },
    "3mp": {
        "input_shape": (3, 2048, 1536),
        "num_layers": 5,
        "bottleneck_channels": 256,
        "base_channels": 32,
    },
    "5mp": {
        "input_shape": (3, 2560, 1920),
        "num_layers": 5,
        "bottleneck_channels": 256,
        "base_channels": 32,
    },
    "8mp": {
        "input_shape": (3, 3072, 2304),
        "num_layers": 6,
        "bottleneck_channels": 512,
        "base_channels": 32,
    },
    "12mp": {
        "input_shape": (3, 4000, 3000),
        "num_layers": 6,
        "bottleneck_channels": 512,
        "base_channels": 32,
    },
    "16mp": {
        "input_shape": (3, 4608, 3456),
        "num_layers": 6,
        "bottleneck_channels": 512,
        "base_channels": 32,
    },
    # Power-of-2 resolutions (useful for testing/development)
    "256x256": {
        "input_shape": (3, 256, 256),
        "num_layers": 4,
        "bottleneck_channels": 128,
        "base_channels": 32,
    },
    "512x512": {
        "input_shape": (3, 512, 512),
        "num_layers": 5,
        "bottleneck_channels": 256,
        "base_channels": 32,
    },
    "1024x1024": {
        "input_shape": (3, 1024, 1024),
        "num_layers": 6,
        "bottleneck_channels": 512,
        "base_channels": 32,
    },
}


def get_camera_config(resolution: str) -> dict[str, Any]:
    """Get configuration for a specific camera resolution.

    Args:
        resolution: Resolution name (e.g., '5mp', 'fullhd', 'vga').

    Returns:
        Configuration dictionary for ConfigurableHourglassAutoencoder.

    Raises:
        ValueError: If resolution name is not found.

    Example:
        >>> config = get_camera_config("5mp")
        >>> from deepsuite.model import ConfigurableHourglassAutoencoder
        >>> model = ConfigurableHourglassAutoencoder(**config)
    """
    if resolution not in camera_configs:
        available = sorted(camera_configs.keys())
        msg = f"Unknown resolution: {resolution}\nAvailable: {available}"
        raise ValueError(msg)
    return camera_configs[resolution]


def list_available_resolutions() -> list[str]:
    """List all available camera resolution preset names.

    Returns:
        Sorted list of resolution names.

    Example:
        >>> resolutions = list_available_resolutions()
        >>> print(resolutions)
        ['12mp', '16mp', '2mp', '256x256', '3mp', '5mp', '8mp', ...]
    """
    return sorted(camera_configs.keys())


def print_camera_resolutions() -> None:
    """Print all available camera resolutions with specifications.

    Displays a formatted table showing each resolution, dimensions,
    layer count, bottleneck size, and compression ratio.

    Example:
        >>> print_camera_resolutions()
        ==================== Camera Resolutions ====================
        VGA:     480x640  | Layers: 3 | Bottleneck: 64x60x80
        5MP:   2560x1920  | Layers: 5 | Bottleneck: 256x80x60
        ...
    """
    import sys

    from deepsuite.model import ConfigurableHourglassAutoencoder

    lines = [
        "=" * 80,
        "Available Camera Resolutions for ConfigurableHourglassAutoencoder",
        "=" * 80,
    ]

    for name in sorted(camera_configs.keys()):
        config = camera_configs[name]
        model = ConfigurableHourglassAutoencoder(**config)
        _, h, w = config["input_shape"]
        lines.append(
            f"\n{name.upper():15} | {h:4d}x{w:4d} | Layers: {config['num_layers']} | "
            f"Bottleneck: {config['bottleneck_channels']:3d}x"
            f"{model.bottleneck_height:3d}x{model.bottleneck_width:3d} | "
            f"Compression: {model.get_compression_ratio():6.1f}x"
        )

    lines.append("\n" + "=" * 80)
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    print_camera_resolutions()
