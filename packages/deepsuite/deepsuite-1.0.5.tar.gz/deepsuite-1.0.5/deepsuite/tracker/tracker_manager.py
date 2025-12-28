"""Tracker Manager module."""

from collections.abc import Sequence

from loguru import logger
from scipy.optimize import linear_sum_assignment
import torch
from torch import nn

from deepsuite.tracker.tracker import Track
from deepsuite.utils.device import get_best_device


class TrackerManager:
    """Manager for multiple object tracks with various filter types.

    Args:
        iou_threshold: Minimum IoU for matching detections to tracks
        max_age: Maximum frames a track can exist without updates
        filter_type: Type of filter ('kalman', 'particle', 'particle_gpu', 'particle_tpu')
        device: Device for computation ('cuda', 'mps', 'cpu', or None for auto-detect)
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_age: int = 30,
        filter_type: str = "kalman",
        device: str | None = None,
    ) -> None:
        self.tracks: list[Track] = []
        self.next_id = 0
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.filter_type = filter_type

        # Auto-detect best device if not specified
        if device is None:
            self.device = str(get_best_device())
        else:
            self.device = device

        logger.info("TrackerManager using device: %s", self.device)

    def update(
        self,
        detections: list[torch.Tensor],
        features: list[torch.Tensor] | None = None,
    ) -> None:
        """Update tracks with new frame detections.

        Args:
            detections: List of [4]-tensors with [x1, y1, x2, y2].
            features: Optional list of appearance embeddings aligned to detections.
        """
        detections = [d.to(self.device) for d in detections]

        # Step 1: Vorhersagen aller aktuellen Tracks
        predictions = [track.predict() for track in self.tracks]

        # Step 2: IoU-Matching
        if predictions and detections:
            iou_matrix = self.compute_iou_matrix(predictions, detections)
            row_inds, col_inds = linear_sum_assignment(-iou_matrix.cpu().numpy())

            matched, unmatched_tracks, unmatched_detections = self.match(
                iou_matrix, row_inds, col_inds
            )
        else:
            matched = []
            unmatched_tracks = list(range(len(self.tracks)))
            unmatched_detections = list(range(len(detections)))

        # Step 3: Update matched Tracks
        for track_idx, det_idx in matched:
            self.tracks[track_idx].update(detections[det_idx])

        # Step 4: Update unmatched Tracks (alter + prüfen)
        for idx in unmatched_tracks:
            track = self.tracks[idx]
            track.time_since_update += 1

        # Step 5: Neue Tracks anlegen
        for det_idx in unmatched_detections:
            self.tracks.append(
                Track(
                    track_id=self.next_id,
                    initial_box=detections[det_idx],
                    feature=features[det_idx] if features is not None else None,
                    filter_type=self.filter_type,
                    device=self.device,
                )
            )

            self.next_id += 1

        # Step 6: Tote Tracks entfernen
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

    @staticmethod
    def compute_similarity_matrix(
        predicted_boxes: Sequence[torch.Tensor],
        predicted_features: Sequence[torch.Tensor],
        gt_boxes: Sequence[torch.Tensor],
        gt_features: Sequence[torch.Tensor],
        alpha: float = 0.5,
        device: str = "cpu",
    ) -> torch.Tensor:
        """Compute a similarity matrix that combines IoU and appearance cosine similarity.

        Args:
            predicted_boxes: List of predicted box tensors [4]
            predicted_features: List of feature tensors [D]
            gt_boxes: List of GT box tensors [4]
            gt_features: List of GT feature tensors [D]
            alpha: Weighting factor between IoU and cosine (0-1)
            device: Torch device
        Returns:
            sim_matrix: Tensor [len(gt_boxes), len(predicted_boxes)]
        """
        iou_mat = TrackerManager.compute_iou_matrix(gt_boxes, predicted_boxes, device=device)

        # [G, D] and [P, D] → [G, P]
        if gt_features and predicted_features and gt_features[0] is not None:
            feats_gt = torch.stack(list(gt_features)).to(device)  # [G, D]
            feats_pred = torch.stack(list(predicted_features)).to(device)  # [P, D]
            # Normalize for cosine similarity
            feats_gt = nn.functional.normalize(feats_gt, dim=1)
            feats_pred = nn.functional.normalize(feats_pred, dim=1)

            # Compute cosine similarity matrix
            cos_sim = feats_gt @ feats_pred.T  # [G, P]
        else:
            cos_sim = torch.zeros_like(iou_mat)

        return alpha * iou_mat + (1 - alpha) * cos_sim

    def get_active_tracks(self) -> list[Track]:
        """Return tracks that received an update in the current frame."""
        return [t for t in self.tracks if t.time_since_update == 0]

    @staticmethod
    def compute_iou_matrix(
        boxes_a: Sequence[torch.Tensor], boxes_b: Sequence[torch.Tensor], device: str = "cpu"
    ) -> torch.Tensor:
        """Compute IoU matrix between two sets of boxes using efficient torch operations.

        Args:
            boxes_a (list of Tensors): each [4]
            boxes_b (list of Tensors): each [4]
            device (str): Torch device
        Returns:
            iou_matrix: Tensor [N, M]
        """
        boxes_a_t = torch.stack(list(boxes_a)).to(device)  # [N, 4]
        boxes_b_t = torch.stack(list(boxes_b)).to(device)  # [M, 4]

        a_exp = boxes_a_t[:, None, :]  # [N, 1, 4]
        b_exp = boxes_b_t[None, :, :]  # [1, M, 4]

        xa = torch.max(a_exp[..., 0], b_exp[..., 0])
        ya = torch.max(a_exp[..., 1], b_exp[..., 1])
        xb = torch.min(a_exp[..., 2], b_exp[..., 2])
        yb = torch.min(a_exp[..., 3], b_exp[..., 3])

        inter_area = (xb - xa).clamp(min=0) * (yb - ya).clamp(min=0)

        area_a = (a_exp[..., 2] - a_exp[..., 0]) * (a_exp[..., 3] - a_exp[..., 1])
        area_b = (b_exp[..., 2] - b_exp[..., 0]) * (b_exp[..., 3] - b_exp[..., 1])

        union = area_a + area_b - inter_area + 1e-6

        iou_mat: torch.Tensor = (inter_area / union).to(device)
        return iou_mat  # [N, M]

    def match(
        self,
        iou_matrix: torch.Tensor,
        row_inds: Sequence[int],
        col_inds: Sequence[int],
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        """Match detections to tracks based on IoU and Hungarian assignment.

        Returns matched pairs and indices of unmatched tracks/detections.
        """
        matched: list[tuple[int, int]] = []
        unmatched_tracks: list[int] = []
        unmatched_detections: list[int] = []
        for r, c in zip(row_inds, col_inds, strict=False):
            if iou_matrix[r, c] >= self.iou_threshold:
                matched.append((r, c))
            else:
                unmatched_tracks.append(r)
                unmatched_detections.append(c)

        unmatched_tracks += [r for r in range(iou_matrix.size(0)) if r not in row_inds]
        unmatched_detections += [c for c in range(iou_matrix.size(1)) if c not in col_inds]

        return matched, unmatched_tracks, unmatched_detections

    def iou(self, box_a: torch.Tensor, box_b: torch.Tensor) -> torch.Tensor:
        """IoU for two [x1, y1, x2, y2] boxes."""
        xa = torch.max(box_a[0], box_b[0])
        ya = torch.max(box_a[1], box_b[1])
        xb = torch.min(box_a[2], box_b[2])
        yb = torch.min(box_a[3], box_b[3])

        inter_area = torch.clamp(xb - xa, min=0) * torch.clamp(yb - ya, min=0)

        box_a_area = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        box_b_area = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

        return inter_area / (box_a_area + box_b_area - inter_area + 1e-6)
