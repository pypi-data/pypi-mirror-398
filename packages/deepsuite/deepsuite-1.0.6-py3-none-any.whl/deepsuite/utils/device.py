"""Device selection utilities (TPU/XLA, CUDA, MPS, CPU)."""

import torch

# Optional TPU/XLA support
try:  # pragma: no cover - optional dependency
    import torch_xla.core.xla_model as xm  # type: ignore
except Exception:
    xm = None  # type: ignore

DEVICE: torch.device | None = None


def get_best_device(force: str | None = None) -> torch.device:
    """Selects the best available device: TPU (XLA) > CUDA > MPS > CPU.

    Args:
        force (str): Optional override ("xla", "cuda", "mps", "cpu")

    Returns:
        torch.device: The selected device
    """
    global DEVICE  # noqa: PLW0603

    if force:
        DEVICE = torch.device(force)
        return DEVICE

    if DEVICE:
        return DEVICE

    # 1. Try TPU/XLA
    if xm is not None:
        DEVICE = xm.xla_device()  # type: ignore[attr-defined]
        return DEVICE

    # 2. Try CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        DEVICE = torch.device("cuda")
    # 3. Try MPS (Apple Silicon GPU)
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        DEVICE = torch.device("mps")
    # 4. Fallback: CPU
    else:
        DEVICE = torch.device("cpu")

    return DEVICE


def set_device(device_str: str) -> None:
    """Set device manually (e.g., 'cuda', 'cpu')."""
    global DEVICE  # noqa: PLW0603
    DEVICE = torch.device(device_str)


def reset_device() -> None:
    """Reset device selection (triggers re-detection)."""
    global DEVICE  # noqa: PLW0603
    DEVICE = None


def is_tpu() -> bool:
    """Return True if the current device is a TPU/XLA device."""
    return str(get_best_device()).startswith("xla")
