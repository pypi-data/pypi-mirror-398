"""Base data loader module for PyTorch Lightning.

This module provides an abstract base class for data loaders that integrate
with PyTorch Lightning's LightningDataModule. It standardizes the interface
for data loading, transformations, and batch creation.

Example:
    Implementing a custom data loader::

        from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader
        from your_transforms import get_train_transforms, get_val_transforms
        from your_dataset import CustomDataset


        class CustomDataLoader(BaseDataLoader):
            def _get_train_transforms(self):
                return get_train_transforms()

            def _get_val_transforms(self):
                return get_val_transforms()

            def setup(self, stage=None):
                self.train_dataset = CustomDataset(split="train", transform=self.train_transforms)
                self.val_dataset = CustomDataset(split="val", transform=self.val_transforms)
"""

import abc
from typing import TYPE_CHECKING, Any

from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader

if TYPE_CHECKING:
    from torch.utils.data import Dataset


class BaseDataLoader(LightningDataModule):
    """Abstract base class for PyTorch Lightning data modules.

    This class provides a standardized interface for data loading with
    PyTorch Lightning, including transform management and DataLoader creation.
    Subclasses must implement abstract methods for transforms and setup.

    Attributes:
        batch_size: Number of samples per batch.
        num_workers: Number of worker processes for data loading.
        randaugment: Whether to use aggressive augmentation.
        train_transforms: Transformations applied to training samples.
        val_transforms: Transformations applied to validation samples.
        train_dataset: Training dataset instance (set in setup).
        val_dataset: Validation dataset instance (set in setup).
    """

    def __init__(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        randaugment: bool = False,
    ) -> None:
        """Initialize the base data loader.

        Args:
            batch_size: Number of samples per batch. Defaults to 32.
            num_workers: Number of worker processes for data loading.
                Use 0 for no multiprocessing. Defaults to 4.
            randaugment: If True, use aggressive random augmentation during
                training. Defaults to False.

        Example:
            >>> loader = MyDataLoader(batch_size=64, num_workers=8, randaugment=True)
        """
        super().__init__()
        self.batch_size = batch_size
        self.randaugment = randaugment
        self.num_workers = num_workers

        self.train_transforms = self._get_train_transforms()
        self.val_transforms = self._get_val_transforms()

        self.train_dataset: Dataset[Any] | None = None
        self.val_dataset: Dataset[Any] | None = None

    @abc.abstractmethod
    def _get_train_transforms(self) -> Any:
        """Return train transforms (Albumentations or Audiomentations).

        This method should return the transformation pipeline for training data.
        The specific type depends on the data modality (images, audio, etc.).

        Returns:
            Transformation pipeline object (e.g., albumentations.Compose or
            audiomentations.Compose).

        Example:
            >>> import albumentations as A
            >>> def _get_train_transforms(self):
            ...     return A.Compose([A.HorizontalFlip(p=0.5), A.RandomBrightnessContrast(p=0.2)])
        """

    @abc.abstractmethod
    def _get_val_transforms(self) -> Any:
        """Return validation transforms.

        This method should return the transformation pipeline for validation data.
        Typically uses minimal or no augmentation compared to training transforms.

        Returns:
            Transformation pipeline object (e.g., albumentations.Compose or
            audiomentations.Compose).

        Example:
            >>> import albumentations as A
            >>> def _get_val_transforms(self):
            ...     return A.Compose([A.Normalize()])
        """

    @abc.abstractmethod
    def setup(self, stage: str | None = None) -> None:
        """Initialize train and validation datasets.

        This method should create self.train_dataset and self.val_dataset
        instances. It's called once per process during trainer initialization.

        Args:
            stage: Either 'fit', 'validate', 'test', or 'predict'. Can be used
                to create different datasets for different stages. Defaults to None.

        Example:
            >>> def setup(self, stage=None):
            ...     self.train_dataset = MyDataset(split="train", transform=self.train_transforms)
            ...     self.val_dataset = MyDataset(split="val", transform=self.val_transforms)
        """

    def train_dataloader(self) -> DataLoader[Any]:
        """Create and return the training DataLoader.

        Returns:
            DataLoader: Training loader with shuffling enabled. Uses the
                configured batch_size and num_workers.

        Raises:
            RuntimeError: If setup() hasn't been called or train_dataset
                is None.

        Example:
            >>> loader = data_module.train_dataloader()
            >>> for batch in loader:
            ...     pass  # Process batch
        """
        if self.train_dataset is None:
            msg = "train_dataset is None. Call setup() first."
            raise RuntimeError(msg)

        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
        )

    def val_dataloader(self) -> DataLoader[Any]:
        """Create and return the validation DataLoader.

        Returns:
            DataLoader: Validation loader with shuffling disabled. Uses the
                configured batch_size and num_workers.

        Raises:
            RuntimeError: If setup() hasn't been called or val_dataset
                is None.

        Example:
            >>> loader = data_module.val_dataloader()
            >>> for batch in loader:
            ...     pass  # Process batch
        """
        if self.val_dataset is None:
            msg = "val_dataset is None. Call setup() first."
            raise RuntimeError(msg)

        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
        )
