"""Audio data loader module for audio signal processing.

This module provides a PyTorch Lightning data module for audio datasets with
support for various audio augmentation strategies using Audiomentations.

Example:
    Basic usage::

        from deepsuite.lightning_base.dataset.audio_loader import AudioLoader
        from pytorch_lightning import Trainer

        # Create data module
        datamodule = AudioLoader(batch_size=32, num_workers=4, randaugment=False)

        # Setup datasets
        datamodule.setup()

        # Use with trainer
        trainer = Trainer(max_epochs=10)
        trainer.fit(model, datamodule)

    With aggressive augmentation::

        datamodule = AudioLoader(batch_size=64, num_workers=8, randaugment=True)
"""

from typing import Any

try:
    import audiomentations as am

    HAS_AUDIOMENTATIONS = True
except ImportError:
    HAS_AUDIOMENTATIONS = False
    am = None  # type: ignore

from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader


class AudioLoader(BaseDataLoader):
    """PyTorch Lightning data module for audio datasets.

    Provides automated augmentation pipelines using Audiomentations with
    support for both standard and aggressive augmentation strategies for
    audio signals.

    Note:
        All audio transforms expect waveform data (numpy arrays or torch tensors)
        at the configured sample rate. Normalization is applied to all pipelines.
    """

    def __init__(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        randaugment: bool = False,
    ) -> None:
        """Initialize the audio data loader.

        Args:
            batch_size: Number of audio samples per batch. Defaults to 32.
            num_workers: Number of worker processes for data loading.
                Defaults to 4.
            randaugment: If True, apply aggressive augmentation including
                noise injection, time stretching, pitch shifting, distortion,
                and gain adjustments. Defaults to False.

        Example:
            >>> loader = AudioLoader(batch_size=64, num_workers=8, randaugment=True)
        """
        super().__init__(
            batch_size=batch_size,
            num_workers=num_workers,
            randaugment=randaugment,
        )

    def _get_train_transforms(self) -> Any:
        """Return training transforms with optional aggressive augmentation.

        If randaugment=True, applies a comprehensive augmentation pipeline:
        - Gaussian noise injection (1-15mV amplitude)
        - Time stretching (0.8x to 1.25x speed)
        - Pitch shifting (±4 semitones)
        - Clipping distortion (0-20% percentile threshold)
        - Gain adjustment (±12dB)
        - Random shifts (±50% of signal length)
        - Normalization

        If randaugment=False, applies conservative augmentation:
        - Gaussian noise injection (1-15mV amplitude)
        - Normalization

        Returns:
            audiomentations.Compose: Augmentation pipeline for training audio.

        Example:
            >>> loader = AudioLoader(randaugment=True)
            >>> transforms = loader._get_train_transforms()
            >>> augmented = transforms(samples=audio_waveform, sample_rate=16000)
        """
        if not HAS_AUDIOMENTATIONS:
            # Return identity transform if audiomentations not available
            return lambda samples, sample_rate: samples

        if self.randaugment:
            return am.Compose(
                [
                    am.AddGaussianNoise(
                        min_amplitude=0.001,
                        max_amplitude=0.015,
                        p=0.5,
                    ),
                    am.TimeStretch(min_rate=0.8, max_rate=1.25, p=0.5),
                    am.PitchShift(min_semitones=-4, max_semitones=4, p=0.5),
                    am.ClippingDistortion(
                        min_percentile_threshold=0,
                        max_percentile_threshold=20,
                        p=0.5,
                    ),
                    am.Gain(min_gain_in_db=-12, max_gain_in_db=12, p=0.5),
                    am.Shift(min_fraction=-0.5, max_fraction=0.5, p=0.5),
                    am.Normalize(p=1.0),
                ]
            )

        return am.Compose(
            [
                am.AddGaussianNoise(
                    min_amplitude=0.001,
                    max_amplitude=0.015,
                    p=0.5,
                ),
                am.Normalize(p=1.0),
            ]
        )

    def _get_val_transforms(self) -> Any:
        """Return validation transforms without augmentation.

        Applies only normalization to validation audio without any
        augmentation or distortion.

        Returns:
            audiomentations.Compose: Preprocessing pipeline for validation audio.

        Example:
            >>> loader = AudioLoader()
            >>> transforms = loader._get_val_transforms()
            >>> preprocessed = transforms(samples=audio_waveform, sample_rate=16000)
        """
        if not HAS_AUDIOMENTATIONS:
            # Return identity transform if audiomentations not available
            return lambda samples, sample_rate: samples

        return am.Compose(
            [
                am.Normalize(p=1.0),
            ]
        )

    def setup(self, stage: str | None = None) -> None:
        """Initialize training and validation datasets.

        This method should be overridden in subclasses to load and prepare
        the actual audio datasets. The transforms from _get_train_transforms()
        and _get_val_transforms() are available via self.train_transforms
        and self.val_transforms.

        Args:
            stage: Either 'fit', 'validate', 'test', or 'predict'. Can be used
                to conditionally create datasets. Defaults to None.

        Example:
            >>> class MyAudioLoader(AudioLoader):
            ...     def setup(self, stage=None):
            ...         self.train_dataset = MyAudioDataset(
            ...             root="./data", split="train", transform=self.train_transforms
            ...         )
            ...         self.val_dataset = MyAudioDataset(
            ...             root="./data", split="val", transform=self.val_transforms
            ...         )
        """
