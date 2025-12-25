"""Device module."""

import torch

DEVICE = None


def get_best_device(force: str = None) -> torch.device:
    """Selects the best available device: TPU (XLA) > CUDA > MPS > CPU.

    Args:
        force (str): Optional override ("xla", "cuda", "mps", "cpu")

    Returns:
        torch.device: The selected device
    """
    global DEVICE

    if force:
        DEVICE = torch.device(force)
        return DEVICE

    if DEVICE:
        return DEVICE

    # 1. Try TPU/XLA
    try:
        import torch_xla.core.xla_model as xm

        DEVICE = xm.xla_device()
        return DEVICE
    except ImportError:
        pass  # torch_xla not available

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


def set_device(device_str: str):
    """Manuell Gerät setzen (z.B. 'cuda', 'cpu')."""
    global DEVICE
    DEVICE = torch.device(device_str)


def reset_device():
    """Gerätewahl zurücksetzen (für Neu-Erkennung)."""
    global DEVICE
    DEVICE = None


def is_tpu():
    """Gibt True zurück, wenn aktuelles Gerät eine TPU ist."""
    return str(get_best_device()).startswith("xla")
