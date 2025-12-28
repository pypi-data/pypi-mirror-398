"""Discriminator models for GAN training.

Provides discriminator architectures for adversarial training,
perceptual quality refinement, and image-to-image translation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from torch import nn

if TYPE_CHECKING:
    import torch


class PatchGANDiscriminator(nn.Module):
    """PatchGAN discriminator for local realism discrimination.

    Outputs a grid of predictions rather than a single scalar,
    allowing the discriminator to focus on local texture quality.

    Args:
        in_channels: Number of input channels (default: 3 for RGB).
        ndf: Base number of discriminator filters (default: 64).
        n_layers: Number of downsampling layers (default: 3).
        use_bias: Use bias in conv layers (default: True).

    Example:
        >>> disc = PatchGANDiscriminator(in_channels=3, ndf=64)
        >>> x = torch.rand(2, 3, 256, 256)
        >>> out = disc(x)  # [2, 1, 30, 30] patch predictions
    """

    def __init__(
        self,
        in_channels: int = 3,
        ndf: int = 64,
        n_layers: int = 3,
        use_bias: bool = True,
    ) -> None:
        super().__init__()

        layers = [
            nn.Conv2d(in_channels, ndf, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
        ]

        nf_mult = 1
        for n in range(1, n_layers):
            nf_mult_prev = nf_mult
            nf_mult = min(2**n, 8)
            layers.extend(
                [
                    nn.Conv2d(
                        ndf * nf_mult_prev,
                        ndf * nf_mult,
                        kernel_size=4,
                        stride=2,
                        padding=1,
                        bias=use_bias,
                    ),
                    nn.BatchNorm2d(ndf * nf_mult),
                    nn.LeakyReLU(0.2, inplace=True),
                ]
            )

        nf_mult_prev = nf_mult
        nf_mult = min(2**n_layers, 8)
        layers.extend(
            [
                nn.Conv2d(
                    ndf * nf_mult_prev,
                    ndf * nf_mult,
                    kernel_size=4,
                    stride=1,
                    padding=1,
                    bias=use_bias,
                ),
                nn.BatchNorm2d(ndf * nf_mult),
                nn.LeakyReLU(0.2, inplace=True),
            ]
        )

        # Final layer: output patch predictions
        layers.append(nn.Conv2d(ndf * nf_mult, 1, kernel_size=4, stride=1, padding=1))

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PixelDiscriminator(nn.Module):
    """Pixel-level discriminator for fine-grained discrimination.

    Operates at full resolution for maximum detail preservation.

    Args:
        in_channels: Number of input channels (default: 3).
        ndf: Base number of filters (default: 64).

    Example:
        >>> disc = PixelDiscriminator(in_channels=3)
        >>> x = torch.rand(2, 3, 256, 256)
        >>> out = disc(x)  # [2, 1, 254, 254] pixel predictions
    """

    def __init__(self, in_channels: int = 3, ndf: int = 64) -> None:
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv2d(in_channels, ndf, kernel_size=1, stride=1, padding=0),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf, ndf * 2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 2, 1, kernel_size=1, stride=1, padding=0),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MultiScaleDiscriminator(nn.Module):
    """Multi-scale discriminator operating at multiple resolutions.

    Combines discriminators at different scales for multi-resolution
    adversarial training.

    Args:
        in_channels: Number of input channels (default: 3).
        num_scales: Number of pyramid levels (default: 3).
        ndf: Base number of filters (default: 64).

    Example:
        >>> disc = MultiScaleDiscriminator(in_channels=3, num_scales=3)
        >>> x = torch.rand(2, 3, 256, 256)
        >>> outs = disc(x)  # List of 3 outputs at different scales
    """

    def __init__(self, in_channels: int = 3, num_scales: int = 3, ndf: int = 64) -> None:
        super().__init__()
        self.num_scales = num_scales
        self.discriminators = nn.ModuleList(
            [PatchGANDiscriminator(in_channels=in_channels, ndf=ndf) for _ in range(num_scales)]
        )
        self.downsample = nn.AvgPool2d(kernel_size=3, stride=2, padding=1, count_include_pad=False)

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        outputs = []
        for disc in self.discriminators:
            outputs.append(disc(x))
            x = self.downsample(x)
        return outputs
