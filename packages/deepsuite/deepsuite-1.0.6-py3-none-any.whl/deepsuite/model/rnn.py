"""Rnn module."""

from loguru import logger
from torch import Tensor, nn

from deepsuite.utils.rnn import RNNType


class BNReluRNN(nn.Module):
    """Recurrent neural network with batch normalization layer & ReLU activation function.

    Args:
        input_size (int): The number of expected features in the input x
        hidden_size (int): The number of features in the hidden state h
        rnn_type (RNNType): The type of RNN to use
        bidirectional (bool): If True, becomes a bidirectional RNN
        dropout_p (float): If non-zero, introduces a Dropout layer on the outputs of each RNN layer except the last layer
        num_layers (int): Number of recurrent layers
        batch_first (bool): If True, then the input and output tensors are provided as (batch, seq, feature)
        bias (bool): If False, then the layer does not use bias weights b_ih and b_hh

    Inputs:
        inputs (Tensor): Input sequence
        input_lengths (Tensor): Lengths of input sequences

    Returns:
        outputs (Tensor): Output sequence

    Shape:
        - inputs: (batch, seq_len, input_size)
        - input_lengths: (batch)
        - outputs: (batch, seq_len, hidden_size)

    Example:
        >>> rnn = RNN(512, 512)
        >>> inputs = torch.randn(10, 20, 512)
        >>> input_lengths = torch.tensor([20, 20, 20, 20, 20, 20, 20, 20, 20, 20])
        >>> outputs = rnn(inputs, input_lengths)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 512,
        rnn_type: RNNType = RNNType.GRU,
        bidirectional: bool = False,
        dropout_p: float = 0.1,
        num_layers: int = 1,
        batch_first: bool = True,
        bias: bool = True,
    ) -> None:
        super().__init__()

        if rnn_type == RNNType.GRU:
            rnn = nn.GRU
        elif rnn_type == RNNType.LSTM:
            rnn = nn.LSTM
        elif rnn_type == RNNType.RNN:
            rnn = nn.RNN
        else:
            logger.error(f"Invalid RNN type: {rnn_type}, defaulting to GRU")
            rnn = nn.GRU

        self.rnn = rnn(
            input_size,
            hidden_size,
            num_layers,
            batch_first=batch_first,
            bidirectional=bidirectional,
            dropout=dropout_p,
            bias=bias,
        )

        self.bn = nn.BatchNorm1d(hidden_size)
        self.glu = nn.GLU()  # Gated ReLU für bessere Features

        self.init_weights()

    def init_weights(self) -> None:
        """Initialisiert Gewichte mit Xavier Uniform für stabileres Training."""
        for param in self.parameters():
            if param.dim() > 1:
                nn.init.xavier_uniform_(param)

    def forward(self, inputs: Tensor, input_lengths: Tensor) -> Tensor:
        logger.debug(f"Input shape: {inputs.shape}, Input lengths: {input_lengths}")

        inputs = inputs.transpose(1, 2)  # (Batch, Features, Seq_len)
        inputs = self.bn(inputs)  # Apply BatchNorm1d
        inputs = inputs.transpose(1, 2)  # Back to (Batch, Seq_len, Features)

        packed_inputs = nn.utils.rnn.pack_padded_sequence(
            inputs, input_lengths.cpu(), batch_first=True, enforce_sorted=False
        )

        packed_outputs, _ = self.rnn(packed_inputs)

        outputs, _ = nn.utils.rnn.pad_packed_sequence(packed_outputs, batch_first=True)

        outputs = self.glu(outputs)  # Statt ReLU: GLU verbessert Feature-Separation

        logger.debug(f"Output shape: {outputs.shape}")

        return outputs
