"""Head Expansion module."""

import torch


def expand_classifier(model, num_old: int, num_new: int):
    old_classifier = model.classifier
    assert isinstance(old_classifier, torch.nn.Linear), "Only Linear heads are supported."

    in_features = old_classifier.in_features
    new_classifier = torch.nn.Linear(in_features, num_old + num_new)

    with torch.no_grad():
        new_classifier.weight[:num_old] = old_classifier.weight
        if old_classifier.bias is not None:
            new_classifier.bias[:num_old] = old_classifier.bias

    model.classifier = new_classifier
    return model
