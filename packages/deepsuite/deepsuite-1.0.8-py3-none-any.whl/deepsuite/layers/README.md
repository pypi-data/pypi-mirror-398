# Layers

Neural network layers and components.

## Modules

### Attention Mechanisms

- **`attention/`** - Attention mechanisms
  - `mla.py` - Multi-Head Latent Attention (DeepSeek-V3)
  - `rope.py` - Rotary Position Embeddings (RoPE)
  - `kv_compression.py` - KV-cache compression

### Mixture-of-Experts

- **`moe.py`** - DeepSeek-V3 MoE with auxiliary-loss-free load balancing

### Specialized Layers

- **`bottleneck.py`** - Bottleneck layer for ResNet-like architectures
- **`complex.py`** - Complex-valued neural networks for audio
- **`dft.py`** - Differentiable Fourier Transform
- **`hermite.py`** - Hermite polynomials for feature expansion
- **`laguerre.py`** - Laguerre polynomials for feature expansion

## Usage

### Multi-Head Latent Attention

```python
from deepsuite.layers.attention import MultiHeadLatentAttention

mla = MultiHeadLatentAttention(
    d=2048,          # Model dimension
    n_h=16,          # Number of heads
    d_h_c=256,       # Compressed KV dimension
    d_h_r=64,        # RoPE dimension per head
)

output = mla(x, attention_mask)  # (batch, seq_len, d)
```

### Rotary Position Embeddings

```python
from deepsuite.layers.attention import RotaryPositionEmbedding

rope = RotaryPositionEmbedding(
    dim=64,           # Dimension per head
    max_seq_len=2048,
    base=10000
)

q_rotated, k_rotated = rope(q, k, seq_len)
```

### Mixture-of-Experts

```python
from deepsuite.layers import DeepSeekMoE

moe = DeepSeekMoE(
    d_model=2048,
    n_shared_experts=1,      # Always active
    n_routed_experts=256,    # Selectively activated
    n_expert_per_token=8,    # Top-K routing
    expert_intermediate_size=8192
)

output, router_logits = moe(x)  # (batch, seq_len, d_model)
```

### Complex-valued Layers

```python
from deepsuite.layers import ComplexConv2d, ComplexBatchNorm2d

conv = ComplexConv2d(
    in_channels=64,
    out_channels=128,
    kernel_size=3,
    padding=1
)

bn = ComplexBatchNorm2d(128)

# Input: (batch, channels, height, width, 2) - letzte Dim: [real, imag]
out = bn(conv(x_complex))
```

## Features

### Attention

- ✅ Effiziente MLA-Implementierung mit KV-Kompression
- ✅ RoPE für relative Positionskodierung
- ✅ Flash Attention kompatibel
- ✅ Kausal Masking für Autoregressive Models

### MoE

- ✅ Auxiliary-Loss-Free Load Balancing
- ✅ Expert Parallelism-ready
- ✅ Dynamisches Top-K Routing
- ✅ Shared + Routed Experts

### Specialized

- ✅ Complex-valued Operations für Audio Processing
- ✅ Polynomial Feature Expansion (Hermite, Laguerre)
- ✅ Differenzierbare DFT/FFT
- ✅ Effiziente Bottleneck-Strukturen

## Layer-Hierarchie

```
layers/
├── attention/
│   ├── mla.py          # Multi-Head Latent Attention
│   ├── rope.py         # Rotary Position Embeddings
│   └── kv_compression.py
├── moe.py              # Mixture-of-Experts
├── bottleneck.py       # ResNet Bottleneck
├── complex.py          # Complex Neural Networks
├── dft.py              # Fourier Transform
├── hermite.py          # Hermite Polynomials
└── laguerre.py         # Laguerre Polynomials
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- MLA & Attention: [docs/llm_modules.md](../../../docs/llm_modules.md)
- MoE: [docs/moe.md](../../../docs/moe.md)
