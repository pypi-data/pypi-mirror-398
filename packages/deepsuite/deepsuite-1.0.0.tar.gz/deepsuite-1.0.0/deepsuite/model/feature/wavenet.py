"""Wavenet module."""

import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from deepsuite.model.conv import Conv1d, ConvTranspose2d, ResidualConv1dGLU
from deepsuite.utils.rnn import RNNType


def _expand_global_features(b: int, t: int, g: torch.Tensor, bct: bool = True) -> torch.Tensor:
    """Expand global conditioning features to all time steps.

    Args:
        b (int): Batch size.
        t (int): Time length.
        g (Tensor): Global features, (B x C) or (B x C x 1).
        bct (bool) : returns (B x C x T) if True, otherwise (B x T x C)

    Returns:
        Tensor: B x C x T or B x T x C or None
    """
    if g is None:
        return None
    g = g.unsqueeze(-1) if g.dim() == 2 else g
    if bct:
        g_bct = g.expand(b, -1, t)
        return g_bct.contiguous()
    g_btc = g.expand(b, -1, t).transpose(1, 2)
    return g_btc.contiguous()


def to_one_hot(tensor: torch.Tensor, n, fill_with: float = 1.0) -> torch.Tensor:
    # we perform one hot encore with respect to the last axis
    one_hot = torch.FloatTensor(tensor.size() + (n,)).zero_()
    if tensor.is_cuda:
        one_hot = one_hot.cuda()
    one_hot.scatter_(len(tensor.size()), tensor.unsqueeze(-1), fill_with)
    return one_hot


def sample_from_discretized_mix_logistic(y, log_scale_min=-7.0):
    """Sample from discretized mixture of logistic distributions.

    Args:
        y (Tensor): B x C x T
        log_scale_min (float): Log scale minimum value

    Returns:
        Tensor: sample in range of [-1, 1].
    """
    assert y.size(1) % 3 == 0
    nr_mix = y.size(1) // 3

    # B x T x C
    y = y.transpose(1, 2)
    logit_probs = y[:, :, :nr_mix]

    # sample mixture indicator from softmax
    temp = logit_probs.data.new(logit_probs.size()).uniform_(1e-5, 1.0 - 1e-5)
    temp = logit_probs.data - torch.log(-torch.log(temp))
    _, argmax = temp.max(dim=-1)

    # (B, T) -> (B, T, nr_mix)
    one_hot = to_one_hot(argmax, nr_mix)
    # select logistic parameters
    means = torch.sum(y[:, :, nr_mix : 2 * nr_mix] * one_hot, dim=-1)
    log_scales = torch.clamp(
        torch.sum(y[:, :, 2 * nr_mix : 3 * nr_mix] * one_hot, dim=-1), min=log_scale_min
    )
    # sample from logistic & clip to interval
    # we don't actually round to the nearest 8bit value when sampling
    u = means.data.new(means.size()).uniform_(1e-5, 1.0 - 1e-5)
    x = means + torch.exp(log_scales) * (torch.log(u) - torch.log(1.0 - u))

    x = torch.clamp(torch.clamp(x, min=-1.0), max=1.0)

    return x


def receptive_field_size(total_layers, num_cycles, kernel_size, dilation=lambda x: 2**x):
    """Compute receptive field size.

    Args:
        total_layers (int): total layers
        num_cycles (int): cycles
        kernel_size (int): kernel size
        dilation (lambda): lambda to compute dilation factor. ``lambda x : 1``
          to disable dilated convolution.

    Returns:
        int: receptive field size in sample

    """
    assert total_layers % num_cycles == 0
    layers_per_cycle = total_layers // num_cycles
    dilations = [dilation(i % layers_per_cycle) for i in range(total_layers)]
    return (kernel_size - 1) * sum(dilations) + 1


