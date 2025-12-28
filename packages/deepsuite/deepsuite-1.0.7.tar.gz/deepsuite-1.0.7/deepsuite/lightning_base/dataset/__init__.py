"""Dataset loading module for PyTorch Lightning.

Provides data loaders and datasets for various modalities including:
- Image data (ImageLoader)
- Audio data (AudioLoader)
- Text/Language models (TextLoader)
- Universal dataset with auto-download (UniversalDataset)
"""

from deepsuite.lightning_base.dataset.audio_loader import AudioLoader
from deepsuite.lightning_base.dataset.base_loader import BaseDataLoader
from deepsuite.lightning_base.dataset.image_loader import ImageLoader
from deepsuite.lightning_base.dataset.text_loader import TextDataLoader, TextDataset
from deepsuite.lightning_base.dataset.universal_set import UniversalDataset

__all__ = [
    "AudioLoader",
    "BaseDataLoader",
    "ImageLoader",
    "TextDataLoader",
    "TextDataset",
    "UniversalDataset",
]
