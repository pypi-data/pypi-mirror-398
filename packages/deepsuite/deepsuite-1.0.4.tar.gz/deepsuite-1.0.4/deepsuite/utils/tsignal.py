"""Signal processing utilities.

This module provides functions for signal processing,
such as converting between frequency and Mel scales,
creating Mel filter banks, and applying perceptual transformations to input data.

The `freq_to_mel` function converts frequency (Hz) to Mel scale.
The `mel_to_freq` function converts Mel scale to frequency (Hz).
The `hz_to_mel` function converts frequency (Hz) to Mel scale.
The `mel_to_hz` function converts Mel scale to frequency (Hz).
The `mel_filter_bank` function creates a Mel filter bank.
The `perceptual_transform` function applies perceptual transformation to input data.

Example:
    >>> freq = torch.tensor(440.0)
    >>> mel = freq_to_mel(freq)
    >>> freq = mel_to_freq(mel)

    >>> mel_filter_bank = mel_filter_bank(n_filters=40, n_fft=512, sample_rate=44_100)
    >>> transformed = perceptual_transform(x, mel_scales=[16, 32, 64],
                                              n_fft=512,
                                              sample_rate=44_100)
"""

import torch


def freq_to_mel(freq: torch.Tensor) -> torch.Tensor:
    """Convert frequency (Hz) to Mel scale.

    Args:
        freq (torch.Tensor): Frequency in Hz.

    Returns:
        torch.Tensor: Frequency in Mel scale.
    """
    return 1127.01048 * torch.log1p(freq / 700.0)


def mel_to_freq(mel: torch.Tensor) -> torch.Tensor:
    """Convert Mel scale to frequency (Hz).

    Args:
        mel (torch.Tensor): Frequency in Mel scale.

    Returns:
        torch.Tensor: Frequency in Hz.
    """
    return 700.0 * (torch.exp(mel / 1127.01048) - 1.0)


def hz_to_mel(hz: torch.Tensor) -> torch.Tensor:
    """Convert frequency (Hz) to Mel scale.

    Args:
        hz (torch.Tensor): Frequency in Hz.

    Returns:
        torch.Tensor: Frequency in Mel scale.

    Example:
        >>> hz = torch.tensor(440.0)
        >>> mel = hz_to_mel(hz)
    """
    return freq_to_mel(hz)


def mel_to_hz(mel: torch.Tensor) -> torch.Tensor:
    """Convert Mel scale to frequency (Hz).

    Args:
        mel (torch.Tensor): Frequency in Mel scale.

    Returns:
        torch.Tensor: Frequency in Hz.

    Example:
        >>> mel = torch.tensor(440.0)
        >>> freq = mel_to_hz(mel)
    """
    return mel_to_freq(mel)


def mel_filter_bank(
    n_filters: int, n_fft: int, sample_rate: int, fmin: float = 0.0, fmax: float | None = None
) -> torch.Tensor:
    """Create a Mel filter bank.

    Args:
        n_filters (int): Number of Mel filters.
        n_fft (int): Number of FFT points.
        sample_rate (int): Sample rate of the audio signal.
        fmin (float, optional): Minimum frequency in Hz. Default is 0.0.
        fmax (float, optional): Maximum frequency in Hz. Default is None.

    Returns:
        torch.Tensor: Mel filter bank with shape (n_filters, n_fft // 2 + 1).

    Example:
        >>> mel_filter_bank = mel_filter_bank(n_filters=40, n_fft=512, sample_rate=44_100)
    """
    assert n_fft % 2 == 0, "n_fft must be even"

    min_hz = fmin if fmin > 0 else 0.0
    max_hz = fmax if fmax else sample_rate / 2

    min_mel = hz_to_mel(torch.tensor(min_hz))
    max_mel = hz_to_mel(torch.tensor(max_hz))

    mel_points = torch.linspace(min_mel, max_mel, steps=n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = torch.floor((n_fft * hz_points) / max_hz).long()

    filter_bank = torch.zeros(n_filters, n_fft // 2 + 1)

    for i in range(1, n_filters + 1):
        start, peak, end = (
            int(bin_points[i - 1].item()),
            int(bin_points[i].item()),
            int(bin_points[i + 1].item()),
        )

        if peak > start:
            filter_bank[i - 1, start:peak] = (
                torch.arange(start, peak, dtype=torch.float32) - start
            ) / (peak - start)

        if end > peak:
            filter_bank[i - 1, peak:end] = (end - torch.arange(peak, end, dtype=torch.float32)) / (
                end - peak
            )

    return filter_bank


def perceptual_transform(
    x: torch.Tensor,
    mel_scales: tuple[int, int, int] = (16, 32, 64),
    n_fft: int = 512,
    sample_rate: int = 44_100,
    eps: float = 1e-7,
) -> torch.Tensor:
    """Apply perceptual transformation to input data.

    Args:
        x (torch.Tensor): Input tensor with shape (batch_size, n_fft).
        mel_scales (tuple, optional): Tuple of Mel scales. Default is (16, 32, 64).
        n_fft (int, optional): Number of FFT points. Default is 512.
        sample_rate (int, optional): Sample rate of the audio signal. Default is 44,100 Hz.
        eps (float, optional): Epsilon value for numerical stability. Default is 1e-7.

    Returns:
        torch.Tensor: Transformed tensor with shape (batch_size, n_fft // 2 + 1 * len(mel_scales)).

    Example:
        >>> x = torch.randn(1, 512)
        >>> transformed = perceptual_transform(x, mel_scales=[16, 32, 64], n_fft=512, sample_rate
        >>> transformed.shape
        torch.Size([1, 96])
    """
    assert mel_scales, "mel_scales must be specified"
    assert len(mel_scales) > 0, "mel_scales must have at least one value"

    mel_filter_banks = [mel_filter_bank(scale, n_fft, sample_rate) for scale in mel_scales]

    # Berechnung des Power-Spektrums
    power_spectrum = 1.0 / (x.view(-1, n_fft // 2 + 1) * n_fft)

    transformed = []
    for mfb in mel_filter_banks:
        filtered_spectrum = torch.matmul(power_spectrum, mfb)
        log_spectrum = torch.log(torch.clamp(filtered_spectrum, min=eps))
        transformed.append(log_spectrum)

    return torch.cat(transformed, dim=-1)
