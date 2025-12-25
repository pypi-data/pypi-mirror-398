from typing import Literal

from einops import rearrange
import torch
from torch import nn

from deepsuite.model.loftr.coarse_matching import CoarseMatching
from deepsuite.model.loftr.fine_matching import FineMatching
from deepsuite.model.loftr.fine_preprocess import FinePreprocess
from deepsuite.model.loftr.position_encoding import PositionEncodingSine
from deepsuite.model.loftr.resnet_fpn import ResnetWithFPN
from deepsuite.model.loftr.transformer import LocalFeatureTransformer


class LoFTR(nn.Module):
    """LoFTR (Detector-Free Local Feature Matching with Transformers)

    Dieses Modul kombiniert Feature-Extraktion, coarse-to-fine Matching
    und Transformer-basierte Verarbeitung zur robusten Bildpaar-Verknüpfung.

    Pipeline:
        1. Featureextraktion mit ResNet-FPN
        2. Positional Encoding auf coarse Features
        3. Transformer-Verarbeitung auf coarse-Ebene
        4. Coarse Matching mit dual_softmax oder sinkhorn
        5. Extraktion lokal feiner Features via Patch-Unfolding
        6. Transformer-Verarbeitung auf Fine-Ebene
        7. Fine Matching auf Patch-Ebene

    Beispiel:
        >>> model = LoFTR(...)
        >>> image0 = torch.randn(1, 1, 256, 256)
        >>> image1 = torch.randn(1, 1, 256, 256)
        >>> out = model(image0, image1)
        >>> print(out["mkpts0_f"].shape)  # Fein-registrierte Punkte

    Hinweis:
        Dieses Modell ist kompatibel mit TorchScript und ONNX, da `mask0` und `mask1`
        explizit als optionale Argumente geführt werden.
    """

    def __init__(
        self,
        backbone_resnet_variant: str = "resnet50",
        backbone_in_channels: int = 1,
        backbone_fpn_out_channels: int = 256,
        sin_coase_d_model: int = 256,
        sin_coarse_temp_bug_fix: bool = True,
        fine_transformer_d_model: int = 128,
        fine_transformer_nhead: int = 8,
        fine_transformer_layer_names: list[str] = ("self", "cross"),
        fine_transformer_attention: Literal["linear", "full"] = "linear",
        coarse_transformer_d_model: int = 256,
        coarse_transformer_nhead: int = 8,
        coarse_transformer_layer_names: list[str] = ("self", "cross") * 4,
        coarse_transformer_attention: Literal["linear", "full"] = "linear",
        coarse_matcher_thr: float = 0.2,
        coarse_matcher_border_rm: int = 2,
        coarse_matcher_match_type: Literal["sinkhorn", "dual_softmax"] = "dual_softmax",
        coarse_matcher_dsmax_temperature: float = 0.1,
        coarse_matcher_skh_init_bin_score: float = 1.0,
        coarse_matcher_train_coarse_percent: float = 0.2,
        coarse_matcher_train_pad_num_gt_min: int = 200,
        coarse_matcher_skh_iters: int = 3,
        coarse_matcher_skh_prefilter: bool = False,
        coarse_matcher_sparse_spvs: bool = True,
        fine_process_coarse_feat: bool = True,
        fine_process_window_size: int = 5,
        fine_process_coarse_model: int = 256,
        fine_process_fine_model: int = 128,
    ) -> None:
        super().__init__()

        self.backbone: ResnetWithFPN = ResnetWithFPN(
            resnet_variant=backbone_resnet_variant,
            in_channels=backbone_in_channels,
            fpn_out_channels=backbone_fpn_out_channels,
        )

        self.pos_encoding = PositionEncodingSine(
            d_model=sin_coase_d_model, temp_bug_fix=sin_coarse_temp_bug_fix
        )

        self.loftr_fine = LocalFeatureTransformer(
            d_model=fine_transformer_d_model,
            nhead=fine_transformer_nhead,
            layer_names=fine_transformer_layer_names,
            attention=fine_transformer_attention,
        )
        self.loftr_coarse = LocalFeatureTransformer(
            d_model=coarse_transformer_d_model,
            nhead=coarse_transformer_nhead,
            layer_names=coarse_transformer_layer_names,
            attention=coarse_transformer_attention,
        )

        self.coarse_matching = CoarseMatching(
            thr=coarse_matcher_thr,
            border_rm=coarse_matcher_border_rm,
            match_type=coarse_matcher_match_type,
            dsmax_temperature=coarse_matcher_dsmax_temperature,
            skh_init_bin_score=coarse_matcher_skh_init_bin_score,
            train_coarse_percent=coarse_matcher_train_coarse_percent,
            train_pad_num_gt_min=coarse_matcher_train_pad_num_gt_min,
            skh_iters=coarse_matcher_skh_iters,
            skh_prefilter=coarse_matcher_skh_prefilter,
            sparse_spvs=coarse_matcher_sparse_spvs,
        )
        self.fine_matching = FineMatching()

        self.fine_preprocess = FinePreprocess(
            fine_concat_coarse_feat=fine_process_coarse_feat,
            fine_window_size=fine_process_window_size,
            coarse_model=fine_process_coarse_model,
            fine_model=fine_process_fine_model,
        )

    def forward(
        self,
        image0: torch.Tensor,
        image1: torch.Tensor,
        mask0: torch.Tensor | None = None,
        mask1: torch.Tensor | None = None,
    ) -> dict:
        """Führt vollständiges Matching zwischen zwei Bildern aus.

        Args:
            image0: Erstes Bild (B, 1, H, W)
            image1: Zweites Bild (B, 1, H, W)
            mask0: Optionale Maske für Bild 0 (B, H, W)
            mask1: Optionale Maske für Bild 1 (B, H, W)

        Returns:
            data (dict): Enthält Matching-Ergebnisse wie:
                - 'mkpts0_f': Fein registrierte Punkte in Bild0
                - 'mkpts1_f': Fein registrierte Punkte in Bild1
                - 'mconf': Matching-Konfidenzen
        """
        assert image0.shape[1] == 1, "Nur 1-Kanalbilder werden unterstützt (Graustufen)"

        device = image0.device
        B = image0.shape[0]

        data = {"bs": B, "hw0_i": image0.shape[2:], "hw1_i": image1.shape[2:]}

        if data["hw0_i"] == data["hw1_i"]:
            feats_c, feats_f = self.backbone(torch.cat([image0, image1], dim=0))
            feat_c0, feat_c1 = feats_c.split(B)
            feat_f0, feat_f1 = feats_f.split(B)
        else:
            feat_c0, feat_f0 = self.backbone(image0)
            feat_c1, feat_f1 = self.backbone(image1)

        data.update(
            {
                "hw0_c": feat_c0.shape[2:],
                "hw1_c": feat_c1.shape[2:],
                "hw0_f": feat_f0.shape[2:],
                "hw1_f": feat_f1.shape[2:],
            }
        )

        feat_c0 = rearrange(self.pos_encoding(feat_c0), "b c h w -> b (h w) c").to(device)
        feat_c1 = rearrange(self.pos_encoding(feat_c1), "b c h w -> b (h w) c").to(device)

        if mask0 is not None and mask1 is not None:
            mask0 = mask0.flatten(1)
            mask1 = mask1.flatten(1)
            feat_c0, feat_c1 = self.loftr_coarse(feat_c0, feat_c1, mask0, mask1)
        else:
            feat_c0, feat_c1 = self.loftr_coarse(feat_c0, feat_c1)

        self.coarse_matching(feat_c0, feat_c1, data, mask_c0=mask0, mask_c1=mask1)

        feat_f0_unf, feat_f1_unf = self.fine_preprocess(feat_f0, feat_f1, feat_c0, feat_c1, data)

        if feat_f0_unf.shape[0] > 0:
            feat_f0_unf, feat_f1_unf = self.loftr_fine(feat_f0_unf, feat_f1_unf)
        self.fine_matching(feat_f0_unf, feat_f1_unf, data)

        return data

    def load_state_dict(self, state_dict, *args, **kwargs):
        """Lädt Gewichtsdaten unter Berücksichtigung älterer Modellbezeichner.

        Manche gespeicherte Modelle verwenden 'matcher.' als Präfix in ihren Schlüsselbezeichnungen.
        Diese Methode entfernt dieses Präfix automatisch, damit die Parameter in aktuelle Modelle geladen
        werden können.

        Beispiel:
            'matcher.backbone.conv1.weight' → 'backbone.conv1.weight'

        Args:
            state_dict (dict): Zustand mit Modellgewichten (ggf. mit veraltetem Präfix)
            *args, **kwargs: Weitere Argumente für das Standardverhalten

        Returns:
            Ergebnis von `super().load_state_dict(...)`
        """
        for k in list(state_dict.keys()):
            if k.startswith("matcher."):
                state_dict[k.replace("matcher.", "", 1)] = state_dict.pop(k)
        return super().load_state_dict(state_dict, *args, **kwargs)

    def __repr__(self):
        return f"LoFTR(coarse_dim={self.loftr_coarse.d_model}, match_type={self.coarse_matching.match_type})"
