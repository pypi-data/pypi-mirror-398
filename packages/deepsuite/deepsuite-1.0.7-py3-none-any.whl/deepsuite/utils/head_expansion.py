"""Head expansion utilities for classification heads."""

import torch
from torch import nn


def expand_classifier(model: nn.Module, num_old: int, num_new: int) -> nn.Module:
    """Expand a ``Linear`` classifier head to accommodate new classes.

    Copies existing weights/bias for the old classes and allocates
    new parameters for the additional classes.

    Args:
        model: Module with attribute ``classifier`` of type ``nn.Linear``.
        num_old: Number of existing classes.
        num_new: Number of new classes to add.

    Returns:
        nn.Module: The input model with an expanded ``classifier`` head.
    """
    old_classifier = model.classifier
    assert isinstance(old_classifier, nn.Linear), "Only Linear heads are supported."

    in_features = old_classifier.in_features
    new_classifier = nn.Linear(in_features, num_old + num_new)

    with torch.no_grad():
        new_classifier.weight[:num_old] = old_classifier.weight
        if old_classifier.bias is not None:
            new_classifier.bias[:num_old] = old_classifier.bias

    model.classifier = new_classifier
    return model
