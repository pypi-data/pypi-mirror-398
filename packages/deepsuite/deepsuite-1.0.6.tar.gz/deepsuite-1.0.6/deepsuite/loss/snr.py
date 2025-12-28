"""Signal-to-Noise Ratio (SNR) und verwandte Metriken.

Die SNR-Metriken sind nützlich, um die Qualität von Audiosignalen zu bewerten.
"""

import torch
from torch import Tensor

from deepsuite.metric.norm import l2_norm


class Signal2NoiseRatio(torch.nn.Module):
    """Signal-to-Distortion Ratio (SDR).

    Args:
        y_true: Wahres Signal.
        y_pred: Vorhergesagtes Signal.
        eps: Kleiner Wert zur Vermeidung von Division durch Null.

    Returns:
        SDR-Wert (Tensor)
    """

    def __init__(self, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, y_true: Tensor, y_pred: Tensor) -> Tensor:
        signal_norm = l2_norm(y_true, y_pred, epsilon=self.eps)
        noise_norm = l2_norm(y_true - y_pred, y_true - y_pred, epsilon=self.eps).square()
        sdr_value = 10 * torch.log10(signal_norm**2 / (noise_norm + self.eps))
        return torch.mean(sdr_value)


class ScaleInvariantSignal2NoiseRatio(torch.nn.Module):
    """Scale-Invariant Signal-to-Noise Ratio (SI-SNR).

    Args:
        y_true: Wahres Signal.
        y_pred: Vorhergesagtes Signal.
        eps: Kleiner Wert zur Vermeidung von Division durch Null.

    Returns:
        SI-SNR-Wert (Tensor)
    """

    def __init__(self, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, y_true: Tensor, y_pred: Tensor) -> torch.Tensor:
        s1_s2_norm = l2_norm(y_true, y_pred, epsilon=self.eps)
        s2_s2_norm = l2_norm(y_pred, y_pred, epsilon=self.eps)

        s_target = (s1_s2_norm / (s2_s2_norm + self.eps)) * y_pred
        e_noise = y_true - s_target

        target_norm = l2_norm(s_target, s_target, epsilon=self.eps)
        noise_norm = l2_norm(e_noise, e_noise, epsilon=self.eps)

        si_snr_value = 10 * torch.log10(target_norm / (noise_norm + self.eps))
        return torch.mean(si_snr_value)


class ScaleInvariantSignal2DistortionRatio(torch.nn.Module):
    """Scale-Invariant Signal-to-Distortion Ratio (SI-SDR).

    Args:
        y_true: Wahres Signal.
        y_pred: Vorhergesagtes Signal.
        eps: Kleiner Wert zur Vermeidung von Division durch Null.

    Returns:
        SI-SDR-Wert (Tensor)
    """

    def __init__(self, eps: float = 1e-8) -> None:
        self.eps = eps

    def forward(self, y_true: Tensor, y_pred: Tensor) -> Tensor:
        true_energy = torch.sum(y_true**2, dim=-1, keepdim=True)
        optimal_scaling = torch.sum(y_true * y_pred, dim=-1, keepdim=True) / (
            true_energy + self.eps
        )

        projection = optimal_scaling * y_true
        noise = y_pred - projection

        ratio = torch.sum(projection**2, dim=-1, keepdim=True) / (
            torch.sum(noise**2, dim=-1, keepdim=True) + self.eps
        )
        si_sdr_value = 10 * torch.log10(ratio + self.eps)

        return torch.mean(si_sdr_value)
