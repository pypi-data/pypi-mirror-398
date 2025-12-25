from torch import nn

from deepsuite.model.loftr.full_attention import FullAttention
from deepsuite.model.loftr.linear_attention import LinearAttention


class LoFTREncoderLayer(nn.Module):
    def __init__(self, d_model, nhead, attention="linear"):
        assert d_model % nhead == 0, "d_model must be divisible by nhead"
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.dim_per_head = d_model // nhead

        # Projections
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.attention = LinearAttention() if attention == "linear" else FullAttention()
        self.merge = nn.Linear(d_model, d_model, bias=False)

        # MLP
        self.mlp = nn.Sequential(
            nn.Linear(d_model, d_model * 2, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(d_model * 2, d_model, bias=False),
        )

        # Norm
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x, source, x_mask=None, source_mask=None):
        bs, len_q = x.shape[:2]

        # === Multi-head Attention ===
        q = self.q_proj(x).reshape(bs, len_q, self.nhead, self.dim_per_head)
        k = self.k_proj(source).reshape(bs, -1, self.nhead, self.dim_per_head)
        v = self.v_proj(source).reshape(bs, -1, self.nhead, self.dim_per_head)

        attended = self.attention(q, k, v, q_mask=x_mask, kv_mask=source_mask)
        attended = self.merge(attended.reshape(bs, len_q, self.d_model))

        x = x + self.norm1(attended)  # Residual 1

        # === Feed-forward ===
        x = x + self.norm2(self.mlp(x))  # Residual 2

        return x
