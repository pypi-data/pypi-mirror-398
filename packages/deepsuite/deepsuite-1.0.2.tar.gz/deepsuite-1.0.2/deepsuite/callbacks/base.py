"""Basisklasse für Modell-Export-Callbacks.

Stellt Hilfsfunktionen bereit, um automatisch Beispielbatches zu laden und
auf das korrekte Gerät zu verschieben, sodass Export-Callbacks (z. B. ONNX,
TorchScript, TensorRT) konsistent arbeiten können.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
import pytorch_lightning as pl
import torch

from deepsuite.utils.device import get_best_device


class ExportBaseCallback(pl.callbacks.ModelCheckpoint):
    """Basisklasse für Export-Callbacks mit Batch-Autoloading."""

    output_dir: Path
    example_input: Any | None

    def __init__(self, output_dir: str = "models", **kwargs: Any) -> None:
        """Initialisiert den Export-Callback.

        Args:
            output_dir: Zielverzeichnis für Exports.
            **kwargs: Zusätzliche Argumente, werden an ModelCheckpoint weitergegeben.
        """
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.example_input = None  # Wird später automatisch gesetzt

    def get_example_input(self, trainer: pl.Trainer) -> Any | None:
        """Lädt einen Beispielbatch und speichert ihn in `example_input`.

        Args:
            trainer: PyTorch-Lightning-Trainer.

        Returns:
            Optional[Any]: Beispielinputbatch (ggf. Tensor oder Strukturen) oder None.

        Beispiel:
            ```python
            from pytorch_lightning import Trainer
            from deepsuite.callbacks.base import ExportBaseCallback

            trainer = Trainer(callbacks=[ExportBaseCallback()])
            trainer.fit(model)
            ```
        """
        if self.example_input is None:  # Nur einmal laden
            try:
                datamodule = trainer.datamodule
                if datamodule is None:
                    logger.error("❌ No DataModule found.")
                    return None

                dataloader = datamodule.train_dataloader()
                if dataloader is None:
                    logger.error("❌ No train_dataloader() found.")
                    return None

                batch = next(iter(dataloader))  # Einen Batch entnehmen

                if isinstance(batch, (tuple, list)):
                    self.example_input = batch[0]
                else:
                    self.example_input = batch

                # Auf dasselbe Gerät wie das Modell verschieben
                if trainer.model is not None:
                    device = trainer.model.device
                    self.example_input = self._move_batch_to_device(self.example_input, device)

                logger.info(
                    "✅ Example batch automatically loaded and moved to the correct device."
                )

            except Exception as e:
                logger.error(f"❌ Could not load example batch: {e}")
                return None

        return self.example_input

    def _move_batch_to_device(self, batch: Any, device: str | torch.device | None = None) -> Any:
        """Verschiebt einen Batch rekursiv auf das angegebene Gerät.

        Args:
            batch: Tensor oder (verschachtelte) Liste/Tuple/Dict aus Tensors.
            device: Zielgerät als str ('cuda', 'cpu') oder torch.device, oder None.

        Returns:
            Any: Der auf das Zielgerät verschobene Batch.
        """
        if device is None:
            device_str: str | torch.device = get_best_device()
        else:
            device_str = device

        if isinstance(batch, torch.Tensor):
            return batch.to(device_str)
        if isinstance(batch, (tuple, list)):
            return type(batch)(self._move_batch_to_device(b, device_str) for b in batch)
        if isinstance(batch, dict):
            return {k: self._move_batch_to_device(v, device_str) for k, v in batch.items()}
        return batch
