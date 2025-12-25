"""Image Loader module."""

import albumentations as A
from albumentations.pytorch import ToTensorV2

from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader


class ImageLoader(BaseDataLoader):
    def __init__(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        randaugment: bool = False,
        image_size: tuple = (256, 256),
    ):
        super().__init__(batch_size=batch_size, num_workers=num_workers, randaugment=randaugment)
        self.image_size = image_size

    def _get_train_transforms(self):
        if self.randaugment:
            # RandAugment-artige schwere Augmentierung
            return A.Compose(
                [
                    A.Resize(self.image_size[0], self.image_size[1]),
                    A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5),
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
                    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                    ToTensorV2(),
                ]
            )
        # Standard-Augmentierung
        return A.Compose(
            [
                A.Resize(self.image_size[0], self.image_size[1]),
                A.HorizontalFlip(p=0.5),
                A.RandomBrightnessContrast(p=0.2),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ToTensorV2(),
            ]
        )

    def _get_val_transforms(self):
        return A.Compose(
            [
                A.Resize(self.image_size[0], self.image_size[1]),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ToTensorV2(),
            ]
        )

    def setup(self, stage=None):
        """Initialize self.train_dataset and self.val_dataset."""
