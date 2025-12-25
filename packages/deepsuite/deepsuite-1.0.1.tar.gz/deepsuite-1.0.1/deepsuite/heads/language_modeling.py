"""Language Modeling Heads.

Output Heads für LLM basierend auf DeepSeek-V3 Architektur.

Referenz: DeepSeek-V3 Technical Report - https://arxiv.org/html/2412.19437v2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from torch import nn

if TYPE_CHECKING:
    from torch import Tensor


class LanguageModelingHead(nn.Module):
    """Standard LM Head für Next-Token Prediction.

    Projiziert Hidden States auf Vocabulary Logits.

    Args:
        d_model: Hidden dimension des Modells.
        vocab_size: Größe des Vokabulars.
        bias: Ob Bias verwendet werden soll. Defaults to False.
        tie_weights: Ob Weights mit Input Embeddings geteilt werden sollen.
            Defaults to True (Standard in LLMs).

    Attributes:
        projection: Linear Layer für Vocabulary Projection.

    Shape:
        - Input: (batch_size, seq_len, d_model)
        - Output: (batch_size, seq_len, vocab_size)

    Examples:
        >>> head = LanguageModelingHead(d_model=768, vocab_size=50000)
        >>> hidden = torch.randn(2, 10, 768)
        >>> logits = head(hidden)
        >>> print(logits.shape)
        torch.Size([2, 10, 50000])

    Note:
        Weight Tying reduziert Parameter und verbessert oft die Performance.
        Wird in GPT, BERT, LLaMA, DeepSeek verwendet.
    """

    def __init__(
        self,
        d_model: int,
        vocab_size: int,
        bias: bool = False,
        tie_weights: bool = True,
    ) -> None:
        """Initialize LM head."""
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.tie_weights = tie_weights

        self.projection = nn.Linear(d_model, vocab_size, bias=bias)

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize projection weights.

        Verwendet Kaiming Normal initialization für bessere Gradientenfluss.
        """
        nn.init.normal_(self.projection.weight, mean=0.0, std=0.02)
        if self.projection.bias is not None:
            nn.init.zeros_(self.projection.bias)

    def forward(self, hidden_states: Tensor) -> Tensor:
        """Project hidden states to vocabulary logits.

        Args:
            hidden_states: Hidden states of shape (batch_size, seq_len, d_model).

        Returns:
            Logits of shape (batch_size, seq_len, vocab_size).

        Examples:
            >>> head = LanguageModelingHead(d_model=512, vocab_size=10000)
            >>> hidden = torch.randn(2, 5, 512)
            >>> logits = head(hidden)
            >>> print(logits.shape)
            torch.Size([2, 5, 10000])
        """
        return self.projection(hidden_states)

    def tie_embedding_weights(self, embedding_layer: nn.Embedding) -> None:
        """Tie weights with input embedding layer.

        Args:
            embedding_layer: Input embedding layer to tie with.

        Examples:
            >>> embedding = nn.Embedding(10000, 512)
            >>> head = LanguageModelingHead(d_model=512, vocab_size=10000)
            >>> head.tie_embedding_weights(embedding)

        Note:
            Embedding und Head müssen gleiche Dimensionen haben.
        """
        if not self.tie_weights:
            return

        if embedding_layer.weight.shape != self.projection.weight.shape:
            msg = (
                f"Cannot tie weights: embedding shape {embedding_layer.weight.shape} "
                f"!= projection shape {self.projection.weight.shape}"
            )
            raise ValueError(msg)

        self.projection.weight = embedding_layer.weight


class MultiTokenPredictionHead(nn.Module):
    """Multi-Token Prediction (MTP) Head für DeepSeek-V3.

    Prediziert zusätzliche Future Tokens für verbesserte Supervision.

    Args:
        d_model: Hidden dimension.
        vocab_size: Vocabulary size.
        mtp_depth: Anzahl zusätzlicher Future Tokens (D). Defaults to 1.
        bias: Ob Bias verwendet werden soll. Defaults to False.

    Attributes:
        mtp_heads: Liste von LM Heads für jeden Depth Level.

    Shape:
        - Input: List[(batch_size, seq_len-k, d_model)] für k=1..mtp_depth
        - Output: List[(batch_size, seq_len-k, vocab_size)] für k=1..mtp_depth

    Examples:
        >>> head = MultiTokenPredictionHead(d_model=768, vocab_size=50000, mtp_depth=2)
        >>> hidden_list = [
        ...     torch.randn(2, 9, 768),  # k=1
        ...     torch.randn(2, 8, 768),  # k=2
        ... ]
        >>> logits_list = head(hidden_list)
        >>> print([x.shape for x in logits_list])
        [torch.Size([2, 9, 50000]), torch.Size([2, 8, 50000])]

    Note:
        MTP wird nur während Training verwendet. In Inferenz wird
        nur der Main Head benötigt.

    References:
        DeepSeek-V3 nutzt D=1 (prediziert 2 Tokens total).
    """

    def __init__(
        self,
        d_model: int,
        vocab_size: int,
        mtp_depth: int = 1,
        bias: bool = False,
    ) -> None:
        """Initialize MTP head."""
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.mtp_depth = mtp_depth

        # Create separate heads für jeden Depth Level
        self.mtp_heads = nn.ModuleList(
            [
                LanguageModelingHead(
                    d_model=d_model, vocab_size=vocab_size, bias=bias, tie_weights=False
                )
                for _ in range(mtp_depth)
            ]
        )

    def forward(self, hidden_states_list: list[Tensor]) -> list[Tensor]:
        """Predict future tokens at multiple depths.

        Args:
            hidden_states_list: List of hidden states für k=1..mtp_depth,
                each of shape (batch_size, seq_len-k, d_model).

        Returns:
            List of logits für k=1..mtp_depth,
                each of shape (batch_size, seq_len-k, vocab_size).

        Examples:
            >>> head = MultiTokenPredictionHead(d_model=512, vocab_size=1000, mtp_depth=1)
            >>> hidden_list = [torch.randn(2, 9, 512)]
            >>> logits_list = head(hidden_list)
            >>> print(logits_list[0].shape)
            torch.Size([2, 9, 1000])

        Raises:
            ValueError: If length of hidden_states_list != mtp_depth.
        """
        if len(hidden_states_list) != self.mtp_depth:
            msg = f"Expected {self.mtp_depth} hidden states, got {len(hidden_states_list)}"
            raise ValueError(msg)

        logits_list = []
        for hidden_states, head in zip(hidden_states_list, self.mtp_heads, strict=True):
            logits = head(hidden_states)
            logits_list.append(logits)

        return logits_list


