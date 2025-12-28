import torch
from torch import nn


class FullAttention(nn.Module):
    def __init__(self, use_dropout=False, attention_dropout=0.1) -> None:
        super().__init__()
        self.use_dropout = use_dropout
        self.dropout = nn.Dropout(attention_dropout) if use_dropout else nn.Identity()

    def forward(self, queries, keys, values, q_mask=None, kv_mask=None):
        """Args:
            queries: [N, L, H, D]
            keys:    [N, S, H, D]
            values:  [N, S, H, D]
            q_mask:  [N, L] or None
            kv_mask: [N, S] or None
        Returns:
            output:  [N, L, H, D].
        """
        d_k = queries.size(-1)
        scale = 1.0 / d_k**0.5

        attn_logits = torch.einsum("nlhd,nshd->nlsh", queries, keys) * scale

        if kv_mask is not None:
            q_mask_exp = q_mask[:, :, None, None] if q_mask is not None else 1
            kv_mask_exp = kv_mask[:, None, :, None]
            mask = (q_mask_exp * kv_mask_exp).bool()
            attn_logits = attn_logits.masked_fill(~mask, float("-inf"))

        attn_weights = torch.softmax(attn_logits, dim=2)
        attn_weights = self.dropout(attn_weights)

        output = torch.einsum("nlsh,nshd->nlhd", attn_weights, values)
        return output.contiguous()
