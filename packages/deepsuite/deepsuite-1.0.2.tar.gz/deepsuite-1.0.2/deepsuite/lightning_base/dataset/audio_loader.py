"""Audio Loader module."""

import audiomentations as am

from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader


class AudioLoader(BaseDataLoader):
    def __init__(
        self, batch_size: int = 32, num_workers: int = 4, randaugment: bool = False
    ) -> None:
        super().__init__(batch_size=batch_size, num_workers=num_workers, randaugment=randaugment)

    def _get_train_transforms(self):
        if self.randaugment:
            return am.Compose(
                [
                    am.AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
                    am.TimeStretch(min_rate=0.8, max_rate=1.25, p=0.5),
                    am.PitchShift(min_semitones=-4, max_semitones=4, p=0.5),
                    am.ClippingDistortion(
                        min_percentile_threshold=0, max_percentile_threshold=20, p=0.5
                    ),
                    am.Gain(min_gain_in_db=-12, max_gain_in_db=12, p=0.5),
                    am.Shift(min_fraction=-0.5, max_fraction=0.5, p=0.5),
                    am.Normalize(p=1.0),
                ]
            )
        return am.Compose(
            [
                am.AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
                am.Normalize(p=1.0),
            ]
        )

    def _get_val_transforms(self):
        return am.Compose(
            [
                am.Normalize(p=1.0),
            ]
        )

    def setup(self, stage=None):
        """Initialize self.train_dataset and self.val_dataset."""
