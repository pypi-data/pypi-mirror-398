"""Fpn module."""

from torch import nn


class FPN(nn.Module):
    """Feature Pyramid Network (FPN) mit flexiblen Channel-Größen."""

    def __init__(self, in_channels_list, out_channels) -> None:
        super().__init__()
        self.lateral_convs = nn.ModuleList()
        self.output_convs = nn.ModuleList()

        for in_channels in in_channels_list:
            self.lateral_convs.append(nn.Conv2d(in_channels, out_channels, kernel_size=1))
            self.output_convs.append(
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
            )

    def forward(self, features):
        # Laterale Verbindungen
        laterals = [
            lateral_conv(feature) for lateral_conv, feature in zip(self.lateral_convs, features)
        ]

        # Top-down Pfad
        for i in range(len(laterals) - 1, 0, -1):
            laterals[i - 1] += nn.functional.interpolate(
                laterals[i], scale_factor=2, mode="nearest"
            )

        # Ausgabe
        outputs = [
            output_conv(lateral) for output_conv, lateral in zip(self.output_convs, laterals)
        ]
        return outputs
