"""Mel-Spektrum-basierter RMSE-Verlust.

Author:
    Anton Feldmann

"""

import torch

from deepsuite.loss.rmse import RMSE
from deepsuite.utils.tsignal import perceptual_transform


class MelLoss(torch.nn.Module):
    """Verlustfunktion für Mel-Spektren basierend auf RMSE.

    Args:
        mel_scales (tuple): Anzahl der Mel-Filterbänke.
        n_fft (int): FFT-Größe.
        sample_rate (int): Abtastrate des Audios.
        eps (float): Kleiner Wert für numerische Stabilität.

    Examples:
        >>> loss_fn = MelLoss()
        >>> y_true = torch.rand(10, 512)  # Simulierte Audiodaten
        >>> y_pred = torch.rand(10, 512)  # Vorhersagen
        >>> loss = loss_fn(y_true, y_pred)
        >>> loss
        tensor(0.2321)
    """

    def __init__(self, mel_scales=(16, 32, 64), n_fft=512, sample_rate=44_100, eps=1e-7):
        super().__init__()
        self.mel_scales = mel_scales
        self.n_fft = n_fft
        self.sample_rate = sample_rate
        self.eps = eps
        self.rmse_loss = RMSE(self.eps)

    def forward(self, y_true: torch.Tensor, y_pred: torch.Tensor) -> torch.Tensor:
        """Berechnet den Mel-Spektrum-basierten RMSE-Loss.

        Args:
            y_true (torch.Tensor): Wahre Audiodaten.
            y_pred (torch.Tensor): Vorhergesagte Audiodaten.

        Returns:
            torch.Tensor: Skalarer Loss-Wert.
        """
        # Mel-Spektren berechnen
        pvec_true = perceptual_transform(
            y_true, self.mel_scales, self.n_fft, self.sample_rate, self.eps
        )
        pvec_pred = perceptual_transform(
            y_pred, self.mel_scales, self.n_fft, self.sample_rate, self.eps
        )

        # Direkt RMSE auf gesamte Batch anwenden (ohne Schleife)
        distances = self.rmse_loss(pvec_pred, pvec_true)

        # Mittelwert über alle Features und Batch berechnen
        return distances.mean()
