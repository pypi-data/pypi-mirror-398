"""Berechnet die Intersection over Union (IoU) für Bounding Boxes.

Dieses Skript enthält eine Funktion, die die IoU für Bounding Boxes berechnet.
Die Funktion unterstützt verschiedene Formen für `box1` und `box2`, solange die letzte Dimension 4 beträgt.

Beispiel:
    >>> import torch
    >>> from deepsuite.metric.bbox_iou import bbox_iou
    >>> box1 = torch.tensor([[0, 0, 2, 2]])
    >>> box2 = torch.tensor([[1, 1, 3, 3]])
    >>> iou = bbox_iou(box1, box2)
    >>> iou
    tensor([0.1429])

Args:
    box1 (torch.Tensor): Ein Tensor, der eine oder mehrere Bounding Boxes darstellt, wobei die letzte Dimension 4 beträgt.
    box2 (torch.Tensor): Ein Tensor, der eine oder mehrere Bounding Boxes darstellt, wobei die letzte Dimension 4 beträgt.
    xywh (bool, optional): Wenn True, sind die Eingabe-Boxen im Format (x, y, w, h). Wenn False, sind die Eingabe-Boxen im Format (x1, y1, x2, y2). Standard ist True.
    giou (bool, optional): Wenn True, wird der Generalized IoU berechnet. Standard ist False.
    diou (bool, optional): Wenn True, wird der Distance IoU berechnet. Standard ist False.
    ciou (bool, optional): Wenn True, wird der Complete IoU berechnet. Standard ist False.
    eps (float, optional): Ein kleiner Wert, um eine Division durch Null

Returns:
    torch.Tensor: IoU-, giou-, diou- oder ciou-Werte, abhängig von den angegebenen Flags.

"""

import numpy as np
import torch

try:
    from torchvision.ops import box_iou_rotated  # type: ignore
except ImportError:
    try:
        import cv2

        def box_iou_rotated(boxes1, boxes2):
            """Compute IoU between rotated boxes using OpenCV
            Format: [cx, cy, width, height, angle_degrees].
            """
            boxes1 = np.asarray(boxes1, dtype=np.float32)
            boxes2 = np.asarray(boxes2, dtype=np.float32)

            ious = np.zeros((len(boxes1), len(boxes2)), dtype=np.float32)

            for i, box1 in enumerate(boxes1):
                for j, box2 in enumerate(boxes2):
                    # Create rotated rectangles
                    rect1 = ((box1[0], box1[1]), (box1[2], box1[3]), box1[4])
                    rect2 = ((box2[0], box2[1]), (box2[2], box2[3]), box2[4])

                    # Get intersection
                    intersection_points = cv2.rotatedRectangleIntersection(rect1, rect2)

                    if intersection_points[0] == 1:  # If intersection exists
                        area_inter = cv2.contourArea(intersection_points[1])
                    else:
                        area_inter = 0.0

                    # Calculate areas
                    area1 = box1[2] * box1[3]
                    area2 = box2[2] * box2[3]
                    union = area1 + area2 - area_inter

                    ious[i, j] = area_inter / union if union > 0 else 0.0

            return ious

    except ImportError:
        raise ImportError(
            "box_iou_rotated requires either torchvision >= 0.15.0 with "
            "compiled ops, or OpenCV with rotatedRectangleIntersection support. "
            "Install with: pip install opencv-python-headless"
        )


