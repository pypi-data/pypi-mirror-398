"""RNN-based tracker module."""

from typing import Literal, cast

from torch import Tensor, nn


class RNNTracker(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        rnn_type: Literal["GRU", "LSTM", "RNN"] = "GRU",
    ) -> None:
        super().__init__()
        self.rnn: nn.Module
        if rnn_type == "GRU":
            self.rnn = nn.GRU(input_dim, hidden_dim, batch_first=True)
        elif rnn_type == "LSTM":
            self.rnn = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        else:
            self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: Tensor) -> Tensor:
        rnn_out_any, _ = self.rnn(x)
        rnn_out = cast("Tensor", rnn_out_any)
        out_any = self.fc(rnn_out[:, -1, :])
        return cast("Tensor", out_any)
