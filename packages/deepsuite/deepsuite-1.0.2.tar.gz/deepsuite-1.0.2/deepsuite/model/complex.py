"""Complex module."""

import torch
from torch import nn

from deepsuite.layers.dft import WITH_COMPLEXPYTORCH, ComplexLinear, DFTLayer, complex_relu


# **Hauptmodell für komplexwertiges Lernen von Longitude & Latitude**
class ComplexLearningModel(nn.Module):
    """Ein neuronales Netz, das komplexwertige Features mit Longitude & Latitude lernt.

    Args:
        n_fft (int): Anzahl der FFT-Punkte.
        hidden_dim (int): Größe der versteckten Layer.
    """

    def __init__(self, n_fft: int, hidden_dim: int = 128) -> None:
        super().__init__()
        self.dft_layer = DFTLayer(n_fft)  # Fourier-Transformation als Feature-Extractor

        # Komplexwertige Fully Connected Layers
        self.fc1 = ComplexLinear(n_fft, hidden_dim)  # Falls complexPyTorch verfügbar ist
        self.fc2 = ComplexLinear(hidden_dim, hidden_dim)

        # Ausgabe-Schicht: Vorhersage von Longitude & Latitude
        self.output = ComplexLinear(hidden_dim, 2)

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        """Args:
            signal (torch.Tensor): Eingabe-Tensor mit komplexen Zahlen.

        Returns:
            torch.Tensor: Vorhergesagte Longitude & Latitude.
        """
        if WITH_COMPLEXPYTORCH:
            assert signal.dtype == torch.complex128, (
                "Eingabe muss komplexwertig sein (torch.complex128)"
            )

        x = self.dft_layer(signal.to(signal.device))  # DFT ausführen
        x = complex_relu(self.fc1(x.to(signal.device)))  # Komplexe Aktivierung
        x = complex_relu(self.fc2(x.to(signal.device)))  # Noch eine versteckte Schicht
        x = self.output(x.to(signal.device))  # Longitude & Latitude vorhersagen

        return x
