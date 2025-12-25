"""Base Loader module."""

import abc

from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader


class BaseDataLoader(LightningDataModule):
    def __init__(
        self, batch_size: int = 32, num_workers: int = 4, randaugment: bool = False
    ) -> None:
        super().__init__()
        self.batch_size = batch_size
        self.randaugment = randaugment
        self.num_workers = num_workers

        self.train_transforms = self._get_train_transforms()
        self.val_transforms = self._get_val_transforms()

        self.train_dataset = None
        self.val_dataset = None

    @abc.abstractmethod
    def _get_train_transforms(self):
        """Return train transforms (Albumentations or Audiomentations)."""

    @abc.abstractmethod
    def _get_val_transforms(self):
        """Return validation transforms."""

    @abc.abstractmethod
    def setup(self, stage=None):
        """Initialize self.train_dataset and self.val_dataset."""

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
        )
