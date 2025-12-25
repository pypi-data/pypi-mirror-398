"""Search Space module."""

from ray import tune


def basic_classification_search_space():
    return {
        "lr": tune.loguniform(1e-5, 1e-2),
        "batch_size": tune.choice([16, 32, 64, 128]),
        "num_classes": 10,
    }


def continual_learning_search_space():
    return {
        "lr": tune.loguniform(1e-5, 1e-3),
        "alpha": tune.uniform(0.3, 0.9),
        "batch_size": tune.choice([32, 64, 128]),
        "num_classes": 10,  # wird später überschrieben
    }
