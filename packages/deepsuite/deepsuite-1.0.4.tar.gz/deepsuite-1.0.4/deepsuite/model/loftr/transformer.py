from torch import nn

from deepsuite.model.loftr.encoder_layer import LoFTREncoderLayer


class LocalFeatureTransformer(nn.Module):
    def __init__(
        self,
        d_model: int = 128,
        nhead: int = 8,
        layer_names: list[str] = ("self", "cross"),
        attention: str = "linear",
    ):
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.layer_names = layer_names
        self.attention_type = attention

        self.layers = nn.ModuleList(
            [
                LoFTREncoderLayer(self.d_model, self.nhead, attention=self.attention_type)
                for _ in self.layer_names
            ]
        )

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, feat0, feat1, mask0=None, mask1=None):
        assert feat0.size(2) == self.d_model, "Input feature dim must match d_model"

        for name, layer in zip(self.layer_names, self.layers):
            if name == "self":
                feat0 = layer(feat0, feat0, mask0, mask0)
                feat1 = layer(feat1, feat1, mask1, mask1)
            elif name == "cross":
                feat0 = layer(feat0, feat1, mask0, mask1)
                feat1 = layer(feat1, feat0, mask1, mask0)
            else:
                raise KeyError(f"Unknown layer type: {name}")

        return feat0, feat1
