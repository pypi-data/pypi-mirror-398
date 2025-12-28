"""ONNX-Export-Callback für PyTorch Lightning.

Dieses Modul enthält einen Callback, der das beste Modell nach ONNX exportiert,
sobald es gespeichert wurde.

Beispiel:
    ```python
    from pytorch_lightning import Trainer
    from deepsuite.callbacks.onnx import ONNXExportCallback

    trainer = Trainer(callbacks=[ONNXExportCallback(opversion=12)])
    trainer.fit(model)
    ```
"""

from pathlib import Path
from typing import Any

from loguru import logger
import pytorch_lightning as pl
import torch

from deepsuite.callbacks.base import ExportBaseCallback


class ONNXExportCallback(ExportBaseCallback):
    """Exportiert das Modell nach ONNX (.onnx)."""

    def __init__(
        self,
        output_dir: str = "models",
        simplify: bool = False,
        opversion: int = 12,
        **kwargs: Any,
    ) -> None:
        """Initialisiert den ONNX-Export-Callback.

        Args:
            output_dir: Verzeichnis für exportierte Modelle.
            simplify: Falls True, wird das ONNX-Modell vereinfacht (erfordert onnx-simplifier).
            opversion: ONNX OpSet-Version.
            **kwargs: Zusätzliche Parameter für ModelCheckpoint.
        """
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.simplify = simplify
        self.opversion = opversion

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """Exportiert das beste validierte Modell nach ONNX.

        Lädt den besten Checkpoint, setzt den Modus auf Eval, holt einen
        Beispielinput und führt den Export durch.
        """
        super().on_validation_end(trainer, pl_module)

        best_checkpoint_path = self.best_model_path
        if not best_checkpoint_path or not Path(best_checkpoint_path).exists():
            logger.warning("❌ Kein gültiger Checkpoint gefunden. ONNX-Export übersprungen.")
            return

        logger.info(f"🔹 Lade bestes Modell: {best_checkpoint_path}")
        state = torch.load(best_checkpoint_path, map_location="cpu")
        pl_module.load_state_dict(state["state_dict"])  # type: ignore[index]
        pl_module.eval()

        example_input: Any | None = self.get_example_input(trainer)
        if example_input is None:
            logger.warning("❌ Kein Beispiel-Input verfügbar. ONNX-Export übersprungen.")
            return

        checkpoint_name = Path(best_checkpoint_path).stem
        onnx_path = self.output_dir / f"{checkpoint_name}.onnx"
        logger.info(f"🔹 Exportiere nach ONNX: {onnx_path}")

        try:
            self._export_onnx(pl_module, example_input, onnx_path, self.opversion)
        except Exception as e:
            logger.error(f"❌ Fehler beim ONNX-Export: {e}")
            return

        if self.simplify:
            self._maybe_simplify(onnx_path)

    @staticmethod
    def _export_onnx(
        module: torch.nn.Module, example_input: Any, onnx_path: Path, opversion: int
    ) -> None:
        """Führt den eigentlichen `torch.onnx.export`-Aufruf aus."""
        dynamic_axes = None
        if isinstance(example_input, torch.Tensor) and example_input.dim() >= 1:
            dynamic_axes = {"input": {0: "batch"}}

        torch.onnx.export(
            module,
            example_input,
            str(onnx_path),
            opset_version=opversion,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
        )
        logger.info(f"✅ ONNX-Modell gespeichert: {onnx_path}")

        try:
            try:
                import onnx
                from onnxsim import simplify
            except ImportError:
                logger.warning("⚠️ onnx oder onnxsim nicht installiert. Vereinfachung übersprungen.")
                return

            logger.info("🔹 Vereinfache ONNX-Modell mit onnx-simplifier…")
            model = onnx.load(str(onnx_path))
            model_simp, check = simplify(model)
            if check:
                onnx.save(model_simp, str(onnx_path))
                logger.info("✅ ONNX-Modell vereinfacht und gespeichert.")
            else:
                logger.warning("⚠️ onnx-simplifier konnte das Modell nicht verifizieren.")
        except Exception as e:
            logger.warning(f"⚠️ Konnte ONNX nicht vereinfachen: {e}")
