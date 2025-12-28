"""Embedding Logger module."""

from pytorch_lightning import Callback
from pytorch_lightning.loggers.tensorboard import TensorBoardLogger
import torch

from deepsuite.viz.embedding import log_embedding_plot_to_mlflow


class EmbeddingLoggerCallback(Callback):
    """Logs embedding vectors during validation to TensorBoard and optionally MLflow.

    This callback collects embeddings and corresponding labels from a limited
    number of validation batches. At the end of the epoch, it visualizes them
    in TensorBoard and optionally logs a TSNE plot to MLflow.

    Example:
        >>> callback = EmbeddingLoggerCallback(num_batches=3, log_to_mlflow=True)
        >>> trainer = Trainer(callbacks=[callback])
    """

    def __init__(self, num_batches: int = 1, log_to_mlflow: bool = True) -> None:
        """Initializes the embedding logging callback.

        Args:
            num_batches (int): Number of validation batches to collect for embedding visualization.
            log_to_mlflow (bool): Whether to log a TSNE plot of embeddings to MLflow.
        """
        self.num_batches = num_batches
        self.embeddings = []
        self.labels = []
        self.log_to_mlflow = log_to_mlflow

    def on_validation_batch_end(
        self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx=0
    ) -> None:
        """Collects embeddings and labels from the current batch during validation.

        Args:
            trainer (Trainer): The PyTorch Lightning trainer.
            pl_module (LightningModule): The current Lightning model.
            outputs: The outputs from the validation step (unused).
            batch (Tuple[Tensor, Tensor]): The input batch, typically (x, y).
            batch_idx (int): The index of the current batch.
            dataloader_idx (int): Index of the current dataloader (unused).
        """
        if batch_idx >= self.num_batches:
            return

        x, y = batch
        with torch.no_grad():
            if hasattr(pl_module, "extract_features"):
                features = pl_module.extract_features(x.to(pl_module.device))
            else:
                features = pl_module(x.to(pl_module.device))

        self.embeddings.append(features.cpu())
        self.labels.append(y.cpu())

    def on_validation_epoch_end(self, trainer, pl_module) -> None:
        """Logs collected embeddings to TensorBoard and optionally to MLflow.

        At the end of the validation epoch, this method concatenates the stored
        embeddings and labels, then logs them as an embedding projector to
        TensorBoard. If `log_to_mlflow` is True and `pl_module.use_mlflow` is set,
        it also logs a TSNE image to MLflow.

        Args:
            trainer (Trainer): The PyTorch Lightning trainer.
            pl_module (LightningModule): The current Lightning model.
        """
        if not self.embeddings or not self.labels:
            return

        embeddings = torch.cat(self.embeddings, dim=0)
        labels = torch.cat(self.labels, dim=0)

        # TensorBoard Logging
        tb_logger = None
        for logger in trainer.loggers if isinstance(trainer.loggers, list) else [trainer.logger]:
            if isinstance(logger, TensorBoardLogger):
                tb_logger = logger.experiment  # SummaryWriter
                break

        if tb_logger:
            tb_logger.add_embedding(
                mat=embeddings,
                metadata=labels.tolist(),
                global_step=trainer.global_step,
                tag="val_embeddings",
            )

        # MLflow Logging
        if self.log_to_mlflow and getattr(pl_module, "use_mlflow", False):
            log_embedding_plot_to_mlflow(
                embeddings=embeddings, labels=labels, step=trainer.global_step
            )

        # Puffer leeren
        self.embeddings.clear()
        self.labels.clear()
