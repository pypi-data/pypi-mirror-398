"""Dieses Modul enthält ein PyTorch-Modell, das sowohl die Laguerre- als auch die Hermite-Polynome
auf eine Eingabe anwendet.

Beispiel:
    >>> import torch
    >>> from deepsuite.layers.polynomial_net import PolynomialNet
    >>> poly_net = PolynomialNet(laguerre_order=3, hermite_order=2)
    >>> x = torch.tensor([0.0, 1.0, 2.0])
    >>> laguerre_features, hermite_features = poly_net(x)
    >>> laguerre_features.shape, hermite_features.shape
    (torch.Size([3, 4]), torch.Size([3, 3]))
"""

import torch
from torch import nn

from deepsuite.layers.hermite import HermiteLayer
from deepsuite.layers.laguerre import LaguerreLayer


class PolynomialNet(nn.Module):
    """Ein PyTorch-Modell, das sowohl die Laguerre- als auch die Hermite-Polynome
    auf eine Eingabe anwendet.

    Args:
        laguerre_order (int): Maximale Ordnung der Laguerre-Polynome.
        hermite_order (int): Maximale Ordnung der Hermite-Polynome.

    Attributes:
        laguerre_layer (LaguerreLayer): Layer zur Berechnung der Laguerre-Polynome.
        hermite_layer (HermiteLayer): Layer zur Berechnung der Hermite-Polynome.

    Examples:
        >>> import torch
        >>> from deepsuite.model.polynomial import PolynomialNet
        >>> poly_net = PolynomialNet(laguerre_order=3, hermite_order=2)
        >>> x = torch.tensor([0.0, 1.0, 2.0])
        >>> laguerre_features, hermite_features = poly_net(x)
        >>> laguerre_features.shape, hermite_features.shape
        (torch.Size([3, 4]), torch.Size([3, 3]))
    """

    def __init__(self, laguerre_order: int, hermite_order: int) -> None:
        super().__init__()

        if not isinstance(laguerre_order, int) or laguerre_order < 0:
            raise ValueError(f"laguerre_order must be a non-negative integer, got {laguerre_order}")

        if not isinstance(hermite_order, int) or hermite_order < 0:
            raise ValueError(f"hermite_order must be a non-negative integer, got {hermite_order}")

        self.laguerre_layer = LaguerreLayer(max_order=laguerre_order)
        self.hermite_layer = HermiteLayer(max_order=hermite_order)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Führt die Eingabe durch die Laguerre- und Hermite-Layer.

        Args:
            x (torch.Tensor): Eingabe-Tensor der Form (batch_size,)

        Returns:
            tuple[torch.Tensor, torch.Tensor]: Laguerre- und Hermite-Features.

        Raises:
            TypeError: Wenn `x` kein `torch.Tensor` ist.
            ValueError: Wenn `x` nicht 1D ist.
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")
        if x.dim() != 1:
            raise ValueError(f"Expected x to have 1 dimension, but got shape {x.shape}")

        laguerre_features = self.laguerre_layer(x)  # Shape: (batch_size, laguerre_order+1)
        hermite_features = self.hermite_layer(x)  # Shape: (batch_size, hermite_order+1)

        return laguerre_features, hermite_features


