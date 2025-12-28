"""Hermite module."""

import torch

r"""Hermite-Polynome.

Die Hermite-Polynome sind eine Familie von orthogonalen Polynomen, die in der Quantenmechanik und der Wahrscheinlichkeitstheorie verwendet werden. Sie sind definiert durch die Rekursionsformel

.. math::
    H_n(x) = 2x H_{n-1}(x) - 2(n-1) H_{n-2}(x)

mit den Anfangsbedingungen H_0(x) = 1 und H_1(x) = 2x. Die Hermite-Polynome können auch durch die explizite Formel

.. math::
    H_n(x) = (-1)^n e^{x^2} \\frac{d^n}{dx^n} e^{-x^2}

berechnet werden
"""


def hermite(n: int, x: torch.Tensor) -> torch.Tensor:
    """Berechnet die Hermite-Polynome H_n(x) iterativ.

    .. math::
        H_n(x) = 2x H_{n-1}(x) - 2(n-1) H_{n-2}(x)

    Args:
        n (int): Ordnung des Hermite-Polynoms (n >= 0).
        x (torch.Tensor): Eingabewerte (muss ein Tensor sein).

    Returns:
        torch.Tensor: Berechnete Hermite-Polynome.

    Raises:
        TypeError: Falls `x` kein Tensor ist.
        ValueError: Falls `n` negativ.

    Examples:
        >>> x = torch.tensor([0.0, 1.0, 2.0])
        >>> hermite(2, x)
        tensor([-2.,  2.,  8.])
    """
    if not isinstance(x, torch.Tensor):
        raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

    if n < 0:
        raise ValueError(f"Order n must be non-negative, but got n={n}")

    if n == 0:
        return torch.ones_like(x)
    if n == 1:
        return 2 * x

    # Initialisierung von H_0(x) und H_1(x)
    h_prev = torch.ones_like(x)  # H_0(x) = 1
    h_curr = 2 * x  # H_1(x) = 2x

    # Iterative Berechnung für H_n(x)
    for i in range(2, n + 1):
        h_next = 2 * x * h_curr - 2 * (i - 1) * h_prev
        h_prev, h_curr = h_curr, h_next  # Werte für nächsten Durchlauf verschieben

    return h_curr
