"""Darknet module."""

from torch import nn

from deepsuite.model.feature.darknet import CSPDarknetBackbone


class CSPDarknet(CSPDarknetBackbone):
    def __init__(self, num_classes=1000, stage_indices=(5,)):
        super().__init__(stage_indices=stage_indices)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(1024, num_classes)

    def forward(self, x):
        x = super().forward(x, return_stages=False)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x
