"""Autoencoder models for latent representation learning.

Provides encoder-decoder architectures for image compression,
feature extraction, and dimensionality reduction tasks.

Architectures:
- ConvEncoder/ConvDecoder: Fixed 4-layer architecture for 256x256 images
- ConfigurableHourglassAutoencoder: Flexible architecture for any image size
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.lightning_base import BaseModule

if TYPE_CHECKING:
    from collections.abc import Sequence


class ConvEncoder(nn.Module):
    """Convolutional encoder for fixed-size RGB images.

    Maps image [B, C, H, W] to latent tensor [B, Cz, H/16, W/16].

    Args:
        in_channels: Number of input channels (default: 3 for RGB).
        z_channels: Number of latent channels (default: 128).
        depth: Number of downsampling layers (default: 4).

    Example:
        >>> encoder = ConvEncoder(in_channels=3, z_channels=128)
        >>> x = torch.rand(2, 3, 256, 256)
        >>> z = encoder(x)  # [2, 128, 16, 16]
    """

    def __init__(
        self,
        in_channels: int = 3,
        z_channels: int = 128,
        depth: int = 4,
    ) -> None:
        super().__init__()
        channels = [in_channels] + [32 * (2**i) for i in range(depth - 1)] + [z_channels]
        layers: list[nn.Module] = []
        for i in range(depth):
            layers.extend(
                [
                    nn.Conv2d(channels[i], channels[i + 1], 3, stride=2, padding=1),
                    nn.ReLU(inplace=True),
                ]
            )
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode image to latent representation."""
        return self.net(x)

    def quantize(self, z: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
        """Quantize latent tensor for compression.

        Args:
            z: Latent tensor.
            scale: Quantization scale factor.

        Returns:
            torch.Tensor: Quantized latent (rounded to nearest int * scale).
        """
        return torch.round(z * scale) / scale


class ConvDecoder(nn.Module):
    """Convolutional decoder for image reconstruction.

    Maps latent [B, Cz, h, w] to reconstructed image [B, C, H, W].

    Args:
        z_channels: Number of latent channels (default: 128).
        out_channels: Number of output channels (default: 3 for RGB).
        depth: Number of upsampling layers (default: 4).

    Example:
        >>> decoder = ConvDecoder(z_channels=128, out_channels=3)
        >>> z = torch.rand(2, 128, 16, 16)
        >>> x_hat = decoder(z)  # [2, 3, 256, 256]
    """

    def __init__(
        self,
        z_channels: int = 128,
        out_channels: int = 3,
        depth: int = 4,
    ) -> None:
        super().__init__()
        channels = [z_channels] + [128 // (2**i) for i in range(depth - 1)] + [out_channels]
        layers: list[nn.Module] = []
        for i in range(depth - 1):
            layers.extend(
                [
                    nn.ConvTranspose2d(
                        channels[i],
                        channels[i + 1],
                        4,
                        stride=2,
                        padding=1,
                    ),
                    nn.ReLU(inplace=True),
                ]
            )
        # Final layer without ReLU, use Sigmoid for [0,1] range
        layers.append(
            nn.ConvTranspose2d(
                channels[-2],
                channels[-1],
                4,
                stride=2,
                padding=1,
            )
        )
        layers.append(nn.Sigmoid())
        self.net = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent representation to image."""
        return self.net(z)


class AutoencoderModule(BaseModule):  # type: ignore[misc]
    """Lightning module for autoencoder training.

    Combines encoder and decoder with reconstruction loss.

    Args:
        z_channels: Latent dimension (default: 128).
        lr: Learning rate (default: 1e-3).
        loss_fn: Reconstruction loss function (default: MSE).
        **kwargs: Additional arguments for BaseModule.

    Example:
        >>> model = AutoencoderModule(z_channels=128, lr=1e-3)
        >>> trainer = pl.Trainer(max_epochs=10)
        >>> trainer.fit(model, datamodule)
    """

    def __init__(
        self,
        z_channels: int = 128,
        lr: float = 1e-3,
        loss_fn: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.save_hyperparameters()
        self.encoder = ConvEncoder(z_channels=z_channels)
        self.decoder = ConvDecoder(z_channels=z_channels)
        self.lr = lr
        self.loss_fn = loss_fn if loss_fn is not None else nn.MSELoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode and decode image."""
        z = self.encoder(x)
        return self.decoder(z)

    def training_step(  # type: ignore[override]
        self,
        batch: Any,
        _batch_idx: int,
    ) -> torch.Tensor:
        """Compute training loss."""
        x = batch[0] if isinstance(batch, tuple | list) else batch
        x_hat = self(x)
        loss = self.loss_fn(x_hat, x)
        self.log("train/loss", loss, prog_bar=True)
        return loss

    def validation_step(  # type: ignore[override]
        self,
        batch: Any,
        _batch_idx: int,
    ) -> torch.Tensor:
        """Compute validation loss."""
        x = batch[0] if isinstance(batch, tuple | list) else batch
        x_hat = self(x)
        val_loss = self.loss_fn(x_hat, x)
        self.log("val/loss", val_loss, prog_bar=True)

        # Log additional metrics if available
        try:
            from deepsuite.metric.image_quality import psnr, ssim

            self.log("val/psnr", psnr(x_hat, x), prog_bar=True)
            self.log("val/ssim", ssim(x_hat, x), prog_bar=True)
        except ImportError:
            pass

        return val_loss

    def configure_optimizers(self) -> torch.optim.Optimizer:
        """Create optimizer for training."""
        return torch.optim.Adam(self.parameters(), lr=self.lr)


class ConvBlock(nn.Module):
    """Convolutional block for downsampling.

    Applies Conv2d -> BatchNorm -> ReLU with stride=2.

    Args:
        in_channels: Number of input channels.
        out_channels: Number of output channels.
        kernel_size: Convolution kernel size (default: 3).
        stride: Stride (default: 2 for downsampling).
        padding: Padding (default: 1).
        activation: Activation function (default: ReLU).
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 2,
        padding: int = 1,
        activation: type[nn.Module] = nn.ReLU,  # noqa: ARG002
    ) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply convolution block."""
        return self.block(x)


class TransposedConvBlock(nn.Module):
    """Transposed convolution block for upsampling.

    Applies ConvTranspose2d -> BatchNorm -> ReLU with stride=2.

    Args:
        in_channels: Number of input channels.
        out_channels: Number of output channels.
        kernel_size: Transposed convolution kernel size (default: 4).
        stride: Stride (default: 2 for upsampling).
        padding: Padding (default: 1).
        activation: Activation function (default: ReLU).
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 4,
        stride: int = 2,
        padding: int = 1,
        activation: type[nn.Module] = nn.ReLU,  # noqa: ARG002
    ) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.ConvTranspose2d(
                in_channels,
                out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply transposed convolution block."""
        return self.block(x)


class HourglassEncoder(nn.Module):
    """Hourglass encoder with configurable layers.

    Progressively downsamples spatial dimensions while increasing channels.

    Args:
        in_channels: Number of input channels (typically 3 for RGB).
        channel_schedule: List of output channels for each layer.
        use_batch_norm: Whether to use batch normalization (default: True).
    """

    def __init__(
        self,
        in_channels: int,
        channel_schedule: Sequence[int],
        use_batch_norm: bool = True,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.channel_schedule = list(channel_schedule)
        self.use_batch_norm = use_batch_norm

        # Calculate bottleneck dimensions (will be set in parent class)
        layers: list[nn.Module] = []

        # Build encoder layers
        in_ch = in_channels
        for out_ch in channel_schedule:
            if use_batch_norm:
                layers.append(ConvBlock(in_ch, out_ch, stride=2))
            else:
                layers.append(
                    nn.Sequential(
                        nn.Conv2d(in_ch, out_ch, 3, stride=2, padding=1),
                        nn.ReLU(inplace=True),
                    )
                )
            in_ch = out_ch

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Downsample image to latent representation."""
        return self.net(x)


class HourglassDecoder(nn.Module):
    """Hourglass decoder with configurable layers.

    Progressively upsamples spatial dimensions while decreasing channels.

    Args:
        out_channels: Number of output channels (typically 3 for RGB).
        channel_schedule: List of channels for each layer (should match encoder).
        use_batch_norm: Whether to use batch normalization (default: True).
    """

    def __init__(
        self,
        out_channels: int,
        channel_schedule: Sequence[int],
        use_batch_norm: bool = True,
    ) -> None:
        super().__init__()
        self.out_channels = out_channels
        self.channel_schedule = list(channel_schedule)
        self.use_batch_norm = use_batch_norm

        layers: list[nn.Module] = []

        # Build decoder layers (reverse of encoder schedule)
        in_ch = channel_schedule[0]
        for _i, out_ch in enumerate(channel_schedule[1:]):
            if use_batch_norm:
                layers.append(TransposedConvBlock(in_ch, out_ch, stride=2))
            else:
                layers.append(
                    nn.Sequential(
                        nn.ConvTranspose2d(
                            in_ch,
                            out_ch,
                            4,
                            stride=2,
                            padding=1,
                        ),
                        nn.ReLU(inplace=True),
                    )
                )
            in_ch = out_ch

        # Final layer to output channels
        layers.append(
            nn.ConvTranspose2d(
                in_ch,
                out_channels,
                4,
                stride=2,
                padding=1,
            )
        )
        layers.append(nn.Sigmoid())

        self.net = nn.Sequential(*layers)
        self.output_shape: tuple[int, ...] | None = None

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Upsample latent representation to reconstructed image."""
        return self.net(z)


class ConfigurableHourglassAutoencoder(nn.Module):
    """Flexible hourglass autoencoder for variable-size images.

    Automatically generates encoder/decoder layers based on input size
    and desired number of compression layers.

    Args:
        input_shape: Tuple of (channels, height, width).
        num_layers: Number of encoder/decoder layers (2-8).
        bottleneck_channels: Channels at bottleneck layer.
        base_channels: Starting number of channels (default: 32).
        use_batch_norm: Whether to use batch normalization (default: True).

    Attributes:
        bottleneck_shape: Tuple of (channels, height, width) at bottleneck.
        compression_ratio: Spatial compression ratio (original_h*w / bottleneck_h*w).

    Example:
        >>> # Standard 256x256 image with 4 layers
        >>> model = ConfigurableHourglassAutoencoder(
        ...     input_shape=(3, 256, 256), num_layers=4, bottleneck_channels=128
        ... )
        >>> x = torch.rand(2, 3, 256, 256)
        >>> x_hat = model(x)
        >>> latent = model.encode(x)  # [2, 128, 16, 16]

        >>> # Different camera resolutions
        >>> vga = ConfigurableHourglassAutoencoder((3, 480, 640), num_layers=3)
        >>> mp5 = ConfigurableHourglassAutoencoder((3, 2560, 1920), num_layers=5)
        >>> mp12 = ConfigurableHourglassAutoencoder((3, 4000, 3000), num_layers=6)
    """

    def __init__(
        self,
        input_shape: tuple[int, int, int],
        num_layers: int = 4,
        bottleneck_channels: int = 128,
        base_channels: int = 32,
        use_batch_norm: bool = True,
    ) -> None:
        super().__init__()

        if len(input_shape) != 3:
            msg = f"input_shape must be (C, H, W), got {input_shape}"
            raise ValueError(msg)

        in_channels, height, width = input_shape

        if height < (2**num_layers) or width < (2**num_layers):
            msg = (
                f"Image too small for {num_layers} layers. "
                f"Minimum size: {2**num_layers}x{2**num_layers}"
            )
            raise ValueError(msg)

        self.input_shape = input_shape
        self.num_layers = num_layers
        self.bottleneck_channels = bottleneck_channels
        self.base_channels = base_channels

        # Generate channel schedule
        channel_schedule = self._generate_channel_schedule(
            num_layers,
            base_channels,
            bottleneck_channels,
        )

        # Store dimensions for later use
        self.bottleneck_height = height // (2**num_layers)
        self.bottleneck_width = width // (2**num_layers)
        self.bottleneck_shape = (
            bottleneck_channels,
            self.bottleneck_height,
            self.bottleneck_width,
        )

        # Build encoder and decoder
        self.encoder = HourglassEncoder(
            in_channels,
            channel_schedule,
            use_batch_norm,
        )
        self.decoder = HourglassDecoder(
            in_channels,
            channel_schedule[::-1],
            use_batch_norm,
        )

    @staticmethod
    def _generate_channel_schedule(
        num_layers: int,
        base_channels: int,
        bottleneck_channels: int,
    ) -> list[int]:
        """Generate channel schedule for exponential growth.

        Args:
            num_layers: Number of layers.
            base_channels: Starting channels.
            bottleneck_channels: Target bottleneck channels.

        Returns:
            List of channels for each layer.
        """
        schedule = []
        for i in range(num_layers):
            channels = min(base_channels * (2**i), bottleneck_channels)
            schedule.append(channels)
        # Ensure last layer has bottleneck channels
        schedule[-1] = bottleneck_channels
        return schedule

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode and decode image through bottleneck.

        Args:
            x: Input image tensor [B, C, H, W].

        Returns:
            Reconstructed image tensor [B, C, H, W].
        """
        latent = self.encoder(x)
        return self.decoder(latent)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode image to latent representation.

        Args:
            x: Input image tensor [B, C, H, W].

        Returns:
            Latent tensor [B, C_bottleneck, H_bottleneck, W_bottleneck].
        """
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent representation to image.

        Args:
            z: Latent tensor [B, C_bottleneck, H_bottleneck, W_bottleneck].

        Returns:
            Reconstructed image [B, C, H, W].
        """
        return self.decoder(z)

    def get_compression_ratio(self) -> float:
        """Get spatial compression ratio.

        Ratio of original spatial size to bottleneck spatial size.

        Returns:
            Compression ratio (original_h * original_w / bottleneck_h / bottleneck_w).
        """
        _, h, w = self.input_shape
        _, bottleneck_h, bottleneck_w = self.bottleneck_shape
        input_size = h * w
        bottleneck_size = bottleneck_h * bottleneck_w
        if bottleneck_size == 0:
            return float("inf")
        return float(input_size / bottleneck_size)

    def get_config(self) -> dict[str, Any]:
        """Get model configuration dictionary.

        Returns:
            Configuration dict suitable for ConfigurableHourglassAutoencoder(**config).
        """
        return {
            "input_shape": self.input_shape,
            "num_layers": self.num_layers,
            "bottleneck_channels": self.bottleneck_channels,
            "base_channels": self.base_channels,
        }
