"""Utilities for teacher model handling in continual learning setups.

Includes helpers for copying, freezing, and loading a teacher model
(e.g., for knowledge distillation or self-supervision).
"""

import copy
from typing import Any, cast

import torch
from torch import nn


def copy_teacher(student_model: nn.Module) -> nn.Module:
    """Create a frozen copy of the student model to use as a teacher.

    The copied model is put into evaluation mode and its parameters
    are frozen (i.e., `requires_grad = False`).

    Args:
        student_model (nn.Module): The model to be copied and frozen.

    Returns:
        nn.Module: A frozen, evaluation-mode copy of the input model.
    """
    teacher_model = copy.deepcopy(student_model)
    teacher_model.eval()
    freeze_teacher(teacher_model)
    return teacher_model


def freeze_teacher(model: nn.Module):
    """Freeze all parameters of a model (no gradients will be computed).

    Args:
        model (nn.Module): The model whose parameters will be frozen.

    Returns:
        None
    """
    for param in model.parameters():
        param.requires_grad = False


def load_teacher(
    checkpoint_path: str, model_class: type[nn.Module], **model_kwargs: Any
) -> nn.Module:
    """Load a model from a checkpoint and prepare it as a teacher.

    Loads a model's weights from a file (PyTorch or Lightning checkpoint),
    applies them to a new model instance, and freezes it.

    Only state dicts are supported — full Lightning models will be filtered
    to extract just the weights.

    Args:
        checkpoint_path (str): Path to the `.pt` or `.ckpt` file to load.
        model_class (type[nn.Module]): The class of the model to instantiate.
        **model_kwargs: Keyword arguments to initialize `model_class`.

    Returns:
        nn.Module: A frozen, evaluation-ready teacher model.
    """
    model = model_class(**model_kwargs)

    state_dict_raw: Any = torch.load(checkpoint_path, map_location="cpu")  # type: ignore
    state_dict = cast("dict[str, Any]", state_dict_raw)

    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]

    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)  # type: ignore

    if missing_keys or unexpected_keys:
        print(f"Warnung: Missing keys {missing_keys}, Unexpected keys {unexpected_keys}")

    model.eval()
    freeze_teacher(model)
    return model
