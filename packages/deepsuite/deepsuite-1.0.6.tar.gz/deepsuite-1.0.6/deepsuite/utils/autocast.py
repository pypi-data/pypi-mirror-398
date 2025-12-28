"""Automatic mixed precision utilities.

Provides a unified interface for PyTorch's autocast functionality, enabling
mixed precision training to improve performance and reduce memory usage.
"""

from typing import Any

import torch


def autocast(enable: bool = True, device: str = "cuda") -> Any:
    """Create an autocast context manager for mixed precision operations.

    Wraps PyTorch's automatic mixed precision (AMP) context manager to enable
    or disable mixed precision computation. When enabled, operations are
    automatically cast to lower precision (e.g., float16) where safe,
    improving performance and reducing memory usage.

    Args:
        enable: Whether to enable mixed precision. If False, operations run
            in their default precision. Defaults to True.
        device: Device type for autocast. Common values:
            - "cuda": NVIDIA GPU with float16 (default)
            - "cpu": CPU with bfloat16 (if supported)
            - "mps": Apple Silicon with float16
            Defaults to "cuda".

    Returns:
        Context manager that enables/disables automatic mixed precision
        for operations within its scope.

    Note:
        - On CUDA devices, autocast uses float16 for eligible operations
        - On CPU (with compatible hardware), autocast uses bfloat16
        - Not all operations benefit from mixed precision; some maintain float32
        - Gradient scaling is typically needed with autocast for training stability

    Examples:
        >>> # Basic usage with autocast enabled
        >>> with autocast(enable=True, device="cuda"):
        ...     output = model(input_tensor)
        ...     loss = criterion(output, target)
        ...     # Operations inside use mixed precision

        >>> # Disable autocast for specific operations
        >>> with autocast(enable=False):
        ...     high_precision_result = sensitive_operation(data)

        >>> # Typical training loop with gradient scaling
        >>> scaler = torch.cuda.amp.GradScaler()
        >>> for inputs, targets in dataloader:
        ...     with autocast(enable=True, device="cuda"):
        ...         outputs = model(inputs)
        ...         loss = criterion(outputs, targets)
        ...     scaler.scale(loss).backward()
        ...     scaler.step(optimizer)
        ...     scaler.update()

        >>> # CPU autocast (requires bfloat16 support)
        >>> with autocast(enable=True, device="cpu"):
        ...     output = model(input_tensor)
    """
    return torch.amp.autocast(device_type=device, enabled=enable)
