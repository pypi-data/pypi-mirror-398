"""Laguerre module."""

r"""Dieses Modul enthält eine PyTorch-Layer-Klasse, die Laguerre-Polynome auf die Eingabe anwendet.

Die Klasse `LaguerreLayer` ist ein PyTorch-Modul, das die Laguerre-Polynome auf die Eingabe anwendet.
Die Laguerre-Polynome sind eine Familie von orthogonalen Polynomen, die in der Quantenmechanik und der Wahrscheinlichkeitstheorie verwendet werden.

Sie sind definiert durch die Rekursionsformel:

.. math::
    L_n(x) = \frac{(2n-1-x) L_{n-1}(x) - (n-1) L_{n-2}(x)}{n}

mit den Anfangsbedingungen :math:`L_0(x) = 1` und :math:`L_1(x) = 1-x`.

Die explizite Formel lautet:

.. math::
    L_n(x) = \\sum_{k=0}^n  \binom{n}{k} \frac{(-1)^k x^k}{k!}
"""

import torch
from torch import nn

from deepsuite.utils.laguerre import laguerre


class LaguerreLayer(nn.Module):
    """PyTorch-Modul, das die Laguerre-Polynome auf die Eingabe anwendet.

    Args:
        max_order (int): Die maximale Ordnung der Laguerre-Polynome.

    Attributes:
        max_order (int): Die maximale Ordnung der Laguerre-Polynome.

    Examples:
        >>> import torch
        >>> from deepsuite.layers.laguerre import LaguerreLayer
        >>> laguerre_layer = LaguerreLayer(max_order=3)
        >>> x = torch.tensor([0.0, 1.0, 2.0])
        >>> laguerre_layer(x)
        tensor([[1.0000, 0.0000, 0.0000, 0.0000],
                [1.0000, 1.0000, 0.0000, 0.0000],
                 [1.0000, 2.0000, 2.0000, 0.0000]])
    """

    def __init__(self, max_order: int) -> None:
        super().__init__()
        self.max_order = max_order

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Wendet die Laguerre-Polynome auf die Eingabe an.

        Args:
            x (torch.Tensor): Eingabe-Tensor (1D), auf die die Laguerre-Polynome angewendet werden.

        Returns:
            torch.Tensor: Tensor mit den berechneten Laguerre-Polynomen.

        Raises:
            TypeError: Wenn `x` kein `torch.Tensor` ist.
            AssertionError: Wenn `x` keine 1D-Form hat.

        Examples:
            >>> import torch
            >>> from deepsuite.layers.laguerre import LaguerreLayer
            >>> laguerre_layer = LaguerreLayer(max_order=3)
            >>> x = torch.tensor([0.0, 1.0, 2.0])
            >>> laguerre_layer(x)
            tensor([[1.0000, 0.0000, 0.0000, 0.0000],
                    [1.0000, 1.0000, 0.0000, 0.0000],
                    [1.0000, 2.0000, 2.0000, 0.0000]])
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

        assert x.dim() == 1, f"Expected x to have 1 dimension (batch), but got {x.shape}"

        # Berechnung der Laguerre-Polynome bis zur max_order
        laguerre_features = [laguerre(n, x) for n in range(self.max_order + 1)]

        return torch.stack(laguerre_features, dim=-1)  # Shape: (batch_size, max_order+1)
