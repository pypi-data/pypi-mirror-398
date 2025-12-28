"""CenterNet object detection model for keypoint-based detection.

This module implements CenterNet (Center Keypoint Detection), which models
objects as central keypoints with associated size attributes instead of
traditional bounding boxes with corners.

Architecture consists of:
- Backbone for feature extraction
- Multi-Scale Center Head for keypoint, size, and offset predictions
- NMS (Non-Maximum Suppression) for noise suppression

References:
    Zhou, X., Wang, D., & Krähenbühl, P. (2019).
    Objects as Points. arXiv preprint arXiv:1904.07850.
    https://arxiv.org/abs/1904.07850

Example:
    ```python
    import torch
    from deepsuite.model.detection.centernet import CenterNet

    model = CenterNet(num_classes=80, in_channels=3)
    x = torch.randn(2, 3, 512, 512)
    detections = model(x)
    # detections: List[dict] with 'boxes', 'scores', 'classes'
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from torch import norm, stack, tensor, topk, zeros
from torch.nn import Module
import torch.nn.functional as F
from torchvision.ops import batched_nms

from deepsuite.heads.centernet import MultiScaleCenterNetHead
from deepsuite.model.feature.fpn import FPN

if TYPE_CHECKING:
    from torch import Tensor


def topk_heatmap(heatmap: Tensor, k: int = 100) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Extract Top-K peaks from heatmaps for keypoint detection.

    This function performs max pooling and identifies the K highest activations
    per class in the heatmap. It returns the positions and class labels.

    Args:
        heatmap: Heatmap tensor. Shape: (batch, classes, height, width).
                 Values should typically be between 0 and 1.
        k: Number of top peaks per batch to extract. Default: 100.

    Returns:
        tuple: A tuple of five tensors:
            - scores: Shape (batch, k*classes). Confidence scores.
            - classes: Shape (batch, k*classes). Class labels.
            - ys: Shape (batch, k*classes). Y-coordinates (row indices).
            - xs: Shape (batch, k*classes). X-coordinates (column indices).

    Example:
        ```python
        heatmap = torch.randn(2, 80, 64, 64)  # Batch=2, 80 classes, 64x64 heatmap
        scores, classes, ys, xs = topk_heatmap(heatmap, k=100)
        print(f"Scores: {scores.shape}")  # (2, 8000)
        ```
    """
    B, C, H, W = heatmap.shape

    # Wende Max-Pooling an und behalte nur Peaks
    heatmap = F.max_pool2d(heatmap, kernel_size=3, stride=1, padding=1) * (
        heatmap == heatmap.max(dim=1, keepdim=True)[0]
    )

    # Flatten für Top-K Extraktion
    heatmap = heatmap.view(B, C, -1)
    topk_scores, topk_inds = topk(heatmap, k)  # (B, C, k)

    # Reshape zurück zu (B, C*k)
    topk_scores = topk_scores.view(B, -1)
    topk_inds = topk_inds.view(B, -1)

    # Extrahiere Klassenlabel und Positionen
    topk_classes = topk_inds // (H * W)
    topk_inds = topk_inds % (H * W)

    topk_ys = (topk_inds // W).float()
    topk_xs = (topk_inds % W).float()

    return topk_scores, topk_classes, topk_ys, topk_xs


def match_triplets(
    tl_coords: Tensor, br_coords: Tensor, ct_coords: Tensor, max_center_dist: float = 2.0
) -> list[tuple[int, int]]:
    """Match Top-Left/Bottom-Right keypoint pairs with center keypoints.

    In CenterNet, objects are detected by their centers (center keypoints).
    This function validates that detected top-left/bottom-right corner pairs
    have a center keypoint that lies close to the computed center.

    Args:
        tl_coords: Tensor of shape (N, 2) with (x, y) top-left coordinates.
        br_coords: Tensor of shape (N, 2) with (x, y) bottom-right coordinates.
        ct_coords: Tensor of shape (M, 2) with possible center keypoints.
        max_center_dist: Maximum Euclidean distance for validation. Default: 2.0.

    Returns:
        list[tuple[int, int]]: List of (tl_idx, br_idx) pairs that are valid.

    Example:
        ```python
        tl = torch.tensor([[10.0, 20.0], [50.0, 60.0]])  # 2 TL keypoints
        br = torch.tensor([[30.0, 40.0], [70.0, 80.0]])  # 2 BR keypoints
        ct = torch.tensor([[20.0, 30.0], [60.0, 70.0]])  # 2 center keypoints

        matches = match_triplets(tl, br, ct, max_center_dist=5.0)
        # Example output: [(0, 0), (1, 1)]
        ```
    """
    matched: list[tuple[int, int]] = []
    for i, (tl_x, tl_y) in enumerate(tl_coords):
        for j, (br_x, br_y) in enumerate(br_coords):
            # Überprüfe, ob Box gültig ist (bottom-right > top-left)
            if br_x <= tl_x or br_y <= tl_y:
                continue

            # Berechne Center aus top-left und bottom-right
            cx = (tl_x + br_x) / 2
            cy = (tl_y + br_y) / 2

            # Überprüfe, ob ein Center-Keypoint nahe liegt
            center = tensor([cx, cy], device=ct_coords.device)
            dists = norm(ct_coords - center, dim=1)

            if (dists < max_center_dist).any():
                matched.append((i, j))

    return matched


def apply_nms(boxes: Tensor, iou_thresh: float = 0.5) -> Tensor:
    """Apply Non-Maximum Suppression (NMS) to detections.

    This function suppresses overlapping detections based on
    Intersection over Union (IoU) and keeps only those with highest scores.

    Args:
        boxes: Tensor of shape (N, 6+) with at least:
               - Columns 0-3: Bounding box coordinates [x1, y1, x2, y2]
               - Column 4: Confidence score
               - Column 5: Class label
               Further columns are ignored.
        iou_thresh: IoU threshold for NMS. Overlaps > iou_thresh are suppressed.
                   Default: 0.5.

    Returns:
        Tensor: Filtered detections (only boxes that passed NMS).

    Example:
        ```python
        detections = torch.tensor(
            [
                [10, 20, 100, 120, 0.9, 1],  # High confidence, class 1
                [15, 25, 105, 125, 0.85, 1],  # Overlaps with above, lower score
                [200, 200, 300, 300, 0.95, 2],  # Different class, high score
            ]
        )
        filtered = apply_nms(detections, iou_thresh=0.5)
        # Output: keeps boxes 0 and 2, removes 1 (overlap with 0)
        ```
    """
    if boxes.numel() == 0:
        return boxes

    # Extrahiere Komponenten
    coords = boxes[:, :4]  # [x1, y1, x2, y2]
    scores = boxes[:, 4]  # Confidence scores
    classes = boxes[:, 5]  # Class labels

    # Wende batched NMS an (clustert pro Klasse)
    keep = batched_nms(coords, scores, classes, iou_thresh)

    return boxes[keep]


def rescale_boxes(
    boxes: Tensor, input_size: tuple[int, int], output_size: tuple[int, int]
) -> Tensor:
    h_in, w_in = input_size
    h_out, w_out = output_size
    scale_x = w_in / w_out
    scale_y = h_in / h_out
    boxes[:, [0, 2]] *= scale_x
    boxes[:, [1, 3]] *= scale_y
    return boxes


class CenterNetModel(Module):
    def __init__(
        self,
        backbone,
        in_channels_list,
        fpn_out_channels=256,
        num_classes=1,
        use_bbox=True,
        do_rescale=True,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        self.neck = FPN(in_channels_list, fpn_out_channels)
        self.head = MultiScaleCenterNetHead(
            [fpn_out_channels] * len(in_channels_list), num_classes=num_classes, use_bbox=use_bbox
        )
        self.do_rescale = do_rescale

    def forward(self, x):
        features = self.backbone(x)  # [C3, C4, C5]
        pyramid = self.neck(features)  # [P3, P4, P5]
        return self.head(pyramid)  # list of dicts


class CenterNetDecoder(Module):
    def __init__(self, topk=100, score_thresh=0.1, do_rescale=True) -> None:
        super().__init__()
        self.topk = topk
        self.score_thresh = score_thresh
        self.do_rescale = do_rescale

    def forward(self, outputs, img_size):
        B = outputs[0]["tl_heat"].shape[0]
        all_boxes = []

        for b in range(B):
            all_scale_boxes = []

            for scale_out in outputs:
                tl_scores, tl_classes, tl_ys, tl_xs = topk_heatmap(
                    scale_out["tl_heat"][b : b + 1], self.topk
                )
                br_scores, _, br_ys, br_xs = topk_heatmap(
                    scale_out["br_heat"][b : b + 1], self.topk
                )
                _, _, ct_ys, ct_xs = topk_heatmap(scale_out["ct_heat"][b : b + 1], self.topk)

                tl_coords = stack([tl_xs[0], tl_ys[0]], dim=1)
                br_coords = stack([br_xs[0], br_ys[0]], dim=1)
                ct_coords = stack([ct_xs[0], ct_ys[0]], dim=1)

                pairs = match_triplets(tl_coords, br_coords, ct_coords)

                for i, j in pairs:
                    x1, y1 = tl_coords[i]
                    x2, y2 = br_coords[j]
                    score = (tl_scores[0][i] + br_scores[0][j]) / 2
                    cls = tl_classes[0][i]
                    if score >= self.score_thresh:
                        all_scale_boxes.append(
                            tensor([x1, y1, x2, y2, score, cls], device=tl_coords.device)
                        )

                if "bbox" in scale_out:
                    reg = scale_out["bbox"][b]
                    for i, j in pairs:
                        center_x = (tl_coords[i][0] + br_coords[j][0]) / 2
                        center_y = (tl_coords[i][1] + br_coords[j][1]) / 2
                        cxi = int(center_x.item())
                        cyi = int(center_y.item())
                        box_reg = reg[:, cyi, cxi]
                        pred_cx, pred_cy, w, h = box_reg
                        x1 = pred_cx - w / 2
                        y1 = pred_cy - h / 2
                        x2 = pred_cx + w / 2
                        y2 = pred_cy + h / 2
                        score = (tl_scores[0][i] + br_scores[0][j]) / 2
                        cls = tl_classes[0][i]
                        if score >= self.score_thresh:
                            all_scale_boxes.append(
                                tensor([x1, y1, x2, y2, score, cls], device=reg.device)
                            )

            if all_scale_boxes:
                boxes = stack(all_scale_boxes)
            else:
                boxes = zeros((0, 6), device=outputs[0]["tl_heat"].device)

            heatmap_size = scale_out["tl_heat"].shape[2:]
            if self.do_rescale:
                boxes = rescale_boxes(boxes, img_size, heatmap_size)

            all_boxes.append(boxes)

        return all_boxes