class WaveNet(nn.Module):
    def __init__(
        self,
        out_channels: int = 256,
        layers: int = 20,
        stacks: int = 2,
        residual_channels: int = 512,
        gate_channels: int = 512,
        skip_out_channels: int = 512,
        kernel_size: int = 3,
        dropout: float = 1 - 0.95,
        cin_channels: int = -1,
        gin_channels: int = -1,
        n_speakers: int | None = None,
        weight_normalization: bool = True,
        upsample_conditional_features: bool = False,
        upsample_scales=None,
        freq_axis_kernel_size=3,
        scalar_input=False,
        use_speaker_embedding=True,
        legacy=True,
    ) -> None:
        super().__init__()
        assert layers % stacks == 0
        self.scalar_input = scalar_input
        self.out_channels = out_channels
        self.cin_channels = cin_channels
        self.legacy = legacy
        layers_per_stack = layers // stacks

        if scalar_input:
            self.first_conv = Conv1d.conv1x1(1, residual_channels)
        else:
            self.first_conv = Conv1d.conv1x1(out_channels, residual_channels)

        self.conv_layers = nn.ModuleList()
        for layer in range(layers):
            dilation = 2 ** (layer % layers_per_stack)
            conv = ResidualConv1dGLU(
                residual_channels,
                gate_channels,
                kernel_size=kernel_size,
                skip_out_channels=skip_out_channels,
                bias=True,  # magenda uses bias, but musyoku doesn't
                dilation=dilation,
                dropout=dropout,
                cin_channels=cin_channels,
                gin_channels=gin_channels,
                weight_normalization=weight_normalization,
            )
            self.conv_layers.append(conv)
        self.last_conv_layers = nn.ModuleList(
            [
                nn.ReLU(inplace=True),
                Conv1d.conv1x1(
                    skip_out_channels, skip_out_channels, weight_normalization=weight_normalization
                ),
                nn.ReLU(inplace=True),
                Conv1d.conv1x1(
                    skip_out_channels, out_channels, weight_normalization=weight_normalization
                ),
            ]
        )

        if gin_channels > 0 and use_speaker_embedding:
            assert n_speakers is not None
            self.embed_speakers = nn.Embedding(
                num_embeddings=n_speakers, embedding_dim=gin_channels, padding_idx=None
            )
            self.embed_speakers.weight.data.normal_(0, std=0.1)
        else:
            self.embed_speakers = None

        # Upsample conv net
        if upsample_conditional_features:
            self.upsample_conv = nn.ModuleList()
            for s in upsample_scales:
                freq_axis_padding = (freq_axis_kernel_size - 1) // 2
                convt = ConvTranspose2d(
                    1,
                    1,
                    (freq_axis_kernel_size, s),
                    padding=(freq_axis_padding, 0),
                    dilation=1,
                    stride=(1, s),
                    weight_normalization=weight_normalization,
                )
                self.upsample_conv.append(convt)
                # assuming we use [0, 1] scaled features
                # this should avoid non-negative upsampling output
                self.upsample_conv.append(nn.ReLU(inplace=True))
        else:
            self.upsample_conv = None

        self.receptive_field = receptive_field_size(layers, stacks, kernel_size)

    def has_speaker_embedding(self) -> bool:
        return self.embed_speakers is not None

    def local_conditioning_enabled(self) -> bool:
        return self.cin_channels > 0

    def forward(
        self,
        x: torch.Tensor,
        c: torch.Tensor | None = None,
        g: torch.Tensor | None = None,
        softmax: bool = False,
    ) -> torch.Tensor:
        """Forward step.

        Args:
            x (Tensor): One-hot encoded audio signal, shape (B x C x T)
            c (Tensor): Local conditioning features,
              shape (B x cin_channels x T)
            g (Tensor): Global conditioning features,
              shape (B x gin_channels x 1) or speaker Ids of shape (B x 1).
              Note that ``self.use_speaker_embedding`` must be False when you
              want to disable embedding layer and use external features
              directly (e.g., one-hot vector).
              Also type of input tensor must be FloatTensor, not LongTensor
              in case of ``self.use_speaker_embedding`` equals False.
            softmax (bool): Whether applies softmax or not.

        Returns:
            Tensor: output, shape B x out_channels x T
        """
        _b, _, _t = x.size()

        if g is not None:
            if self.embed_speakers is not None:
                # (B x 1) -> (B x 1 x gin_channels)
                g = self.embed_speakers(g.view(_b, -1))
                # (B x gin_channels x 1)
                g = g.transpose(1, 2)

                assert g.dim() == 3

        # Expand global conditioning features to all time steps
        g_bct = _expand_global_features(_b, _t, g, bct=True)

        if c is not None and self.upsample_conv is not None:
            # B x 1 x C x T
            c = c.unsqueeze(1)
            for f in self.upsample_conv:
                c = f(c)
            # B x C x T
            c = c.squeeze(1)
            assert c.size(-1) == x.size(-1)

        # Feed data to network
        x = self.first_conv(x)
        skips = None
        for f in self.conv_layers:
            x, h = f(x, c, g_bct)
            if skips is None:
                skips = h
            else:
                skips += h
                if self.legacy:
                    skips *= math.sqrt(0.5)

        x = skips
        for f in self.last_conv_layers:
            x = f(x)

        x = F.softmax(x, dim=1) if softmax else x

        return x

    def incremental_forward(
        self,
        initial_input=None,
        c=None,
        g=None,
        T=100,
        test_inputs=None,
        tqdm=lambda x: x,
        softmax=True,
        quantize=True,
        log_scale_min=-7.0,
    ) -> torch.Tensor:
        """Incremental forward step.

        Due to linearized convolutions, inputs of shape (B x C x T) are reshaped
        to (B x T x C) internally and fed to the network for each time step.
        Input of each time step will be of shape (B x 1 x C).

        Args:
            initial_input (Tensor): Initial decoder input, (B x C x 1)
            c (Tensor): Local conditioning features, shape (B x C' x T)
            g (Tensor): Global conditioning features, shape (B x C'' or B x C''x 1)
            T (int): Number of time steps to generate.
            test_inputs (Tensor): Teacher forcing inputs (for debugging)
            tqdm (lamda) : tqdm
            softmax (bool) : Whether applies softmax or not
            quantize (bool): Whether quantize softmax output before feeding the
              network output to input for the next time step. TODO: rename
            log_scale_min (float):  Log scale minimum value.

        Returns:
            Tensor: Generated one-hot encoded samples. B x C x T
              or scaler vector B x 1 x T
        """
        self.clear_buffer()
        B = 1

        # Note: shape should be **(B x T x C)**, not (B x C x T) opposed to
        # batch forward due to linealized convolution
        if test_inputs is not None:
            if self.scalar_input:
                if test_inputs.size(1) == 1:
                    test_inputs = test_inputs.transpose(1, 2).contiguous()
            elif test_inputs.size(1) == self.out_channels:
                test_inputs = test_inputs.transpose(1, 2).contiguous()

            B = test_inputs.size(0)
            if T is None:
                T = test_inputs.size(1)
            else:
                T = max(T, test_inputs.size(1))
        # cast to int in case of numpy.int64...
        T = int(T)

        # Global conditioning
        if g is not None:
            if self.embed_speakers is not None:
                g = self.embed_speakers(g.view(B, -1))
                # (B x gin_channels, 1)
                g = g.transpose(1, 2)
                assert g.dim() == 3
        g_btc = _expand_global_features(B, T, g, bct=False)

        # Local conditioning
        if c is not None and self.upsample_conv is not None:
            # B x 1 x C x T
            c = c.unsqueeze(1)
            for f in self.upsample_conv:
                c = f(c)
            # B x C x T
            c = c.squeeze(1)
            assert c.size(-1) == T
        if c is not None and c.size(-1) == T:
            c = c.transpose(1, 2).contiguous()

        outputs: list[torch.Tensor] = []
        if initial_input is None:
            if self.scalar_input:
                initial_input = torch.zeros(B, 1, 1)
            else:
                initial_input = torch.zeros(B, 1, self.out_channels)
                initial_input[:, :, 127] = 1  # TODO: is this ok?
            # https://github.com/pytorch/pytorch/issues/584#issuecomment-275169567
            if next(self.parameters()).is_cuda:
                initial_input = initial_input.cuda()
        elif initial_input.size(1) == self.out_channels:
            initial_input = initial_input.transpose(1, 2).contiguous()

        current_input = initial_input

        for t in tqdm(range(T)):
            if test_inputs is not None and t < test_inputs.size(1):
                current_input = test_inputs[:, t, :].unsqueeze(1)
            elif t > 0:
                current_input = outputs[-1]

            # Conditioning features for single time step
            ct = None if c is None else c[:, t, :].unsqueeze(1)
            gt = None if g is None else g_btc[:, t, :].unsqueeze(1)

            x = current_input
            x = self.first_conv.incremental_forward(x)
            skips = None
            for f in self.conv_layers:
                x, h = f.incremental_forward(x, ct, gt)
                if self.legacy:
                    skips = h if skips is None else (skips + h) * math.sqrt(0.5)
                else:
                    skips = h if skips is None else (skips + h)
            x = skips
            for f in self.last_conv_layers:
                try:
                    x = f.incremental_forward(x)
                except AttributeError:
                    x = f(x)

            # Generate next input by sampling
            if self.scalar_input:
                x = sample_from_discretized_mix_logistic(
                    x.view(B, -1, 1), log_scale_min=log_scale_min
                )
            else:
                x = F.softmax(x.view(B, -1), dim=1) if softmax else x.view(B, -1)
                if quantize:
                    sample = np.random.choice(
                        np.arange(self.out_channels), p=x.view(-1).data.cpu().numpy()
                    )
                    x.zero_()
                    x[:, sample] = 1.0
            outputs += [x.data]

        # T x B x C
        output_tensor: torch.Tensor = torch.stack(outputs)
        # B x C x T
        output_tensor = output_tensor.transpose(0, 1).transpose(1, 2).contiguous()

        self.clear_buffer()
        return output_tensor

    def clear_buffer(self) -> None:
        """Clears the buffer of the WaveNet model."""
        self.first_conv.clear_buffer()
        for f in self.conv_layers:
            f.clear_buffer()
        for f in self.last_conv_layers:
            try:
                f.clear_buffer()
            except AttributeError:
                pass

    def make_generation_fast_(self) -> None:
        """Makes the generation fast by removing weight normalization."""

        def remove_weight_norm(m):
            try:
                nn.utils.remove_weight_norm(m)
            except ValueError:  # this module didn't have weight norm
                return

        self.apply(remove_weight_norm)


