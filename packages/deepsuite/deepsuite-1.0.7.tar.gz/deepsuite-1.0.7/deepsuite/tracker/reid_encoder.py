"""Reid Encoder module."""

import torch
from torch import Tensor, nn


class ReIDEncoder(nn.Module):
    def __init__(
        self,
        base_model: nn.Module,
        output_dim: int = 128,
        use_bn: bool = True,
        dropout: float = 0.0,
    ) -> None:
        """ReID Encoder-Modul.

        Args:
            base_model (nn.Module): Pretrained CNN-Backbone (z. B. ResNet50, EfficientNet, etc.).
            output_dim (int): Dimensionality der Embedding-Vektoren.
            use_bn (bool): Optionaler BatchNorm nach dem FC-Layer.
            dropout (float): Optionaler Dropout vor Embedding-Ausgabe.
        """
        super().__init__()

        # Feature Extractor (alles außer dem letzten FC-Layer)
        self.encoder = nn.Sequential(*list(base_model.children())[:-1])

        # Input-Dim automatisch erkennen (z. B. ResNet → 2048)
        dummy_input = torch.zeros(1, 3, 224, 224)
        with torch.no_grad():
            feat = self.encoder(dummy_input).view(1, -1)
            input_dim = feat.shape[1]

        layers: list[nn.Module] = [nn.Linear(input_dim, output_dim)]
        if use_bn:
            layers.append(nn.BatchNorm1d(output_dim))
        if dropout > 0:
            layers.append(nn.Dropout(dropout))

        self.embedding = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:  # x = [B, C, H, W]
        feat = self.encoder(x).view(x.size(0), -1)  # [B, C]
        emb = self.embedding(feat)  # [B, D]
        return nn.functional.normalize(emb, dim=1)  # L2-normalisiert
