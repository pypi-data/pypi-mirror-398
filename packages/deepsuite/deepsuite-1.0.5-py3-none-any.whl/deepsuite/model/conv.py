"""Conv module."""

import math

import torch
from torch import nn
from torch.nn.functional import linear
from torch.nn.utils.parametrizations import weight_norm


class BaseConv2dBlock(nn.Module):
    """Abstrakte Basisklasse für Conv2d-basierte Blöcke.

    Vereinheitlicht das Conv-BatchNorm-Activation Pattern, das in vielen
    Architekturen verwendet wird. Unterstützt automatische Aktivierungsfunktions-Instanziierung.

    Attributes:
        conv (nn.Conv2d): Convolutional Layer.
        bn (nn.BatchNorm2d | None): Optional Batch-Normalisierungsschicht.
        activation (nn.Module | None): Optional Aktivierungsfunktion.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
        groups: int = 1,
        bias: bool = False,
        use_bn: bool = True,
        activation: type[nn.Module] | nn.Module | None = nn.LeakyReLU,
    ) -> None:
        """Initialisiert den BaseConv2dBlock.

        Args:
            in_channels: Anzahl der Eingabekanäle.
            out_channels: Anzahl der Ausgabekanäle.
            kernel_size: Größe des Convolutional Kernels.
            stride: Schrittweite der Convolution.
            padding: Padding der Convolution.
            groups: Anzahl der Gruppen für die Convolution.
            bias: Ob ein Bias in der Convolution verwendet wird.
            use_bn: Ob Batch Normalization verwendet wird.
            activation: Aktivierungsfunktion (Klasse oder Instanz).
        """
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size, stride, padding, groups=groups, bias=bias
        )
        self.bn = nn.BatchNorm2d(out_channels) if use_bn else None

        # Intelligente Aktivierungsfunktions-Instanziierung
        if activation is None:
            self.activation = None
        elif isinstance(activation, type):
            # Klasse übergeben -> instanziiere mit inplace wenn möglich
            if "inplace" in activation.__init__.__code__.co_varnames:
                self.activation = activation(inplace=True)
            else:
                self.activation = activation()
        else:
            # Bereits instanziiert
            self.activation = activation

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward-Pass durch den Block.

        Args:
            x: Eingabetensor.

        Returns:
            Ausgabetensor nach Conv -> BN -> Activation.
        """
        x = self.conv(x)
        if self.bn is not None:
            x = self.bn(x)
        if self.activation is not None:
            x = self.activation(x)
        return x


class ConvBlock(BaseConv2dBlock):
    """Ein grundlegender Convolutional Block (Conv2d + BatchNorm + Aktivierung).

    Erbt von BaseConv2dBlock und bietet eine einfache Conv-BN-Activation Sequenz.
    Rückwärtskompatibel mit der vorherigen Implementierung.

    Attribute:
        conv (nn.Conv2d): Convolutional Layer.
        bn (nn.BatchNorm2d): Batch-Normalisierungsschicht.
        activation (nn.Module): Aktivierungsfunktion.
    """

    def __init__(
        self,
        in_channels,
        out_channels,
        kernel_size,
        stride=1,
        padding=0,
        groups=1,
        bias=False,
        activation=nn.LeakyReLU,
    ) -> None:
        """Initialisiert den ConvBlock.

        Args:
            in_channels (int): Anzahl der Eingabekanäle.
            out_channels (int): Anzahl der Ausgabekanäle.
            kernel_size (int): Größe des Convolutional Kernels.
            stride (int): Schrittweite der Convolution. Standard ist 1.
            padding (int): Padding der Convolution. Standard ist 0.
            groups (int): Anzahl der Gruppen für die Convolution. Standard ist 1.
            bias (bool): Ob ein Bias in der Convolution verwendet wird. Standard ist False.
            activation (nn.Module): Aktivierungsfunktion. Standard ist LeakyReLU.
        """
        super().__init__(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=groups,
            bias=bias,
            use_bn=True,
            activation=activation,
        )