class PolynomialCartesian2Polar(nn.Module):
    """Ein PyTorch-Modell, das kartesische Koordinaten in Kugelkoordinaten umwandelt
    und dann Laguerre- oder Hermite-Polynome darauf anwendet.

    Args:
        order (int): Die maximale Ordnung der Polynome.
        laguerre (bool): Falls True, werden Laguerre-Polynome verwendet, sonst Hermite-Polynome.

    Attributes:
        polynomial_layer (nn.Module): LaguerreLayer oder HermiteLayer je nach Auswahl.

    Examples:
        >>> import torch
        >>> from deepsuite.layers.polynomial_polar import PolynomialCartesian2Polar
        >>> model = PolynomialCartesian2Polar(order=3, laguerre=True)
        >>> x = torch.tensor([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
        >>> model(x).shape
        torch.Size([2, 3, 4])  # (batch_size, 3 Koordinaten, max_order+1 Polynome)
    """

    def __init__(self, order: int, laguerre: bool = True, clamp: float = 1e-8) -> None:
        super().__init__()
        self.polynomial_layer = (
            LaguerreLayer(max_order=order) if laguerre else HermiteLayer(max_order=order)
        )
        self.max_order = order
        self.clamp_value = clamp

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Wandelt kartesische Koordinaten (x, y, z) in Kugelkoordinaten um
        und wendet Laguerre- oder Hermite-Polynome darauf an.

        Args:
            x (torch.Tensor): Tensor der Form (batch_size, 3), bestehend aus (x, y, z).

        Returns:
            torch.Tensor: Tensor der Form (batch_size, 3, max_order+1) mit Polynomen für r, θ, φ.
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

        if x.dim() != 2 or x.shape[1] != 3:
            raise ValueError(f"Expected input shape (batch_size, 3), but got {x.shape}")

        x_coords, y_coords, z_coords = x[:, 0], x[:, 1], x[:, 2]

        # Radialkoordinate r
        r = torch.sqrt(x_coords**2 + y_coords**2 + z_coords**2)
        r = r.clamp(min=self.clamp_value)

        # Longitude (Azimutwinkel θ)
        longitude = torch.atan2(y_coords, x_coords)  # Verhindert NaN-Probleme

        # Latitude (Polarwinkel φ)
        latitude = torch.acos(z_coords / r)

        # Polynomberechnungen
        radial_polynomial = self.polynomial_layer(r)  # Shape: (batch_size, max_order+1)
        azimuthal_polynomial = self.polynomial_layer(longitude)  # Shape: (batch_size, max_order+1)
        elevation_polynomial = self.polynomial_layer(latitude)  # Shape: (batch_size, max_order+1)

        # Stapeln entlang der zweiten Achse (3 Richtungen: r, θ, φ)
        return torch.stack(
            (radial_polynomial, azimuthal_polynomial, elevation_polynomial), dim=1
        )  # (batch_size, 3, max_order+1)


class PolynomialPolar2Cartesian(nn.Module):
    """Ein PyTorch-Modell, das Kugelkoordinaten (r, θ, φ) in kartesische Koordinaten (x, y, z) umwandelt
    und dann Laguerre- oder Hermite-Polynome darauf anwendet.

    Args:
        order (int): Die maximale Ordnung der Polynome.
        laguerre (bool): Falls True, werden Laguerre-Polynome verwendet, sonst Hermite-Polynome.

    Attributes:
        polynomial_layer (nn.Module): LaguerreLayer oder HermiteLayer je nach Auswahl.

    Examples:
        >>> import torch
        >>> from deepsuite.layers.polynomial_polar import PolynomialPolar2Cartesian
        >>> model = PolynomialPolar2Cartesian(order=3, laguerre=True)
        >>> x = torch.tensor([[1.0, 0.5, 0.8], [2.0, 1.0, 1.5]])  # (r, θ, φ)
        >>> model(x).shape
        torch.Size([2, 3, 4])  # (batch_size, 3 kartesische Koordinaten, max_order+1 Polynome)
    """

    def __init__(self, order: int, laguerre: bool = True) -> None:
        super().__init__()
        self.polynomial_layer = (
            LaguerreLayer(max_order=order) if laguerre else HermiteLayer(max_order=order)
        )
        self.max_order = order

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Wandelt Kugelkoordinaten (r, θ, φ) in kartesische Koordinaten um
        und wendet Laguerre- oder Hermite-Polynome darauf an.

        Args:
           x (torch.Tensor): Tensor der Form (batch_size, 3), bestehend aus (r, θ, φ).

        Returns:
            torch.Tensor: Tensor der Form (batch_size, 3, max_order+1) mit Polynomen für x, y, z.
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected x to be a torch.Tensor, but got {type(x)}")

        if x.dim() != 2 or x.shape[1] != 3:
            raise ValueError(f"Expected input shape (batch_size, 3), but got {x.shape}")

        r, theta, phi = x[:, 0], x[:, 1], x[:, 2]

        # Umrechnung von Kugel- in Kartesische Koordinaten
        x_coords = r * torch.cos(theta) * torch.sin(phi)
        y_coords = r * torch.sin(theta) * torch.sin(phi)
        z_coords = r * torch.cos(phi)

        # Polynomberechnungen
        x_polynomial = self.polynomial_layer(x_coords)  # Shape: (batch_size, max_order+1)
        y_polynomial = self.polynomial_layer(y_coords)  # Shape: (batch_size, max_order+1)
        z_polynomial = self.polynomial_layer(z_coords)  # Shape: (batch_size, max_order+1)

        # Stapeln entlang der zweiten Achse (3 Richtungen: x, y, z)
        return torch.stack(
            (x_polynomial, y_polynomial, z_polynomial), dim=1
        )  # (batch_size, 3, max_order+1)
