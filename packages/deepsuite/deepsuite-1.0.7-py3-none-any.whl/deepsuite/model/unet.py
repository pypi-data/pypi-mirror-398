from typing import Any

import torch
from torch import nn
import torch.nn.functional as F

from deepsuite.model.conv import ConvNormAct


class UpsampleMixin:
    @staticmethod
    def upsample_like(src, tar):
        return F.interpolate(src, size=tar.shape[2:], mode="bilinear", align_corners=False)


class UNetBlock(nn.Module, UpsampleMixin):
    """Ein rekursiver U-Net-ähnlicher Block mit optionaler Tiefenstruktur,
    bestehend aus Encoder- und Decoder-Pfaden sowie Bottleneck-Stufe.

    Parameter:
        height (int): Tiefe des Blocks (Anzahl Encoder-/Decoderstufen).
        in_ch (int): Anzahl der Eingangskanäle.
        mid_ch (int): Kanalanzahl in Zwischenstufen.
        out_ch (int): Anzahl der Ausgangskanäle.
        dilated (bool): Ob im Bottleneck dilated convolution verwendet wird.
        flat (bool): Ob MaxPooling deaktiviert werden soll.
        conv_type (str): Typ der Convolution ("block", "seb", "depth", etc.).
    """

    def __init__(
        self, height, in_ch, mid_ch, out_ch, dilated=False, flat=False, conv_type: str = "block"
    ) -> None:
        super().__init__()

        self.height = height
        self.flat = flat
        self.dilated = dilated

        self.rebnconvin = ConvNormAct(in_ch, out_ch, dilate=1, conv_type=conv_type)

        self.encoders = nn.ModuleList()
        self.pools = nn.ModuleList()

        in_c = out_ch
        for _i in range(height - 1):
            self.encoders.append(ConvNormAct(in_c, mid_ch, dilate=1, conv_type=conv_type))
            if not flat:
                self.pools.append(nn.MaxPool2d(2, stride=2, ceil_mode=True))
            in_c = mid_ch  # bleibt gleich nach dem ersten Step

        bottleneck_dilate = 2 if dilated else 1
        self.bottleneck = ConvNormAct(mid_ch, mid_ch, dilate=bottleneck_dilate, conv_type=conv_type)

        self.decoders = nn.ModuleList()
        for _ in range(height - 2, -1, -1):
            self.decoders.append(ConvNormAct(mid_ch * 2, mid_ch, dilate=1, conv_type=conv_type))

        self.outconv = ConvNormAct(mid_ch * 2, out_ch, dilate=1, conv_type=conv_type)

    def forward(self, x):
        hx = x
        hxin = self.rebnconvin(hx)

        enc_outs = []
        h = hxin

        for i, enc in enumerate(self.encoders):
            h = enc(h)
            enc_outs.append(h)
            if not self.flat:
                h = self.pools[i](h)

        h = self.bottleneck(h)

        for i, dec in enumerate(self.decoders):
            h = UNetBlock.upsample_like(h, enc_outs[-1 - i])
            h = dec(torch.cat([h, enc_outs[-1 - i]], dim=1))

        h = self.outconv(torch.cat([h, hxin], dim=1))
        return h + hxin


