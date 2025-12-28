"""PyTorch Lightning Module Wrappers für End-to-End Training."""

from deepsuite.modules.centernet import CenterNetModule
from deepsuite.modules.deepseek import DeepSeekModule, DeepSeekV3
from deepsuite.modules.gpt import GPT, GPTModule
from deepsuite.modules.tracking import TrackingModule
from deepsuite.modules.yolo import Yolo

__all__ = [
    "GPT",
    "CenterNetModule",
    "DeepSeekModule",
    "DeepSeekV3",
    "GPTModule",
    "TrackingModule",
    "Yolo",
]
