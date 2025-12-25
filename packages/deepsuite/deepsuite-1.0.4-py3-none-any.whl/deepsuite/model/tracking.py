"""Tracking module."""

import torch

from deepsuite.tracker.rnn_tracker import RNNTracker


class Tracker(torch.nn.Module):
    def __init__(self, detection_model, reid_encoder=None, hidden_dim=128, rnn_type="GRU") -> None:
        super().__init__()
        self.detection_model = detection_model
        self.reid_encoder = reid_encoder
        self.tracker = RNNTracker(
            input_dim=4, hidden_dim=hidden_dim, output_dim=4, rnn_type=rnn_type
        )

    def forward(self, frames):
        all_boxes = []
        all_features = []

        for frame in frames:
            # 1. Detection
            boxes = self.detection_model(frame)  # [N, 4]
            all_boxes.append(boxes)

            # 2. (Optional) ReID-Feature extrahieren
            if self.reid_encoder is not None and boxes is not None and len(boxes) > 0:
                crops = self.crop_boxes(frame, boxes)  # → [N, C, H, W]
                features = self.reid_encoder(crops)  # → [N, D]
            else:
                features = [None for _ in boxes]

            all_features.append(features)

        # (Optional: hier könntest du all_features zusammenführen oder in TrackerManager geben)
        box_seq = torch.stack(all_boxes, dim=1)  # [B, T, 4]
        return self.tracker(box_seq)

    def crop_boxes(self, image, boxes, size=(128, 256)):
        """Crop bounding boxes from an image tensor.

        Args:
            image: [C, H, W] tensor
            boxes: [N, 4] tensor (x1, y1, x2, y2)

        Returns:
            Cropped image patches [N, C, H_crop, W_crop]
        """
        from torchvision.transforms.functional import resize

        crops = []
        for box in boxes:
            x1, y1, x2, y2 = box.int()
            crop = image[:, y1:y2, x1:x2]
            if crop.numel() == 0:
                crop = torch.zeros(image.shape[0], *size, device=image.device)
            else:
                crop = resize(crop, size)
            crops.append(crop)

        return torch.stack(crops)
