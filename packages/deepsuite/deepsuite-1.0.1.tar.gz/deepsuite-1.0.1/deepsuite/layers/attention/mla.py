"""Multi-Head Latent Attention (MLA) Implementation.

MLA nutzt Low-Rank KV-Compression für effizienten KV-Cache während der Inferenz.
Dies reduziert den Memory Footprint erheblich (32x in DeepSeek-V3).

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

import torch
from torch import nn
from torch.nn import functional

from .kv_compression import KVCompression
from .rope import RotaryPositionEmbedding


class MultiHeadLatentAttention(nn.Module):
    """Multi-Head Latent Attention mit Low-Rank KV-Compression.

    MLA komprimiert Keys und Values gemeinsam in einen niedrigdimensionalen
    Latent Space, was den KV-Cache während der Inferenz drastisch reduziert.

    Args:
        d: Embedding dimension
        n_h: Number of attention heads
        d_h: Dimension per head (default: d // n_h)
        d_c: KV compression dimension (deutlich kleiner als d)
        d_c_q: Query compression dimension
        d_h_R: Per-head RoPE dimension
        dropout: Dropout probability für Attention

    Shape:
        - Input: (batch_size, seq_len, d)
        - Output: (batch_size, seq_len, d)

    Memory Savings:
        Standard MHA KV-Cache: 2 * seq_len * n_h * d_h
        MLA KV-Cache: seq_len * d_c
        Reduction: ~32x bei DeepSeek-V3 Parametern

    Example:
        >>> mla = MultiHeadLatentAttention(d=7168, n_h=128, d_h=128, d_c=512, d_c_q=1536, d_h_R=64)
        >>> x = torch.randn(2, 512, 7168)  # (B, L, D)
        >>> out = mla(x)
        >>> print(out.shape)  # (2, 512, 7168)
    """

    def __init__(
        self,
        d: int,
        n_h: int,
        d_h: int | None = None,
        d_c: int = 512,
        d_c_q: int = 1536,
        d_h_r: int = 64,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()

        self.d = d
        self.n_h = n_h
        self.d_h = d_h or (d // n_h)
        self.d_c = d_c
        self.d_c_q = d_c_q
        self.d_h_r = d_h_r

        # Scale factor für Attention
        self.scale = self.d_h**-0.5

        # Query Compression Path
        self.W_D_Q = nn.Linear(d, d_c_q, bias=False)
        self.W_U_Q = nn.Linear(d_c_q, n_h * self.d_h, bias=False)
        self.W_Q_R = nn.Linear(d_c_q, d_h_r * n_h, bias=False)

        # RoPE für Queries
        self.rope_q = RotaryPositionEmbedding(dim=d_h_r)

        # KV Compression
        self.kv_compression = KVCompression(d=d, d_c=d_c, n_h=n_h, d_h=self.d_h, d_h_r=d_h_r)

        # Output projection
        self.W_O = nn.Linear(n_h * self.d_h, d, bias=False)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        use_cache: bool = False,
        past_key_value: tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor] | None]:
        """Forward pass through MLA.

        Args:
            x: Input tensor (batch_size, seq_len, d)
            attention_mask: Optional attention mask (batch_size, seq_len, seq_len)
            use_cache: Whether to return cached keys/values für Inferenz
            past_key_value: Cached (keys, values) from previous step

        Returns:
            Tuple of (output, cached_kv) where:
                - output: (batch_size, seq_len, d)
                - cached_kv: Optional[(batch_size, seq_len, d_c)] für compressed KV
        """
        batch_size, seq_len, _ = x.shape

        # 1. Query Projection mit Compression
        # q_compressed shape: (batch_size, seq_len, d_c_q)
        q_compressed = self.W_D_Q(x)

        # q_base shape: (batch_size, seq_len, n_h * d_h)
        q_base = self.W_U_Q(q_compressed)

        # q_rope shape: (batch_size, seq_len, n_h * d_h_r)
        q_rope = self.W_Q_R(q_compressed)

        # Reshape für multi-head
        # q_base: (batch_size, seq_len, n_h, d_h - d_h_r)
        q_base = q_base.view(batch_size, seq_len, self.n_h, -1)

        # q_rope: (batch_size, seq_len, n_h, d_h_r)
        q_rope = q_rope.view(batch_size, seq_len, self.n_h, self.d_h_r)

        # 2. Key & Value Projection mit Compression
        k, v = self.kv_compression(x)

        # 3. Apply RoPE zu Queries und Keys
        q_rope, k_rope = self.rope_q(q_rope, k[..., -self.d_h_r :], seq_len=seq_len)

        # Update k mit rotated Teil
        k = torch.cat([k[..., : -self.d_h_r], k_rope], dim=-1)

        # Concatenate Query: q = [q_base; q_rope]
        # q shape: (batch_size, seq_len, n_h, d_h)
        q = torch.cat([q_base, q_rope], dim=-1)

        # 4. Handle Caching für Inferenz
        if use_cache and past_key_value is not None:
            # Concatenate mit cached KV
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=1)
            v = torch.cat([past_v, v], dim=1)

        # 5. Scaled Dot-Product Attention
        # Transpose für matmul: (B, H, L, D)
        q = q.transpose(1, 2)  # (batch_size, n_h, seq_len, d_h)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Attention scores: (B, H, L, L)
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        # Apply mask if provided
        if attention_mask is not None:
            # Mask shape: (batch_size, 1, seq_len, seq_len) oder (batch_size, seq_len, seq_len)
            if attention_mask.dim() == 3:
                attention_mask = attention_mask.unsqueeze(1)
            attn_scores = attn_scores.masked_fill(attention_mask == 0, float("-inf"))

        # Softmax
        attn_weights = functional.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Weighted sum: (B, H, L, D_h)
        attn_output = torch.matmul(attn_weights, v)

        # 6. Reshape und Output Projection
        # (B, H, L, D_h) -> (B, L, H, D_h) -> (B, L, H*D_h)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.n_h * self.d_h)

        # Output projection: (B, L, D)
        output = self.W_O(attn_output)

        # 7. Return with optional cache
        cached_kv = (k, v) if use_cache else None

        return output, cached_kv

    def extra_repr(self) -> str:
        """Return extra representation string for debugging."""
        compression_ratio = (2 * self.n_h * self.d_h) / self.d_c
        return (
            f"d={self.d}, n_h={self.n_h}, d_h={self.d_h}, "
            f"d_c={self.d_c}, d_c_q={self.d_c_q}, d_h_r={self.d_h_r}, "
            f"kv_compression_ratio={compression_ratio:.1f}x"
        )


class MultiHeadLatentAttentionWithFlash(MultiHeadLatentAttention):
    """MLA mit Flash Attention Support für noch schnellere Verarbeitung.

    Nutzt torch.nn.functional.scaled_dot_product_attention wenn verfügbar,
    sonst fällt es zurück auf Standard-Implementation.

    Requires: PyTorch >= 2.0
    """

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        use_cache: bool = False,
        past_key_value: tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor] | None]:
        """Forward mit Flash Attention."""
        batch_size, seq_len, _ = x.shape

        # Query, Key, Value Projection (same as base)
        q_compressed = self.W_D_Q(x)
        q_base = self.W_U_Q(q_compressed)
        q_rope = self.W_Q_R(q_compressed)

        q_base = q_base.view(batch_size, seq_len, self.n_h, -1)
        q_rope = q_rope.view(batch_size, seq_len, self.n_h, self.d_h_R)

        k, v = self.kv_compression(x)

        # Apply RoPE
        q_rope, k_rope = self.rope_q(q_rope, k[..., -self.d_h_R :], seq_len=seq_len)
        k = torch.cat([k[..., : -self.d_h_R], k_rope], dim=-1)
        q = torch.cat([q_base, q_rope], dim=-1)

        # Handle caching
        if use_cache and past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=1)
            v = torch.cat([past_v, v], dim=1)

        # Transpose: (B, L, H, D) -> (B, H, L, D)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Flash Attention (PyTorch 2.0+)
        try:
            attn_output = functional.scaled_dot_product_attention(
                q,
                k,
                v,
                attn_mask=attention_mask,
                dropout_p=self.dropout.p if self.training else 0.0,
                is_causal=(attention_mask is None),  # Causal mask wenn keine explizite Mask
            )
        except AttributeError:
            # Fallback zu Standard-Attention
            attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
            if attention_mask is not None:
                if attention_mask.dim() == 3:
                    attention_mask = attention_mask.unsqueeze(1)
                attn_scores = attn_scores.masked_fill(attention_mask == 0, float("-inf"))
            attn_weights = functional.softmax(attn_scores, dim=-1)
            attn_weights = self.dropout(attn_weights)
            attn_output = torch.matmul(attn_weights, v)

        # Reshape und Output
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.n_h * self.d_h)
        output = self.W_O(attn_output)

        cached_kv = (k, v) if use_cache else None
        return output, cached_kv
