"""Root Mean Squared Error (RMSE) Loss.

Author:
    Anton Feldmann
"""

import torch
from torch import nn


class RMSE(nn.Module):
    """Root Mean Squared Error (RMSE) Loss.

    Args:
        esp (float, optional): Kleiner Wert, um Division durch Null zu vermeiden. Default: 1e-6.
        criterion (nn.Module, optional): Verlustfunktion, standardmäßig `MSELoss`.

    Attributes:
        esp (float): Kleiner Wert, um Division durch Null
        criterion (nn.Module): Verlustfunktion

    Examples:
        >>> criterion = RMSE()
        >>> x = torch.tensor([1.0, 2.0, 3.0])
        >>> y = torch.tensor([1.0, 2.0, 2.0])
        >>> loss = criterion(x, y)
        >>> loss
        tensor(0.5774)
    """

    def __init__(self, esp: float = 1e-6, criterion: nn.Module | None = None) -> None:
        """Root Mean Squared Error (RMSE) Loss.

        Args:
            esp (float, optional): Kleiner Wert, um Division durch Null zu vermeiden. Default: 1e-6.
            criterion (nn.Module, optional): Verlustfunktion, standardmäßig `MSELoss`.
        """
        super().__init__()
        self.esp = esp
        self.criterion = criterion if criterion is not None else nn.MSELoss()

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Berechnet den RMSE-Loss.

        Args:
            x (torch.Tensor): Vorhergesagte Werte.
            y (torch.Tensor): Wahre Werte.

        Returns:
            torch.Tensor: RMSE-Wert.
        """
        loss = torch.sqrt(self.criterion(x, y) + self.esp)
        return loss
