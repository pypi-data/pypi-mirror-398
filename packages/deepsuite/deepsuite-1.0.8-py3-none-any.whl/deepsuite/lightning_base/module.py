r"""Base Lightning module with Ray Tune integration and metrics.

This module provides a convenient base class for training models with
PyTorch Lightning, optional MLflow logging, Ray Tune-based hyperparameter
search, and common classification metrics.

Mathematical background: the model optimizes a loss :math:`L(\theta)` over
parameters :math:`\theta`, e.g. minimizing :math:`L(\theta)` such that
:math:`\theta^* = \arg\\min_\theta L(\theta)`. For MSE this is
:math:`L(y, \\hat{y}) = \frac{1}{N} \\sum_{i=1}^{N} (y_i - \\hat{y}_i)^2`.
"""

from collections.abc import Sequence
import inspect
from typing import TYPE_CHECKING

from loguru import logger
import pytorch_lightning as pl
from ray import tune
from ray.tune.integration.pytorch_lightning import TuneReportCheckpointCallback
import torch
from torchmetrics import AUROC, Accuracy, F1Score, Precision, Recall

from deepsuite.config.config_manager import ConfigManager
from deepsuite.lightning_base.trainer import BaseTrainer
from deepsuite.loss import get_loss

if TYPE_CHECKING:
    from torchviz import Digraph

try:
    from torchinfo import ModelStatistics, summary

    HAS_TORCHINFO = True
except ImportError:
    HAS_TORCHINFO = False

try:
    from torchviz import Digraph, make_dot  # type: ignore

    HAS_TORCHVIZ = True
except ImportError:
    HAS_TORCHVIZ = False
    Digraph = None  # type: ignore
    make_dot = None  # type: ignore


