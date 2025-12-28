"""GPT Language Model Module.

PyTorch Lightning Module für GPT-style Transformer (GPT-2/GPT-3 Architektur).

Referenzen:
- GPT-2: Language Models are Unsupervised Multitask Learners
- GPT-3: Language Models are Few-Shot Learners
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch
from torch import nn

from deepsuite.heads.language_modeling import LanguageModelingHead
from deepsuite.lightning_base.module import BaseModule
from deepsuite.loss.language_modeling import (
    LanguageModelingLoss,
    PerplexityMetric,
    TokenAccuracyMetric,
)

if TYPE_CHECKING:
    from torch import Tensor


class GPTAttention(nn.Module):
    """Multi-Head Self-Attention für GPT.

    Standard scaled dot-product attention mit causal masking.

    Args:
        d_model: Hidden dimension. Defaults to 768.
        n_heads: Number of attention heads. Defaults to 12.
        dropout: Dropout rate. Defaults to 0.1.
        bias: Whether to use bias in projections. Defaults to True.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> attn = GPTAttention(d_model=768, n_heads=12)
        >>> x = torch.randn(2, 128, 768)
        >>> output = attn(x)
        >>> print(output.shape)
        torch.Size([2, 128, 768])
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        dropout: float = 0.1,
        bias: bool = True,
    ) -> None:
        """Initialize GPT attention."""
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        if d_model % n_heads != 0:
            msg = f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
            raise ValueError(msg)

        # QKV projection
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=bias)

        # Output projection
        self.proj = nn.Linear(d_model, d_model, bias=bias)

        # Dropout
        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: Tensor,
        attention_mask: Tensor | None = None,
    ) -> Tensor:
        """Forward pass.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).
            attention_mask: Optional attention mask (batch_size, seq_len, seq_len).

        Returns:
            Output tensor (batch_size, seq_len, d_model).

        Examples:
            >>> attn = GPTAttention(d_model=512, n_heads=8)
            >>> x = torch.randn(2, 64, 512)
            >>> output = attn(x)
        """
        batch_size, seq_len, _ = x.shape

        # QKV projection and split
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)

        # Scaled dot-product attention
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / (self.d_head**0.5)

        # Apply causal mask
        if attention_mask is None:
            # Create causal mask
            causal_mask = torch.triu(
                torch.ones(seq_len, seq_len, device=x.device), diagonal=1
            ).bool()
            attn_scores = attn_scores.masked_fill(causal_mask, float("-inf"))
        else:
            attn_scores = attn_scores + attention_mask

        # Softmax and dropout
        attn_weights = torch.softmax(attn_scores, dim=-1)
        attn_weights = self.attn_dropout(attn_weights)

        # Apply attention to values
        output = torch.matmul(attn_weights, v)

        # Reshape and project
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        output = self.proj(output)
        return self.resid_dropout(output)


class GPTFFN(nn.Module):
    """Position-wise Feed-Forward Network für GPT.

    Args:
        d_model: Hidden dimension. Defaults to 768.
        d_ffn: FFN intermediate dimension. Defaults to 3072 (4 * d_model).
        dropout: Dropout rate. Defaults to 0.1.
        bias: Whether to use bias. Defaults to True.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> ffn = GPTFFN(d_model=768, d_ffn=3072)
        >>> x = torch.randn(2, 128, 768)
        >>> output = ffn(x)
        >>> print(output.shape)
        torch.Size([2, 128, 768])
    """

    def __init__(
        self,
        d_model: int = 768,
        d_ffn: int = 3072,
        dropout: float = 0.1,
        bias: bool = True,
    ) -> None:
        """Initialize GPT FFN."""
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ffn, bias=bias)
        self.fc2 = nn.Linear(d_ffn, d_model, bias=bias)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x: Tensor) -> Tensor:
        """Forward pass.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).

        Returns:
            Output tensor (batch_size, seq_len, d_model).

        Examples:
            >>> ffn = GPTFFN(d_model=512, d_ffn=2048)
            >>> x = torch.randn(2, 64, 512)
            >>> output = ffn(x)
        """
        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)
        return self.dropout(x)


