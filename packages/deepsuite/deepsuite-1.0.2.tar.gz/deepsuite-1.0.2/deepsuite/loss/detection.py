"""Detection Loss.
--------------

This module contains the detection loss class for computing training losses for object detection tasks.

Example:
>>> import torch
>>> from deepsuite.loss import DetectionLoss
>>> criterion = DetectionLoss(model)
>>> preds = torch.randn(2, 10)
>>> batch = {"cls": torch.randint(0, 10, (2,))}
>>> loss, loss_items = criterion(preds, batch)
>>> loss
tensor(2.4175)
>>> loss_items
tensor(2.4175)

Attributes:
DetectionLoss: The class for computing detection losses.

Methods:
__call__: Compute the detection loss between predictions and true labels.

References:
https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html
https://pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html
"""

import torch
from torch import nn

from deepsuite.loss.bbox import BboxLoss
from deepsuite.utils.anchor import make_anchors
from deepsuite.utils.bbox import dist2bbox
from deepsuite.utils.taskAlignedAssigner import TaskAlignedAssigner
from deepsuite.utils.xy import xywh2xyxy


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

    def __init__(self, model, tal_topk=10) -> None:
        """Initializes DetectionLoss with the model, defining model-related properties and BCE loss function.

        Args:
            model (nn.Module): The model instance.
            tal_topk (int): Top-k value for task-aligned assignment. Default is 10.
        """
        device = next(model.parameters()).device  # get model device
        h = model.args  # hyperparameters

        m = model.model[-1]  # Detect() module
        self.bce = nn.BCEWithLogitsLoss(reduction="none")
        self.hyp = h
        self.stride = m.stride  # model strides
        self.nc = m.nc  # number of classes
        self.no = m.nc + m.reg_max * 4
        self.reg_max = m.reg_max
        self.device = device

        self.use_dfl = m.reg_max > 1

        self.assigner = TaskAlignedAssigner(topk=tal_topk, num_classes=self.nc, alpha=0.5, beta=6.0)
        self.bbox_loss = BboxLoss(m.reg_max).to(device)
        self.proj = torch.arange(m.reg_max, dtype=torch.float, device=device)

    def preprocess(self, targets, batch_size, scale_tensor):
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
            _, counts = i.unique(return_counts=True)
            counts = counts.to(dtype=torch.int32)
            out = torch.zeros(batch_size, counts.max(), ne - 1, device=self.device)
            for j in range(batch_size):
                matches = i == j
                if n := matches.sum():
                    out[j, :n] = targets[matches, 1:]
            out[..., 1:5] = xywh2xyxy(out[..., 1:5].mul_(scale_tensor))
        return out

    def bbox_decode(self, anchor_points, pred_dist):
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

        return dist2bbox(pred_dist, anchor_points, xywh=False)

    def __call__(self, preds, batch):
        """Calculate the sum of the loss for box, cls and dfl multiplied by batch size.

        Args:
            preds (torch.Tensor): Predicted logits or probabilities.
            batch (dict): A dictionary containing the true labels and bounding boxes.

        Returns:
            tuple: A tuple containing the total loss and the detached loss items.
        """
        loss = torch.zeros(3, device=self.device)  # box, cls, dfl
        feats = preds[1] if isinstance(preds, tuple) else preds
        pred_distri, pred_scores = torch.cat(
            [xi.view(feats[0].shape[0], self.no, -1) for xi in feats], 2
        ).split((self.reg_max * 4, self.nc), 1)

        pred_scores = pred_scores.permute(0, 2, 1).contiguous()
        pred_distri = pred_distri.permute(0, 2, 1).contiguous()

        dtype = pred_scores.dtype
        batch_size = pred_scores.shape[0]
        imgsz = (
            torch.tensor(feats[0].shape[2:], device=self.device, dtype=dtype) * self.stride[0]
        )  # image size (h,w)
        anchor_points, stride_tensor = make_anchors(feats, self.stride, 0.5)

        # Targets
        targets = torch.cat(
            (batch["batch_idx"].view(-1, 1), batch["cls"].view(-1, 1), batch["bboxes"]), 1
        )
        targets = self.preprocess(
            targets.to(self.device), batch_size, scale_tensor=imgsz[[1, 0, 1, 0]]
        )
        gt_labels, gt_bboxes = targets.split((1, 4), 2)  # cls, xyxy
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
