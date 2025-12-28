"""Doa module."""

import torch

from deepsuite.layers.dft import ComplexLinear


class DoA(torch.nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int) -> None:
        """Initialize the DoA (Direction of Arrival) model using complex numbers.

        Args:
            input_dim (int): Dimension of the input features.
            hidden_dim (int): Dimension of the hidden layers.
        """
        super().__init__()
        self.fc1 = ComplexLinear(input_dim, hidden_dim)
        self.fc2 = ComplexLinear(hidden_dim, hidden_dim)

        # Finale Schicht: Reale Werte für Azimuth & Elevation
        self.fc3 = torch.nn.Linear(hidden_dim * 2, 2, bias=False, dtype=torch.float32)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform the forward pass of the DoA model.

        Args:
            x (torch.Tensor): Complex-valued input tensor of shape (batch_size, input_dim).

        Returns:
            torch.Tensor: Real-valued tensor containing the azimuth and elevation angles.
        """
        if not torch.is_complex(x):
            raise ValueError("Input tensor must be of dtype torch.complex64")

        x = self.complex_relu(self.fc1(x))
        x = self.complex_relu(self.fc2(x))

        # Sicherstellen, dass die Tensorform gleich bleibt
        x_real = torch.cat([x.real, x.imag], dim=-1)  # Stabile Konvertierung in reelle Werte

        return self.fc3(x_real)  # Ausgabe sind reale Azimuth- & Elevationswerte