class DepthwiseSeparableConv(nn.Module):
    """Depthwise Separable Convolution Block.

    Verwendet BaseConv2dBlock für beide Phasen: Depthwise und Pointwise Convolution.
    Effizientere Alternative zu Standard-Convolutions durch Aufteilung in zwei Schritte.

    Attribute:
        depthwise (BaseConv2dBlock): Depthwise Convolutional Block.
        pointwise (BaseConv2dBlock): Pointwise Convolutional Block.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        activation: type[nn.Module] = nn.ReLU,
    ) -> None:
        """Initialisiert die DepthwiseSeparableConv.

        Args:
            in_channels: Anzahl der Eingabekanäle.
            out_channels: Anzahl der Ausgabekanäle.
            stride: Schrittweite der Convolution.
            activation: Aktivierungsfunktion.
        """
        super().__init__()
        # Depthwise: Jeder Kanal wird separat gefaltet (groups=in_channels)
        self.depthwise = BaseConv2dBlock(
            in_channels=in_channels,
            out_channels=in_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            groups=in_channels,
            bias=False,
            use_bn=True,
            activation=activation,
        )

        # Pointwise: 1x1 Convolution zur Kanalkombination
        self.pointwise = BaseConv2dBlock(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=1,
            stride=1,
            padding=0,
            groups=1,
            bias=False,
            use_bn=True,
            activation=activation,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward-Pass durch die DepthwiseSeparableConv.

        Args:
            x: Eingabetensor.

        Returns:
            Ausgabetensor nach Depthwise -> Pointwise Convolution.
        """
        x = self.depthwise(x)
        return self.pointwise(x)


