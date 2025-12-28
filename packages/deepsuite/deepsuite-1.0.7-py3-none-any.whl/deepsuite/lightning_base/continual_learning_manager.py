"""Continual Learning Manager module."""

from copy import deepcopy
from pathlib import Path

from loguru import logger
import torch

from deepsuite.config.config_manager import ConfigManager
from deepsuite.lightning_base.trainer import BaseTrainer


class ContinualLearningManager:
    def __init__(self, save_dir="configs", model_save_dir="teachers") -> None:
        self.config_manager = ConfigManager(save_dir)
        self.model_save_dir = Path(model_save_dir)
        self.model_save_dir.mkdir(parents=True, exist_ok=True)

    def save_teacher_model(self, model, stage_idx, num_classes, example_input=None):
        """Speichert das Teacher-Modell als TorchScript."""
        save_path = self.model_save_dir / f"teacher_stage_{stage_idx + 1}_{num_classes}_classes.pt"
        model.eval()
        example_input = (
            example_input if example_input else torch.randn(1, 3, 224, 224, device=model.device)
        )
        traced_model = torch.jit.trace(model, example_input)
        traced_model.save(str(save_path))
        logger.info(f"🔹 Teacher-Modell gespeichert: {save_path}")
        return save_path

    def run(
        self,
        base_model_class,
        datamodule_fn,
        num_classes_stages,
        search_space_template,
        num_samples=10,
        max_epochs=10,
        trainer_kwargs: dict | None = None,
    ):
        """Führt Continual Learning mit automatischem Tuning & anschließendem Training durch.

        if trainer_kwargs is None:
            trainer_kwargs = {}

        Args:
            base_model_class: z.B. BaseModule oder dein Detector-Modell
            datamodule_fn: Funktion, die ein Datamodule für eine bestimmte Klassenzahl zurückgibt
            num_classes_stages: z.B. [10, 15, 20]
            search_space_template: dict mit Tune Search Space
            num_samples: Ray Tune Samples
            max_epochs: Trainingsepochen pro Stage
            trainer_kwargs: Extra-Parameter für BaseTrainer
        """
        if trainer_kwargs is None:
            trainer_kwargs = {}

        teacher_model = None

        for idx, num_classes in enumerate(num_classes_stages):
            logger.info(f"🚀 Starte Continual Stage {idx + 1} mit {num_classes} Klassen")

            search_space = deepcopy(search_space_template)
            search_space["num_classes"] = num_classes

            datamodule = datamodule_fn(num_classes)

            # Tune + Train direkt über BaseModule
            model = base_model_class(teacher_model=teacher_model, search_space=search_space)
            best_config = model.optimize_hyperparameters(
                datamodule=datamodule, num_samples=num_samples, max_epochs=max_epochs
            )

            # Final trainieren mit besten Parametern
            final_model = base_model_class(**best_config, teacher_model=teacher_model)
            trainer = BaseTrainer(max_epochs=max_epochs, **trainer_kwargs)
            trainer.fit(final_model, datamodule)

            self.config_manager.save_yaml(best_config, f"stage_{idx + 1}_{num_classes}_classes")
            self.save_teacher_model(final_model, idx, num_classes)

            teacher_model = deepcopy(final_model).eval()

        logger.success("🏁 Continual Learning + Tune abgeschlossen!")
        return teacher_model
