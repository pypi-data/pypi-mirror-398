from typing import Literal

import torch
from torch import nn
import torch.nn.functional as F

INF = 1e9


class CoarseMatching(nn.Module):
    """Modul zur Durchführung des groben Feature-Matchings zwischen zwei Bild-Features.
    Unterstützt 'dual_softmax' oder 'sinkhorn' für differentielles Matching.
    """

    def __init__(
        self,
        thr: float = 0.2,
        border_rm: int = 2,
        match_type: Literal["sinkhorn", "dual_softmax"] = "dual_softmax",
        dsmax_temperature: float = 0.1,
        skh_init_bin_score: float = 1.0,
        train_coarse_percent: float = 0.2,
        train_pad_num_gt_min: int = 200,
        skh_iters: int = 3,
        skh_prefilter: bool = False,
        sparse_spvs: bool = True,
    ) -> None:
        """Initialisiert das CoarseMatching-Modul.

        Args:
            thr (float): Konfidenz-Schwelle für Matches.
            border_rm (int): Anzahl zu entfernender Randpixel.
            match_type (str): Matching-Verfahren, z.B. 'dual_softmax' oder 'sinkhorn'.
            dsmax_temperature (float): Temperatur für Softmax bei dual_softmax.
            skh_init_bin_score (float): Anfangswert für Dustbin-Score (Sinkhorn).
            train_coarse_percent (float): Anteil der Trainings-Matches.
            train_pad_num_gt_min (int): Minimum an Ground-Truth-Pads im Training.
            skh_iters (int): Anzahl der Iterationen bei Sinkhorn.
            skh_prefilter (bool): Entferne Dustbin-Matches bei Inferenz.
            sparse_spvs (bool): Gibt an, ob zusätzliche supervision gespeichert wird.
        """
        super().__init__()

        self.thr = thr
        self.border_rm = border_rm
        self.train_coarse_percent = train_coarse_percent
        self.train_pad_num_gt_min = train_pad_num_gt_min
        self.sparse_spvs = sparse_spvs
        self.match_type = match_type
        if self.match_type == "dual_softmax":
            self.temperature = dsmax_temperature
        elif self.match_type == "sinkhorn":
            self.bin_score = nn.Parameter(torch.tensor(skh_init_bin_score, requires_grad=True))
            self.skh_iters = skh_iters
            self.skh_prefilter = skh_prefilter
        else:
            raise NotImplementedError(f"Unbekannter Matching-Typ: {self.match_type}")

    def forward(self, feat_c0, feat_c1, data, mask_c0=None, mask_c1=None) -> None:
        """Führt das Matching zwischen zwei Featurekarten durch.

        Args:
            feat_c0 (Tensor): Featurekarte 0 [B, L, C]
            feat_c1 (Tensor): Featurekarte 1 [B, S, C]
            data (dict): Zusätzliche Daten für spätere Verarbeitung
            mask_c0/mask_c1 (Tensor): Optional gültige Masken [B, L] / [B, S]
        """
        _N, L, S, C = feat_c0.shape[0], feat_c0.shape[1], feat_c1.shape[1], feat_c0.shape[2]

        # Feature-Normalisierung
        scale = C**0.5
        feat_c0 = feat_c0 / scale
        feat_c1 = feat_c1 / scale

        # Ähnlichkeitsmatrix berechnen: [B, L, S]
        sim_matrix = torch.bmm(feat_c0, feat_c1.transpose(1, 2))

        if mask_c0 is not None:
            valid_mask = mask_c0[:, :, None] & mask_c1[:, None, :]
            sim_matrix = sim_matrix.masked_fill(~valid_mask, -INF)

        # Matching-Verfahren wählen
        if self.match_type == "dual_softmax":
            sim_matrix = sim_matrix / self.temperature
            conf_matrix = F.softmax(sim_matrix, dim=1) * F.softmax(sim_matrix, dim=2)

        elif self.match_type == "sinkhorn":
            log_assign_matrix = CoarseMatching.log_optimal_transport(
                sim_matrix, self.bin_score, self.skh_iters
            )
            assign_matrix = log_assign_matrix.exp()  # [B, L+1, S+1]
            conf_matrix = assign_matrix[:, :-1, :-1]

            # Entferne Matches mit Dustbin-Zuordnung bei Inferenz
            if not self.training and self.skh_prefilter:
                filter0 = assign_matrix.argmax(dim=2) == S
                filter1 = assign_matrix.argmax(dim=1) == L
                conf_matrix[filter0[:, :-1].unsqueeze(2).expand_as(conf_matrix)] = 0
                conf_matrix[filter1[:, :-1].unsqueeze(1).expand_as(conf_matrix)] = 0

            if self.sparse_spvs:
                data["conf_matrix_with_bin"] = assign_matrix.clone()

        else:
            raise NotImplementedError(f"Unknown match_type {self.match_type}")

        data["conf_matrix"] = conf_matrix
        data.update(self.get_coarse_match(conf_matrix, data))

    @staticmethod
    def mask_border(m, b: int, v) -> None:
        """Maskiert Ränder (z. B. zur Vermeidung von Artefakten)."""
        if b <= 0:
            return
        m[:, :b] = v
        m[:, :, :b] = v
        m[:, :, :, :b] = v
        m[:, :, :, :, :b] = v
        m[:, -b:] = v
        m[:, :, -b:] = v
        m[:, :, :, -b:] = v
        m[:, :, :, :, -b:] = v

    @staticmethod
    def mask_border_with_padding(m, bd, v, p_m0, p_m1) -> None:
        """Maskiert Ränder unter Berücksichtigung von Padding-Masken."""
        if bd <= 0:
            return
        m[:, :bd] = v
        m[:, :, :bd] = v
        m[:, :, :, :bd] = v
        m[:, :, :, :, :bd] = v

        h0s = p_m0.sum(1).max(-1)[0].int()
        w0s = p_m0.sum(-1).max(-1)[0].int()
        h1s = p_m1.sum(1).max(-1)[0].int()
        w1s = p_m1.sum(-1).max(-1)[0].int()

        for b, (h0, w0, h1, w1) in enumerate(zip(h0s, w0s, h1s, w1s, strict=False)):
            m[b, h0 - bd :] = v
            m[b, :, w0 - bd :] = v
            m[b, :, :, h1 - bd :] = v
            m[b, :, :, :, w1 - bd :] = v

    @staticmethod
    def compute_max_candidates(p_m0, p_m1):
        """Berechnet die maximale Anzahl möglicher Matches anhand der gültigen Masken."""
        h0s = p_m0.sum(1).max(-1)[0]
        w0s = p_m0.sum(-1).max(-1)[0]
        h1s = p_m1.sum(1).max(-1)[0]
        w1s = p_m1.sum(-1).max(-1)[0]

        area0 = h0s * w0s
        area1 = h1s * w1s
        return torch.sum(torch.minimum(area0, area1))

    @staticmethod
    def log_optimal_transport(scores, alpha, iters):
        """Berechnet differentielles Matching via optimalen Transport (in Logspace).

        Args:
            scores (Tensor): Ähnlichkeitsmatrix [B, M, N]
            alpha (Tensor): Dustbin-Logit
            iters (int): Anzahl Sinkhorn-Iterationen

        Returns:
            Tensor: Normalisierte log-Wahrscheinlichkeitsmatrix
        """
        b, m, n = scores.shape
        ms, ns = torch.tensor(m).to(scores), torch.tensor(n).to(scores)

        bins0 = alpha.expand(b, m, 1)
        bins1 = alpha.expand(b, 1, n)
        alpha = alpha.expand(b, 1, 1)

        couplings = torch.cat([torch.cat([scores, bins0], -1), torch.cat([bins1, alpha], -1)], 1)

        norm = -(ms + ns).log()
        log_mu = torch.cat([norm.expand(m), ns.log()[None] + norm])[None].expand(b, -1)
        log_nu = torch.cat([norm.expand(n), ms.log()[None] + norm])[None].expand(b, -1)

        Z = CoarseMatching.log_sinkhorn_iterations(couplings, log_mu, log_nu, iters)
        return Z - norm

    @staticmethod
    def log_sinkhorn_iterations(Z, log_mu, log_nu, iters):
        """Sinkhorn-Normalisierung im Logspace.

        Args:
            Z (Tensor): Log-Kostenmatrix
            log_mu, log_nu (Tensor): Log-Verteilungen
            iters (int): Anzahl Iterationen

        Returns:
            Tensor: Log-normalisierte Matrix
        """
        u, v = torch.zeros_like(log_mu), torch.zeros_like(log_nu)
        for _ in range(iters):
            u = log_mu - torch.logsumexp(Z + v.unsqueeze(1), dim=2)
            v = log_nu - torch.logsumexp(Z + u.unsqueeze(2), dim=1)
        return Z + u.unsqueeze(2) + v.unsqueeze(1)

    @torch.no_grad()
    def get_coarse_match(self, conf_matrix, data):
        """Ermittelt grobe Matches aus der Konfidenzmatrix."""
        _device = conf_matrix.device
        H0, W0 = data["hw0_c"]
        H1, W1 = data["hw1_c"]

        mask = (conf_matrix > self.thr).view(-1, H0, W0, H1, W1)

        if "mask0" not in data:
            self.mask_border(mask, self.border_rm, False)
        else:
            self.mask_border_with_padding(mask, self.border_rm, False, data["mask0"], data["mask1"])

        mask = mask.view(-1, H0 * W0, H1 * W1)
        mask = (
            mask
            * (conf_matrix == conf_matrix.max(dim=2, keepdim=True)[0])
            * (conf_matrix == conf_matrix.max(dim=1, keepdim=True)[0])
        )

        mask_v, all_j_ids = mask.max(dim=2)
        b_ids, i_ids = torch.where(mask_v)
        j_ids = all_j_ids[b_ids, i_ids]
        mconf = conf_matrix[b_ids, i_ids, j_ids]

        if len(b_ids) == 0:
            return {
                "b_ids": b_ids,
                "i_ids": i_ids,
                "j_ids": j_ids,
                "gt_mask": torch.empty(0, dtype=torch.bool, device=_device),
                "m_bids": b_ids,
                "mkpts0_c": torch.empty(0, 2, device=_device),
                "mkpts1_c": torch.empty(0, 2, device=_device),
                "mconf": torch.empty(0, device=_device),
            }

        scale = data["hw0_i"][0] / data["hw0_c"][0]
        scale0 = scale * data["scale0"][b_ids] if "scale0" in data else scale
        scale1 = scale * data["scale1"][b_ids] if "scale1" in data else scale

        mkpts0_c = torch.stack([i_ids % W0, i_ids // W0], dim=1) * scale0.unsqueeze(1)
        mkpts1_c = torch.stack([j_ids % W1, j_ids // W1], dim=1) * scale1.unsqueeze(1)

        return {
            "b_ids": b_ids,
            "i_ids": i_ids,
            "j_ids": j_ids,
            "gt_mask": mconf == 0,
            "m_bids": b_ids[mconf != 0],
            "mkpts0_c": mkpts0_c[mconf != 0],
            "mkpts1_c": mkpts1_c[mconf != 0],
            "mconf": mconf[mconf != 0],
        }

    def __repr__(self) -> str:
        return (
            f"CoarseMatching(match_type={self.match_type}, thr={self.thr}, "
            f"train_coarse_percent={self.train_coarse_percent}, "
            f"sinkhorn={self.match_type == 'sinkhorn'})"
        )