class SEBlock(nn.Module):
    """Squeeze-and-Excitation Block.

    Attribute:
        fc1 (nn.Conv2d): Erste Fully Connected Layer.
        fc2 (nn.Conv2d): Zweite Fully Connected Layer.
        activation (nn.Module): Aktivierungsfunktion.
    """

    def __init__(self, in_channels, reduction=4, activation=nn.SiLU) -> None:
        """Initialisiert den SEBlock.

        Args:
            in_channels (int): Anzahl der Eingabekanäle.
            reduction (int): Reduktionsverhältnis für die Fully Connected Layers. Standard ist 4.
            activation (nn.Module): Aktivierungsfunktion. Standard ist SiLU.
        """
        super().__init__()
        self.fc1 = nn.Conv2d(in_channels, in_channels // reduction, kernel_size=1)
        self.fc2 = nn.Conv2d(in_channels // reduction, in_channels, kernel_size=1)
        self.activation = activation()

    def forward(self, x):
        """Forward-Pass durch den SEBlock.

        Args:
            x (torch.Tensor): Eingabetensor.

        Returns:
            torch.Tensor: Ausgabetensor.
        """
        scale = x.mean((2, 3), keepdim=True)
        scale = self.activation(self.fc1(scale))
        scale = torch.sigmoid(self.fc2(scale))
        return x * scale


class Conv1d(nn.Conv1d):
    """Extended nn.Conv1d for incremental dilated convolutions.

    Attributes:
        input_buffer (torch.Tensor): Buffer for input data.
        _linearized_weight (torch.Tensor): Linearized weight tensor.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the Conv1d layer.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.input_buffer = None
        self._linearized_weight = None
        self.register_backward_hook(self._clear_linearized_weight)

    def incremental_forward(self, input: torch.Tensor) -> torch.Tensor:
        """Incremental forward pass for dilated convolutions.

        Args:
            input (torch.Tensor): Input tensor of shape (B, T, C).

        Returns:
            torch.Tensor: Output tensor.

        Raises:
            RuntimeError: If the method is called in training mode.
        """
        if self.training:
            raise RuntimeError("incremental_forward only supports eval mode")

        # run forward pre hooks (e.g., weight norm)
        for hook in self._forward_pre_hooks.values():
            hook(self, input)

        # reshape weight
        weight = self._get_linearized_weight()
        kw = self.kernel_size[0]
        dilation = self.dilation[0]

        bsz = input.size(0)  # input: bsz x len x dim
        if kw > 1:
            input = input.data
            if self.input_buffer is None:
                self.input_buffer = input.new(bsz, kw + (kw - 1) * (dilation - 1), input.size(2))
                self.input_buffer.zero_()
            else:
                # shift buffer
                self.input_buffer[:, :-1, :] = self.input_buffer[:, 1:, :].clone()
            # append next input
            self.input_buffer[:, -1, :] = input[:, -1, :]
            input = self.input_buffer
            if dilation > 1:
                input = input[:, 0::dilation, :].contiguous()

        output = linear(input=input.view(bsz, -1), weight=weight, bias=self.bias)

        return output.view(bsz, 1, -1)

    @staticmethod
    def factory(
        in_channels, out_channels, kernel_size, dropout=0, std_mul=4.0, **kwargs
    ) -> nn.Module:
        m = Conv1d(in_channels, out_channels, kernel_size, **kwargs)
        std = math.sqrt((std_mul * (1.0 - dropout)) / (m.kernel_size[0] * in_channels))
        m.weight.data.normal_(mean=0, std=std)
        if m.bias is not None:
            m.bias.data.zero_()
        m._linearized_weight = None
        return weight_norm(m)

    @staticmethod
    def conv1x1(in_channels, out_channels, bias=True, weight_normalization=True):
        """1-by-1 convolution layer."""
        if weight_normalization:
            assert bias
            return Conv1d.factory(
                in_channels,
                out_channels,
                kernel_size=1,
                padding=0,
                dilation=1,
                bias=bias,
                std_mul=1.0,
            )
        return Conv1d(in_channels, out_channels, kernel_size=1, padding=0, dilation=1, bias=bias)

    def conv1x1_forward(self, x, is_incremental) -> torch.Tensor:
        """Conv1x1 forward."""
        return self.incremental_forward(x) if is_incremental else self(x)

    def clear_buffer(self) -> None:
        """Clear the input buffer."""
        self.input_buffer = None

    def _get_linearized_weight(self):
        """Get the linearized weight tensor.

        Returns:
            torch.Tensor: Linearized weight tensor.
        """
        if self._linearized_weight is None:
            kw = self.kernel_size[0]
            # nn.Conv1d
            if self.weight.size() == (self.out_channels, self.in_channels, kw):
                weight = self.weight.transpose(1, 2).contiguous()
            else:
                # fairseq.modules.conv_tbc.ConvTBC
                weight = self.weight.transpose(2, 1).transpose(1, 0).contiguous()
            assert weight.size() == (self.out_channels, kw, self.in_channels)
            self._linearized_weight = weight.view(self.out_channels, -1)
        return self._linearized_weight

    def _clear_linearized_weight(self, *args) -> None:
        """Clear the linearized weight tensor.

        Args:
            *args: Variable length argument list.
        """
        self._linearized_weight = None


class CausalConv1d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, dilation) -> None:
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels, out_channels, kernel_size, dilation=dilation, padding=self.padding
        )

    def forward(self, x):
        x = self.conv(x)
        return x[:, :, : -self.padding]  # Causal Padding entfernen


class ResidualConv1dGLU(nn.Module):
    """Residual dilated conv1d + Gated linear unit.

    Args:
        residual_channels (int): Residual input / output channels
        gate_channels (int): Gated activation channels.
        kernel_size (int): Kernel size of convolution layers.
        skip_out_channels (int): Skip connection channels. If None, set to same
          as ``residual_channels``.
        cin_channels (int): Local conditioning channels. If negative value is
          set, local conditioning is disabled.
        gin_channels (int): Global conditioning channels. If negative value is
          set, global conditioning is disabled.
        dropout (float): Dropout probability.
        padding (int): Padding for convolution layers. If None, proper padding
          is computed depends on dilation and kernel_size.
        dilation (int): Dilation factor.
        weight_normalization (bool): If True, DeepVoice3-style weight
          normalization is applied.
    """

    def __init__(
        self,
        residual_channels,
        gate_channels,
        kernel_size,
        skip_out_channels=None,
        cin_channels=-1,
        gin_channels=-1,
        dropout=1 - 0.95,
        padding=None,
        dilation=1,
        causal=True,
        bias=True,
        weight_normalization=True,
        *args,
        **kwargs,
    ) -> None:
        super().__init__()
        self.dropout = dropout
        if skip_out_channels is None:
            skip_out_channels = residual_channels
        if padding is None:
            # no future time stamps available
            padding = (kernel_size - 1) * dilation if causal else (kernel_size - 1) // 2 * dilation
        self.causal = causal

        self.conv = Conv1d(
            residual_channels,
            gate_channels,
            kernel_size,
            padding=padding,
            dilation=dilation,
            bias=bias,
            *args,
            **kwargs,
        )

        if weight_normalization:
            assert bias, "weight normalization requires bias=True"
            self.conv = Conv1d.factory(
                residual_channels,
                gate_channels,
                kernel_size,
                padding=padding,
                dilation=dilation,
                bias=bias,
                std_mul=1.0,
                *args,
                **kwargs,
            )
        else:
            self.conv = Conv1d(
                residual_channels,
                gate_channels,
                kernel_size,
                padding=padding,
                dilation=dilation,
                bias=bias,
                *args,
                **kwargs,
            )

        # local conditioning
        if cin_channels > 0:
            self.conv1x1c = Conv1d.conv1x1(
                cin_channels, gate_channels, bias=bias, weight_normalization=weight_normalization
            )
        else:
            self.conv1x1c = None

        # global conditioning
        if gin_channels > 0:
            self.conv1x1g = Conv1d.conv1x1(
                gin_channels, gate_channels, bias=bias, weight_normalization=weight_normalization
            )
        else:
            self.conv1x1g = None

        # conv output is split into two groups
        gate_out_channels = gate_channels // 2
        self.conv1x1_out = Conv1d.conv1x1(
            gate_out_channels,
            residual_channels,
            bias=bias,
            weight_normalization=weight_normalization,
        )
        self.conv1x1_skip = Conv1d.conv1x1(
            gate_out_channels,
            skip_out_channels,
            bias=bias,
            weight_normalization=weight_normalization,
        )

    def forward(self, x, c=None, g=None):
        return self._forward(x, c, g, False)

    def incremental_forward(self, x, c=None, g=None):
        return self._forward(x, c, g, True)

    def _forward(self, x, c, g, is_incremental):
        """Forward.

        Args:
            x (Tensor): B x C x T
            c (Tensor): B x C x T, Local conditioning features
            g (Tensor): B x C x T, Expanded global conditioning features
            is_incremental (Bool) : Whether incremental mode or not

        Returns:
            Tensor: output
        """
        residual = x
        x = torch.nn.functional.dropout(x, p=self.dropout, training=self.training)
        if is_incremental:
            splitdim = -1
            x = self.conv.incremental_forward(x)
        else:
            splitdim = 1
            x = self.conv(x)
            # remove future time steps
            x = x[:, :, : residual.size(-1)] if self.causal else x

        a, b = x.split(x.size(splitdim) // 2, dim=splitdim)

        # local conditioning
        if c is not None:
            assert self.conv1x1c is not None
            c = self.conv1x1c.conv1x1_forward(c, is_incremental)
            ca, cb = c.split(c.size(splitdim) // 2, dim=splitdim)
            a, b = a + ca, b + cb

        # global conditioning
        if g is not None:
            assert self.conv1x1g is not None
            g = self.conv1x1g.conv1x1_forward(g, is_incremental)
            ga, gb = g.split(g.size(splitdim) // 2, dim=splitdim)
            a, b = a + ga, b + gb

        x = torch.tanh(a) * torch.sigmoid(b)

        # For skip connection
        s = self.conv1x1_skip.conv1x1_forward(x, is_incremental)

        # For residual connection
        x = self.conv1x1_out.conv1x1_forward(x, is_incremental)

        x = (x + residual) * math.sqrt(0.5)
        return x, s

    def clear_buffer(self) -> None:
        for c in [self.conv, self.conv1x1_out, self.conv1x1_skip, self.conv1x1c, self.conv1x1g]:
            if c is not None:
                c.clear_buffer()


def ConvTranspose2d(in_channels, out_channels, kernel_size, weight_normalization=True, **kwargs):
    freq_axis_kernel_size = kernel_size[0]
    m = nn.ConvTranspose2d(in_channels, out_channels, kernel_size, **kwargs)
    m.weight.data.fill_(1.0 / freq_axis_kernel_size)
    m.bias.data.zero_()
    if weight_normalization:
        return weight_norm(m)
    return m