class U2NetLike(nn.Module):
    """Generische U²-Net-Architektur mit konfigurierbarer Tiefenstruktur über ein Stage-Config-Format.

    Parameter:
        cfg (dict): Konfigurationsdictionary mit folgenden Keys:
            - in_ch (int): Eingangs-Kanalanzahl.
            - out_ch (int): Ausgangs-Kanalanzahl.
            - stages (list[dict]): Liste der Blöcke mit Parametern, aufgeteilt in:
                - Encoder/Bottleneck: erste 6 Stufen
                - Decoder: restliche Stufen
                Jeder Eintrag sollte enthalten:
                    - "block": Klassenobjekt des Blocks (z. B. UNetBlock)
                    - "params": Tupel mit positionalen Parametern
                    - "kwargs" (optional): Dictionary mit Keyword-Argumenten
                    - "flat" (optional): Deaktiviert Pooling (für Bottlenecks)
            - side_outputs (int, optional): Anzahl an Side-Ausgaben (Default: 6)
    """

    def __init__(self, cfg) -> None:
        super().__init__()

        self.in_ch = cfg["in_ch"]
        self.out_ch = cfg["out_ch"]

        # Encoder + Bottleneck
        self.enc_stages = nn.ModuleList()
        self.pools = nn.ModuleList()

        for stage in cfg["stages"][:6]:
            block = stage["block"]
            params = stage["params"]
            flat = stage.get("flat", False)
            kwargs = stage.get("kwargs", {})
            self.enc_stages.append(block(*params, **kwargs))
            self.pools.append(None if flat else nn.MaxPool2d(2, stride=2, ceil_mode=True))

        # Decoder
        self.dec_stages = nn.ModuleList()
        for stage in cfg["stages"][6:]:
            block = stage["block"]
            params = stage["params"]
            kwargs = stage.get("kwargs", {})
            self.dec_stages.append(block(*params, **kwargs))

        # Side outputs
        num_sides = cfg.get("side_outputs", 6)
        self.side_outs = nn.ModuleList(
            [
                nn.Conv2d(stage["params"][-1], self.out_ch, 3, padding=1)
                for stage in cfg["stages"][:num_sides]
            ]
        )

        # Fusion layer
        self.outconv = nn.Conv2d(6 * self.out_ch, self.out_ch, 1)

    def forward(self, x, return_dict=False) -> tuple[torch.Tensor, ...] | dict[str, Any]:
        """Vorwärtsdurchlauf des Netzes.

        Args:
            x (Tensor): Eingangstensor der Form (B, C, H, W)
            return_dict (bool): Wenn True, Rückgabe als Dictionary

        Returns:
            tuple oder dict:
                - tuple: (sigmoid(d0), sigmoid(d1), ..., sigmoid(d6))
                - dict: {
                    "out": d0 (logits),
                    "side": [d1, ..., d6] (logits),
                    "sigmoid": [sigmoid(d0), sigmoid(d1), ..., sigmoid(d6)]
                  }
        """
        feats = []
        hx = x

        # Encoder
        for i, stage in enumerate(self.enc_stages):
            hx = stage(hx)
            feats.append(hx)
            pool = self.pools[i]
            if pool is not None:
                hx = pool(hx)

        # Decoder
        for i, stage in enumerate(self.dec_stages):
            up = UNetBlock.upsample_like(hx, feats[-1 - i])
            hx = stage(torch.cat([up, feats[-1 - i]], dim=1))

        # Side outputs
        d_outputs = []
        for i, side in enumerate(self.side_outs):
            d = side(feats[i] if i < 5 else hx)
            d = UNetBlock.upsample_like(d, hx) if i < 5 else d
            d_outputs.append(d)

        d0 = self.outconv(torch.cat(d_outputs, dim=1))

        sig = [F.sigmoid(d0)] + [F.sigmoid(d) for d in d_outputs]

        if return_dict:
            return {
                "out": d0,
                "side": d_outputs,
                "sigmoid": sig,
            }
        return tuple(sig)


