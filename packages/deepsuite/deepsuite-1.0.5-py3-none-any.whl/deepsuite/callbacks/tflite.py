"""TFLite-Export-Callback (Stub) für PyTorch Lightning.

Hinweis: Eine direkte Konvertierung von PyTorch nach TFLite ist nicht nativ verfügbar.
Gängige Pipelines nutzen ONNX → TensorFlow → TFLite (z. B. mit `onnx2tf`).
Dieser Callback dient als Platzhalter und dokumentiert die erforderlichen Schritte.

Beispiel:
```python
from pytorch_lightning import Trainer
from deepsuite.callbacks.tflite import TFLiteExportCallback

trainer = Trainer(callbacks=[TFLiteExportCallback()])
trainer.fit(model)
```
"""

from pathlib import Path
from typing import Any

from loguru import logger
import pytorch_lightning as pl

from deepsuite.callbacks.base import ExportBaseCallback
from deepsuite.callbacks.onnx import ONNXExportCallback


class TFLiteExportCallback(ExportBaseCallback):
    """Stub-Callback für TFLite-Export mit dokumentierten Schritten."""

    def __init__(self, output_dir: str = "models", opversion: int = 12, **kwargs: Any) -> None:
        """Initialisiert den TFLite-Stub-Callback."""
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.opversion = opversion

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """Exportiert ONNX und beschreibt die Konvertierung nach TFLite."""
        super().on_validation_end(trainer, pl_module)

        best_checkpoint_path = self.best_model_path
        if not best_checkpoint_path or not Path(best_checkpoint_path).exists():
            logger.warning("❌ Kein gültiger Checkpoint gefunden. TFLite-Export übersprungen.")
            return

        logger.info("🔹 TFLite-Export (Stub): Erzeuge zunächst ONNX als Zwischenschritt…")
        example_input = self.get_example_input(trainer)
        if example_input is None:
            logger.warning("❌ Kein Beispiel-Input verfügbar. Export übersprungen.")
            return

        # ONNX-Export
        checkpoint_name = Path(best_checkpoint_path).stem
        onnx_path = self.output_dir / f"{checkpoint_name}.onnx"
        try:
            import torch

            state = torch.load(best_checkpoint_path, map_location="cpu")
            pl_module.load_state_dict(state["state_dict"])  # type: ignore[index]
            pl_module.eval()

            ONNXExportCallback._export_onnx(pl_module, example_input, onnx_path, self.opversion)
        except Exception as e:
            logger.error(f"❌ ONNX-Export fehlgeschlagen: {e}")
            return

        # Hinweise zur Konvertierung
        logger.info("i️  Konvertierungsschritte nach TFLite:")
        logger.info("   1) ONNX → TensorFlow (z. B. mit onnx2tf)")
        logger.info("   2) TensorFlow → TFLite (tflite_convert oder tf.lite.TFLiteConverter)")
        logger.info("   3) Optional: Quantisierung (dynamic/int8)")
        logger.info(f"   Bereitgestelltes ONNX: {onnx_path}")
