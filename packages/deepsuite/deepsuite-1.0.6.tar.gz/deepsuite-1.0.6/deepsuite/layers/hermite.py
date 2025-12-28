"""Hermite module."""

r"""Dieses Modul enthält eine PyTorch-Layer-Klasse, die Hermite-Polynome auf die Eingabe anwendet.

Die Hermite-Polynome sind eine Familie von orthogonalen Polynomen, die in der Quantenmechanik und der Wahrscheinlichkeitstheorie verwendet werden. Sie sind definiert durch die Rekursionsformel:

.. math::
    H_n(x) = 2x H_{n-1}(x) - 2(n-1) H_{n-2}(x)

mit den Anfangsbedingungen :math:`H_0(x) = 1` und :math:`H_1(x) = 2x`.

Die explizite Formel lautet:

.. math::
    H_n(x) = (-1)^n e^{x^2} \\frac{d^n}{dx^n} e^{-x^2}
"""

import torch
from torch import nn

from deepsuite.utils.hermite import hermite


class HermiteLayer(nn.Module):
    """PyTorch-Modul, das die Hermite-Polynome auf die Eingabe anwendet.

    Args:
        max_order (int): Die maximale Ordnung der Hermite-Polynome.

    Attributes:
        max_order (int): Die maximale Ordnung der Hermite-Polynome.

    Examples:
        >>> import torch
        >>> from deepsuite.layers.hermite import HermiteLayer
        >>> hermite_layer = HermiteLayer(max_order=3)
        >>> x = torch.tensor([0.0, 1.0, 2.0])
        >>> hermite_layer(x)
        tensor([[ 1.0000,  0.0000,  0.0000,  0.0000],
                [ 1.0000,  2.0000,  4.0000,  0.0000],
                [ 1.0000,  4.0000, 14.0000,  0.0000]])
    """

    def __init__(self, max_order: int) -> None:
        super().__init__()
        self.max_order = max_order

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Wendet die Hermite-Polynome auf die Eingabe an.

        Args:
            x (torch.Tensor): Eingabe-Tensor (1D), auf die die Hermite-Polynome angewendet werden.

        Returns:
            torch.Tensor: Tensor mit den berechneten Hermite-Polynomen.

        Raises:
            TypeError: Wenn `x` kein `torch.Tensor` ist.
            ValueError: Wenn `x` keine 1D-Form hat.

        Examples:
            >>> import torch
            >>> from deepsuite.layers.hermite import HermiteLayer
            >>> hermite_layer = HermiteLayer(max_order=3)
            >>> x = torch.tensor([0.0, 1.0, 2.0])
            >>> hermite_layer(x)
            tensor([[ 1.0000,  0.0000,  0.0000,  0.0000],
                    [ 1.0000,  2.0000,  4.0000,  0.0000],
                    [ 1.0000,  4.0000, 14.0000,  0.0000]])
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

        if x.dim() != 1:
            raise ValueError(f"Expected x to have 1 dimension (batch), but got shape {x.shape}")

        # Anwenden der Hermite-Polynome bis zur max_order
        hermite_features = [hermite(n, x) for n in range(self.max_order + 1)]

        # Die Stack-Operation setzt voraus, dass alle Hermite-Ergebnisse dieselbe Shape haben
        return torch.stack(hermite_features, dim=-1)  # Shape: (batch_size, max_order+1)
