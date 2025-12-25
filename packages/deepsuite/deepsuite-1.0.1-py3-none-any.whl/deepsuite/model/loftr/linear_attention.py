import torch
from torch import nn
import torch.nn.functional as F


class LinearAttention(nn.Module):
    def __init__(self, eps=1e-6):
        super().__init__()
        self.feature_map = lambda x: F.elu(x) + 1  # Inlined for speed
        self.eps = eps

    def forward(self, queries, keys, values, q_mask=None, kv_mask=None):
        """Args:
            queries: [N, L, H, D]
            keys:    [N, S, H, D]
            values:  [N, S, H, D]
            q_mask:  [N, L] or None
            kv_mask: [N, S] or None
        Returns:
            output:  [N, L, H, D]
        """
        Q = self.feature_map(queries)
        K = self.feature_map(keys)

        if q_mask is not None:
            Q = Q * q_mask[:, :, None, None]  # shape broadcasting

        if kv_mask is not None:
            kv_mask_ = kv_mask[:, :, None, None]
            K = K * kv_mask_
            values = values * kv_mask_

        scale = 1.0 / values.size(1)  # normalize to prevent fp16 overflow
        values = values * scale

        # Compute key-value summary per head
        KV = torch.einsum("nshd,nshv->nhdv", K, values)  # [N, H, D, V]
        normalizer = torch.einsum("nlhd,nshd->nlh", Q, K.sum(dim=1)) + self.eps  # [N, L, H]
        Z = 1.0 / normalizer

        output = torch.einsum("nlhd,nhdv,nlh->nlhv", Q, KV, Z) * values.size(1)
        return output.contiguous()
