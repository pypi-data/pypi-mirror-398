"""DFT-Layer und komplexwertiges neuronales Netz für Longitude & Latitude mit complexPyTorch.

Dieses Modell kann sowohl mit komplexen Zahlen als auch mit realen Zahlen umgehen.
Es unterstützt:
- **GPU-Berechnungen**
- **Mobilgeräte ohne complexPyTorch**
- **TorchScript für Mobile Deployment**

Author:
    Anton Feldmann <anton.feldmann@gmail.com>

Version:
    1.0

Date:
    2025-05-27

License:
    MIT
"""

import torch
from torch import nn
import torch.linalg as la

from deepsuite.utils.complex import Complex


# **DFT (Diskrete Fourier-Transformation) als PyTorch-Modell**
class DFT(nn.Module):
    """Diskrete Fourier-Transformation (DFT) als PyTorch-Modell.
    Dieses Modell berechnet die Fourier-Transformation eines Signals und kann auch die inverse DFT ausführen.

    Args:
        n_fft (int): Anzahl der FFT-Punkte (Größe des Spektrums).
        dtype (torch.dtype, optional): Datentyp der DFT-Matrix (Standard: torch.float32).

    Beispiel:
        >>> dft = DFT(4)
        >>> x = torch.tensor([[1, 2, 3, 4]], dtype=torch.complex128)
        >>> X = dft(x)  # DFT ausführen
        >>> x_reconstructed = dft.rewind(X)  # IDFT ausführen
    """

    def __init__(self, n_fft: int, dtype=torch.float32) -> None:
        super().__init__()

        # Sicherstellen, dass n_fft eine ganze Zahl ist.
        if not isinstance(n_fft, int):
            raise TypeError(f"n_fft must be an integer, got {type(n_fft)}")
        self.n_fft = n_fft  # Speichert die FFT-Größe.

        # **Erstellen der DFT-Matrix**
        indices: torch.Tensor = torch.arange(n_fft, dtype=dtype)
        omega: torch.Tensor = (
            -2j * torch.pi * indices[:, None] * indices / n_fft
        )  # Formel der DFT-Matrix

        if Complex.has_complex():
            dft_matrix: torch.Tensor = torch.exp(omega).to(
                torch.complex128
            )  # Falls complexPyTorch verfügbar ist
        else:
            dft_matrix = torch.exp(omega)  # Falls nicht, bleibt es float

        # Speichert die DFT-Matrix als nicht-lernbaren Buffer (optimiert für GPU-Nutzung).
        self.register_buffer("dft_matrix", dft_matrix)

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        """Führt die DFT auf das Eingabe-Signal aus.

        Args:
            signal (torch.Tensor): Eingangssignal mit (batch_size, n_fft).

        Returns:
            torch.Tensor: Frequenzdarstellung des Signals.
        """
        assert signal.shape[-1] == self.n_fft, (
            f"Expected last dimension {self.n_fft}, got {signal.shape[-1]}"
        )
        assert isinstance(self.dft_matrix, torch.Tensor), "DFT matrix must be a torch.Tensor"

        if Complex.has_complex():
            assert signal.dtype == torch.complex128, (
                "Signal must be complex-valued (torch.complex128)"
            )

        return signal @ self.dft_matrix.to(signal.device)  # GPU-Kompatibilität

    def rewind(self, signal: torch.Tensor) -> torch.Tensor:
        """Berechnet die inverse DFT (IDFT), um das Originalsignal wiederherzustellen.

        Args:
            signal (torch.Tensor): Frequenzdarstellung des Signals.

        Returns:
            torch.Tensor: Rekonstruiertes Zeitsignal.
        """
        assert isinstance(signal, torch.Tensor), "Input signal must be a torch.Tensor"
        assert isinstance(self.dft_matrix, torch.Tensor), "DFT matrix must be a torch.Tensor"

        if Complex.has_complex():
            idft_matrix: torch.Tensor = self.dft_matrix.conj().T / self.n_fft
        else:
            idft_matrix = la.pinv(self.dft_matrix).T / self.n_fft  # ignore: complexPyTorch

        return signal @ idft_matrix.to(signal.device)  # GPU-Kompatibilität

    inverse = rewind  # Alias für inverse DFT


DFTLayer = DFT
