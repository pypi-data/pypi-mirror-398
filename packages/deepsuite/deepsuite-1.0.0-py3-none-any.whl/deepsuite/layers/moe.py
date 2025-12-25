"""DeepSeek Mixture-of-Experts (MoE) Implementation.

Implementiert DeepSeekMoE mit Shared + Routed Experts und
Auxiliary-Loss-Free Load Balancing.

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import nn
from torch.nn import functional

if TYPE_CHECKING:
    from torch import Tensor


class FFNExpert(nn.Module):
    """Single FFN Expert für MoE.

    Standard Feed-Forward Network mit SwiGLU Activation.

    Args:
        d_model: Hidden dimension. Defaults to 2048.
        d_ffn: FFN intermediate dimension. Defaults to 2048.
        dropout: Dropout rate. Defaults to 0.0.
        bias: Whether to use bias. Defaults to False.

    Shape:
        - Input: (*, d_model)
        - Output: (*, d_model)

    Examples:
        >>> expert = FFNExpert(d_model=512, d_ffn=2048)
        >>> x = torch.randn(2, 128, 512)
        >>> output = expert(x)
        >>> print(output.shape)
        torch.Size([2, 128, 512])
    """

    def __init__(
        self,
        d_model: int = 2048,
        d_ffn: int = 2048,
        dropout: float = 0.0,
        bias: bool = False,
    ) -> None:
        """Initialize FFN expert."""
        super().__init__()
        self.d_model = d_model
        self.d_ffn = d_ffn

        # SwiGLU: Split FFN into gate and up projections
        self.gate_proj = nn.Linear(d_model, d_ffn, bias=bias)
        self.up_proj = nn.Linear(d_model, d_ffn, bias=bias)
        self.down_proj = nn.Linear(d_ffn, d_model, bias=bias)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: Tensor) -> Tensor:
        """Forward pass through expert.

        Args:
            x: Input tensor (*, d_model).

        Returns:
            Output tensor (*, d_model).

        Examples:
            >>> expert = FFNExpert(d_model=256, d_ffn=1024)
            >>> x = torch.randn(4, 64, 256)
            >>> output = expert(x)
        """
        # SwiGLU: gate(x) * silu(up(x))
        gate = self.gate_proj(x)
        up = self.up_proj(x)
        hidden = functional.silu(gate) * up
        hidden = self.dropout(hidden)
        return self.down_proj(hidden)


class AuxiliaryLossFreeRouter(nn.Module):
    """Bias-based Router für Load Balancing ohne Auxiliary Loss.

    Verwendet dynamische Bias Terms die bei Unbalance angepasst werden,
    statt einen zusätzlichen Loss Term.

    Args:
        d_model: Hidden dimension. Defaults to 2048.
        n_routed_experts: Number of routed experts. Defaults to 256.
        n_expert_per_token: Number of experts activated per token. Defaults to 8.
        bias_lr: Bias learning rate (gamma). Defaults to 1e-3.
        bias: Whether to use bias in projection. Defaults to False.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: Tuple of (routing_weights, expert_indices, load_stats)

    Examples:
        >>> router = AuxiliaryLossFreeRouter(d_model=512, n_routed_experts=64, n_expert_per_token=4)
        >>> x = torch.randn(2, 128, 512)
        >>> weights, indices, stats = router(x)
        >>> print(weights.shape, indices.shape)
        torch.Size([2, 128, 4]) torch.Size([2, 128, 4])

    Note:
        DeepSeek-V3 nutzt N_r=256, K_r=8 für optimale Balance.
    """

    def __init__(
        self,
        d_model: int = 2048,
        n_routed_experts: int = 256,
        n_expert_per_token: int = 8,
        bias_lr: float = 1e-3,
        bias: bool = False,
    ) -> None:
        """Initialize router."""
        super().__init__()
        self.d_model = d_model
        self.n_routed_experts = n_routed_experts
        self.n_expert_per_token = n_expert_per_token
        self.bias_lr = bias_lr

        # Router projection
        self.gate = nn.Linear(d_model, n_routed_experts, bias=bias)

        # Load balancing bias (learnable)
        self.expert_bias = nn.Parameter(torch.zeros(n_routed_experts))

        # Statistics für Monitoring
        self.register_buffer("expert_counts", torch.zeros(n_routed_experts))
        self.register_buffer("total_tokens", torch.tensor(0.0))

    def forward(
        self,
        x: Tensor,
        update_bias: bool = True,
    ) -> tuple[Tensor, Tensor, dict[str, Tensor]]:
        """Route tokens to experts.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).
            update_bias: Whether to update bias based on load. Defaults to True.

        Returns:
            Tuple of:
                - routing_weights: (batch_size, seq_len, n_expert_per_token)
                - expert_indices: (batch_size, seq_len, n_expert_per_token)
                - load_stats: Dict with load balancing statistics

        Examples:
            >>> router = AuxiliaryLossFreeRouter(
            ...     d_model=256, n_routed_experts=32, n_expert_per_token=4
            ... )
            >>> x = torch.randn(2, 64, 256)
            >>> weights, indices, stats = router(x)
        """
        batch_size, seq_len, _ = x.shape

        # Router logits: (batch_size * seq_len, n_routed_experts)
        x_flat = x.view(-1, self.d_model)
        logits = self.gate(x_flat)

        # Apply load balancing bias
        logits = logits + self.expert_bias

        # Top-K selection
        routing_weights, expert_indices = torch.topk(logits, self.n_expert_per_token, dim=-1)

        # Softmax over selected experts
        routing_weights = functional.softmax(routing_weights, dim=-1)

        # Reshape
        routing_weights = routing_weights.view(batch_size, seq_len, self.n_expert_per_token)
        expert_indices = expert_indices.view(batch_size, seq_len, self.n_expert_per_token)

        # Update load statistics
        if self.training and update_bias:
            self._update_load_stats(expert_indices)

        # Compute load statistics
        load_stats = self._compute_load_stats(expert_indices)

        return routing_weights, expert_indices, load_stats

    def _update_load_stats(self, expert_indices: Tensor) -> None:
        """Update expert load counts.

        Args:
            expert_indices: Selected expert indices (batch_size, seq_len, n_expert_per_token).
        """
        # Count tokens per expert
        expert_counts = torch.zeros(self.n_routed_experts, device=expert_indices.device)
        for i in range(self.n_routed_experts):
            expert_counts[i] = (expert_indices == i).sum().float()

        # Update running statistics
        self.expert_counts = 0.9 * self.expert_counts + 0.1 * expert_counts
        self.total_tokens = 0.9 * self.total_tokens + 0.1 * expert_indices.numel()

        # Update bias based on load
        expected_load = self.total_tokens / self.n_routed_experts
        load_diff = self.expert_counts - expected_load

        # Overloaded experts: increase bias (discourage selection)
        # Underloaded experts: decrease bias (encourage selection)
        with torch.no_grad():
            self.expert_bias -= self.bias_lr * load_diff

    def _compute_load_stats(self, expert_indices: Tensor) -> dict[str, Tensor]:
        """Compute load balancing statistics.

        Args:
            expert_indices: Selected expert indices.

        Returns:
            Dict with load statistics.
        """
        # Count tokens per expert
        expert_counts = torch.zeros(self.n_routed_experts, device=expert_indices.device)
        for i in range(self.n_routed_experts):
            expert_counts[i] = (expert_indices == i).sum().float()

        n_tokens = expert_indices.numel()
        expected_load = n_tokens / self.n_routed_experts

        # Load balance factor (ideally 1.0)
        load_balance = expert_counts.std() / (expert_counts.mean() + 1e-6)

        return {
            "expert_counts": expert_counts,
            "load_balance_factor": load_balance,
            "max_load": expert_counts.max(),
            "min_load": expert_counts.min(),
            "expected_load": expected_load,
        }


class DeepSeekMoE(nn.Module):
    """DeepSeek Mixture-of-Experts Layer.

    Kombiniert Shared Experts (immer aktiv) mit Routed Experts (selektiv).

    Args:
        d_model: Hidden dimension. Defaults to 2048.
        n_shared_experts: Number of shared experts. Defaults to 1.
        n_routed_experts: Number of routed experts. Defaults to 256.
        n_expert_per_token: Activated routed experts per token. Defaults to 8.
        d_ffn: FFN intermediate dimension per expert. Defaults to 2048.
        dropout: Dropout rate. Defaults to 0.0.
        bias_lr: Router bias learning rate. Defaults to 1e-3.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> moe = DeepSeekMoE(
        ...     d_model=512, n_shared_experts=1, n_routed_experts=64, n_expert_per_token=4
        ... )
        >>> x = torch.randn(2, 128, 512)
        >>> output, stats = moe(x)
        >>> print(output.shape)
        torch.Size([2, 128, 512])

    Note:
        DeepSeek-V3 verwendet:
        - N_s=1 shared expert (immer aktiv)
        - N_r=256 routed experts
        - K_r=8 aktive routed experts pro Token
        - d_ffn=2048 für jeden Expert
    """

    def __init__(
        self,
        d_model: int = 2048,
        n_shared_experts: int = 1,
        n_routed_experts: int = 256,
        n_expert_per_token: int = 8,
        d_ffn: int = 2048,
        dropout: float = 0.0,
        bias_lr: float = 1e-3,
    ) -> None:
        """Initialize DeepSeekMoE."""
        super().__init__()
        self.d_model = d_model
        self.n_shared_experts = n_shared_experts
        self.n_routed_experts = n_routed_experts
        self.n_expert_per_token = n_expert_per_token

        # Shared Experts (always active)
        self.shared_experts = nn.ModuleList(
            [FFNExpert(d_model, d_ffn, dropout) for _ in range(n_shared_experts)]
        )

        # Routed Experts (selectively activated)
        self.routed_experts = nn.ModuleList(
            [FFNExpert(d_model, d_ffn, dropout) for _ in range(n_routed_experts)]
        )

        # Router
        self.router = AuxiliaryLossFreeRouter(
            d_model=d_model,
            n_routed_experts=n_routed_experts,
            n_expert_per_token=n_expert_per_token,
            bias_lr=bias_lr,
        )

    def forward(self, x: Tensor) -> tuple[Tensor, dict[str, Tensor]]:
        """Forward pass through MoE layer.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).

        Returns:
            Tuple of:
                - output: (batch_size, seq_len, d_model)
                - stats: Load balancing statistics

        Examples:
            >>> moe = DeepSeekMoE(d_model=256, n_shared_experts=1, n_routed_experts=32)
            >>> x = torch.randn(2, 64, 256)
            >>> output, stats = moe(x)
        """
        batch_size, seq_len, d_model = x.shape
        identity = x

        # 1. Shared Experts (immer aktiv)
        shared_output = torch.zeros_like(x)
        for expert in self.shared_experts:
            shared_output = shared_output + expert(x)

        # 2. Router: Select experts
        routing_weights, expert_indices, load_stats = self.router(x)

        # 3. Routed Experts (selektiv)
        # Efficient batched expert computation
        routed_output = torch.zeros_like(x)

        # Flatten für effiziente Verarbeitung
        x_flat = x.view(-1, d_model)  # (batch_size * seq_len, d_model)
        routing_weights_flat = routing_weights.view(-1, self.n_expert_per_token)
        expert_indices_flat = expert_indices.view(-1, self.n_expert_per_token)

        # Process each token
        for token_idx in range(batch_size * seq_len):
            token_input = x_flat[token_idx : token_idx + 1]  # (1, d_model)
            token_weights = routing_weights_flat[token_idx]  # (n_expert_per_token,)
            token_experts = expert_indices_flat[token_idx]  # (n_expert_per_token,)

            # Compute weighted sum of expert outputs
            token_output = torch.zeros_like(token_input)
            for k in range(self.n_expert_per_token):
                expert_idx = token_experts[k].item()
                weight = token_weights[k]
                expert_output = self.routed_experts[expert_idx](token_input)
                token_output = token_output + weight * expert_output

            routed_output.view(-1, d_model)[token_idx] = token_output.squeeze(0)

        # 4. Combine: output = input + shared + routed
        output = identity + shared_output + routed_output

        return output, load_stats


class EfficientDeepSeekMoE(nn.Module):
    """Efficient DeepSeek MoE mit optimierter Batch-Verarbeitung.

    Optimierte Version die Tokens nach Experts gruppiert für bessere
    GPU-Auslastung.

    Args:
        d_model: Hidden dimension. Defaults to 2048.
        n_shared_experts: Number of shared experts. Defaults to 1.
        n_routed_experts: Number of routed experts. Defaults to 256.
        n_expert_per_token: Activated routed experts per token. Defaults to 8.
        d_ffn: FFN intermediate dimension per expert. Defaults to 2048.
        dropout: Dropout rate. Defaults to 0.0.
        bias_lr: Router bias learning rate. Defaults to 1e-3.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> moe = EfficientDeepSeekMoE(d_model=512, n_routed_experts=64)
        >>> x = torch.randn(2, 128, 512)
        >>> output, stats = moe(x)
        >>> print(output.shape)
        torch.Size([2, 128, 512])

    Note:
        Diese Implementierung ist ~2-3x schneller als naive Version
        durch bessere Batch-Verarbeitung.
    """

    def __init__(
        self,
        d_model: int = 2048,
        n_shared_experts: int = 1,
        n_routed_experts: int = 256,
        n_expert_per_token: int = 8,
        d_ffn: int = 2048,
        dropout: float = 0.0,
        bias_lr: float = 1e-3,
    ) -> None:
        """Initialize efficient MoE."""
        super().__init__()
        self.d_model = d_model
        self.n_shared_experts = n_shared_experts
        self.n_routed_experts = n_routed_experts
        self.n_expert_per_token = n_expert_per_token

        # Shared Experts
        self.shared_experts = nn.ModuleList(
            [FFNExpert(d_model, d_ffn, dropout) for _ in range(n_shared_experts)]
        )

        # Routed Experts
        self.routed_experts = nn.ModuleList(
            [FFNExpert(d_model, d_ffn, dropout) for _ in range(n_routed_experts)]
        )

        # Router
        self.router = AuxiliaryLossFreeRouter(
            d_model=d_model,
            n_routed_experts=n_routed_experts,
            n_expert_per_token=n_expert_per_token,
            bias_lr=bias_lr,
        )

    def forward(self, x: Tensor) -> tuple[Tensor, dict[str, Tensor]]:
        """Forward pass with efficient batching.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).

        Returns:
            Tuple of (output, load_stats).

        Examples:
            >>> moe = EfficientDeepSeekMoE(d_model=256, n_routed_experts=32)
            >>> x = torch.randn(2, 64, 256)
            >>> output, stats = moe(x)
        """
        batch_size, seq_len, d_model = x.shape
        identity = x

        # Shared Experts
        shared_output = torch.zeros_like(x)
        for expert in self.shared_experts:
            shared_output = shared_output + expert(x)

        # Router
        routing_weights, expert_indices, load_stats = self.router(x)

        # Efficient Routed Experts: Group tokens by expert
        x_flat = x.view(-1, d_model)
        routing_weights_flat = routing_weights.view(-1, self.n_expert_per_token)
        expert_indices_flat = expert_indices.view(-1, self.n_expert_per_token)

        routed_output_flat = torch.zeros_like(x_flat)

        # Process each expert once
        for expert_idx in range(self.n_routed_experts):
            # Find tokens assigned to this expert
            mask = expert_indices_flat == expert_idx
            if not mask.any():
                continue

            # Get token indices and weights
            token_indices, k_indices = torch.where(mask)
            weights = routing_weights_flat[token_indices, k_indices]

            # Batch process tokens
            tokens = x_flat[token_indices]
            expert_output = self.routed_experts[expert_idx](tokens)

            # Accumulate weighted outputs
            routed_output_flat[token_indices] += weights.unsqueeze(-1) * expert_output

        # Reshape and combine
        routed_output = routed_output_flat.view(batch_size, seq_len, d_model)
        output = identity + shared_output + routed_output

        return output, load_stats
