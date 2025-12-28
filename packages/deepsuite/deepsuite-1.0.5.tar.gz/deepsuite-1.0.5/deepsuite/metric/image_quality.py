"""Image quality metrics for reconstruction and compression tasks.

Provides PSNR, SSIM, MS-SSIM, and LPIPS metrics commonly used in
image-to-image translation, compression, and autoencoder evaluation.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def psnr(pred: torch.Tensor, target: torch.Tensor, max_val: float = 1.0) -> torch.Tensor:
    """Compute Peak Signal-to-Noise Ratio (PSNR).

    Args:
        pred: Predicted image tensor [B, C, H, W] or [C, H, W].
        target: Target image tensor with same shape as pred.
        max_val: Maximum possible pixel value (1.0 for normalized images).

    Returns:
        torch.Tensor: PSNR value in dB (scalar).

    Example:
        >>> pred = torch.rand(1, 3, 256, 256)
        >>> target = torch.rand(1, 3, 256, 256)
        >>> psnr_val = psnr(pred, target)
    """
    mse = F.mse_loss(pred, target)
    if mse == 0:
        return torch.tensor(float("inf"))
    return 20 * torch.log10(torch.tensor(max_val)) - 10 * torch.log10(mse)


def ssim(
    pred: torch.Tensor,
    target: torch.Tensor,
    window_size: int = 11,
    sigma: float = 1.5,
    data_range: float = 1.0,
    K1: float = 0.01,
    K2: float = 0.03,
) -> torch.Tensor:
    """Compute Structural Similarity Index (SSIM).

    Args:
        pred: Predicted image [B, C, H, W].
        target: Target image [B, C, H, W].
        window_size: Size of Gaussian window.
        sigma: Standard deviation of Gaussian kernel.
        data_range: Value range of input (1.0 for normalized images).
        K1: Algorithm stability constant (default 0.01).
        K2: Algorithm stability constant (default 0.03).

    Returns:
        torch.Tensor: Mean SSIM value (scalar).

    Example:
        >>> pred = torch.rand(2, 3, 256, 256)
        >>> target = torch.rand(2, 3, 256, 256)
        >>> ssim_val = ssim(pred, target)
    """
    C1 = (K1 * data_range) ** 2
    C2 = (K2 * data_range) ** 2

    # Create Gaussian window
    coords = torch.arange(window_size, dtype=pred.dtype, device=pred.device)
    coords -= window_size // 2
    g = torch.exp(-(coords**2) / (2 * sigma**2))
    g /= g.sum()
    window = g.unsqueeze(0) * g.unsqueeze(1)
    window = window.unsqueeze(0).unsqueeze(0)  # [1, 1, K, K]
    window = window.expand(pred.size(1), 1, window_size, window_size).contiguous()

    # Compute means
    mu1 = F.conv2d(pred, window, padding=window_size // 2, groups=pred.size(1))
    mu2 = F.conv2d(target, window, padding=window_size // 2, groups=target.size(1))

    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2

    # Compute variances and covariance
    sigma1_sq = (
        F.conv2d(pred * pred, window, padding=window_size // 2, groups=pred.size(1)) - mu1_sq
    )
    sigma2_sq = (
        F.conv2d(target * target, window, padding=window_size // 2, groups=target.size(1)) - mu2_sq
    )
    sigma12 = (
        F.conv2d(pred * target, window, padding=window_size // 2, groups=pred.size(1)) - mu1_mu2
    )

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    )

    return ssim_map.mean()


def ms_ssim(
    pred: torch.Tensor,
    target: torch.Tensor,
    window_size: int = 11,
    sigma: float = 1.5,
    data_range: float = 1.0,
    weights: list[float] | None = None,
) -> torch.Tensor:
    """Compute Multi-Scale Structural Similarity Index (MS-SSIM).

    Args:
        pred: Predicted image [B, C, H, W].
        target: Target image [B, C, H, W].
        window_size: Size of Gaussian window.
        sigma: Standard deviation of Gaussian kernel.
        data_range: Value range of input.
        weights: Scale weights (default: [0.0448, 0.2856, 0.3001, 0.2363, 0.1333]).

    Returns:
        torch.Tensor: MS-SSIM value (scalar).

    Example:
        >>> pred = torch.rand(2, 3, 256, 256)
        >>> target = torch.rand(2, 3, 256, 256)
        >>> ms_ssim_val = ms_ssim(pred, target)
    """
    if weights is None:
        weights = [0.0448, 0.2856, 0.3001, 0.2363, 0.1333]

    levels = len(weights)
    mssim = []

    for _ in range(levels):
        ssim_val = ssim(pred, target, window_size, sigma, data_range)
        mssim.append(ssim_val)

        # Downsample for next scale
        pred = F.avg_pool2d(pred, kernel_size=2, stride=2)
        target = F.avg_pool2d(target, kernel_size=2, stride=2)

    # Combine scales
    mssim_tensor = torch.stack(mssim)
    weights_tensor = torch.tensor(weights, device=pred.device)
    return (mssim_tensor**weights_tensor).prod()
