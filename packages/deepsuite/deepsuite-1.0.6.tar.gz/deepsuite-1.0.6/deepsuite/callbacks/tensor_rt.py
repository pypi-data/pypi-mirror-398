"""TensorRT-Export-Callback für PyTorch Lightning.

Dieses Modul enthält einen Callback, der das beste Modell zu TensorRT
exportiert, nachdem es gespeichert wurde. Nur auf Linux und Windows verfügbar.

Example:
    .. code-block:: python

        from pytorch_lightning import Trainer
        from deepsuite.callbacks.tensor_rt import TensorRTExportCallback

        trainer = Trainer(callbacks=[TensorRTExportCallback()])
        trainer.fit(model)

Hinweis:
    TensorRT wird nur auf Linux und Windows unterstützt.
    Dieser Callback wirft einen ImportError auf macOS.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger
import torch

from deepsuite.callbacks.base import ExportBaseCallback
from deepsuite.callbacks.torchscript import TorchScriptExportCallback

if TYPE_CHECKING:
    import pytorch_lightning as pl

# TensorRT ist nur auf Linux und Windows verfügbar
if sys.platform in ("linux", "win32"):
    try:
        import torch_tensorrt  # noqa: F401

        TENSORRT_AVAILABLE = True
    except ImportError:
        TENSORRT_AVAILABLE = False
        logger.warning("torch_tensorrt nicht verfügbar. Installation: pip install torch-tensorrt")
else:
    TENSORRT_AVAILABLE = False
    logger.info(f"TensorRT wird auf {sys.platform} nicht unterstützt. Nur Linux/Windows.")


class TensorRTExportCallback(ExportBaseCallback):
    """Exportiert das beste Modell zu TensorRT (.trt) mittels TorchScript.

    Hinweis:
        Nur auf Linux und Windows verfügbar. Auf macOS wirft dieser Callback
        einen Fehler während der Initialisierung.
    """

    def __init__(
        self,
        output_dir: str = "models",
        precision: str = "fp16",
        workspace_size: int = 1 << 20,
        **kwargs: Any,
    ) -> None:
        """Initialisiert den TensorRT-Export-Callback.

        Args:
            output_dir: Verzeichnis für Exports.
            precision: TensorRT Precision-Modus ('fp16', 'fp32', 'int8').
            workspace_size: Workspace-Größe in Bytes für TensorRT.
            **kwargs: Zusätzliche Parameter für ModelCheckpoint.

        Raises:
            RuntimeError: Falls TensorRT auf dieser Plattform nicht verfügbar ist.
        """
        if not TENSORRT_AVAILABLE:
            raise RuntimeError(
                f"TensorRT ist auf {sys.platform} nicht verfügbar. "
                "Nur Linux und Windows werden unterstützt. "
                "Installation: pip install 'deepsuite[tensorrt]' (nur Linux/Windows)"
            )

        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.precision = precision
        self.workspace_size = workspace_size

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """Exportiert das beste Modell zu TensorRT nach Validierung.

        Exportiert zunächst zu TorchScript, konvertiert dann zu TensorRT
        mit Precision-Handling.

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

        example_input = self.get_example_input(trainer)
        if example_input is None:
            logger.warning("❌ Kein Beispiel-Input verfügbar. TensorRT-Export übersprungen.")
            return

        checkpoint_name = Path(best_checkpoint_path).stem
        ts_path = self.output_dir / f"{checkpoint_name}.pt"

        # Exportiere TorchScript-Modell
        if not ts_path.exists():
            logger.info(f"🔹 Exportiere TorchScript-Modell: {ts_path}")
            try:
                TorchScriptExportCallback._export_torchscript(
                    pl_module,
                    example_input,
                    ts_path,
                    optimize=True,
                )
            except Exception as e:
                logger.error(f"❌ TorchScript-Export fehlgeschlagen: {e}")
                return
        else:
            logger.info(f"✅ TorchScript-Modell existiert bereits: {ts_path}")

        # Lade und verifiziere TorchScript-Modell
        try:
            torchscript_model = torch.jit.load(str(ts_path))
            logger.info(f"✅ TorchScript-Modell geladen: {ts_path}")
        except Exception as e:
            logger.error(f"❌ TorchScript-Modell konnte nicht geladen werden: {e}")
            return

        # Konvertiere zu TensorRT
        trt_path = self.output_dir / f"{checkpoint_name}.trt"
        logger.info(f"🔹 Konvertiere TorchScript zu TensorRT: {trt_path}")

        try:
            self._convert_to_tensorrt(torchscript_model, trt_path, example_input)
        except Exception as e:
            logger.error(f"❌ TensorRT-Konvertierung fehlgeschlagen: {e}")

    def _convert_to_tensorrt(
        self, torchscript_model: Any, trt_path: Path, example_input: Any
    ) -> None:
        """Konvertiert ein TorchScript-Modell zu TensorRT.

        Args:
            torchscript_model: Geladenes TorchScript-Modell.
            trt_path: Ziel-Pfad für TensorRT-Modell.
            example_input: Beispiel-Input für Konvertierung.
        """
        try:
            import torch_tensorrt

            precision_map = {
                "fp32": torch.float32,
                "fp16": torch.float16,
                "int8": torch.int8,
            }
            precision_type = precision_map.get(self.precision, torch.float16)

            trt_model = torch_tensorrt.ts.compile(
                torchscript_model,
                inputs=[torch_tensorrt.Input(example_input.shape, dtype=precision_type)],
                workspace_size=self.workspace_size,
            )

            torch.jit.save(trt_model, str(trt_path))
            logger.info(f"✅ TensorRT-Modell gespeichert: {trt_path}")

        except Exception as e:
            logger.error(f"❌ TensorRT-Konvertierung fehlgeschlagen: {e}")
            raise
