import math

import torch
from torch import nn


class PositionEncodingSine(nn.Module):
    def __init__(self, d_model=256, temp_bug_fix=True):
        assert d_model % 4 == 0, "d_model must be divisible by 4"
        super().__init__()
        self.d_model = d_model
        self.temp_bug_fix = temp_bug_fix

    def forward(self, x):
        _, _, H, W = x.shape
        device = x.device

        y_embed = torch.linspace(0, H - 1, H, device=device).unsqueeze(1).repeat(1, W)
        x_embed = torch.linspace(0, W - 1, W, device=device).unsqueeze(0).repeat(H, 1)

        if self.temp_bug_fix:
            dim_t = torch.exp(
                torch.arange(0, self.d_model // 2, 2, dtype=torch.float32, device=device)
                * (-math.log(10000.0) / (self.d_model // 2))
            )
        else:
            dim_t = torch.exp(
                torch.arange(0, self.d_model // 2, 2, dtype=torch.float32, device=device)
                * (-math.log(10000.0) / self.d_model)
            )

        pos_x = x_embed[None, :, :, None] * dim_t[None, None, None, :]
        pos_y = y_embed[None, :, :, None] * dim_t[None, None, None, :]

        pos_enc = torch.zeros((1, self.d_model, H, W), device=device)
        pos_enc[0, 0::4, :, :] = pos_x.sin().permute(0, 3, 1, 2)
        pos_enc[0, 1::4, :, :] = pos_x.cos().permute(0, 3, 1, 2)
        pos_enc[0, 2::4, :, :] = pos_y.sin().permute(0, 3, 1, 2)
        pos_enc[0, 3::4, :, :] = pos_y.cos().permute(0, 3, 1, 2)

        return x + pos_enc


if __name__ == "__main__":
    pe = PositionEncodingSine(d_model=256)
    dummy = torch.randn(1, 256, 60, 80)
    out = pe(dummy)

    print(out.shape)
