# Wir versuchen, complexPyTorch zu importieren.
# Falls es nicht verfügbar ist (z. B. auf Mobilgeräten), wird eine Fallback-Implementierung genutzt.
"""Complex module."""

import torch
from torch import nn

try:
    from complexPyTorch.complexFunctions import complex_relu  # Komplexe ReLU-Aktivierung
    from complexPyTorch.complexLayers import ComplexLinear  # Komplexwertige lineare Schicht
except ImportError:
    # Falls complexPyTorch nicht installiert ist, nutzen wir Standard-PyTorch als Ersatz.
    complex_relu = torch.nn.functional.relu  # Normales ReLU für reelle Zahlen

    class ComplexPhaseLayer(nn.Module):
        """Speichert und verarbeitet die Phase einer komplexen Zahl.

        Args:
            hidden_dim (int): Größe der versteckten Schicht.

        Returns:
            torch.Tensor: Gespeicherte und berechnete Phase.
        """

        def __init__(self, hidden_dim: int) -> None:
            super().__init__()
            self.phase_fc = nn.Linear(hidden_dim, hidden_dim)  # Phase als eigenes Feature lernen

        def forward(self, real: torch.Tensor, imag: torch.Tensor) -> torch.Tensor:
            """Berechnet und speichert die Phase der komplexen Zahl.

            Args:
                real (torch.Tensor): Realteil der komplexen Zahl.
                imag (torch.Tensor): Imaginärteil der komplexen Zahl.

            Returns:
                torch.Tensor: Phasenwerte der komplexen Zahlen.
            """
            phase = torch.atan2(imag, real)  # Phase berechnen
            return self.phase_fc(
                phase.view(phase.shape[0], -1)
            )  # Phase durch lineare Schicht lernen

    class ComplexLinear(nn.Module):
        """Ersatz für `ComplexLinear`, falls `complexPyTorch` nicht verfügbar ist.
        - Führt separate Berechnungen für Real- und Imaginärteil durch.
        """

        def __init__(self, in_features: int, out_features: int) -> None:
            super().__init__()
            self.real_linear = nn.Linear(in_features, out_features)  # Realteil
            self.imag_linear = nn.Linear(in_features, out_features)  # Imaginärteil
            self.phase_layer = nn.Linear(
                in_features, out_features
            )  # Phase als zusätzliches Feature

        def forward(self, signal: torch.Tensor) -> torch.Tensor:
            _batch_size, _, _ = signal.shape
            real, imag = signal[:, :, 0], signal[:, :, 1]  # Real- & Imaginärteil extrahieren

            real_out = self.real_linear(real) - self.imag_linear(imag)
            imag_out = self.real_linear(imag) + self.imag_linear(real)
            phase_out = self.phase_layer(torch.atan2(imag, real))  # Phasen-Feature lernen

            return torch.stack((real_out, imag_out, phase_out), dim=-1)
