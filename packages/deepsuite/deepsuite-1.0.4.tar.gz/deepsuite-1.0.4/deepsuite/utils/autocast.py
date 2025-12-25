"""Autocast module."""

from typing import Any

import torch


def autocast(enable: bool = True, device: str = "cuda") -> Any:
    """Context manager to enable/disable autocast."""
    return torch.amp.autocast(device_type=device, enabled=enable)