class BaseModule(pl.LightningModule):
    """PyTorch Lightning base module with metrics and tuning helpers."""

    def __init__(
        self,
        search_space: dict | None = None,  # Ray Tune Search Space
        log_every_n_steps=50,
        use_mlflow=False,
        loss_name: str = "mse",
        loss_params: dict | None = None,
        loss_fn=torch.nn.functional.mse_loss,
        optimizer=torch.optim.Adam,
        metrics: Sequence[str] = ("accuracy", "precision", "recall"),
        num_classes: int = 10,  # Default value added to docstring
        teacher_model: torch.nn.Module | None = None,  # Default value added to docstring
    ) -> None:
        """Initializes the BaseModel with the given parameters.

        Parameters
        ----------
        search_space : dict, optional
            Dictionary defining the Ray Tune search space. Default: ``None``.
        log_every_n_steps : int, optional
            Number of steps between logging metrics. Default: ``50``.
        use_mlflow : bool, optional
            Whether to enable MLflow logging. Default: ``False``.
        loss_fn : callable, optional
            Loss function to use. Default: ``torch.nn.functional.mse_loss``.
        optimizer : callable, optional
            Optimizer function to use. Default: ``torch.optim.Adam``.
        metrics : list, optional
            List of additional metrics to log. Default: ``['accuracy', 'precision', 'recall']``.
        num_classes : int, optional
            Number of classes for classification tasks. Default: ``10``.
        teacher_model : torch.nn.Module, optional
            Teacher model for knowledge distillation. Default: ``None``.
        """
        super().__init__()
        self.use_mlflow = use_mlflow
        self.log_every_n_steps = log_every_n_steps

        self.batch = [2**x for x in range(2, 8, 1)]
        self.search_space = search_space or {
            "lr": tune.loguniform(1e-5, 1e-2),  # Default Suche für Learning Rate
            "batch_size": tune.choice(self.batch),
        }
        self.loss_fn = loss_fn or get_loss(loss_name, **(loss_params or {}))
        self.optimizer = optimizer

        self.save_hyperparameters()

        self.metrics = {
            "accuracy": Accuracy(task="multiclass", num_classes=num_classes),
            "f1": F1Score(task="multiclass", num_classes=num_classes, average="macro"),
            "auroc": AUROC(task="multiclass", num_classes=num_classes, average="macro"),
            "precision": Precision(task="multiclass", num_classes=num_classes, average="macro"),
            "recall": Recall(task="multiclass", num_classes=num_classes, average="macro"),
        }
        self.active_metrics = {
            name: metric for name, metric in self.metrics.items() if name in metrics
        }

        self.teacher_model = teacher_model.eval() if teacher_model else None

    def training_step(self, *args, **kwargs) -> torch.Tensor:
        batch: tuple[torch.Tensor, torch.Tensor] = args[0]

        x, y = batch
        y_hat = self(x)

        if self.teacher_model:
            with torch.no_grad():
                teacher_logits = self.teacher_model(x)
            loss = self.loss_fn(teacher_logits, y_hat, y)
        else:
            loss = self.loss_fn(y_hat, y)

        # Logging für TensorBoard & optional MLflow
        self.log("train/loss", loss, prog_bar=True, on_step=True, on_epoch=True, logger=True)

        for name, metric in self.active_metrics.items():
            self.log(f"train/{name}", metric(y_hat, y).detach(), prog_bar=True, on_epoch=True)

        return loss

    def validation_step(self, *args, **kwargs) -> torch.Tensor:
        batch: tuple[torch.Tensor, torch.Tensor] = args[0]

        x, y = batch
        y_hat = self(x)
        val_loss = self.compute_loss(y_hat, y)

        # Collect embeddings
        if hasattr(self, "extract_features"):
            with torch.no_grad():
                features = self.extract_features(x)
                self._val_embeddings.append(features.detach().cpu())
                self._val_labels.append(y.detach().cpu())

        # Logging für TensorBoard & optional MLflow
        self.log("val/loss", val_loss, prog_bar=True, on_epoch=True, logger=True)

        for name, metric in self.active_metrics.items():
            self.log(f"val/{name}", metric(y_hat, y).detach(), prog_bar=True, on_epoch=True)

        return val_loss

    def configure_optimizers(self):
        """Configure and return the optimizer.

        Returns:
            torch.optim.Optimizer: Optimizer initialized with configured learning rate.
        """
        # Uses the optimized hyperparameters from Ray Tune
        lr = self.hparams.get("lr", 1e-3)  # Use default value if not set
        return self.optimizer(self.parameters(), lr=lr)

    def compute_loss(self, y_hat, y):
        """Berechnet den Loss für die gegebenen Vorhersagen und Labels. Standard: MSE-Loss."""
        return self.loss_fn(y_hat, y)

    def on_train_epoch_end(self) -> None:
        """Wird am Ende eines Trainings-Epochs aufgerufen.
        Setzt alle Metriken zurück.
        """
        for metric in self.active_metrics.values():
            metric.reset()

    def on_validation_epoch_end(self) -> None:
        """Wird am Ende einer Validierungs-Epoch aufgerufen.
        Setzt alle Metriken zurück.
        """
        for metric in self.active_metrics.values():
            metric.reset()

    def on_after_batch_transfer(self, batch, _):
        x, y = batch
        return x.to(self.device), y.to(self.device)

    def optimize_hyperparameters(self, datamodule, num_samples=10, max_epochs=10):
        """Startet die Hyperparameter-Suche mit Ray Tune."""
        logger.info("Starte Hyperparameter-Optimierung mit Ray Tune...")

        try:
            analysis = tune.run(
                lambda config: BaseModule.ray_tune_train(config, datamodule, max_epochs),
                config=self.search_space,
                num_samples=num_samples,
                resources_per_trial={"cpu": 1, "gpu": 1},
            )
            best_config = analysis.best_config
            logger.info(f"Beste Hyperparameter gefunden: {best_config}")
            return best_config

        except Exception as e:
            logger.exception(f"Fehler bei der Hyperparameter-Suche: {e}")
            raise  # Fehler weitergeben

    def model_summary(self, input_size: Sequence[int] = (1, 3, 224, 224)) -> ModelStatistics | None:
        """Zeigt eine Model-Übersicht, falls `torchinfo` installiert ist."""
        if HAS_TORCHINFO:
            return summary(model=self, input_size=input_size)
        logger.warning(
            "⚠️ `torchinfo` ist nicht installiert. `summary()` kann nicht ausgeführt werden."
        )
        return None

    def visualize_model(self, input_tensor: torch.Tensor) -> "Digraph | None":
        """Zeigt ein Computation Graph mit `torchviz`, falls verfügbar."""
        if HAS_TORCHVIZ:
            y_hat = self(input_tensor)
            return make_dot(y_hat, params=dict(self.named_parameters()))
        logger.debug("⚠️  `torchviz` ist nicht installiert. Graph-Visualisierung nicht verfügbar.")
        return None

    def tune_then_train(self, datamodule, max_epochs=10):
        """Tuned und trainiert direkt danach mit besten Parametern."""
        best_config = self.optimize_hyperparameters(
            datamodule, num_samples=10, max_epochs=max_epochs
        )
        model = self.__class__(**best_config)  # <- gleiche Klasse nochmal neu starten
        trainer = BaseTrainer(max_epochs=max_epochs)
        trainer.fit(model, datamodule)
        return model

    @staticmethod
    def ray_tune_train(
        config, datamodule, max_epochs=10, model_class=None, save_name="best_config"
    ):
        """Trains the model with Ray Tune based on hyperparameters."""
        assert isinstance(
            datamodule, pl.LightningDataModule
        ), "datamodule must be a LightningDataModule."

        model_class = model_class or BaseModule  # fallback

        model_params = {
            k: v for k, v in config.items() if k in inspect.signature(model_class).parameters
        }

        logger.info(f"Creating model {model_class.__name__} with parameters: {model_params}")
        model = model_class(**model_params)

        metrics = {"loss": "val/loss"}
        available_metrics = ["accuracy", "f1", "auroc", "precision", "recall"]

        selected_metrics = config.get("metrics", [])
        if isinstance(selected_metrics, str):
            selected_metrics = [selected_metrics]
        elif selected_metrics is None:
            selected_metrics = []

        for metric in selected_metrics:
            if metric in available_metrics:
                metrics[metric] = f"val/{metric}"

        logger.info(f"Training metrics used for Ray Tune: {metrics}")

        callbacks = [
            TuneReportCheckpointCallback(
                metrics=metrics, filename="checkpoint", on="validation_end"
            )
        ]

        trainer = BaseTrainer(
            max_epochs=max_epochs,
            auto_batch_size=True,
            callbacks=callbacks,
            logger=False,  # Kein TensorBoard bei Ray Tune
            enable_progress_bar=False,
        )

        logger.info("Starting training with Ray Tune...")
        try:
            trainer.fit(model, datamodule)
            logger.info("Training completed successfully.")
        except Exception as e:
            logger.exception(f"Error during training: {e}")
            raise  # Fehler weitergeben

        # ⬇️ Auto-Save the best config after training
        config_manager = ConfigManager()
        config_manager.save_yaml(config, name=save_name)
        logger.info(f"Best configuration saved under '{save_name}'.")

        return config  # <- falls du es zurückgeben möchtest
