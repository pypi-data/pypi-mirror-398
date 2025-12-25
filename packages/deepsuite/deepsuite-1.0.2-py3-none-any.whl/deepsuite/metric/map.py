"""Map module."""

from deepsuite.metric.bbox_iou import bbox_iou


def evaluate_map(pred_boxes, gt_boxes, iou_thresh=0.5):
    """Args:
        pred_boxes (List[Tensor]): pro Bild, Tensor[N, 6] mit (x1, y1, x2, y2, score, cls)
        gt_boxes (List[Tensor]): pro Bild, Tensor[M, 5] mit (x1, y1, x2, y2, cls)
        iou_thresh (float): IoU Threshold für einen True Positive

    Returns:
        dict: {"precision": ..., "recall": ..., "AP": ...}
    """
    TP, FP, FN = 0, 0, 0

    for preds, gts in zip(pred_boxes, gt_boxes):
        if preds.numel() == 0 and gts.numel() == 0:
            continue
        if preds.numel() == 0:
            FN += gts.shape[0]
            continue
        if gts.numel() == 0:
            FP += preds.shape[0]
            continue

        ious = bbox_iou(preds[:, :4].unsqueeze(1), gts[:, :4].unsqueeze(0), xywh=False)  # (P, G)
        max_ious, max_idxs = ious.max(dim=1)

        matched_gt = set()
        for i, (iou, gt_idx) in enumerate(zip(max_ious, max_idxs)):
            if iou >= iou_thresh and int(gt_idx.item()) not in matched_gt:
                if preds[i, 5] == gts[gt_idx, 4]:  # class match
                    TP += 1
                    matched_gt.add(int(gt_idx.item()))
                else:
                    FP += 1
            else:
                FP += 1
        FN += gts.shape[0] - len(matched_gt)

    precision = TP / (TP + FP + 1e-7)
    recall = TP / (TP + FN + 1e-7)
    ap50 = precision * recall  # Vereinfachtes AP

    return {"precision": precision, "recall": recall, "AP@0.5": ap50}
