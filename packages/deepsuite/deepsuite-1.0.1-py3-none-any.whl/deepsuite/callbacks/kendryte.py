from pathlib import Path
from typing import Any

from loguru import logger
import pytorch_lightning as pl
import torch

from deepsuite.callbacks.base import ExportBaseCallback
from deepsuite.callbacks.onnx import ONNXExportCallback


class KendryteExportCallback(ExportBaseCallback):
    """Exportiert ONNX und bereitet Kendryte-Konvertierung vor.

    Dies umfasst ONNX-Export, optionale Quantisierung und Platzhalter
    für KMODEL-Konvertierung.
    """

    def __init__(
        self,
        output_dir: str = "models",
        quantize: bool = True,
        quant_type: str = "QInt8",
        opversion: int = 12,
        **kwargs: Any,
    ) -> None:
        """Initialisiert den Kendryte-Export-Callback.

        Args:
            output_dir: Verzeichnis für exportierte Modelle.
            quantize: Ob dynamische Quantisierung des ONNX-Modells
                durchgeführt wird.
            quant_type: Quantisierungstyp ("QInt8" oder "QUInt8").
            opversion: ONNX OpSet-Version.
            **kwargs: Zusätzliche Parameter für ModelCheckpoint.
        """
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quantize = quantize
        self.quant_type = quant_type
        self.opversion = opversion

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """Exportiert das Modell und optional quantisiert es für Kendryte.

        Dies lädt den besten Checkpoint, exportiert nach ONNX und führt
        optional Quantisierung durch.
        """
        super().on_validation_end(trainer, pl_module)

        best_checkpoint_path = self.best_model_path
        if not best_checkpoint_path or not Path(best_checkpoint_path).exists():
            logger.warning("❌ Kein gültiger Checkpoint gefunden. Kendryte-Export übersprungen.")
            return

        logger.info(f"🔹 Lade bestes Modell: {best_checkpoint_path}")
        state = torch.load(best_checkpoint_path, map_location="cpu")
        pl_module.load_state_dict(state["state_dict"])  # type: ignore[index]
        pl_module.eval()

        example_input = self.get_example_input(trainer)
        if example_input is None:
            logger.warning("❌ Kein Beispiel-Input verfügbar. Kendryte-Export übersprungen.")
            return

        checkpoint_name = Path(best_checkpoint_path).stem
        onnx_path = self.output_dir / f"{checkpoint_name}.onnx"

        # Schritt 1: ONNX-Export
        try:
            ONNXExportCallback._export_onnx(  # noqa: SLF001
                pl_module, example_input, onnx_path, self.opversion
            )
        except Exception as e:
            logger.error(f"❌ ONNX-Export fehlgeschlagen: {e}")
            return

        # Schritt 2: (optional) Quantisierung
        if self.quantize:
            self._maybe_quantize(onnx_path, checkpoint_name)

        # Schritt 3: Platzhalter für KMODEL-Konvertierung
        self._kendryte_placeholder(onnx_path)

    def _maybe_quantize(self, onnx_path: Path, checkpoint_name: str) -> None:
        """Versucht die dynamische Quantisierung des ONNX-Modells.

        Nutzt onnxruntime falls verfügbar, sonst wird eine Warnung geloggt.
        """
        try:
            from onnxruntime.quantization import QuantType, quantize_dynamic  # noqa: PLC0415
        except ImportError:
            logger.warning("⚠️ onnxruntime nicht installiert. Quantisierung übersprungen.")
            return

        try:
            quant_map = {
                "QInt8": QuantType.QInt8,
                "QUInt8": QuantType.QUInt8,
            }
            qtype = quant_map.get(self.quant_type, QuantType.QInt8)

            quantized_onnx_path = self.output_dir / f"{checkpoint_name}_quant.onnx"
            logger.info(f"🔹 Quantisiere ONNX-Modell: {quantized_onnx_path}")
            quantize_dynamic(
                model_input=onnx_path,
                model_output=quantized_onnx_path,
                weight_type=qtype,
            )
            logger.info(f"✅ Quantisiertes ONNX-Modell gespeichert: {quantized_onnx_path}")
        except Exception as e:
            logger.warning(f"⚠️ Quantisierung übersprungen/fehlgeschlagen: {e}")

    def _kendryte_placeholder(self, onnx_path: Path) -> None:
        """Platzhalter-Hinweis zur externen KMODEL-Konvertierung."""
        logger.info(
            "i️  Kendryte-KMODEL-Konvertierung erfordert externe Tools/SDKs. "
            "Bitte konvertieren Sie das ONNX-Modell mit den "
            "Kendryte-Werkzeugen (K210/K230)."
        )
        logger.info(f"   Bereitgestelltes ONNX: {onnx_path}")
