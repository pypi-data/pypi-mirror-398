"""Rnn module."""

from enum import IntEnum

from loguru import logger
from torch import nn


class RNNType(IntEnum):
    """Enum class for RNN types.

    Attributes:
        GRU (int): Gated Recurrent Unit
        LSTM (int): Long Short-Term Memory
        RNN (int): Vanilla Recurrent Neural Network

    Example:
        >>> RNNType.GRU
    """

    GRU = 0
    LSTM = 1
    RNN = 2

    def choose(self) -> type[nn.Module]:
        """Return the RNN module class corresponding to the enum value."""
        if self == RNNType.GRU:
            return nn.GRU
        if self == RNNType.LSTM:
            return nn.LSTM
        if self == RNNType.RNN:
            return nn.RNN
        logger.error(f"Invalid RNN type: {self}, defaulting to GRU")
        return nn.GRU

    @staticmethod
    def from_str(rnn_type: str) -> type[nn.Module]:
        """Parse a string and return the corresponding RNN module class."""
        if rnn_type.lower() == "gru":
            return nn.GRU
        if rnn_type.lower() == "lstm":
            return nn.LSTM
        if rnn_type.lower() == "rnn":
            return nn.RNN
        logger.error(f"Invalid RNN type: {rnn_type}, defaulting to GRU")
        return nn.GRU
