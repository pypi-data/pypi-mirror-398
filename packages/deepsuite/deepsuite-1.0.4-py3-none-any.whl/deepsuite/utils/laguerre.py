"""Laguerre-Polynome.

Die Laguerre-Polynome sind eine Familie von orthogonalen Polynomen, die in der Quantenmechanik und der Wahrscheinlichkeitstheorie verwendet werden. Sie sind definiert durch die Rekursionsformel

L_n(x) = (2n-1-x) L_{n-1}(x) - (n-1) L_{n-2}(x) / n

mit den Anfangsbedingungen L_0(x) = 1 und L_1(x) = 1-x. Die Laguerre-Polynome können auch durch die explizite Formel

L_n(x) = sum_{k=0}^n binom{n}{k} (-1)^k x^k / k!

berechnet werden

"""

import torch


def laguerre(n: int, x: torch.Tensor) -> torch.Tensor:
    r"""Berechnet die Laguerre-Polynome L_n(x) iterativ.

    .. math::
        L_n(x) = \\sum_{k=0}^n  \\binom{n}{k} \\frac{(-1)^k x^k}{k!}

    Args:
        n (int): Ordnung des Laguerre-Polynoms (n >= 0).
        x (torch.Tensor): Eingabewerte (muss ein Tensor sein).

    Returns:
        torch.Tensor: Berechnete Laguerre-Polynome.

    Raises:
        TypeError: Falls `x` kein Tensor ist.
        ValueError: Falls `n` negativ ist.

    Examples:
        >>> x = torch.tensor([0.0, 1.0, 2.0])
        >>> laguerre(2, x)
        tensor([ 1.,  0., -0.5])
    """
    if not isinstance(x, torch.Tensor):
        raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

    if n < 0:
        raise ValueError(f"Order n must be non-negative, but got n={n}")

    if n == 0:
        return torch.ones_like(x)
    if n == 1:
        return 1 - x

    # Initialisierung von L_0(x) und L_1(x)
    l_prev = torch.ones_like(x)  # L_0(x) = 1
    l_curr = 1 - x  # L_1(x) = 1 - x

    # Iterative Berechnung für L_n(x)
    for i in range(2, n + 1):
        l_next = ((2 * i - 1 - x) * l_curr - (i - 1) * l_prev) / i
        l_prev, l_curr = l_curr, l_next  # Werte für nächsten Durchlauf verschieben

    return l_curr
