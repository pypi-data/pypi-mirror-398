"""APTT - Advanced PyTorch Training Toolkit.

A PyTorch Lightning-based framework for deep learning with focus on:
- Object Detection (YOLO, CenterNet)
- Object Tracking
- Continual Learning
- Audio/Signal Processing
"""

__version__ = "1.0.2"

# Core Lightning Modules
from deepsuite.lightning_base.continual_learning_manager import ContinualLearningManager

# Base Classes
from deepsuite.lightning_base.module import BaseModule
from deepsuite.lightning_base.trainer import BaseTrainer
from deepsuite.model.autoencoder import AutoencoderModule, ConvDecoder, ConvEncoder
from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.detection.centernet import CenterNetModel

# Model Architectures
from deepsuite.model.detection.yolo import YOLO
from deepsuite.model.discriminator import (
    MultiScaleDiscriminator,
    PatchGANDiscriminator,
    PixelDiscriminator,
)

__all__ = [
    # Model Architectures
    "YOLO",
    "AutoencoderModule",
    "BackboneAdapter",
    # Base Classes
    "BaseModule",
    "BaseTrainer",
    "CenterNetModel",
    "ContinualLearningManager",
    "ConvDecoder",
    "ConvEncoder",
    "MultiScaleDiscriminator",
    "PatchGANDiscriminator",
    "PixelDiscriminator",
    # Version
    "__version__",
]
