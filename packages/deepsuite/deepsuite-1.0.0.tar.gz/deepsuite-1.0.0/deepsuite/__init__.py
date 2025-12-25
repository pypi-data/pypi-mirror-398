"""APTT - Advanced PyTorch Training Toolkit.

A PyTorch Lightning-based framework for deep learning with focus on:
- Object Detection (YOLO, CenterNet)
- Object Tracking
- Continual Learning
- Audio/Signal Processing
"""

__version__ = "1.0.3"

# Core Lightning Modules
from deepsuite.lightning_base.continual_learning_manager import ContinualLearningManager

# Base Classes
from deepsuite.lightning_base.module import BaseModule
from deepsuite.lightning_base.trainer import BaseTrainer
from deepsuite.model.backend_adapter import BackboneAdapter
from deepsuite.model.detection.centernet import CenterNetModel

# Model Architectures
from deepsuite.model.detection.yolo import YOLO
from deepsuite.modules.centernet import CenterNetModule
from deepsuite.modules.tracking import TrackingModule
from deepsuite.modules.yolo import Yolo

__all__ = [
    # Version
    "__version__",
    # Lightning Modules (end-to-end trainable)
    "Yolo",
    "CenterNetModule",
    "TrackingModule",
    # Base Classes
    "BaseModule",
    "BaseTrainer",
    "ContinualLearningManager",
    # Model Architectures
    "YOLO",
    "CenterNetModel",
    "BackboneAdapter",
]