class WaveNetRNN(WaveNet):
    """WaveNetRNN is an extension of the WaveNet model that incorporates RNN layers for improved sequence modeling.

    Args:
        out_channels (int): Number of output channels.
        layers (int): Number of layers in the WaveNet.
        stacks (int): Number of stacks in the WaveNet.
        residual_channels (int): Number of residual channels.
        gate_channels (int): Number of gate channels.
        kernel_size (int): Size of the convolutional kernel.
        dropout (float): Dropout rate.
        rnn_hidden_size (int): Number of hidden units in the RNN.
        rnn_layers (int): Number of RNN layers.
        bidirectional (bool): If True, use bidirectional RNN.
        rnn_type (str): Type of RNN ('gru', 'lstm', 'rnn').
        cin_channels (int): Number of local conditioning channels.
        gin_channels (int): Number of global conditioning channels.
        n_speakers (int): Number of speakers for speaker embedding.
        weight_normalization (bool): If True, apply weight normalization.
        upsample_conditional_features (bool): If True, upsample conditional features.
        upsample_scales (list): List of upsample scales.
        freq_axis_kernel_size (int): Kernel size for frequency axis.
        scalar_input (bool): If True, use scalar input.
        use_speaker_embedding (bool): If True, use speaker embedding.
        legacy (bool): If True, use legacy mode.
    """

    def __init__(
        self,
        out_channels=256,
        layers=20,
        stacks=2,
        residual_channels=256,
        gate_channels=256,
        kernel_size=3,
        dropout=1 - 0.95,
        rnn_hidden_size=256,
        rnn_layers=2,
        bidirectional=True,
        rnn_type: str = "gru",
        cin_channels=-1,
        gin_channels=-1,
        n_speakers=None,
        weight_normalization=True,
        upsample_conditional_features=False,
        upsample_scales=None,
        freq_axis_kernel_size=3,
        scalar_input=False,
        use_speaker_embedding=True,
        legacy=True,
    ) -> None:
        """Initialize the WaveNetRNN model."""
        super().__init__(
            out_channels=out_channels,
            layers=layers,
            stacks=stacks,
            residual_channels=residual_channels,
            gate_channels=gate_channels,
            skip_out_channels=out_channels,
            kernel_size=kernel_size,
            dropout=dropout,
            cin_channels=cin_channels,
            gin_channels=gin_channels,
            n_speakers=n_speakers,
            weight_normalization=weight_normalization,
            upsample_conditional_features=upsample_conditional_features,
            upsample_scales=upsample_scales,
            freq_axis_kernel_size=freq_axis_kernel_size,
            scalar_input=scalar_input,
            use_speaker_embedding=use_speaker_embedding,
            legacy=legacy,
        )

        assert rnn_type.lower() in ["gru", "lstm", "rnn"], f"Invalid RNN type: {rnn_type}"
        assert rnn_hidden_size % (2 if bidirectional else 1) == 0, (
            "rnn_hidden_size must be divisible by 2 if bidirectional=True"
        )
        assert rnn_layers > 0, "rnn_layers must be greater than 0"
        assert rnn_hidden_size > 0, "rnn_hidden_size must be greater than 0"
        assert rnn_layers > 0, "rnn_layers must be greater than 0"

        self.rnn = RNNType.from_str(rnn_type.lower())(
            input_size=out_channels,
            hidden_size=rnn_hidden_size,
            num_layers=rnn_layers,
            batch_first=True,
            bidirectional=bidirectional,
        )

        rnn_output_size = rnn_hidden_size * (2 if bidirectional else 1)
        self.output_layer = nn.Linear(rnn_output_size, out_channels)

    def forward(
        self,
        x: torch.Tensor,
        c: torch.Tensor | None = None,
        g: torch.Tensor | None = None,
        softmax: bool = False,
    ) -> torch.Tensor:
        """Forward pass through the WaveNetRNN model.

        Args:
            x (Tensor): Input tensor of shape (B, C, T).
            c (Tensor): Local conditioning features.
            g (Tensor): Global conditioning features.
            softmax (bool): Whether to apply softmax to the output.

        Returns:
            Tensor: Output tensor of shape (B, C, T).
        """
        skips = super().forward(x, c=c, g=g, softmax=softmax)
        x = skips.permute(0, 2, 1)  # (B, T, C) for RNN
        x, _ = self.rnn(x)
        x = self.output_layer(x)
        x = x.permute(0, 2, 1)  # back to (B, C, T)
        return x
