import torch
from torch import nn
import torch.nn.functional as F


class FinePreprocess(nn.Module):
    def __init__(
        self,
        fine_concat_coarse_feat: bool = True,
        fine_window_size: int = 5,
        coarse_model: int = 256,
        fine_model: int = 128,
    ) -> None:
        super().__init__()

        self.cat_c_feat = fine_concat_coarse_feat
        self.W = fine_window_size

        d_model_c = coarse_model
        d_model_f = fine_model
        self.d_model_f = d_model_f

        if self.cat_c_feat:
            self.down_proj = nn.Linear(d_model_c, d_model_f, bias=True)
            self.merge_feat = nn.Linear(2 * d_model_f, d_model_f, bias=True)

        self._reset_parameters()

    def _reset_parameters(self) -> None:
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.kaiming_normal_(p, mode="fan_out", nonlinearity="relu")

    def forward(self, feat_f0, feat_f1, feat_c0, feat_c1, data):
        W = self.W
        stride = data["hw0_f"][0] // data["hw0_c"][0]
        data.update({"W": W})

        if data["b_ids"].shape[0] == 0:
            empty = torch.empty(0, W**2, self.d_model_f, device=feat_f0.device)
            return empty, empty

        # 1. Unfold local windows
        def unfold(x):
            return F.unfold(x, kernel_size=(W, W), stride=stride, padding=W // 2)

        def reshape_unfold(x):
            return x.view(x.size(0), self.d_model_f, W * W, -1).permute(0, 3, 2, 1)

        feat_f0_unfold = reshape_unfold(unfold(feat_f0))  # [N, L, W*W, C]
        feat_f1_unfold = reshape_unfold(unfold(feat_f1))

        # 2. Select only matched patches
        b_ids, i_ids, j_ids = data["b_ids"], data["i_ids"], data["j_ids"]
        feat_f0_unfold = feat_f0_unfold[b_ids, i_ids]  # [M, W*W, C]
        feat_f1_unfold = feat_f1_unfold[b_ids, j_ids]

        if self.cat_c_feat:
            # Coarse features -> linear projection
            coarse_cat = torch.cat([feat_c0[b_ids, i_ids], feat_c1[b_ids, j_ids]], dim=0)
            feat_c_win = self.down_proj(coarse_cat)  # [2M, C]

            # Repeat coarse across window
            feat_c_win = feat_c_win.unsqueeze(1).expand(-1, W * W, -1)  # [2M, W*W, C]

            # Concatenate with fine-level windows
            feat_cat = torch.cat(
                [torch.cat([feat_f0_unfold, feat_f1_unfold], dim=0), feat_c_win], dim=-1
            )
            merged = self.merge_feat(feat_cat)  # [2M, W*W, C]
            feat_f0_unfold, feat_f1_unfold = torch.chunk(merged, 2, dim=0)

        return feat_f0_unfold, feat_f1_unfold


if __name__ == "__main__":
    module = FinePreprocess()
    feat_f0 = torch.randn(2, 128, 60, 80)
    feat_f1 = torch.randn(2, 128, 60, 80)
    feat_c0 = torch.randn(2, 256, 30 * 40)  # coarse sequence
    feat_c1 = torch.randn(2, 256, 30 * 40)

    data = {
        "hw0_f": (60, 80),
        "hw0_c": (30, 40),
        "b_ids": torch.tensor([0, 1]),
        "i_ids": torch.tensor([100, 200]),
        "j_ids": torch.tensor([120, 220]),
    }

    out0, out1 = module(feat_f0, feat_f1, feat_c0.permute(0, 2, 1), feat_c1.permute(0, 2, 1), data)
