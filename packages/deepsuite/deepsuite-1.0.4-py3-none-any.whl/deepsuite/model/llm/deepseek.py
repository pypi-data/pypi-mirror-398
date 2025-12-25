"""DeepSeek-V3 Language Model Module.

PyTorch Lightning Module für DeepSeek-V3 Architektur mit MLA und MoE.

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.heads.language_modeling import CombinedLMHead
from deepsuite.layers.attention.mla import MultiHeadLatentAttention
from deepsuite.layers.moe import EfficientDeepSeekMoE
from deepsuite.lightning_base.module import BaseModule
from deepsuite.loss.language_modeling import (
    LanguageModelingLoss,
    MultiTokenPredictionLoss,
    PerplexityMetric,
    TokenAccuracyMetric,
)

if TYPE_CHECKING:
    from torch import Tensor


class DeepSeekTransformerBlock(nn.Module):
    """DeepSeek-V3 Transformer Block mit MLA und MoE.

    Args:
        d_model: Hidden dimension. Defaults to 2048.
        n_heads: Number of attention heads. Defaults to 32.
        d_head: Dimension per head. Defaults to 64.
        d_kv_compression: KV compression dimension. Defaults to 512.
        d_q_compression: Query compression dimension. Defaults to 512.
        d_rope: RoPE dimension per head. Defaults to 64.
        d_ffn: FFN intermediate dimension. Defaults to 8192.
        dropout: Dropout rate. Defaults to 0.0.
        layer_norm_eps: Layer norm epsilon. Defaults to 1e-6.
        use_moe: Whether to use MoE instead of standard FFN. Defaults to False.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> block = DeepSeekTransformerBlock(d_model=768, n_heads=12)
        >>> x = torch.randn(2, 128, 768)
        >>> output = block(x)
        >>> print(output.shape)
        torch.Size([2, 128, 768])

    Note:
        MoE Layer wird in Phase 2 hinzugefügt. Aktuell nutzen wir Standard FFN.
    """

    def __init__(
        self,
        d_model: int = 2048,
        n_heads: int = 32,
        d_head: int = 64,
        d_kv_compression: int = 512,
        d_q_compression: int = 512,
        d_rope: int = 64,
        d_ffn: int = 8192,
        dropout: float = 0.0,
        layer_norm_eps: float = 1e-6,
        use_moe: bool = False,
        n_shared_experts: int = 1,
        n_routed_experts: int = 256,
        n_expert_per_token: int = 8,
    ) -> None:
        """Initialize DeepSeek transformer block."""
        super().__init__()
        self.d_model = d_model
        self.use_moe = use_moe

        # Pre-attention layer norm
        self.ln_1 = nn.LayerNorm(d_model, eps=layer_norm_eps)

        # Multi-Head Latent Attention
        self.attention = MultiHeadLatentAttention(
            d=d_model,
            n_h=n_heads,
            d_h=d_head,
            d_c=d_kv_compression,
            d_c_q=d_q_compression,
            d_h_r=d_rope,
            dropout=dropout,
        )

        # Pre-FFN layer norm
        self.ln_2 = nn.LayerNorm(d_model, eps=layer_norm_eps)

        # FFN oder MoE
        if use_moe:
            # DeepSeek MoE Layer
            self.ffn = EfficientDeepSeekMoE(
                d_model=d_model,
                n_shared_experts=n_shared_experts,
                n_routed_experts=n_routed_experts,
                n_expert_per_token=n_expert_per_token,
                d_ffn=d_ffn,
                dropout=dropout,
            )
        else:
            # Standard FFN: SwiGLU Activation
            self.ffn = nn.Sequential(
                nn.Linear(d_model, d_ffn),
                nn.SiLU(),
                nn.Dropout(dropout),
                nn.Linear(d_ffn, d_model),
                nn.Dropout(dropout),
            )

    def forward(
        self,
        x: Tensor,
        attention_mask: Tensor | None = None,
    ) -> Tensor:
        """Forward pass through transformer block.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).
            attention_mask: Optional attention mask (batch_size, seq_len, seq_len).

        Returns:
            Output tensor (batch_size, seq_len, d_model).

        Examples:
            >>> block = DeepSeekTransformerBlock(d_model=512, n_heads=8)
            >>> x = torch.randn(2, 64, 512)
            >>> output = block(x)
        """
        # Pre-norm + Attention + Residual
        residual = x
        x = self.ln_1(x)
        x, _ = self.attention(x, attention_mask=attention_mask)  # MLA returns (output, cache)
        x = residual + x

        # Pre-norm + FFN/MoE + Residual
        residual = x
        x = self.ln_2(x)

        if self.use_moe:
            # MoE returns (output, stats)
            x, _ = self.ffn(x)
            return residual + x
        # Standard FFN
        x = self.ffn(x)
        return residual + x


class DeepSeekV3(nn.Module):
    """DeepSeek-V3 Language Model.

    Args:
        vocab_size: Vocabulary size. Defaults to 50000.
        d_model: Hidden dimension. Defaults to 2048.
        n_layers: Number of transformer layers. Defaults to 24.
        n_heads: Number of attention heads. Defaults to 32.
        d_head: Dimension per head. Defaults to 64.
        d_kv_compression: KV compression dimension. Defaults to 512.
        d_q_compression: Query compression dimension. Defaults to 512.
        d_rope: RoPE dimension per head. Defaults to 64.
        d_ffn: FFN intermediate dimension. Defaults to 8192.
        max_seq_len: Maximum sequence length. Defaults to 2048.
        dropout: Dropout rate. Defaults to 0.1.
        layer_norm_eps: Layer norm epsilon. Defaults to 1e-6.
        use_mtp: Whether to use Multi-Token Prediction. Defaults to True.
        mtp_depth: MTP depth. Defaults to 1.
        tie_weights: Whether to tie embedding and output weights. Defaults to True.

    Shape:
        - Input: (batch_size, seq_len)
        - Output: (batch_size, seq_len, vocab_size)

    Examples:
        >>> model = DeepSeekV3(vocab_size=10000, d_model=512, n_layers=6)
        >>> input_ids = torch.randint(0, 10000, (2, 128))
        >>> logits = model(input_ids)
        >>> print(logits.shape)
        torch.Size([2, 128, 10000])
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        d_model: int = 2048,
        n_layers: int = 24,
        n_heads: int = 32,
        d_head: int = 64,
        d_kv_compression: int = 512,
        d_q_compression: int = 512,
        d_rope: int = 64,
        d_ffn: int = 8192,
        max_seq_len: int = 2048,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-6,
        use_mtp: bool = True,
        mtp_depth: int = 1,
        tie_weights: bool = True,
        use_moe: bool = False,
        n_shared_experts: int = 1,
        n_routed_experts: int = 256,
        n_expert_per_token: int = 8,
    ) -> None:
        """Initialize DeepSeek-V3 model."""
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layers = n_layers
        self.max_seq_len = max_seq_len
        self.use_mtp = use_mtp
        self.mtp_depth = mtp_depth

        # Token Embeddings
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.dropout = nn.Dropout(dropout)

        # Transformer Layers
        self.layers = nn.ModuleList(
            [
                DeepSeekTransformerBlock(
                    d_model=d_model,
                    n_heads=n_heads,
                    d_head=d_head,
                    d_kv_compression=d_kv_compression,
                    d_q_compression=d_q_compression,
                    d_rope=d_rope,
                    d_ffn=d_ffn,
                    dropout=dropout,
                    layer_norm_eps=layer_norm_eps,
                    use_moe=use_moe,
                    n_shared_experts=n_shared_experts,
                    n_routed_experts=n_routed_experts,
                    n_expert_per_token=n_expert_per_token,
                )
                for _ in range(n_layers)
            ]
        )

        # Final Layer Norm
        self.ln_f = nn.LayerNorm(d_model, eps=layer_norm_eps)

        # Output Head
        self.lm_head = CombinedLMHead(
            d_model=d_model,
            vocab_size=vocab_size,
            use_mtp=use_mtp,
            mtp_depth=mtp_depth,
            tie_weights=tie_weights,
        )

        # Weight Tying
        if tie_weights:
            self.lm_head.tie_embedding_weights(self.embedding)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        """Initialize weights.

        Args:
            module: Module to initialize.
        """
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor | None = None,
        return_mtp: bool = False,
    ) -> Tensor | tuple[Tensor, list[Tensor]]:
        """Forward pass through model.

        Args:
            input_ids: Input token IDs (batch_size, seq_len).
            attention_mask: Optional attention mask (batch_size, seq_len).
            return_mtp: Whether to return MTP logits (for training).

        Returns:
            If return_mtp=False: Logits (batch_size, seq_len, vocab_size)
            If return_mtp=True: Tuple of (main_logits, mtp_logits)

        Examples:
            >>> model = DeepSeekV3(vocab_size=1000, d_model=512, n_layers=4)
            >>> input_ids = torch.randint(0, 1000, (2, 64))
            >>> logits = model(input_ids)
            >>> print(logits.shape)
            torch.Size([2, 64, 1000])
        """
        # Embedding
        x = self.embedding(input_ids)
        x = self.dropout(x)

        # Transformer Layers
        for layer in self.layers:
            x = layer(x, attention_mask=attention_mask)

        # Final Layer Norm
        x = self.ln_f(x)

        # Output Head
        if return_mtp and self.use_mtp and self.training:
            # Prepare MTP hidden states
            mtp_hidden = [x[:, :-k, :] for k in range(1, self.mtp_depth + 1)]
            main_logits, mtp_logits = self.lm_head(x, mtp_hidden)
            return main_logits, mtp_logits
        main_logits, _ = self.lm_head(x, None)
        return main_logits

    def generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int | None = None,
    ) -> Tensor:
        """Generate new tokens autoregressively.

        Args:
            input_ids: Input token IDs (batch_size, seq_len).
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (higher = more random).
            top_k: Top-k sampling (None = disabled).

        Returns:
            Generated token IDs (batch_size, seq_len + max_new_tokens).

        Examples:
            >>> model = DeepSeekV3(vocab_size=1000, d_model=512, n_layers=4)
            >>> model.eval()
            >>> input_ids = torch.randint(0, 1000, (1, 10))
            >>> generated = model.generate(input_ids, max_new_tokens=20)
            >>> print(generated.shape)
            torch.Size([1, 30])
        """
        self.eval()
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Crop to max_seq_len
                input_ids_cropped = input_ids[:, -self.max_seq_len :]

                # Forward pass
                logits = self(input_ids_cropped, return_mtp=False)

                # Get next token logits
                next_token_logits = logits[:, -1, :] / temperature

                # Top-k sampling
                if top_k is not None:
                    v, _ = torch.topk(next_token_logits, min(top_k, next_token_logits.size(-1)))
                    next_token_logits[next_token_logits < v[:, [-1]]] = -float("Inf")

                # Sample
                probs = torch.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

                # Append
                input_ids = torch.cat([input_ids, next_token], dim=1)

        return input_ids


