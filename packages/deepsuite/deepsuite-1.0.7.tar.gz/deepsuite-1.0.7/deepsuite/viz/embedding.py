"""Embedding module."""

import io

from loguru import logger
import matplotlib.pyplot as plt
import mlflow
from PIL import Image
from sklearn.manifold import TSNE
from torch import Tensor, isnan


def log_embedding_plot_to_mlflow(
    embeddings: Tensor, labels: Tensor, step: int, components: int = 2
) -> None:
    """Log a TSNE embedding plot to MLflow as an image.

    This function reduces high-dimensional embeddings to 2D (or `components`-D),
    generates a scatter plot colored by labels, and logs the plot to MLflow
    using `mlflow.log_image`.

    If the embedding tensor contains NaNs, the function exits early
    and logs a warning.

    Args:
        embeddings (Tensor): The input embeddings tensor of shape (N, D),
            where N is the number of samples and D the feature dimension.
        labels (Tensor): A tensor of labels corresponding to the embeddings (N,).
        step (int): The current global step used to name the image artifact.
        components (int): Number of TSNE components to reduce to. Defaults to 2.

    Returns:
        None
    """
    if isnan(embeddings).any():
        logger.warning("NaNs in embeddings - skipping TSNE logging.")
        return

    # Reduzieren auf 2D
    tsne = TSNE(n_components=components)
    reduced = tsne.fit_transform(embeddings.numpy())

    plt.figure(figsize=(6, 6))
    scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=labels.numpy(), cmap="tab10", alpha=0.7)
    plt.colorbar(scatter)

    # Als Bild in Buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    img = Image.open(buf)
    mlflow.log_image(img, f"embeddings_epoch_{step}.png")