class CombinedLMHead(nn.Module):
    """Combined Main + MTP Head für komplettes LLM.

    Kombiniert Standard LM Head mit optionalem MTP Head.

    Args:
        d_model: Hidden dimension.
        vocab_size: Vocabulary size.
        use_mtp: Ob MTP verwendet werden soll. Defaults to True.
        mtp_depth: MTP depth wenn aktiviert. Defaults to 1.
        bias: Ob Bias verwendet werden soll. Defaults to False.
        tie_weights: Weight tying mit Embeddings. Defaults to True.

    Attributes:
        main_head: Main LM head für next-token prediction.
        mtp_head: Optional MTP head für future predictions.

    Shape:
        - Main Input: (batch_size, seq_len, d_model)
        - MTP Input: List[(batch_size, seq_len-k, d_model)]
        - Main Output: (batch_size, seq_len, vocab_size)
        - MTP Output: List[(batch_size, seq_len-k, vocab_size)]

    Examples:
        >>> head = CombinedLMHead(d_model=768, vocab_size=50000, use_mtp=True)
        >>> main_hidden = torch.randn(2, 10, 768)
        >>> mtp_hidden = [torch.randn(2, 9, 768)]
        >>>
        >>> main_logits, mtp_logits = head(main_hidden, mtp_hidden)
        >>> print(main_logits.shape)
        torch.Size([2, 10, 50000])
        >>> print(mtp_logits[0].shape)
        torch.Size([2, 9, 50000])
    """

    def __init__(
        self,
        d_model: int,
        vocab_size: int,
        use_mtp: bool = True,
        mtp_depth: int = 1,
        bias: bool = False,
        tie_weights: bool = True,
    ) -> None:
        """Initialize combined LM head."""
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.use_mtp = use_mtp
        self.mtp_depth = mtp_depth

        # Main head
        self.main_head = LanguageModelingHead(
            d_model=d_model,
            vocab_size=vocab_size,
            bias=bias,
            tie_weights=tie_weights,
        )

        # Optional MTP head
        if use_mtp:
            self.mtp_head = MultiTokenPredictionHead(
                d_model=d_model,
                vocab_size=vocab_size,
                mtp_depth=mtp_depth,
                bias=bias,
            )
        else:
            self.mtp_head = None

    def forward(
        self,
        main_hidden: Tensor,
        mtp_hidden: list[Tensor] | None = None,
    ) -> tuple[Tensor, list[Tensor] | None]:
        """Forward pass through combined head.

        Args:
            main_hidden: Main hidden states (batch_size, seq_len, d_model).
            mtp_hidden: Optional MTP hidden states für training.
                List of length mtp_depth with shapes (batch_size, seq_len-k, d_model).

        Returns:
            Tuple of (main_logits, mtp_logits):
                - main_logits: (batch_size, seq_len, vocab_size)
                - mtp_logits: None oder List[(batch_size, seq_len-k, vocab_size)]

        Examples:
            >>> # Training mode with MTP
            >>> head = CombinedLMHead(d_model=512, vocab_size=1000, use_mtp=True)
            >>> main_hidden = torch.randn(2, 10, 512)
            >>> mtp_hidden = [torch.randn(2, 9, 512)]
            >>> main_logits, mtp_logits = head(main_hidden, mtp_hidden)
            >>>
            >>> # Inference mode ohne MTP
            >>> main_logits, _ = head(main_hidden, None)
        """
        # Main prediction
        main_logits = self.main_head(main_hidden)

        # MTP prediction (nur während training)
        mtp_logits = None
        if self.use_mtp and mtp_hidden is not None and self.training:
            mtp_logits = self.mtp_head(mtp_hidden)

        return main_logits, mtp_logits

    def tie_embedding_weights(self, embedding_layer: nn.Embedding) -> None:
        """Tie main head weights with input embeddings.

        Args:
            embedding_layer: Input embedding layer.

        Examples:
            >>> embedding = nn.Embedding(10000, 512)
            >>> head = CombinedLMHead(d_model=512, vocab_size=10000)
            >>> head.tie_embedding_weights(embedding)
        """
        self.main_head.tie_embedding_weights(embedding_layer)
