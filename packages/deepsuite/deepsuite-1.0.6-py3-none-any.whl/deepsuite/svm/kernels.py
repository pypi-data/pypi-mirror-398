"""Kernels for various machine learning tasks.

This module provides implementations of various kernel functions
commonly used in machine learning, particularly in support vector
machines and other kernelized algorithms. The kernels included are:
- Linear Kernel
- RBF Kernel (Gaussian Kernel)
- Polynomial Kernel
- Sigmoid Kernel
- Laplacian Kernel
- Chi-squared Kernel
- Histogram Intersection Kernel
- Gaussian Kernel
- Cosine Kernel

Each kernel function computes a kernel matrix between two sets of
vectors, which can be used to measure similarity in a high-dimensional
space. The kernels are implemented using PyTorch for efficient
computation on both CPU and GPU. The functions are designed to be
compatible with PyTorch tensors and can handle batches of data.
The kernels are defined mathematically as follows:
- Linear Kernel: K(x, x') = x · x'
- RBF Kernel: K(x, x') = exp(-gamma * ||x - x'||^2)
- Polynomial Kernel: K(x, x') = (gamma * x^T x' + coef0)^degree
- Sigmoid Kernel: K(x, x') = tanh(gamma * x^T x' + coef0)
- Laplacian Kernel: K(x, x') = exp(-gamma * ||x - x'||_1)
- Chi-squared Kernel: K(x, x') = exp(-Σ[(x - x')^2 / (x + x' + ε)])
- Histogram Intersection Kernel: K(x, x') = Σ min(x_i, x'_i)
- Gaussian Kernel: K(x, x') = exp(-sum((x_i - x'_i)^2) / (2 * sigma^2))
- Cosine Kernel: K(x, x') = (x · x') / (||x|| * ||x'||)

"""

import torch


def linear_kernel(x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """Compute the linear kernel between two sets of vectors.

    $$  K(x, x') = x · x'

    Parameters
    ----------
    x1 : torch.Tensor
        Tensor of shape (n_samples_1, n_features).
    x2 : torch.Tensor
        Tensor of shape (n_samples_2, n_features).

    Returns:
    -------
    torch.Tensor
        Kernel matrix of shape (n_samples_1, n_samples_2).
    """
    return x1 @ x2.T


def rbf_kernel(x1: torch.Tensor, x2: torch.Tensor, gamma: float = 1.0) -> torch.Tensor:
    """Compute the RBF (Gaussian) kernel between two sets of vectors using gamma.

    $$  K(x, x') = exp(-gamma * ||x - x'||^2)

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors of shape (n_samples, n_features).
    gamma : float
        Kernel coefficient (inverse length-scale).

    Returns:
    -------
    torch.Tensor
        Kernel matrix of shape (n_samples_1, n_samples_2).
    """
    x1_sq = torch.sum(x1**2, dim=1, keepdim=True)
    x2_sq = torch.sum(x2**2, dim=1).unsqueeze(0)
    dist_sq = x1_sq + x2_sq - 2 * (x1 @ x2.T)
    dist_sq = torch.clamp(dist_sq, min=0.0)
    return torch.exp(-gamma * dist_sq)


def polynomial_kernel(
    x1: torch.Tensor, x2: torch.Tensor, degree: int = 3, gamma: float = 1.0, coef0: float = 1.0
) -> torch.Tensor:
    """Compute the polynomial kernel.

    $$  K(x, x') = (gamma * x^T x' + coef0)^degree

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors of shape (n_samples, n_features).
    degree : int
        Degree of the polynomial.
    gamma : float
        Kernel coefficient.
    coef0 : float
        Independent term.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    return (gamma * x1 @ x2.T + coef0) ** degree


def sigmoid_kernel(
    x1: torch.Tensor, x2: torch.Tensor, gamma: float = 1.0, coef0: float = 0.0
) -> torch.Tensor:
    """Compute the sigmoid (tanh) kernel.

    $$ K(x, x') = tanh(gamma * x^T x' + coef0)

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors.
    gamma : float
        Slope parameter.
    coef0 : float
        Offset parameter.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    return torch.tanh(gamma * x1 @ x2.T + coef0)


def laplacian_kernel(x1: torch.Tensor, x2: torch.Tensor, gamma: float = 1.0) -> torch.Tensor:
    """Compute the Laplacian kernel using L1 distance.

    $$  K(x, x') = exp(-gamma * ||x - x'||_1)

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors.
    gamma : float
        Kernel coefficient.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    x1 = x1.unsqueeze(1)
    x2 = x2.unsqueeze(0)
    return torch.exp(-gamma * torch.sum(torch.abs(x1 - x2), dim=2))


def chi2_kernel(x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """Compute the Chi-squared kernel, often used for histogram data.

    $$ K(x, x') = exp(-Σ[(x - x')^2 / (x + x' + ε)])

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors with all elements ≥ 0.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    x1 = x1.unsqueeze(1)
    x2 = x2.unsqueeze(0)
    return torch.exp(-torch.sum((x1 - x2) ** 2 / (x1 + x2 + 1e-10), dim=2))


def histogram_intersection_kernel(x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """Compute the histogram intersection kernel.

    $$ K(x, x') = Σ min(x_i, x'_i)

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors with non-negative values.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    x1 = x1.unsqueeze(1)
    x2 = x2.unsqueeze(0)
    return torch.sum(torch.min(x1, x2), dim=2)


def gaussian_kernel(x1: torch.Tensor, x2: torch.Tensor, sigma: float = 1.0) -> torch.Tensor:
    """Compute the Gaussian kernel using sigma.

    Equivalent to RBF kernel with gamma = 1 / (2 * sigma^2)


    $$  K(x, x') = exp(-sum((x_i - x'_i)^2) / (2 * sigma^2))

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors.
    sigma : float
        Standard deviation.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    x1 = x1.unsqueeze(1)
    x2 = x2.unsqueeze(0)
    return torch.exp(-torch.sum((x1 - x2) ** 2, dim=2) / (2 * sigma**2))


def cosine_kernel(x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """Compute the cosine similarity kernel.

    $$  K(x, x') = (x · x') / (||x|| * ||x'||)

    Parameters
    ----------
    x1, x2 : torch.Tensor
        Input tensors.

    Returns:
    -------
    torch.Tensor
        Kernel matrix.
    """
    x1_norm = x1 / (x1.norm(dim=1, keepdim=True) + 1e-10)
    x2_norm = x2 / (x2.norm(dim=1, keepdim=True) + 1e-10)
    return x1_norm @ x2_norm.T
