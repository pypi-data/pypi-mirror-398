import math

import torch
from torch import nn

from deepsuite.utils.dsnt import Spatial2Numeric


class FineMatching(nn.Module):
    """Modul zur feineren Merkmalabstimmung (Fine Matching) mit dem Soft-Argmax-Ansatz.

    Dieses Modul berechnet feingranulare Koordinatenverschiebungen basierend auf
    Feature-Korrelationen und Heatmaps mittels differentiabler Erwartungswertbildung.

    Funktionen:
    - Extraktion der zentralen Patch-Merkmale
    - Berechnung von Ähnlichkeitskarten
    - Koordinatenberechnung durch spatial Softmax + Soft-Argmax
    - Schätzung der Standardabweichung (Unsicherheit)
    - Aktualisierung von Keypoints (mkpts) für das feine Matching

    Hinweise:
    - Nur aktiv, wenn `M > 0` (also grobes Matching gefunden wurde).
    """

    def __init__(self, temperature: float = 1.0) -> None:
        super().__init__()
        self.dsnt = Spatial2Numeric(temperature=temperature, normalized_coordinates=True)

    def forward(
        self,
        feat_f0: torch.Tensor,  # [M, WW, C]
        feat_f1: torch.Tensor,  # [M, WW, C]
        data: dict,
    ) -> None:
        """Führt Fine Matching auf Basis von Featurekarten durch.

        Parameter:
        ----------
        feat_f0 : Tensor
            Quell-Featurekarten [M, WW, C] (z. B. aus Bild 0)
        feat_f1 : Tensor
            Ziel-Featurekarten [M, WW, C] (z. B. aus Bild 1)
        data : dict
            Zwischenspeicher mit Koordinaten, Skalierungen usw.

        Ergebnisse (im `data`-Dict gespeichert):
        - expec_f : [M, 3] (x, y, std)
        - mkpts0_f : [M, 2]
        - mkpts1_f : [M, 2]
        """
        M, WW, C = feat_f0.shape
        if M == 0:
            assert not self.training, "M darf im Training nicht 0 sein - siehe coarse_matching."
            data.update(
                {
                    "expec_f": torch.empty(0, 3, device=feat_f0.device),
                    "mkpts0_f": data["mkpts0_c"],
                    "mkpts1_f": data["mkpts1_c"],
                }
            )
            return

        W = int(math.sqrt(WW))
        self.M, self.W, self.WW, self.C = M, W, WW, C
        self.scale = data["hw0_i"][0] / data["hw0_f"][0]

        # 1. Pick zentrales Feature
        feat0_center = feat_f0[:, WW // 2, :]  # [M, C]

        # 2. Ähnlichkeitsmatrix: [M, WW]
        sim_matrix = torch.einsum("mc,mrc->mr", feat0_center, feat_f1)

        # 3. Heatmap (Similarity → Softmax)
        softmax_temp = 1.0 / math.sqrt(C)
        heatmap = torch.softmax(sim_matrix * softmax_temp, dim=1).view(M, 1, W, W)  # [M, 1, H, W]

        # 4. Koordinaten-Erwartung (Soft-Argmax)
        coords = self.dsnt(heatmap)  # [M, 1, 2]
        coords = coords.squeeze(1)  # → [M, 2]

        # 5. Unsicherheitsabschätzung: Standardabweichung über das Gitter
        grid = self.dsnt.grid_generator((W, W), device=feat_f0.device, dtype=feat_f0.dtype)
        grid = grid.contiguous().view(1, -1, 2)  # [1, WW, 2]

        prob_flat = heatmap.view(M, -1, 1)  # [M, WW, 1]
        mean = coords.unsqueeze(1)  # [M, 1, 2]
        var = torch.sum(prob_flat * (grid - mean) ** 2, dim=1)  # [M, 2]
        std = torch.sqrt(torch.clamp(var, min=1e-10))  # [M, 2]
        std_sum = std.sum(dim=-1, keepdim=True)  # [M, 1]

        # 6. Ergebnisse speichern
        data.update(
            {
                "expec_f": torch.cat([coords, std_sum], dim=-1),  # [M, 3]
            }
        )

        # 7. Absolutkoordinaten berechnen
        self.get_fine_match(coords, data)

    @torch.no_grad()
    def get_fine_match(self, coords: torch.Tensor, data: dict) -> None:
        """Berechnet feine Keypoint-Koordinaten (absolute Lage in mkpts1_f).

        Args:
            coords : Tensor [M, 2] - relative Verschiebung (normalized)
            data : Dict - enthält coarse-Koordinaten + Skalierungsinfos
        """
        W, scale = self.W, self.scale
        mkpts0_f = data["mkpts0_c"]

        if "scale0" in data:  # ggf. dynamische Skalierung
            scale1 = scale * data["scale1"][data["b_ids"]]
        else:
            scale1 = scale

        # Koordinatenverschiebung anwenden (nur auf mkpts1)
        offset = coords * (W // 2) * scale1.view(-1, 1)
        mkpts1_f = data["mkpts1_c"] + offset

        data.update(
            {
                "mkpts0_f": mkpts0_f,
                "mkpts1_f": mkpts1_f,
            }
        )
