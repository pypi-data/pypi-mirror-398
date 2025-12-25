"""Autoencoder models for latent representation learning.

Provides encoder-decoder architectures for image compression,
feature extraction, and dimensionality reduction tasks.
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import pytorch_lightning as pl

from deepsuite.lightning_base import BaseModule


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

    def __init__(self, in_channels: int = 3, z_channels: int = 128, depth: int = 4) -> None:
        super().__init__()
        channels = [in_channels] + [32 * (2**i) for i in range(depth - 1)] + [z_channels]
        layers = []
        for i in range(depth):
            layers.extend([
                nn.Conv2d(channels[i], channels[i + 1], 3, stride=2, padding=1),
                nn.ReLU(inplace=True),
            ])
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
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

    def __init__(self, z_channels: int = 128, out_channels: int = 3, depth: int = 4) -> None:
        super().__init__()
        channels = [z_channels] + [128 // (2**i) for i in range(depth - 1)] + [out_channels]
        layers = []
        for i in range(depth - 1):
            layers.extend([
                nn.ConvTranspose2d(channels[i], channels[i + 1], 4, stride=2, padding=1),
                nn.ReLU(inplace=True),
            ])
        # Final layer without ReLU, use Sigmoid for [0,1] range
        layers.append(nn.ConvTranspose2d(channels[-2], channels[-1], 4, stride=2, padding=1))
        layers.append(nn.Sigmoid())
        self.net = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
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
        if loss_fn is None:
            self.loss_fn = nn.MSELoss()
        else:
            self.loss_fn = loss_fn

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        x_hat = self.decoder(z)
        return x_hat

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:  # type: ignore[override]
        if isinstance(batch, (tuple, list)):
            x = batch[0]
        else:
            x = batch
        x_hat = self(x)
        loss = self.loss_fn(x_hat, x)
        self.log("train/loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch: Any, batch_idx: int) -> torch.Tensor:  # type: ignore[override]
        if isinstance(batch, (tuple, list)):
            x = batch[0]
        else:
            x = batch
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

    def configure_optimizers(self) -> torch.optim.Optimizer:  # type: ignore[override]
        return torch.optim.Adam(self.parameters(), lr=self.lr)
