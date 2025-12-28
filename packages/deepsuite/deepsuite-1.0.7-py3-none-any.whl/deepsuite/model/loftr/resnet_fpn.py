from torch import nn

from deepsuite.model.feature.fpn import FPN
from deepsuite.model.feature.resnet import ResNetBackbone


class ResnetWithFPN(nn.Module):
    def __init__(
        self, resnet_variant: str = "resnet50", in_channels: int = 1, fpn_out_channels: int = 256
    ) -> None:
        super().__init__()

        self.resnet = ResNetBackbone(
            resnet_variant=resnet_variant,
            in_channels=in_channels,
            stage_indices=(1, 2, 3),  # die Stufen für FPN
        )

        # Kanäle der ResNet-Stufen
        stage_channels = self.resnet.channels_list
        selected_channels = [stage_channels[i] for i in (1, 2, 3)]  # z. B. [128, 256, 512]

        self.fpn = FPN(in_channels_list=selected_channels, out_channels=fpn_out_channels)

    def forward(self, x):
        features = self.resnet(x, return_stages=True)  # List of feature maps
        fpn_features = self.fpn(features)
        # Rückgabe wie in LoFTR erwartet: [coarse_feat, fine_feat]
        return fpn_features[-1], fpn_features[0]  # coarse = tiefstes, fine = oberstes
