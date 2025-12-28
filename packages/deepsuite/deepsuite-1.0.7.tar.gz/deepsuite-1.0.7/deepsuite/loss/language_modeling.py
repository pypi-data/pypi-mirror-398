"""Language Modeling Loss Functions.

Loss functions für LLM Training basierend auf DeepSeek-V3 Architektur.

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import nn
from torch.nn import functional

if TYPE_CHECKING:
    from torch import Tensor


class LanguageModelingLoss(nn.Module):
    """Standard Cross-Entropy Loss für Language Modeling.

    Berechnet den Loss für Next-Token Prediction mit optionaler
    Label Smoothing.

    Args:
        vocab_size: Größe des Vokabulars.
        ignore_index: Index der ignoriert werden soll (typisch: padding token).
            Defaults to -100.
        label_smoothing: Label smoothing factor (0.0 = kein smoothing).
            Defaults to 0.0.
        reduction: Reduction method ('mean', 'sum', 'none'). Defaults to 'mean'.

    Shape:
        - logits: (batch_size, seq_len, vocab_size)
        - labels: (batch_size, seq_len)
        - Output: scalar wenn reduction='mean' oder 'sum', sonst (batch_size, seq_len)

    Examples:
        >>> loss_fn = LanguageModelingLoss(vocab_size=50000)
        >>> logits = torch.randn(2, 10, 50000)
        >>> labels = torch.randint(0, 50000, (2, 10))
        >>> loss = loss_fn(logits, labels)
        >>> print(loss.shape)
        torch.Size([])
    """

    def __init__(
        self,
        vocab_size: int,
        ignore_index: int = -100,
        label_smoothing: float = 0.0,
        reduction: str = "mean",
    ) -> None:
        """Initialize language modeling loss."""
        super().__init__()
        self.vocab_size = vocab_size
        self.ignore_index = ignore_index
        self.label_smoothing = label_smoothing
        self.reduction = reduction

    def forward(self, logits: Tensor, labels: Tensor) -> Tensor:
        """Compute cross-entropy loss.

        Args:
            logits: Predicted logits of shape (batch_size, seq_len, vocab_size).
            labels: Target token indices of shape (batch_size, seq_len).

        Returns:
            Loss value (scalar or tensor depending on reduction).

        Examples:
            >>> loss_fn = LanguageModelingLoss(vocab_size=1000)
            >>> logits = torch.randn(2, 5, 1000)
            >>> labels = torch.randint(0, 1000, (2, 5))
            >>> loss = loss_fn(logits, labels)
        """
        # Reshape: (batch_size * seq_len, vocab_size)
        logits_flat = logits.reshape(-1, self.vocab_size)
        labels_flat = labels.reshape(-1)

        return functional.cross_entropy(
            logits_flat,
            labels_flat,
            ignore_index=self.ignore_index,
            label_smoothing=self.label_smoothing,
            reduction=self.reduction,
        )


class MultiTokenPredictionLoss(nn.Module):
    """Multi-Token Prediction (MTP) Loss für DeepSeek-V3.

    Berechnet den kombinierten Loss aus Main Prediction und
    zusätzlichen Future Token Predictions.

    Args:
        vocab_size: Größe des Vokabulars.
        mtp_depth: Anzahl zusätzlicher Token die vorhergesagt werden (D).
            Defaults to 1.
        mtp_lambda: Gewichtung der MTP Loss Terms. Defaults to 0.3.
        ignore_index: Padding token index. Defaults to -100.
        label_smoothing: Label smoothing factor. Defaults to 0.0.

    Shape:
        - main_logits: (batch_size, seq_len, vocab_size)
        - mtp_logits: List[(batch_size, seq_len, vocab_size)] mit Länge mtp_depth
        - labels: (batch_size, seq_len)
        - Output: scalar loss

    Examples:
        >>> loss_fn = MultiTokenPredictionLoss(vocab_size=50000, mtp_depth=1)
        >>> main_logits = torch.randn(2, 10, 50000)
        >>> mtp_logits = [torch.randn(2, 9, 50000)]  # 1 weniger wegen shift
        >>> labels = torch.randint(0, 50000, (2, 10))
        >>> loss = loss_fn(main_logits, mtp_logits, labels)

    Note:
        MTP verbessert die Modelqualität durch zusätzliche Supervision,
        wird aber nur während Training verwendet.

    References:
        DeepSeek-V3 verwendet D=1 (prediziert 2 Tokens total).
    """

    def __init__(
        self,
        vocab_size: int,
        mtp_depth: int = 1,
        mtp_lambda: float = 0.3,
        ignore_index: int = -100,
        label_smoothing: float = 0.0,
    ) -> None:
        """Initialize MTP loss."""
        super().__init__()
        self.vocab_size = vocab_size
        self.mtp_depth = mtp_depth
        self.mtp_lambda = mtp_lambda

        # Main loss
        self.main_loss_fn = LanguageModelingLoss(
            vocab_size=vocab_size,
            ignore_index=ignore_index,
            label_smoothing=label_smoothing,
            reduction="mean",
        )

        # MTP loss (same criterion)
        self.mtp_loss_fn = LanguageModelingLoss(
            vocab_size=vocab_size,
            ignore_index=ignore_index,
            label_smoothing=label_smoothing,
            reduction="mean",
        )

    def forward(
        self,
        main_logits: Tensor,
        mtp_logits: list[Tensor],
        labels: Tensor,
    ) -> tuple[Tensor, dict[str, Tensor]]:
        """Compute combined MTP loss.

        Args:
            main_logits: Main prediction logits (batch_size, seq_len, vocab_size).
            mtp_logits: List of MTP prediction logits, each of shape
                (batch_size, seq_len-k, vocab_size) für k=1..mtp_depth.
            labels: Target labels (batch_size, seq_len).

        Returns:
            Tuple of (total_loss, loss_dict) where loss_dict contains:
                - 'main_loss': Main prediction loss
                - 'mtp_loss_k': MTP loss für depth k (k=1..mtp_depth)
                - 'total_loss': Gewichtete Summe

        Examples:
            >>> loss_fn = MultiTokenPredictionLoss(vocab_size=1000, mtp_depth=2)
            >>> main_logits = torch.randn(2, 10, 1000)
            >>> mtp_logits = [
            ...     torch.randn(2, 9, 1000),  # k=1
            ...     torch.randn(2, 8, 1000),  # k=2
            ... ]
            >>> labels = torch.randint(0, 1000, (2, 10))
            >>> total_loss, loss_dict = loss_fn(main_logits, mtp_logits, labels)
        """
        # Main loss: predict next token
        main_loss = self.main_loss_fn(main_logits, labels)

        loss_dict = {"main_loss": main_loss}

        # MTP losses: predict future tokens
        mtp_loss_total = torch.tensor(0.0, device=main_logits.device)

        for k, logits_k in enumerate(mtp_logits, start=1):
            # Shift labels: für k=1 verwende labels[:, 1:], für k=2 labels[:, 2:], etc.
            shifted_labels = labels[:, k:]

            # Ensure shapes match
            seq_len_mtp = logits_k.shape[1]
            if shifted_labels.shape[1] > seq_len_mtp:
                shifted_labels = shifted_labels[:, :seq_len_mtp]

            # Truncate logits if needed (avoid overwriting loop variable)
            final_logits_k = (
                logits_k[:, : shifted_labels.shape[1]]
                if shifted_labels.shape[1] < seq_len_mtp
                else logits_k
            )

            mtp_loss_k = self.mtp_loss_fn(final_logits_k, shifted_labels)
            loss_dict[f"mtp_loss_{k}"] = mtp_loss_k
            mtp_loss_total = mtp_loss_total + mtp_loss_k

        # Combine: total = main + lambda * sum(mtp_k)
        total_loss = main_loss + self.mtp_lambda * mtp_loss_total
        loss_dict["total_loss"] = total_loss

        return total_loss, loss_dict


class PerplexityMetric(nn.Module):
    """Perplexity Metrik für Language Modeling.

    Perplexity = exp(CrossEntropyLoss), eine interpretierbare
    Metrik für Modellqualität.

    Args:
        ignore_index: Padding token index. Defaults to -100.

    Shape:
        - Input: (batch_size, seq_len, vocab_size)
        - Target: (batch_size, seq_len)
        - Output: scalar

    Examples:
        >>> metric = PerplexityMetric()
        >>> logits = torch.randn(2, 10, 1000)
        >>> labels = torch.randint(0, 1000, (2, 10))
        >>> ppl = metric(logits, labels)
        >>> print(f"Perplexity: {ppl:.2f}")

    Note:
        Niedrigere Perplexity = besseres Modell.
        GPT-3: ~20, DeepSeek-V3: ~15
    """

    def __init__(self, ignore_index: int = -100) -> None:
        """Initialize perplexity metric."""
        super().__init__()
        self.ignore_index = ignore_index

    def forward(self, logits: Tensor, labels: Tensor) -> Tensor:
        """Compute perplexity.

        Args:
            logits: Predicted logits (batch_size, seq_len, vocab_size).
            labels: Target labels (batch_size, seq_len).

        Returns:
            Perplexity value (scalar).

        Examples:
            >>> metric = PerplexityMetric()
            >>> logits = torch.randn(2, 5, 100)
            >>> labels = torch.randint(0, 100, (2, 5))
            >>> ppl = metric(logits, labels)
        """
        # Flatten
        logits_flat = logits.reshape(-1, logits.size(-1))
        labels_flat = labels.reshape(-1)

        # Cross-entropy
        loss = functional.cross_entropy(
            logits_flat,
            labels_flat,
            ignore_index=self.ignore_index,
            reduction="mean",
        )

        # Perplexity = exp(loss)
        return torch.exp(loss)


class TokenAccuracyMetric(nn.Module):
    """Token-level Accuracy Metrik.

    Berechnet den Anteil korrekt vorhergesagter Tokens.

    Args:
        ignore_index: Padding token index. Defaults to -100.

    Shape:
        - Input: (batch_size, seq_len, vocab_size)
        - Target: (batch_size, seq_len)
        - Output: scalar (0.0 bis 1.0)

    Examples:
        >>> metric = TokenAccuracyMetric()
        >>> logits = torch.randn(2, 10, 1000)
        >>> labels = torch.randint(0, 1000, (2, 10))
        >>> acc = metric(logits, labels)
        >>> print(f"Accuracy: {acc:.2%}")
    """

    def __init__(self, ignore_index: int = -100) -> None:
        """Initialize token accuracy metric."""
        super().__init__()
        self.ignore_index = ignore_index

    def forward(self, logits: Tensor, labels: Tensor) -> Tensor:
        """Compute token accuracy.

        Args:
            logits: Predicted logits (batch_size, seq_len, vocab_size).
            labels: Target labels (batch_size, seq_len).

        Returns:
            Accuracy value (0.0 bis 1.0).

        Examples:
            >>> metric = TokenAccuracyMetric()
            >>> logits = torch.randn(2, 5, 100)
            >>> labels = torch.randint(0, 100, (2, 5))
            >>> acc = metric(logits, labels)
        """
        # Get predictions
        predictions = torch.argmax(logits, dim=-1)

        # Create mask for valid tokens (not padding)
        valid_mask = labels != self.ignore_index

        # Compute accuracy only on valid tokens
        correct = (predictions == labels) & valid_mask
        total = valid_mask.sum()

        if total == 0:
            return torch.tensor(0.0, device=logits.device)

        return correct.sum().float() / total.float()
