"""Rotary Position Embedding (RoPE) Implementation.

Basierend auf "RoFormer: Enhanced Transformer with Rotary Position Embedding"
(Su et al., 2021) und DeepSeek-V3 Technical Report.

Referenz: https://arxiv.org/html/2412.19437v2
"""

import torch
from torch import nn


class RotaryPositionEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) für effiziente Position Encoding.

    RoPE rotiert Query/Key Vektoren basierend auf ihrer Position, ohne
    explizite Position Embeddings zu benötigen.

    Args:
        dim: Dimension des Embeddings (muss gerade sein)
        max_seq_len: Maximale Sequenzlänge
        base: Basis für die Frequenzen (default: 10000)

    Shape:
        - Input: (batch_size, seq_len, n_heads, head_dim)
        - Output: (batch_size, seq_len, n_heads, head_dim)

    Example:
        >>> rope = RotaryPositionEmbedding(dim=64, max_seq_len=2048)
        >>> q = torch.randn(2, 512, 8, 64)  # (B, L, H, D)
        >>> k = torch.randn(2, 512, 8, 64)
        >>> q_rotated, k_rotated = rope(q, k)
    """

    def __init__(self, dim: int, max_seq_len: int = 2048, base: float = 10000.0) -> None:
        super().__init__()
        assert dim % 2 == 0, f"Dimension must be even, got {dim}"

        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = base

        # Frequenzen berechnen: θ_i = base^(-2i/d) für i = 0, 1, ..., d/2-1
        inv_freq = 1.0 / (self.base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

        # Position indices vorberechnen
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len: int) -> None:
        """Baue Cache für sin/cos Werte."""
        # Position indices: [0, 1, 2, ..., seq_len-1]
        t = torch.arange(seq_len, dtype=torch.float32)

        # Compute frequencies: outer product of positions and inv_freq
        # freqs shape: (seq_len, dim/2)
        freqs = torch.outer(t, self.inv_freq)

        # Concatenate to get full dimension
        # emb shape: (seq_len, dim)
        emb = torch.cat([freqs, freqs], dim=-1)

        # Cache sin und cos
        self.register_buffer("cos_cached", emb.cos(), persistent=False)
        self.register_buffer("sin_cached", emb.sin(), persistent=False)

    def _rotate_half(self, x: torch.Tensor) -> torch.Tensor:
        """Rotiere die Hälfte der versteckten Dimensionen.

        Args:
            x: Input tensor (..., dim)

        Returns:
            Rotierter tensor (..., dim)
        """
        x1, x2 = x.chunk(2, dim=-1)
        return torch.cat([-x2, x1], dim=-1)

    def forward(
        self, q: torch.Tensor, k: torch.Tensor, seq_len: int | None = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Apply RoPE zu Query und Key Tensoren.

        Args:
            q: Query tensor (batch_size, seq_len, n_heads, head_dim)
            k: Key tensor (batch_size, seq_len, n_heads, head_dim)
            seq_len: Optionale Sequenzlänge (für dynamische Längen)

        Returns:
            Tuple of (q_rotated, k_rotated)
        """
        if seq_len is None:
            seq_len = q.shape[1]

        # Baue Cache neu wenn Sequenzlänge größer ist
        if seq_len > self.max_seq_len:
            self._build_cache(seq_len)

        # Get cached sin/cos values
        cos = self.cos_cached[:seq_len, ...]  # (seq_len, dim)
        sin = self.sin_cached[:seq_len, ...]  # (seq_len, dim)

        # Reshape für broadcasting: (1, seq_len, 1, dim)
        cos = cos.unsqueeze(0).unsqueeze(2)
        sin = sin.unsqueeze(0).unsqueeze(2)

        # Apply rotation: x * cos + rotate_half(x) * sin
        q_embed = (q * cos) + (self._rotate_half(q) * sin)
        k_embed = (k * cos) + (self._rotate_half(k) * sin)

        return q_embed, k_embed

    def extra_repr(self) -> str:
        """Return extra representation string for debugging."""
        return f"dim={self.dim}, max_seq_len={self.max_seq_len}, base={self.base}"


class RotaryPositionEmbeddingLarge(RotaryPositionEmbedding):
    """RoPE für sehr lange Sequenzen mit verbesserter Skalierung.

    Verwendet einen größeren base-Wert für längere Sequenzen, wie in
    DeepSeek-V3 verwendet.

    Args:
        dim: Dimension des Embeddings
        max_seq_len: Maximale Sequenzlänge (default: 4096)
        base: Basis für die Frequenzen (default: 160000 für lange Sequenzen)
    """

    def __init__(self, dim: int, max_seq_len: int = 4096, base: float = 160000.0) -> None:
        super().__init__(dim=dim, max_seq_len=max_seq_len, base=base)