class GPTBlock(nn.Module):
    """GPT Transformer Block.

    Args:
        d_model: Hidden dimension. Defaults to 768.
        n_heads: Number of attention heads. Defaults to 12.
        d_ffn: FFN intermediate dimension. Defaults to 3072.
        dropout: Dropout rate. Defaults to 0.1.
        layer_norm_eps: Layer norm epsilon. Defaults to 1e-5.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, d_model)

    Examples:
        >>> block = GPTBlock(d_model=768, n_heads=12)
        >>> x = torch.randn(2, 128, 768)
        >>> output = block(x)
        >>> print(output.shape)
        torch.Size([2, 128, 768])
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        d_ffn: int = 3072,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5,
    ) -> None:
        """Initialize GPT block."""
        super().__init__()
        self.ln_1 = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.attention = GPTAttention(d_model, n_heads, dropout)
        self.ln_2 = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.ffn = GPTFFN(d_model, d_ffn, dropout)

    def forward(
        self,
        x: Tensor,
        attention_mask: Tensor | None = None,
    ) -> Tensor:
        """Forward pass.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).
            attention_mask: Optional attention mask.

        Returns:
            Output tensor (batch_size, seq_len, d_model).

        Examples:
            >>> block = GPTBlock(d_model=512, n_heads=8)
            >>> x = torch.randn(2, 64, 512)
            >>> output = block(x)
        """
        # Pre-norm + Attention + Residual
        x = x + self.attention(self.ln_1(x), attention_mask)

        # Pre-norm + FFN + Residual
        return x + self.ffn(self.ln_2(x))


class GPT(nn.Module):
    """GPT Language Model.

    Args:
        vocab_size: Vocabulary size. Defaults to 50257.
        d_model: Hidden dimension. Defaults to 768.
        n_layers: Number of transformer layers. Defaults to 12.
        n_heads: Number of attention heads. Defaults to 12.
        d_ffn: FFN intermediate dimension. Defaults to 3072.
        max_seq_len: Maximum sequence length. Defaults to 1024.
        dropout: Dropout rate. Defaults to 0.1.
        layer_norm_eps: Layer norm epsilon. Defaults to 1e-5.
        tie_weights: Whether to tie embedding and output weights. Defaults to True.

    Shape:
        - Input: (batch_size, seq_len)
        - Output: (batch_size, seq_len, vocab_size)

    Examples:
        >>> model = GPT(vocab_size=10000, d_model=512, n_layers=6)
        >>> input_ids = torch.randint(0, 10000, (2, 128))
        >>> logits = model(input_ids)
        >>> print(logits.shape)
        torch.Size([2, 128, 10000])

    Note:
        Default parameters match GPT-2 small (117M parameters).
        For GPT-2 medium: d_model=1024, n_layers=24, n_heads=16.
        For GPT-2 large: d_model=1280, n_layers=36, n_heads=20.
        For GPT-2 XL: d_model=1600, n_layers=48, n_heads=25.
    """

    def __init__(
        self,
        vocab_size: int = 50257,
        d_model: int = 768,
        n_layers: int = 12,
        n_heads: int = 12,
        d_ffn: int = 3072,
        max_seq_len: int = 1024,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5,
        tie_weights: bool = True,
    ) -> None:
        """Initialize GPT model."""
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layers = n_layers
        self.max_seq_len = max_seq_len

        # Token + Position Embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        self.dropout = nn.Dropout(dropout)

        # Transformer Layers
        self.layers = nn.ModuleList(
            [
                GPTBlock(
                    d_model=d_model,
                    n_heads=n_heads,
                    d_ffn=d_ffn,
                    dropout=dropout,
                    layer_norm_eps=layer_norm_eps,
                )
                for _ in range(n_layers)
            ]
        )

        # Final Layer Norm
        self.ln_f = nn.LayerNorm(d_model, eps=layer_norm_eps)

        # Output Head
        self.lm_head = LanguageModelingHead(
            d_model=d_model,
            vocab_size=vocab_size,
            tie_weights=tie_weights,
        )

        # Weight Tying
        if tie_weights:
            self.lm_head.tie_embedding_weights(self.token_embedding)

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
    ) -> Tensor:
        """Forward pass.

        Args:
            input_ids: Input token IDs (batch_size, seq_len).
            attention_mask: Optional attention mask (batch_size, seq_len).

        Returns:
            Logits (batch_size, seq_len, vocab_size).

        Examples:
            >>> model = GPT(vocab_size=1000, d_model=512, n_layers=4)
            >>> input_ids = torch.randint(0, 1000, (2, 64))
            >>> logits = model(input_ids)
            >>> print(logits.shape)
            torch.Size([2, 64, 1000])
        """
        _, seq_len = input_ids.shape

        # Token + Position Embeddings
        positions = torch.arange(0, seq_len, dtype=torch.long, device=input_ids.device).unsqueeze(0)
        token_emb = self.token_embedding(input_ids)
        pos_emb = self.position_embedding(positions)
        x = self.dropout(token_emb + pos_emb)

        # Transformer Layers
        for layer in self.layers:
            x = layer(x, attention_mask)

        # Final Layer Norm
        x = self.ln_f(x)

        # Output Head
        return self.lm_head(x)

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
            >>> model = GPT(vocab_size=1000, d_model=512, n_layers=4)
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
                logits = self(input_ids_cropped)

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


class GPTModule(BaseModule):
    """PyTorch Lightning Module für GPT Training.

    Args:
        vocab_size: Vocabulary size. Defaults to 50257.
        d_model: Hidden dimension. Defaults to 768.
        n_layers: Number of transformer layers. Defaults to 12.
        n_heads: Number of attention heads. Defaults to 12.
        d_ffn: FFN intermediate dimension. Defaults to 3072.
        max_seq_len: Maximum sequence length. Defaults to 1024.
        learning_rate: Learning rate. Defaults to 3e-4.
        label_smoothing: Label smoothing factor. Defaults to 0.0.
        weight_decay: Weight decay. Defaults to 0.01.
        warmup_steps: Number of warmup steps. Defaults to 2000.
        max_steps: Total training steps. Defaults to 100000.

    Examples:
        >>> module = GPTModule(vocab_size=10000, d_model=512, n_layers=6, learning_rate=3e-4)
        >>> # Use with PyTorch Lightning Trainer
        >>> trainer = pl.Trainer(max_steps=10000)
        >>> trainer.fit(module, datamodule)
    """

    def __init__(
        self,
        vocab_size: int = 50257,
        d_model: int = 768,
        n_layers: int = 12,
        n_heads: int = 12,
        d_ffn: int = 3072,
        max_seq_len: int = 1024,
        learning_rate: float = 3e-4,
        label_smoothing: float = 0.0,
        weight_decay: float = 0.01,
        warmup_steps: int = 2000,
        max_steps: int = 100000,
        **kwargs: Any,
    ) -> None:
        """Initialize GPT Lightning Module."""
        # Dummy loss to satisfy BaseModule
        dummy_loss = lambda x, y: torch.tensor(0.0)  # noqa: E731

        super().__init__(
            loss_fn=dummy_loss,  # Dummy, we override with custom loss
            optimizer=torch.optim.AdamW,
            num_classes=vocab_size,
            **kwargs,
        )
        self.save_hyperparameters()

        # Model
        self.model = GPT(
            vocab_size=vocab_size,
            d_model=d_model,
            n_layers=n_layers,
            n_heads=n_heads,
            d_ffn=d_ffn,
            max_seq_len=max_seq_len,
        )

        # Loss
        self.loss_fn = LanguageModelingLoss(
            vocab_size=vocab_size,
            label_smoothing=label_smoothing,
        )

        # Metrics
        self.train_perplexity = PerplexityMetric()
        self.val_perplexity = PerplexityMetric()
        self.train_accuracy = TokenAccuracyMetric()
        self.val_accuracy = TokenAccuracyMetric()

    def forward(self, input_ids: Tensor, **kwargs: Any) -> Any:
        """Forward pass."""
        return self.model(input_ids)

    def training_step(self, batch: dict[str, Tensor], batch_idx: int) -> Tensor:
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
        logits = self(input_ids)

        # Loss
        loss = self.loss_fn(logits, labels)

        # Metrics
        perplexity = self.train_perplexity(logits, labels)
        accuracy = self.train_accuracy(logits, labels)

        # Logging
        self.log("train/loss", loss, prog_bar=True)
        self.log("train/perplexity", perplexity, prog_bar=True)
        self.log("train/accuracy", accuracy, prog_bar=True)

        return loss

    def validation_step(self, batch: dict[str, Tensor], batch_idx: int) -> Tensor:
        """Validation step.

        Args:
            batch: Dict with 'input_ids' and 'labels'.
            batch_idx: Batch index.

        Returns:
            Loss value.
        """
        input_ids = batch["input_ids"]
        labels = batch["labels"]

        # Forward
        logits = self(input_ids)

        # Loss
        loss = self.loss_fn(logits, labels)

        # Metrics
        perplexity = self.val_perplexity(logits, labels)
        accuracy = self.val_accuracy(logits, labels)

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