class DeepSeekModule(BaseModule):
    """PyTorch Lightning Module für DeepSeek-V3 Training.

    Args:
        vocab_size: Vocabulary size. Defaults to 50000.
        d_model: Hidden dimension. Defaults to 2048.
        n_layers: Number of transformer layers. Defaults to 24.
        n_heads: Number of attention heads. Defaults to 32.
        d_head: Dimension per head. Defaults to 64.
        max_seq_len: Maximum sequence length. Defaults to 2048.
        learning_rate: Learning rate. Defaults to 1e-4.
        use_mtp: Whether to use Multi-Token Prediction. Defaults to True.
        mtp_depth: MTP depth. Defaults to 1.
        mtp_lambda: MTP loss weight. Defaults to 0.3.
        label_smoothing: Label smoothing factor. Defaults to 0.1.
        weight_decay: Weight decay. Defaults to 0.01.
        warmup_steps: Number of warmup steps. Defaults to 2000.
        max_steps: Total training steps. Defaults to 100000.

    Examples:
        >>> module = DeepSeekModule(vocab_size=10000, d_model=512, n_layers=6, learning_rate=3e-4)
        >>> # Use with PyTorch Lightning Trainer
        >>> trainer = pl.Trainer(max_steps=10000)
        >>> trainer.fit(module, datamodule)
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        d_model: int = 2048,
        n_layers: int = 24,
        n_heads: int = 32,
        d_head: int = 64,
        max_seq_len: int = 2048,
        _learning_rate: float = 1e-4,
        use_mtp: bool = True,
        mtp_depth: int = 1,
        mtp_lambda: float = 0.3,
        label_smoothing: float = 0.1,
        _weight_decay: float = 0.01,
        _warmup_steps: int = 2000,
        _max_steps: int = 100000,
        **kwargs: Any,
    ) -> None:
        """Initialize DeepSeek Lightning Module."""
        # Dummy loss to satisfy BaseModule
        dummy_loss = lambda x, y: torch.tensor(0.0)  # noqa: E731, ARG005

        super().__init__(
            loss_fn=dummy_loss,  # Dummy, we override with custom loss
            optimizer=torch.optim.AdamW,
            num_classes=vocab_size,
            **kwargs,
        )
        self.save_hyperparameters()

        # Model
        self.model = DeepSeekV3(
            vocab_size=vocab_size,
            d_model=d_model,
            n_layers=n_layers,
            n_heads=n_heads,
            d_head=d_head,
            max_seq_len=max_seq_len,
            use_mtp=use_mtp,
            mtp_depth=mtp_depth,
        )

        # Loss
        if use_mtp:
            self.loss_fn = MultiTokenPredictionLoss(
                vocab_size=vocab_size,
                mtp_depth=mtp_depth,
                mtp_lambda=mtp_lambda,
                label_smoothing=label_smoothing,
            )
        else:
            self.loss_fn = LanguageModelingLoss(
                vocab_size=vocab_size,
                label_smoothing=label_smoothing,
            )

        # Metrics
        self.train_perplexity = PerplexityMetric()
        self.val_perplexity = PerplexityMetric()
        self.train_accuracy = TokenAccuracyMetric()
        self.val_accuracy = TokenAccuracyMetric()

    def forward(self, input_ids: Tensor, **_kwargs: Any) -> Any:
        """Forward pass."""
        return self.model(input_ids, return_mtp=self.training and self.hparams.use_mtp)

    def training_step(self, batch: dict[str, Tensor], _batch_idx: int) -> Tensor:
        """Training step.

        Args:
            batch: Dict with 'input_ids' and 'labels'.
            batch_idx: Batch index.

        Returns:
            Loss value.
        """
        input_ids = batch["input_ids"]
        labels = batch["labels"]

        # Forward
        if self.hparams.use_mtp:
            main_logits, mtp_logits = self(input_ids)
            loss, loss_dict = self.loss_fn(main_logits, mtp_logits, labels)

            # Log detailed losses
            self.log("train/main_loss", loss_dict["main_loss"], prog_bar=True)
            for k in range(1, self.hparams.mtp_depth + 1):
                self.log(f"train/mtp_loss_{k}", loss_dict[f"mtp_loss_{k}"])
        else:
            main_logits = self(input_ids)
            loss = self.loss_fn(main_logits, labels)

        # Metrics
        perplexity = self.train_perplexity(main_logits, labels)
        accuracy = self.train_accuracy(main_logits, labels)

        # Logging
        self.log("train/loss", loss, prog_bar=True)
        self.log("train/perplexity", perplexity, prog_bar=True)
        self.log("train/accuracy", accuracy, prog_bar=True)

        return loss

    def validation_step(self, batch: dict[str, Tensor], _batch_idx: int) -> Tensor:
        """Validation step.

        Args:
            batch: Dict with 'input_ids' and 'labels'.
            batch_idx: Batch index.

        Returns:
            Loss value.
        """
        input_ids = batch["input_ids"]
        labels = batch["labels"]

        # Forward (no MTP in validation)
        main_logits = self.model(input_ids, return_mtp=False)

        # Use only main loss for validation
        val_loss_fn = LanguageModelingLoss(vocab_size=self.hparams.vocab_size)
        loss = val_loss_fn(main_logits, labels)

        # Metrics
        perplexity = self.val_perplexity(main_logits, labels)
        accuracy = self.val_accuracy(main_logits, labels)

        # Logging
        self.log("val/loss", loss, prog_bar=True)
        self.log("val/perplexity", perplexity, prog_bar=True)
        self.log("val/accuracy", accuracy, prog_bar=True)

        return loss

    def configure_optimizers(self) -> dict[str, Any]:
        """Configure optimizer and scheduler.

        Returns:
            Dict with optimizer and lr_scheduler.
        """
        # Optimizer
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
            betas=(0.9, 0.95),
        )

        # Cosine Learning Rate Schedule with Warmup
        def lr_lambda(current_step: int) -> float:
            if current_step < self.hparams.warmup_steps:
                return float(current_step) / float(max(1, self.hparams.warmup_steps))
            progress = float(current_step - self.hparams.warmup_steps) / float(
                max(1, self.hparams.max_steps - self.hparams.warmup_steps)
            )
            return max(0.1, 0.5 * (1.0 + torch.cos(torch.tensor(progress * 3.141592653589793))))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
                "frequency": 1,
            },
        }
