"""Image data loader module for computer vision tasks.

This module provides a PyTorch Lightning data module for image datasets with
support for various augmentation strategies using Albumentations.

Example:
    Basic usage::

        from deepsuite.lightning_base.dataset.image_loader import ImageLoader
        from pytorch_lightning import Trainer

        # Create data module
        datamodule = ImageLoader(batch_size=32, num_workers=4, randaugment=False, image_size=(224, 224))

        # Setup datasets
        datamodule.setup()

        # Use with trainer
        trainer = Trainer(max_epochs=10)
        trainer.fit(model, datamodule)

    With aggressive augmentation::

        datamodule = ImageLoader(batch_size=64, num_workers=8, randaugment=True, image_size=(256, 256))
"""

from typing import Any

try:
    import albumentations as A  # noqa: N812
    from albumentations.pytorch import ToTensorV2

    HAS_ALBUMENTATIONS = True
except ImportError:
    HAS_ALBUMENTATIONS = False
    A = None  # type: ignore
    ToTensorV2 = None  # type: ignore

from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader


class ImageLoader(BaseDataLoader):
    """PyTorch Lightning data module for image datasets.

    Provides automated augmentation pipelines using Albumentations with
    support for both standard and aggressive (RandAugment-style) augmentation.

    Attributes:
        image_size: Target image size as (height, width) tuple.

    Note:
        Uses ImageNet normalization by default (mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]). Override _get_train_transforms() and
        _get_val_transforms() to customize.
    """

    def __init__(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        randaugment: bool = False,
        image_size: tuple[int, int] = (256, 256),
    ) -> None:
        """Initialize the image data loader.

        Args:
            batch_size: Number of images per batch. Defaults to 32.
            num_workers: Number of worker processes for data loading.
                Defaults to 4.
            randaugment: If True, apply aggressive augmentation (RandAugment-style)
                with shifts, rotations, cutouts, and color jittering.
                Defaults to False.
            image_size: Target image size as (height, width) tuple.
                Defaults to (256, 256).

        Example:
            >>> loader = ImageLoader(batch_size=64, image_size=(224, 224), randaugment=True)
        """
        super().__init__(
            batch_size=batch_size,
            num_workers=num_workers,
            randaugment=randaugment,
        )
        self.image_size = image_size

    def _get_train_transforms(self) -> Any:
        """Return training transforms with optional RandAugment.

        If randaugment=True, applies an aggressive augmentation pipeline including:
        - Geometric transformations (shift, scale, rotation, flip)
        - Texture augmentations (blur, dropout, coarse dropout)
        - Color augmentations (brightness/contrast, hue/saturation, RGB shift)
        - Noise (Gaussian noise)

        If randaugment=False, applies conservative augmentation with:
        - Horizontal flip
        - Random brightness/contrast adjustment
        - ImageNet normalization

        Returns:
            albumentations.Compose: Augmentation pipeline for training images.

        Example:
            >>> loader = ImageLoader(randaugment=True)
            >>> transforms = loader._get_train_transforms()
            >>> augmented = transforms(image=image)
        """
        if not HAS_ALBUMENTATIONS:
            # Return identity transform if albumentations not available
            return lambda image: image

        if self.randaugment:
            # RandAugment-style aggressive augmentation
            return A.Compose(
                [
                    A.Resize(self.image_size[0], self.image_size[1]),
                    A.ShiftScaleRotate(
                        shift_limit=0.1,
                        scale_limit=0.1,
                        rotate_limit=15,
                        p=0.5,
                    ),
                    A.HorizontalFlip(p=0.5),
                    A.CoarseDropout(
                        num_holes_range=(0, 1),
                        hole_height_range=(5, 32),
                        hole_width_range=(5, 32),
                        fill=0,
                        p=0.5,
                    ),
                    A.RandomBrightnessContrast(p=0.5),
                    A.HueSaturationValue(p=0.5),
                    A.RGBShift(p=0.5),
                    A.GaussNoise(p=0.5),
                    A.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                    ToTensorV2(),
                ]
            )

        # Standard conservative augmentation
        return A.Compose(
            [
                A.Resize(self.image_size[0], self.image_size[1]),
                A.HorizontalFlip(p=0.5),
                A.RandomBrightnessContrast(p=0.2),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
                ToTensorV2(),
            ]
        )

    def _get_val_transforms(self) -> Any:
        """Return validation transforms without augmentation.

        Applies minimal preprocessing:
        - Resize to target image_size
        - ImageNet normalization
        - Convert to PyTorch tensor format

        Returns:
            albumentations.Compose: Preprocessing pipeline for validation images.

        Example:
            >>> loader = ImageLoader()
            >>> transforms = loader._get_val_transforms()
            >>> preprocessed = transforms(image=image)
        """
        if not HAS_ALBUMENTATIONS:
            # Return identity transform if albumentations not available
            return lambda image: image

        return A.Compose(
            [
                A.Resize(self.image_size[0], self.image_size[1]),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
                ToTensorV2(),
            ]
        )

    def setup(self, stage: str | None = None) -> None:
        """Initialize training and validation datasets.

        This method should be overridden in subclasses to load and prepare
        the actual image datasets. The transforms from _get_train_transforms()
        and _get_val_transforms() are available via self.train_transforms
        and self.val_transforms.

        Args:
            stage: Either 'fit', 'validate', 'test', or 'predict'. Can be used
                to conditionally create datasets. Defaults to None.

        Example:
            >>> class MyImageLoader(ImageLoader):
            ...     def setup(self, stage=None):
            ...         self.train_dataset = MyImageDataset(
            ...             root="./data", split="train", transform=self.train_transforms
            ...         )
            ...         self.val_dataset = MyImageDataset(
            ...             root="./data", split="val", transform=self.val_transforms
            ...         )
        """
