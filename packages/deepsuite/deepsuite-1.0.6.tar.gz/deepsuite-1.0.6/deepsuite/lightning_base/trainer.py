"""Trainer module and registry-coupled helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, RichProgressBar
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.loggers import MLFlowLogger, TensorBoardLogger
from pytorch_lightning.tuner import Tuner
from pytorch_lightning.utilities.model_summary import ModelSummary

from deepsuite.callbacks.kendryte import KendryteExportCallback
from deepsuite.callbacks.onnx import ONNXExportCallback
from deepsuite.callbacks.tensor_rt import TensorRTExportCallback
from deepsuite.callbacks.tflite import TFLiteExportCallback
from deepsuite.callbacks.torchscript import TorchScriptExportCallback
from deepsuite.registry import HeadRegistry

if TYPE_CHECKING:
    from pytorch_lightning.loggers.logger import Logger


class BaseTrainer(pl.Trainer):
    """Convenience trainer with sensible defaults and optional exports.

    This class extends PyTorch Lightning's ``Trainer`` by adding:
    - Automatic batch size scaling
    - Optional MLflow experiment logging
    - Optional export callbacks (ONNX, TensorRT, TorchScript, etc.)
    - Rich progress bar for training

    Args:
        log_dir: Directory for log files.
        auto_batch_size: Enable automatic batch size scaling.
        mlflow_experiment: Optional MLflow experiment name.
        model_output_dir: Directory for exported models.
        export_formats: Optional list of export formats (e.g., ["onnx", "tensor_rt"]).
        early_stopping: Optional custom ``EarlyStopping`` callback.
        model_checkpoint: Optional custom ``ModelCheckpoint`` callback.
        **kwargs: Additional ``Trainer`` keyword arguments.

    Attributes:
        auto_batch_size: Whether automatic batch size scaling is enabled.

    Example:
        .. code-block:: python

            trainer = BaseTrainer(log_dir="logs", mlflow_experiment="my_experiment")
            trainer.fit(model, datamodule=datamodule)
    """

    def __init__(
        self,
        log_dir: str = "logs",
        auto_batch_size: bool = True,
        mlflow_experiment: str | None = None,
        model_output_dir: str = "models",
        export_formats: list[str] | None = None,
        early_stopping: EarlyStopping | None = None,
        model_checkpoint: ModelCheckpoint | None = None,
        **kwargs: Any,
    ) -> None:
        # Callbacks initialisieren
        callbacks = kwargs.pop("callbacks", [])
        callbacks.append(RichProgressBar())

        activated_callbacks = []

        if export_formats and "tensor_rt" in export_formats:
            callbacks.append(TensorRTExportCallback(output_dir=model_output_dir))
            activated_callbacks.append("TensorRT")

        if export_formats and "torchscript" in export_formats:
            callbacks.append(TorchScriptExportCallback(output_dir=model_output_dir))
            activated_callbacks.append("TorchScript")

        if export_formats and "onnx" in export_formats:
            callbacks.append(ONNXExportCallback(output_dir=model_output_dir))
            activated_callbacks.append("ONNX")

        if export_formats and "kendryte" in export_formats:
            callbacks.append(KendryteExportCallback(output_dir=model_output_dir))
            activated_callbacks.append("Kendryte")

        if export_formats and "tflite" in export_formats:
            callbacks.append(TFLiteExportCallback(output_dir=model_output_dir))
            activated_callbacks.append("TFLite (stub)")

        if not early_stopping:
            early_stopping = EarlyStopping(monitor="val_acc", patience=5, mode="max")
            logger.info("i️   EarlyStopping aktiviert: Monitor='val_acc', Patience=5")
        else:
            logger.info("i️   Custom EarlyStopping verwendet.")

        if not model_checkpoint:
            model_checkpoint = ModelCheckpoint(
                monitor="val_acc",
                mode="max",
                save_top_k=1,
                dirpath="models",
                filename="best-checkpoint_{epoch:03d}-{val_acc:.4f}",
            )
            logger.info("i️   ModelCheckpoint aktiviert: Monitor='val_acc', Top-1, Pfad='models'")
        else:
            logger.info("i️   Custom ModelCheckpoint verwendet.")

        # Logge aktivierte Callbacks
        if activated_callbacks:
            logger.info(f"🔹 Aktivierte Export-Callbacks: {', '.join(activated_callbacks)}")
        else:
            logger.info("⚠️ Keine Export-Callbacks aktiviert.")

        # Standard-Logger: TensorBoard
        loggers: list[Logger] = [TensorBoardLogger(save_dir=log_dir, name="tensorboard")]

        self.mlflow = False

        # Optional: MLflow
        if mlflow_experiment:
            mlflow_logger = MLFlowLogger(experiment_name=mlflow_experiment)
            loggers.append(mlflow_logger)
            logger.debug(f"use mlflow experiment: {mlflow_experiment}")
            self.mlflow = True

        super().__init__(
            logger=loggers, callbacks=callbacks, accelerator="gpu", devices="auto", **kwargs
        )

        # Falls gewünscht, automatische Batch-Größe optimieren
        self.auto_batch_size = auto_batch_size

    def tune_batch_size(
        self, model: pl.LightningModule, datamodule: pl.LightningDataModule | None = None
    ) -> int | None:
        """Optimiert die Batch-Größe des Modells.

        Args:
            model: PyTorch-Modell.
            datamodule: PyTorch Lightning DataModule.

        Returns:
            int: Optimierte Batch-Größe oder None.

        Example:
            trainer = BaseTrainer(log_dir="logs", use_mlflow=True)
            new_batch_size = trainer.tune_batch_size(model, datamodule=datamodule)
        """
        if self.auto_batch_size:
            tuner = Tuner(self)
            new_batch_size = tuner.scale_batch_size(model, datamodule=datamodule, mode="power")
            logger.info(f"🔹 Optimierte Batch-Größe: {new_batch_size}")
            return new_batch_size
        return None

    def fit(self, model: pl.LightningModule, *args: Any, **kwargs: Any) -> None:
        """Trainiert das Modell.

        Args:
            model: PyTorch-Lightning-Modul.
            *args: Weitere Argumente für den Trainer.
            **kwargs: Weitere Argumente für den Trainer.

        Beispiel:
            trainer = BaseTrainer(log_dir="logs", use_mlflow=True)
            trainer.fit(model, datamodule=datamodule)
        """
        # Model Summary beim Start ausgeben
        model_summary = ModelSummary(model, max_depth=3)
        logger.info("\n" + "=" * 50)
        logger.info("MODULE SUMMARY")
        logger.info("=" * 50)
        logger.info(str(model_summary))
        logger.info("=" * 50 + "\n")

        super().fit(model, *args, **kwargs)
        logger.info("🔹 Training abgeschlossen.\n" + "=" * 50)


def build_trainer_from_config(trainer_cfg: dict | None = None) -> BaseTrainer:
    """Build a BaseTrainer from a config dict.

    Args:
        trainer_cfg: Keyword-args for BaseTrainer.

    Returns:
        BaseTrainer: Initialized trainer.
    """
    trainer_cfg = trainer_cfg or {}
    return BaseTrainer(**trainer_cfg)


def train_heads_with_registry(
    head_cfgs: list[dict],
    module_builder,
    datamodule: pl.LightningDataModule,
    trainer_cfg: dict | None = None,
    share_backbone: bool | None = None,
):
    """Instantiate heads via HeadRegistry and run training with BaseTrainer.

    Args:
        head_cfgs: List of head config dicts: {"name": str, "args": dict}
        module_builder: Callable accepting (heads, share_backbone) -> LightningModule
        datamodule: LightningDataModule to provide data loaders
        trainer_cfg: Dict for BaseTrainer construction
        share_backbone: Optional flag passed to module_builder

    Returns:
        BaseTrainer: The trainer after running fit.
    """
    heads = []
    for cfg in head_cfgs:
        name = cfg.get("name")
        args = cfg.get("args", {})
        head_cls = HeadRegistry.get(name)
        heads.append(head_cls(**args))

    module = module_builder(heads=heads, share_backbone=bool(share_backbone))
    trainer = build_trainer_from_config(trainer_cfg)
    trainer.fit(module, datamodule=datamodule)
    return trainer
