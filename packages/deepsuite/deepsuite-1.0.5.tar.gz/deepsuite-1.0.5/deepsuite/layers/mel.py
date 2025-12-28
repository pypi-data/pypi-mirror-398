"""Audio models for acoustic classification and synthesis.

Includes mel-spectrogram feature extraction, CNN backbones, and multi-task
audio classification modules for applications like animal vocalization analysis.
"""

import numpy as np
import torch
from torch import nn


class MelSpectrogramExtractor(nn.Module):
    """Extract Mel-spectrogram features from raw audio.

    Uses librosa-compatible mel-scale filterbank computation for acoustic
    feature extraction from waveforms.

    Args:
        sample_rate: Audio sample rate in Hz. Default: 16000.
        n_mels: Number of mel bands. Default: 64.
        n_fft: FFT window size. Default: 400.
        hop_length: Hop length for STFT. Default: 160.
        f_min: Minimum frequency in Hz. Default: 50.
        f_max: Maximum frequency in Hz. Default: 8000.

    Attributes:
        mel_fb: Registered buffer for mel filterbank matrix.

    Example:
        >>> extractor = MelSpectrogramExtractor(sample_rate=16000)
        >>> waveform = torch.randn(1, 16000)  # 1 second at 16kHz
        >>> mel = extractor(waveform)  # [1, 64, time_frames]
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        n_mels: int = 64,
        n_fft: int = 400,
        hop_length: int = 160,
        f_min: int = 50,
        f_max: int = 8000,
    ) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.f_min = f_min
        self.f_max = f_max

        mel_fb = torch.from_numpy(self._mel_scale(sample_rate, n_fft, n_mels, f_min, f_max)).float()
        self.register_buffer("mel_fb", mel_fb)

    @staticmethod
    def _mel_scale(sr: int, n_fft: int, n_mels: int, f_min: float, f_max: float) -> np.ndarray:
        """Compute mel filterbank (librosa-compatible).

        Args:
            sr: Sample rate in Hz.
            n_fft: FFT window size.
            n_mels: Number of mel bands.
            f_min: Minimum frequency.
            f_max: Maximum frequency.

        Returns:
            Mel filterbank matrix of shape (n_mels, n_fft // 2 + 1).
        """

        def hz_to_mel(f: float) -> float:
            return 2595 * np.log10(1 + f / 700)

        def mel_to_hz(m: float) -> float:
            return 700 * (10 ** (m / 2595) - 1)

        mel_f = np.linspace(hz_to_mel(f_min), hz_to_mel(f_max), n_mels + 2)
        hz_f = mel_to_hz(mel_f)
        bin_hz = np.linspace(0, sr / 2, n_fft // 2 + 1)

        fb = np.zeros((n_mels, n_fft // 2 + 1))
        for m in range(1, n_mels + 1):
            f_m_left = hz_f[m - 1]
            f_m = hz_f[m]
            f_m_right = hz_f[m + 1]

            for k in range(n_fft // 2 + 1):
                if bin_hz[k] < f_m_left or bin_hz[k] > f_m_right:
                    continue
                if bin_hz[k] < f_m:
                    fb[m - 1, k] = (bin_hz[k] - f_m_left) / (f_m - f_m_left)
                else:
                    fb[m - 1, k] = (f_m_right - bin_hz[k]) / (f_m_right - f_m)

        return fb

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        """Compute Mel-spectrogram from raw audio.

        Args:
            waveform: Audio tensor of shape [B, time_steps] or [time_steps].

        Returns:
            Mel-spectrogram of shape [B, n_mels, time_frames].
        """
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        stft = torch.stft(
            waveform,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            return_complex=False,
        )
        spec = stft[..., 0] ** 2 + stft[..., 1] ** 2  # [B, freq, time]
        # Project to mel bands: [n_mels, freq] × [B, freq, time] -> [B, n_mels, time]
        mel = torch.einsum("mf,bft->bmt", self.mel_fb, spec)
        return torch.log(torch.clamp(mel, min=1e-9))
