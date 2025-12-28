"""Inference utilities for running tracking over a dataloader."""

from collections.abc import Callable, Iterable, Iterator
from typing import Any

import torch
from torch import Tensor, nn

from deepsuite.tracker.tracker_manager import TrackerManager


def crop_boxes_from_image(image: Tensor, boxes: Tensor, size: int = 128) -> Tensor:
    crops = []
    for box in boxes:
        x1, y1, x2, y2 = box.int()
        crop = image[:, y1:y2, x1:x2]
        crop_resized = torch.nn.functional.interpolate(
            crop.unsqueeze(0), size=(size, size), mode="bilinear"
        )
        crops.append(crop_resized.squeeze(0))
    return torch.stack(crops)


def run_tracking(
    detector: Callable[[Tensor], Iterable[Tensor]] | nn.Module,
    dataloader: Iterable[dict[str, Any]],
    reid_encoder: nn.Module | None = None,
    device: str = "cpu",
) -> Iterator[tuple[Any, list[list[tuple[int, Tensor]]]]]:
    tracker = TrackerManager(filter_type="kalman", device=device)

    for batch in dataloader:
        images = batch["image"].to(device)
        frame_id = batch["frame_id"]

        # YOLO etc.
        detections = detector(images)  # → boxes [B, N, 4]

        all_tracks = []
        for b, boxes in enumerate(detections):
            frame = images[b]
            crops = crop_boxes_from_image(frame, boxes)  # eigene crop-Funktion

            if reid_encoder:
                with torch.no_grad():
                    features = reid_encoder(crops)
            else:
                features = [None] * len(boxes)

            tracker.update(boxes, features)
            tracks = tracker.get_active_tracks()

            all_tracks.append([(t.id, t.boxes[-1]) for t in tracks])

        yield frame_id, all_tracks
