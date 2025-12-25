"""Rnn Tracker module."""

from torch import nn


class RNNTracker(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, rnn_type="GRU") -> None:
        super(RNNTracker, self).__init__()
        if rnn_type == "GRU":
            self.rnn = nn.GRU(input_dim, hidden_dim, batch_first=True)
        elif rnn_type == "LSTM":
            self.rnn = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        else:
            self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        rnn_out, _ = self.rnn(x)
        out = self.fc(rnn_out[:, -1, :])
        return out
