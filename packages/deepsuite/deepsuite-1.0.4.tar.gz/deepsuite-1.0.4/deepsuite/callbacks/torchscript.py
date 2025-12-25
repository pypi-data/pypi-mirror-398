"""TorchScript-Export-Callback für PyTorch Lightning.

Dieses Modul enthält einen Callback, der das beste Modell nach TorchScript
exportiert, sobald es gespeichert wurde.

Beispiel:
    ```python
    from pytorch_lightning import Trainer
    from deepsuite.callbacks.torchscript import TorchScriptExportCallback

    trainer = Trainer(callbacks=[TorchScriptExportCallback()])
    trainer.fit(model)
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
import pytorch_lightning as pl
import torch

from deepsuite.callbacks.base import ExportBaseCallback


class TorchScriptExportCallback(ExportBaseCallback):
    """Exportiert das Modell nach TorchScript (.pt)."""

    def __init__(
        self, output_dir: str = "models", optimize: bool = True, **kwargs: Any
    ) -> None:
        """Initialisiert den TorchScript-Export-Callback.

        Args:
            output_dir: Verzeichnis für exportierte Modelle.
            optimize: Falls True, wird TorchScript mit optimize_for_inference
                optimiert.
            **kwargs: Zusätzliche Parameter für ModelCheckpoint.
        """
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.optimize = optimize

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """Exportiert das beste validierte Modell nach TorchScript.

        Lädt den besten Checkpoint, setzt den Modus auf Eval, holt einen
        Beispielinput und führt den TorchScript-Export mit optionaler
        Optimierung durch.

        Args:
            trainer: PyTorch-Lightning-Trainer.
            pl_module: PyTorch-Lightning-Modul.
        """
        super().on_validation_end(trainer, pl_module)

        best_checkpoint_path = self.best_model_path
        if not best_checkpoint_path or not Path(best_checkpoint_path).exists():
            logger.warning("❌ Kein gültiger Checkpoint gefunden. Export übersprungen.")
            return

        logger.info(f"🔹 Lade bestes Modell: {best_checkpoint_path}")

        state = torch.load(best_checkpoint_path, map_location="cpu")
        pl_module.load_state_dict(state["state_dict"])  # type: ignore[index]
        pl_module.eval()

        # Beispiel-Input automatisch holen
        example_input = self.get_example_input(trainer)
        if example_input is None:
            logger.warning("❌ Kein Beispiel-Input verfügbar. TorchScript-Export übersprungen.")
            return

        # TorchScript Export
        checkpoint_name = Path(best_checkpoint_path).stem
        ts_path = self.output_dir / f"{checkpoint_name}.pt"
        logger.info(f"🔹 Exportiere nach TorchScript: {ts_path}")

        try:
            self._export_torchscript(pl_module, example_input, ts_path, self.optimize)
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ Fehler beim TorchScript-Export: {e}")

    @staticmethod
    def _export_torchscript(
        module: torch.nn.Module,
        example_input: Any,
        model_path: Path,
        optimize: bool = True,
    ) -> None:
        """Erstellt ein TorchScript-Modell aus einem PyTorch-Modul.

        Args:
            module: PyTorch-Modul zum Exportieren.
            example_input: Beispiel-Input für Tracing.
            model_path: Ziel-Pfad für das TorchScript-Modell.
            optimize: Falls True, wird optimize_for_inference angewendet.
        """
        try:
            logger.info(f"🔹 Konvertiere Modell nach TorchScript: {model_path}")
            traced_model = torch.jit.trace(module, example_inputs=example_input)

            if optimize:
                logger.info("🔹 Wende `optimize_for_inference()` an...")
                traced_model = torch.jit.optimize_for_inference(traced_model)

            traced_model.save(str(model_path))
            logger.info(f"✅ TorchScript-Modell gespeichert: {model_path}")

        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ Fehler beim TorchScript-Export: {e}")
            raise