def bbox_iou(
    box1: torch.Tensor,
    box2: torch.Tensor,
    xywh: bool = True,
    giou: bool = False,
    diou: bool = False,
    ciou: bool = False,
    eps: float = 1e-7,
):
    """Calculates the Intersection over Union (IoU) between bounding boxes.

    This function supports various shapes for `box1` and `box2` as long as the last dimension is 4.
    For instance, you may pass tensors shaped like (4,), (N, 4), (B, N, 4), or (B, N, 1, 4).
    Internally, the code will split the last dimension into (x, y, w, h) if `xywh=True`,
    or (x1, y1, x2, y2) if `xywh=False`.

    Args:
        box1 (torch.Tensor): A tensor representing one or more bounding boxes, with the last dimension being 4.
        box2 (torch.Tensor): A tensor representing one or more bounding boxes, with the last dimension being 4.
        xywh (bool, optional): If True, input boxes are in (x, y, w, h) format. If False, input boxes are in
                               (x1, y1, x2, y2) format. Defaults to True.
        giou (bool, optional): If True, calculate Generalized IoU. Defaults to False.
        diou (bool, optional): If True, calculate Distance IoU. Defaults to False.
        ciou (bool, optional): If True, calculate Complete IoU. Defaults to False.
        eps (float, optional): A small value to avoid division by zero. Defaults to 1e-7.

    Returns:
        (torch.Tensor): IoU, giou, diou, or ciou values depending on the specified flags.
    """
    # Get the coordinates of bounding boxes
    if xywh:  # transform from xywh to xyxy
        (x1, y1, w1, h1), (x2, y2, w2, h2) = box1.chunk(4, -1), box2.chunk(4, -1)
        w1_, h1_, w2_, h2_ = w1 / 2, h1 / 2, w2 / 2, h2 / 2
        b1_x1, b1_x2, b1_y1, b1_y2 = x1 - w1_, x1 + w1_, y1 - h1_, y1 + h1_
        b2_x1, b2_x2, b2_y1, b2_y2 = x2 - w2_, x2 + w2_, y2 - h2_, y2 + h2_
    else:  # x1, y1, x2, y2 = box1
        b1_x1, b1_y1, b1_x2, b1_y2 = box1.chunk(4, -1)
        b2_x1, b2_y1, b2_x2, b2_y2 = box2.chunk(4, -1)
        w1, h1 = b1_x2 - b1_x1, b1_y2 - b1_y1 + eps
        w2, h2 = b2_x2 - b2_x1, b2_y2 - b2_y1 + eps

    # Intersection area
    inter = (b1_x2.minimum(b2_x2) - b1_x1.maximum(b2_x1)).clamp_(0) * (
        b1_y2.minimum(b2_y2) - b1_y1.maximum(b2_y1)
    ).clamp_(0)

    # Union Area
    union = w1 * h1 + w2 * h2 - inter + eps

    # IoU
    iou = inter / union
    if ciou or diou or giou:
        cw = b1_x2.maximum(b2_x2) - b1_x1.minimum(b2_x1)  # convex (smallest enclosing box) width
        ch = b1_y2.maximum(b2_y2) - b1_y1.minimum(b2_y1)  # convex height
        if ciou or diou:  # Distance or Complete IoU https://arxiv.org/abs/1911.08287v1
            c2 = cw.pow(2) + ch.pow(2) + eps  # convex diagonal squared
            rho2 = (
                (b2_x1 + b2_x2 - b1_x1 - b1_x2).pow(2) + (b2_y1 + b2_y2 - b1_y1 - b1_y2).pow(2)
            ) / 4  # center dist**2
            if (
                ciou
            ):  # https://github.com/Zzh-tju/DIoU-SSD-pytorch/blob/master/utils/box/box_utils.py#L47
                v = (4 / np.pi**2) * ((w2 / h2).atan() - (w1 / h1).atan()).pow(2)
                with torch.no_grad():
                    alpha = v / (v - iou + (1 + eps))
                return iou - (rho2 / c2 + v * alpha)  # CIoU
            return iou - rho2 / c2  # DIoU
        c_area = cw * ch + eps  # convex area
        return iou - (c_area - union) / c_area  # GIoU https://arxiv.org/pdf/1902.09630.pdf
    return iou  # IoU


def rotated_bbox_iou(boxes1: torch.Tensor, boxes2: torch.Tensor) -> torch.Tensor:
    """Berechnet die IoU (Intersection over Union) für rotierte Bounding Boxes mit GPU-Unterstützung.

    Args:
        boxes1 (Tensor): Tensor mit Form (B, 5) für Bounding Boxes (Cx, Cy, W, H, θ) in Grad.
        boxes2 (Tensor): Tensor mit Form (B, 5) für Bounding Boxes (Cx, Cy, W, H, θ) in Grad.

    Returns:
        Tensor: IoU-Werte mit Form (B,)
    """
    assert boxes1.shape == boxes2.shape, "Beide Tensoren müssen dieselbe Form haben!"
    # Konvertiere Bounding Boxes in das erwartete Format für torchvision:
    # Erwartetes Format: (x_center, y_center, width, height, angle in Grad)
    return box_iou_rotated(boxes1, boxes2)
