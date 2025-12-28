from typing import Literal

import torch
from torch import nn
import torch.nn.functional as F


class TwinBlock(nn.Module):
    """Einfacher vollständig verbundener Netzwerkzweig (MLP) für Vektordaten,
    z. B. abgeflachte Bilder mit 784 Pixeln (28x28).

    Beispiel:
        >>> model = TwinBlock()
        >>> eingabe = torch.randn(32, 784)
        >>> ausgabe = model(eingabe)  # Form: (32, 512)
    """

    def __init__(self) -> None:
        super().__init__()
        self.fc1 = nn.Linear(784, 1024)
        self.fc2 = nn.Linear(1024, 1024)
        self.fc3 = nn.Linear(1024, 512)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Führt die Eingabe durch drei Dense-Schichten mit ReLU-Aktivierungen.

        Args:
            x: Eingabetensor der Form (Batchgröße, 784)

        Returns:
            Tensor der Form (Batchgröße, 512) – eingebettete Repräsentation
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return F.relu(self.fc3(x))


class TwinBlockCNN(nn.Module):
    """Convolutional Twin Network für Bilddaten (z. B. 28x28-Graustufenbilder).
    Nutzt 2 Convolutional-Layer + MaxPooling + Dropout.

    Beispiel:
        >>> model = TwinBlockCNN()
        >>> bild = torch.randn(16, 1, 28, 28)
        >>> embedding = model(bild)  # Form: (16, 512)
    """

    def __init__(self) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 32, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(7 * 7 * 32, 1024)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(1024, 512)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Leitet Bilddaten durch CNN, Pooling, Dropout und zwei Fully Connected Layer.

        Args:
            x: Eingabetensor der Form (Batchgröße, 1, 28, 28)

        Returns:
            Tensor der Form (Batchgröße, 512) – eingebettete Repräsentation
        """
        x = F.relu(self.conv1(x))  # Erste Faltung
        x = self.pool(x)  # Erstes Pooling
        x = F.relu(self.conv2(x))  # Zweite Faltung
        x = self.pool(x)  # Zweites Pooling
        x = x.view(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))  # Erste Dense-Schicht
        x = self.dropout(x)  # Dropout (nur im Training)
        return self.fc2(x)  # Letzte Dense-Schicht


class SiameseNet(nn.Module):
    """Siamese Neural Network zum Vergleich von zwei Eingaben hinsichtlich ihrer Ähnlichkeit.

    Das Netzwerk kann entweder mit Bilddaten (CNN-Zweig) oder Vektordaten (Dense-Zweig)
    arbeiten und verwendet eine von zwei Vergleichsmethoden:

    - 'subtract': Absoluter Unterschied der Embeddings
    - 'concat'  : Verkettung beider Embeddings

    Beispiel:
        >>> net = SiameseNet(is_image=True, comparison_type="subtract")
        >>> x1, x2 = torch.randn(8, 1, 28, 28), torch.randn(8, 1, 28, 28)
        >>> logits, probs = net(x1, x2)
    """

    def __init__(
        self, is_image: bool = True, comparison_type: Literal["subtract", "concat"] = "subtract"
    ) -> None:
        """Initialisiert das Siamese-Netzwerk.

        Args:
            is_image: True für Bilddaten (CNN), False für Vektordaten (Dense).
            comparison_type: 'subtract' oder 'concat' zur Vergleichsbildung.
        """
        super().__init__()
        self.comparison_type = comparison_type

        # Twin-Netzwerk entsprechend dem Datentyp wählen
        self.twin = TwinBlockCNN() if is_image else TwinBlock()

        # Dimensionen anpassen je nach Vergleichsstrategie
        input_dim = 512 if comparison_type == "subtract" else 512 * 2

        # Klassifikations-Block (nach dem Vergleich)
        self.fc1 = nn.Linear(input_dim, 1024)
        self.out = nn.Linear(1024, 1)

    def forward_once(self, x: torch.Tensor) -> torch.Tensor:
        """Gibt das Embedding einer einzelnen Eingabe zurück.

        Args:
            x: Tensor der Eingabe (Bild oder Vektor)

        Returns:
            Tensor mit eingebetteter Darstellung (Form: [batch_size, 512])
        """
        return self.twin(x)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Vorwärtsdurchlauf durch beide Zweige + Vergleich + Klassifikation.

        Args:
            x1: Erstes Eingabebeispiel (Tensor)
            x2: Zweites Eingabebeispiel (Tensor)

        Returns:
            logits: Rohwert vor der Sigmoid-Funktion (Form: [batch_size])
            prob: Ähnlichkeitswahrscheinlichkeit nach Sigmoid (Form: [batch_size])
        """
        o1 = self.forward_once(x1)
        o2 = self.forward_once(x2)

        # Vergleichsstrategie anwenden
        if self.comparison_type == "subtract":
            diff = torch.abs(o1 - o2)
        elif self.comparison_type == "concat":
            diff = torch.cat([o1, o2], dim=1)
        else:
            raise ValueError("Ungültiger Vergleichstyp: 'subtract' oder 'concat' erwartet.")

        fc = F.relu(self.fc1(diff))
        logits = self.out(fc)
        prob = torch.sigmoid(logits).squeeze(1)

        return logits.squeeze(1), prob
