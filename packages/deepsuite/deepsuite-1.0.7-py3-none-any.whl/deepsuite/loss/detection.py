"""Detection Loss.

Loss computation for object detection including bbox regression, classification
and optional DFL.

Example:
    .. code-block:: python

        criterion = DetectionLoss(model)
        loss, items = criterion(preds, batch)

References:
    https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html
    https://pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html
"""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast

import torch
from torch import nn

from deepsuite.loss.bbox import BboxLoss
from deepsuite.utils.anchor import make_anchors
from deepsuite.utils.bbox import dist2bbox
from deepsuite.utils.taskAlignedAssigner import TaskAlignedAssigner
from deepsuite.utils.xy import xywh2xyxy


class HypParams(Protocol):
    box: float
    cls: float
    dfl: float
    overlap_mask: bool


class DetectModule(Protocol):
    stride: Sequence[int]
    nc: int
    reg_max: int


class DetectModel(Protocol):
    args: HypParams
    model: Sequence[DetectModule]

    def parameters(self) -> Any: ...


class DetectionLoss:
    """Criterion class for computing training losses for object detection tasks.

    This class computes the loss for object detection tasks, including bounding box regression,
    classification, and distribution focal loss (DFL).

    Attributes:
        bce (nn.BCEWithLogitsLoss): Binary cross-entropy loss with logits.
        hyp (dict): Hyperparameters for the model.
        stride (list): Model strides.
        nc (int): Number of classes.
        no (int): Number of outputs (classes + 4 * reg_max).
        reg_max (int): Maximum value for the regularization.
        device (torch.device): Device on which the model is running.
        use_dfl (bool): Whether to use distribution focal loss.
        assigner (TaskAlignedAssigner): Assigner for task-aligned assignment.
        bbox_loss (Bbox): Bounding box loss instance.
        proj (torch.Tensor): Projection tensor for DFL.
    """

    def __init__(self, model: DetectModel, tal_topk: int = 10) -> None:
        """Initializes DetectionLoss with the model, defining model-related properties and BCE loss function.

        Args:
            model (nn.Module): The model instance.
            tal_topk (int): Top-k value for task-aligned assignment. Default is 10.
        """
        device = next(model.parameters()).device  # get model device
        h: HypParams = model.args  # hyperparameters

        m: DetectModule = model.model[-1]  # Detect() module
        self.bce = nn.BCEWithLogitsLoss(reduction="none")
        self.hyp = h
        self.strides: Sequence[int] = m.stride  # model strides
        self.nc = m.nc  # number of classes
        self.no = m.nc + m.reg_max * 4
        self.reg_max = m.reg_max
        self.device = device

        self.use_dfl = m.reg_max > 1

        self.assigner = TaskAlignedAssigner(topk=tal_topk, num_classes=self.nc, alpha=0.5, beta=6.0)
        self.bbox_loss = BboxLoss(m.reg_max).to(device)
        self.proj = torch.arange(m.reg_max, dtype=torch.float, device=device)

    def preprocess(
        self, targets: torch.Tensor, batch_size: int, scale_tensor: torch.Tensor
    ) -> torch.Tensor:
        """Preprocesses the target counts and matches with the input batch size to output a tensor.

        Args:
            targets (torch.Tensor): Target tensor containing batch indices, class labels, and bounding boxes.
            batch_size (int): Size of the batch.
            scale_tensor (torch.Tensor): Tensor for scaling bounding boxes.

        Returns:
            torch.Tensor: Preprocessed target tensor.
        """
        nl, ne = targets.shape
        if nl == 0:
            out = torch.zeros(batch_size, 0, ne - 1, device=self.device)
        else:
            i = targets[:, 0]  # image index
            _, counts = torch.unique(i, return_counts=True)
            counts = counts.to(dtype=torch.int32)
            out = torch.zeros(batch_size, counts.max(), ne - 1, device=self.device)
            for j in range(batch_size):
                matches = i == j
                if n := matches.sum():
                    out[j, :n] = targets[matches, 1:]
            out[..., 1:5] = xywh2xyxy(out[..., 1:5].mul_(scale_tensor))
        return out

    def bbox_decode(self, anchor_points: torch.Tensor, pred_dist: torch.Tensor) -> torch.Tensor:
        """Decode predicted object bounding box coordinates from anchor points and distribution.

        Args:
            anchor_points (torch.Tensor): Anchor points.
            pred_dist (torch.Tensor): Predicted distances.

        Returns:
            torch.Tensor: Decoded bounding box coordinates.
        """
        if self.use_dfl:
            b, a, c = pred_dist.shape  # batch, anchors, channels
            pred_dist = (
                pred_dist.view(b, a, 4, c // 4).softmax(3).matmul(self.proj.type(pred_dist.dtype))
            )

        return cast("torch.Tensor", dist2bbox(pred_dist, anchor_points, xywh=False))

    def __call__(
        self, preds: torch.Tensor | tuple[torch.Tensor, ...], batch: Mapping[str, torch.Tensor]
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Calculate the sum of the loss for box, cls and dfl multiplied by batch size.

        Args:
            preds (torch.Tensor): Predicted logits or probabilities.
            batch (dict): A dictionary containing the true labels and bounding boxes.

        Returns:
            tuple: A tuple containing the total loss and the detached loss items.
        """
        loss = torch.zeros(3, device=self.device)  # box, cls, dfl
        feats = preds[1] if isinstance(preds, tuple) else preds
        split_out: tuple[torch.Tensor, torch.Tensor] = cast(
            "tuple[torch.Tensor, torch.Tensor]",
            torch.cat([xi.view(feats[0].shape[0], self.no, -1) for xi in feats], 2).split(  # type: ignore[no-untyped-call]
                (self.reg_max * 4, self.nc), 1
            ),
        )
        pred_distri, pred_scores = split_out

        pred_scores = pred_scores.permute(0, 2, 1).contiguous()
        pred_distri = pred_distri.permute(0, 2, 1).contiguous()

        dtype = pred_scores.dtype
        batch_size = pred_scores.shape[0]
        imgsz = (
            torch.tensor(feats[0].shape[2:], device=self.device, dtype=dtype) * self.strides[0]
        )  # image size (h,w)
        anchor_points, stride_tensor = make_anchors(feats, self.strides, 0.5)

        # Targets
        targets = torch.cat(
            (batch["batch_idx"].view(-1, 1), batch["cls"].view(-1, 1), batch["bboxes"]), 1
        )
        targets = self.preprocess(
            targets.to(self.device), batch_size, scale_tensor=imgsz[[1, 0, 1, 0]]
        )
        gt_labels, gt_bboxes = targets.split((1, 4), 2)  # type: ignore[no-untyped-call]  # cls, xyxy
        mask_gt = gt_bboxes.sum(2, keepdim=True).gt_(0.0)

        # Pboxes
        pred_bboxes = self.bbox_decode(anchor_points, pred_distri)  # xyxy, (b, h*w, 4)

        _, target_bboxes, target_scores, fg_mask, _ = self.assigner(
            pred_scores.detach().sigmoid(),
            (pred_bboxes.detach() * stride_tensor).type(gt_bboxes.dtype),
            anchor_points * stride_tensor,
            gt_labels,
            gt_bboxes,
            mask_gt,
        )

        target_scores_sum = max(target_scores.sum(), 1)

        # Cls loss
        loss[1] = self.bce(pred_scores, target_scores.to(dtype)).sum() / target_scores_sum  # BCE

        # Bbox loss
        if fg_mask.sum():
            target_bboxes /= stride_tensor
            loss[0], loss[2] = self.bbox_loss(
                pred_distri,
                pred_bboxes,
                anchor_points,
                target_bboxes,
                target_scores,
                target_scores_sum,
                fg_mask,
            )

        loss[0] *= self.hyp.box  # box gain
        loss[1] *= self.hyp.cls  # cls gain
        loss[2] *= self.hyp.dfl  # dfl gain

        return loss.sum() * batch_size, loss.detach()  # loss(box, cls, dfl)
