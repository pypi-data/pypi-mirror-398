"""This module provides a function to calculate the norm of two vectors.

The `l2_norm` function calculates the L2 norm of the difference between two vectors.
The function takes two arguments, `a` and `b`, which are the two vectors.
It calculates the L2 norm by taking the dot product of the two vectors and taking the square root of the result.
The function returns the L2 norm of the difference between the two vectors.
"""

import torch


def l2_norm(a: torch.Tensor, b: torch.Tensor, epsilon: float = 1e-8) -> torch.Tensor:
    """Calculate the L2 norm of the difference between two vectors.

    Args:
        a (torch.Tensor): First vector.
        b (torch.Tensor): Second vector.

    Returns:
        torch.Tensor: L2 norm of the difference between the
    """
    return torch.sqrt(torch.sum(a * b, dim=-1, keepdim=True) + epsilon)
