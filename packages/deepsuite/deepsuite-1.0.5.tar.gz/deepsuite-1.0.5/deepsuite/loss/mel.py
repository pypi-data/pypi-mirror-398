"""Mel-spectrum based RMSE loss.

This loss computes RMSE on perceptual Mel-spectral features for audio.

Author:
    Anton Feldmann
"""

import torch

from deepsuite.loss.rmse import RMSE
from deepsuite.utils.tsignal import perceptual_transform


class MelLoss(torch.nn.Module):
    """RMSE-based loss on Mel spectra.

    Args:
        mel_scales (tuple[int, ...]): Number of Mel filter banks.
        n_fft (int): FFT size.
        sample_rate (int): Audio sample rate.
        eps (float): Small epsilon for numerical stability.

    Example:
        .. code-block:: python

            loss_fn = MelLoss()
            y_true = torch.rand(10, 512)
            y_pred = torch.rand(10, 512)
            loss = loss_fn(y_true, y_pred)
    """

    def __init__(self, mel_scales=(16, 32, 64), n_fft=512, sample_rate=44_100, eps=1e-7) -> None:
        super().__init__()
        self.mel_scales = mel_scales
        self.n_fft = n_fft
        self.sample_rate = sample_rate
        self.eps = eps
        self.rmse_loss = RMSE(self.eps)

    def forward(self, y_true: torch.Tensor, y_pred: torch.Tensor) -> torch.Tensor:
        """Compute Mel-spectrum-based RMSE loss.

        Args:
            y_true (torch.Tensor): Ground truth audio.
            y_pred (torch.Tensor): Predicted audio.

        Returns:
            torch.Tensor: Scalar loss value.
        """
        # Mel-spectra features
        pvec_true = perceptual_transform(
            y_true, self.mel_scales, self.n_fft, self.sample_rate, self.eps
        )
        pvec_pred = perceptual_transform(
            y_pred, self.mel_scales, self.n_fft, self.sample_rate, self.eps
        )

        # RMSE across batch
        distances = self.rmse_loss(pvec_pred, pvec_true)

        # Mean over features and batch
        from typing import cast

        return cast("torch.Tensor", distances.mean())
