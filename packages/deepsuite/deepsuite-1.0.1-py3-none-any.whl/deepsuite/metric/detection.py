"""Detection module."""

from collections import defaultdict

import torch

from deepsuite.metric.map import evaluate_map


class DetectionMetrics:
    def __init__(
        self, iou_thresholds=None, num_classes=1, per_class_ap=False, max_detections=100
    ) -> None:
        self.iou_thresholds = iou_thresholds or [0.5 + 0.05 * i for i in range(10)]
        self.num_classes = num_classes
        self.per_class_ap = per_class_ap
        self.max_detections = max_detections
        self.reset()

    def reset(self):
        self.tp = defaultdict(int)
        self.fp = defaultdict(int)
        self.fn = defaultdict(int)
        self.classwise_ap = defaultdict(list) if self.per_class_ap else None
        self.recalls = []

    def update(self, pred_boxes, gt_boxes):
        # Limit detections for AR@K
        if self.max_detections:
            pred_boxes = [
                preds[torch.argsort(preds[:, 4], descending=True)[: self.max_detections]]
                if preds.shape[0] > self.max_detections
                else preds
                for preds in pred_boxes
            ]

        for t in self.iou_thresholds:
            stats = evaluate_map(pred_boxes, gt_boxes, iou_thresh=t)
            self.tp[t] += stats["precision"] * (stats["recall"] + 1e-7)
            self.fp[t] += 1 - stats["precision"]
            self.fn[t] += 1 - stats["recall"]
            self.recalls.append(stats["recall"])

        # Optional: AP pro Klasse
        if self.per_class_ap:
            for cls_id in range(self.num_classes):
                cls_preds = [p[p[:, 5] == cls_id] for p in pred_boxes]
                cls_gts = [g[g[:, 4] == cls_id] for g in gt_boxes]
                stats = evaluate_map(cls_preds, cls_gts, iou_thresh=0.5)
                self.classwise_ap[cls_id].append(stats["AP@0.5"])

    def compute(self):
        aps = []
        for t in self.iou_thresholds:
            p = self.tp[t] / (self.tp[t] + self.fp[t] + 1e-7)
            r = self.tp[t] / (self.tp[t] + self.fn[t] + 1e-7)
            ap = p * r
            aps.append(ap)

        result = {
            "mAP@[.5:.95]": sum(aps) / len(aps),
            "AP@0.5": aps[0],
            "AP@0.75": aps[5] if len(aps) > 5 else None,
            "AR@{}": sum(self.recalls) / len(self.recalls) if self.recalls else 0.0,
        }

        if self.per_class_ap:
            result["AP-per-class"] = {
                cls: sum(ap_list) / len(ap_list) if ap_list else 0.0
                for cls, ap_list in self.classwise_ap.items()
            }

        return result
