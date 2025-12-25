"""KV Compression für Multi-Head Latent Attention.

Implementiert Low-Rank Joint Compression für Keys und Values zur
Reduzierung des KV-Cache während der Inferenz.

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

import torch
from torch import nn

from .rope import RotaryPositionEmbedding


class KVCompression(nn.Module):
    """Low-Rank KV Compression für effiziente Attention.

    Komprimiert Keys und Values von d-dimensional zu d_c-dimensional
    (d_c << d), um den KV-Cache während der Inferenz zu reduzieren.

    Args:
        d: Input dimension (embedding dimension)
        d_c: Compressed dimension für KV (typisch d_c << d)
        n_h: Number of attention heads
        d_h: Dimension per head
        d_h_R: Per-head RoPE dimension

    Shape:
        - Input: (batch_size, seq_len, d)
        - Output Keys: (batch_size, seq_len, n_h, d_h)
        - Output Values: (batch_size, seq_len, n_h, d_h)

    Example:
        >>> kv_compress = KVCompression(d=7168, d_c=512, n_h=128, d_h=128, d_h_R=64)
        >>> x = torch.randn(2, 512, 7168)  # (B, L, D)
        >>> k, v = kv_compress(x)
        >>> print(k.shape)  # (2, 512, 128, 128)
    """

    def __init__(self, d: int, d_c: int, n_h: int, d_h: int, d_h_r: int = 64) -> None:
        super().__init__()

        self.d = d
        self.d_c = d_c
        self.n_h = n_h
        self.d_h = d_h
        self.d_h_r = d_h_r

        # Down-projection: d -> d_c (gemeinsam für K und V)
        self.W_D_KV = nn.Linear(d, d_c, bias=False)

        # Up-projections: d_c -> (n_h * d_h)
        self.W_U_K = nn.Linear(d_c, n_h * d_h, bias=False)
        self.W_U_V = nn.Linear(d_c, n_h * d_h, bias=False)

        # RoPE für Keys (nur auf einem Teil der Dimension)
        self.W_K_R = nn.Linear(d, d_h_r, bias=False)
        self.rope = RotaryPositionEmbedding(dim=d_h_r)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Komprimiere Input zu Keys und Values.

        Args:
            x: Input tensor (batch_size, seq_len, d)

        Returns:
            Tuple of (keys, values):
                - keys: (batch_size, seq_len, n_h, d_h)
                - values: (batch_size, seq_len, n_h, d_h)
        """
        batch_size, seq_len, _ = x.shape

        # 1. Down-project zu compressed representation
        # c^{KV} shape: (batch_size, seq_len, d_c)
        c_kv = self.W_D_KV(x)

        # 2. Up-project zu Keys und Values
        # k_base shape: (batch_size, seq_len, n_h * d_h)
        k_base = self.W_U_K(c_kv)
        v = self.W_U_V(c_kv)

        # 3. RoPE für Keys
        # k_rope shape: (batch_size, seq_len, d_h_R)
        k_rope = self.W_K_R(x)

        # Reshape für multi-head
        # k_base: (batch_size, seq_len, n_h, d_h - d_h_R)
        k_base = k_base.view(batch_size, seq_len, self.n_h, -1)

        # k_rope für RoPE vorbereiten
        # k_rope: (batch_size, seq_len, n_h, d_h_r)
        k_rope = k_rope.view(batch_size, seq_len, 1, self.d_h_r).expand(
            batch_size, seq_len, self.n_h, self.d_h_r
        )

        # Apply RoPE (nutzt identische Query für Kompatibilität)
        k_rope, _ = self.rope(k_rope, k_rope, seq_len=seq_len)

        # 4. Concatenate: k = [k_base; k_rope]
        # k shape: (batch_size, seq_len, n_h, d_h)
        k = torch.cat([k_base, k_rope], dim=-1)

        # 5. Reshape values
        # v shape: (batch_size, seq_len, n_h, d_h)
        v = v.view(batch_size, seq_len, self.n_h, self.d_h)

        return k, v

    def extra_repr(self) -> str:
        """Return extra representation string for debugging."""
        compression_ratio = self.d / self.d_c
        return (
            f"d={self.d}, d_c={self.d_c}, n_h={self.n_h}, d_h={self.d_h}, "
            f"d_h_r={self.d_h_r}, compression_ratio={compression_ratio:.1f}x"
        )


class AdaptiveKVCompression(KVCompression):
    """Adaptive KV Compression mit layer-spezifischen Kompressionsraten.

    Erlaubt unterschiedliche Kompressionsraten für verschiedene Transformer-Layer,
    da tiefere Layer oft weniger Kompression benötigen.

    Args:
        d: Input dimension
        d_c: Compressed dimension
        n_h: Number of heads
        d_h: Dimension per head
        d_h_R: RoPE dimension
        layer_idx: Layer index (0-based)
        total_layers: Total number of layers
        min_compression: Minimum compression ratio
        max_compression: Maximum compression ratio

    Example:
        >>> # Layer 0: max compression, Layer 60: min compression
        >>> kv_compress = AdaptiveKVCompression(
        ...     d=7168,
        ...     d_c=512,
        ...     n_h=128,
        ...     d_h=128,
        ...     layer_idx=0,
        ...     total_layers=61,
        ...     min_compression=8,
        ...     max_compression=32,
        ... )
    """

    def __init__(
        self,
        d: int,
        d_c: int,
        n_h: int,
        d_h: int,
        d_h_r: int = 64,
        layer_idx: int = 0,
        total_layers: int = 61,
        min_compression: float = 8.0,
        max_compression: float = 32.0,
    ) -> None:
        # Adaptiere d_c basierend auf layer_idx
        layer_ratio = layer_idx / max(total_layers - 1, 1)
        compression_ratio = max_compression - ((max_compression - min_compression) * layer_ratio)

        # Berechne adaptive d_c
        adaptive_d_c = int(d / compression_ratio)
        adaptive_d_c = max(adaptive_d_c, d_c)  # Nicht kleiner als d_c

        super().__init__(d=d, d_c=adaptive_d_c, n_h=n_h, d_h=d_h, d_h_r=d_h_r)

        self.layer_idx = layer_idx
        self.total_layers = total_layers
        self.compression_ratio = compression_ratio

    def extra_repr(self) -> str:
        """Return extra representation string for debugging."""
        base_repr = super().extra_repr()
        return (
            f"{base_repr}, layer_idx={self.layer_idx}, "
            f"adaptive_compression={self.compression_ratio:.1f}x"
        )