class U2Net(U2NetLike):
    """Standard U²-Net-Konfiguration (groß), basierend auf UNetBlock-Stufen."""

    def __init__(self) -> None:
        cfg = {
            "in_ch": 3,
            "out_ch": 1,
            "stages": [
                {
                    "block": UNetBlock,
                    "params": (7, 3, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage1
                {
                    "block": UNetBlock,
                    "params": (6, 64, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage2
                {
                    "block": UNetBlock,
                    "params": (4, 64, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage3
                {
                    "block": UNetBlock,
                    "params": (5, 64, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage4
                {
                    "block": UNetBlock,
                    "params": (4, 64, 16, 64),
                    "flat": True,
                    "kwargs": {"conv_type": "block"},
                },  # stage5
                {
                    "block": UNetBlock,
                    "params": (4, 64, 16, 64),
                    "flat": True,
                    "kwargs": {"conv_type": "block"},
                },  # stage6
                {
                    "block": UNetBlock,
                    "params": (4, 128, 16, 64),
                    "flat": True,
                    "kwargs": {"conv_type": "block"},
                },  # stage5d
                {
                    "block": UNetBlock,
                    "params": (4, 128, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage4d
                {
                    "block": UNetBlock,
                    "params": (5, 128, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage3d
                {
                    "block": UNetBlock,
                    "params": (6, 128, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage2d
                {
                    "block": UNetBlock,
                    "params": (7, 128, 16, 64),
                    "kwargs": {"conv_type": "block"},
                },  # stage1d
            ],
        }
        super().__init__(cfg=cfg)


class U2NetP(U2NetLike):
    """Kompakte U²-Net-Variante mit reduzierter Tiefe (U²-NetP)."""

    def __init__(self) -> None:
        cfg = {
            "in_ch": 3,
            "out_ch": 1,
            "stages": [
                {"block": UNetBlock, "params": (7, 3, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (6, 64, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (5, 64, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (4, 64, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (4, 64, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (4, 64, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (4, 128, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (4, 128, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (5, 128, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (6, 128, 16, 64), "kwargs": {"conv_type": "block"}},
                {"block": UNetBlock, "params": (7, 128, 16, 64), "kwargs": {"conv_type": "block"}},
            ],
        }
        super().__init__(cfg=cfg)


class NestedUNet(nn.Module, UpsampleMixin):
    """UNet++-ähnliches Netzwerk mit dichten Skip-Verbindungen zwischen
    hierarchischen Convolutional-Stages.

    Args:
        in_ch (int): Eingangskanäle
        out_ch (int): Ausgangskanäle
        filters (list[int]): Anzahl an Feature-Kanälen pro Ebene
        depth (int): Anzahl der Downsampling-Stufen
        conv_type (str): Art des Convolution-Blocks
    """

    def __init__(
        self,
        in_ch=3,
        out_ch=1,
        filters=None,
        conv_type="block",
        deep_supervision=True,
        activaten=nn.Sigmoid,
    ) -> None:
        if filters is None:
            filters = [64, 128, 256, 512]
        super().__init__()
        self.deep_supervision = deep_supervision
        self.depth = len(filters)

        self.down_blocks = nn.ModuleList()
        self.pool = nn.MaxPool2d(2, stride=2, ceil_mode=True)

        # Encoder-Stufen
        prev_ch = in_ch
        for f in filters:
            self.down_blocks.append(ConvNormAct(prev_ch, f, conv_type=conv_type))
            prev_ch = f

        # Nested decoder Pfade: x_ij
        self.nest_blocks = nn.ModuleDict()
        for j in range(1, self.depth):  # columns j
            for i in range(self.depth - j):  # rows i
                key = f"x_{i}_{j}"
                in_chs = filters[i] + j * filters[i + 1]
                self.nest_blocks[key] = ConvNormAct(in_chs, filters[i], conv_type=conv_type)

        # Ausgang
        self.final = nn.Conv2d(filters[0], out_ch, kernel_size=1)

        # Optional: Side-Outputs für Deep Supervision
        if self.deep_supervision:
            self.side_outputs = nn.ModuleList(
                [nn.Conv2d(filters[0], out_ch, kernel_size=1) for _ in range(self.depth)]
            )

        self.final_activation = activaten() if activaten is not None else nn.Identity()

    def forward(self, x):
        enc = []
        hx = x

        # Encoder
        for block in self.down_blocks:
            hx = block(hx)
            enc.append(hx)
            hx = self.pool(hx)

        # x_i_0: direkte Feature Maps vom Encoder
        x = {f"x_{i}_0": enc[i] for i in range(self.depth)}

        # Nested Blöcke
        for j in range(1, self.depth):
            for i in range(self.depth - j):
                ups = [self.upsample_like(x[f"x_{i + 1}_{k}"], x[f"x_{i}_{0}"]) for k in range(j)]
                cat = torch.cat([x[f"x_{i}_{0}"], *ups], dim=1)
                x[f"x_{i}_{j}"] = self.nest_blocks[f"x_{i}_{j}"](cat)

        # Ausgang (Hauptpfad: x_0_{depth-1})
        out = self.final(x[f"x_0_{self.depth - 1}"])

        if self.deep_supervision:
            outs = [
                F.interpolate(
                    self.side_outputs[j](x[f"x_0_{j}"]),
                    size=x["x_0_0"].shape[2:],
                    mode="bilinear",
                    align_corners=False,
                )
                for j in range(self.depth)
            ]
            return tuple([self.final_activation(o) for o in outs])

        return self.final_activation(out)


class UNet(U2NetLike):
    def __init__(self, in_ch=3, out_ch=1, base=64, depth=4, block=ConvNormAct) -> None:
        stages = []

        # Encoder
        ch = in_ch
        for d in range(depth):
            out = base * (2**d)
            stages.append({"block": block, "params": (ch, out)})
            ch = out

        # Bottleneck
        bottleneck_ch = base * (2**depth)
        stages.append({"block": block, "params": (ch, bottleneck_ch), "flat": True})

        # Decoder
        for d in reversed(range(depth)):
            in_d = bottleneck_ch + base * (2**d)
            out_d = base * (2**d)
            stages.append({"block": block, "params": (in_d, out_d)})

        cfg = {
            "in_ch": in_ch,
            "out_ch": out_ch,
            "stages": stages,
            "side_outputs": depth + 1,
        }

        super().__init__(cfg)


class UNetFactory:
    """Factory zur Erstellung von UNet-basierten Modellen.
    Unterstützt:
        - U2Net
        - U2NetP
        - NestedUNet (UNet++).
    """

    _registry = {
        "unet": {
            "class": UNet,
            "description": "Einfaches symmetrisches U-Net mit Encoder/Decoder-Struktur.",
            "configurable": True,
            "default_config": {
                "in_ch": 3,
                "out_ch": 1,
                "base": 64,
                "depth": 4,
                "block": ConvNormAct,
            },
        },
        "u2net": {
            "class": U2Net,
            "description": "Großes U²-Net mit tiefem Encoder/Decoder.",
            "configurable": False,
        },
        "u2netp": {
            "class": U2NetP,
            "description": "Kompakte Variante des U²-Net.",
            "configurable": False,
        },
        "unet++": {
            "class": NestedUNet,
            "description": "UNet++ mit dichten Skip-Verbindungen.",
            "configurable": True,
            "default_config": {
                "in_ch": 3,
                "out_ch": 1,
                "filters": [64, 128, 256, 512],
                "conv_type": "block",
                "deep_supervision": True,
            },
        },
        "nestedunet": "unet++",  # Alias
    }

    @staticmethod
    def list_available(with_description=False):
        """Gibt die verfügbaren Modellnamen zurück.

        Args:
            with_description (bool): Wenn True, auch Beschreibung mit ausgeben.

        Returns:
            list[str] oder dict[str, str]
        """
        entries = {}
        for name, info in UNetFactory._registry.items():
            if isinstance(info, str):
                continue  # Alias
            if with_description:
                entries[name] = info["description"]
            else:
                entries[name] = None
        return entries if with_description else list(entries.keys())

    @staticmethod
    def build_model(name="unet++", **kwargs):
        """Baut ein Modell anhand des Namens.

        Args:
            name (str): Modellname
            kwargs: Zusätzliche Parameter (z.B. für UNet++)

        Returns:
            nn.Module
        """
        name = name.lower().strip()
        # Aliasauflösung
        if name in UNetFactory._registry and isinstance(UNetFactory._registry[name], str):
            name = UNetFactory._registry[name]

        if name not in UNetFactory._registry:
            raise ValueError(f"Unbekannter Modellname: '{name}'")

        entry = UNetFactory._registry[name]
        cls = entry["class"]

        if entry.get("configurable", False):
            cfg = entry.get("default_config", {}).copy()
            cfg.update(kwargs)
            return cls(**cfg)
        return cls()
