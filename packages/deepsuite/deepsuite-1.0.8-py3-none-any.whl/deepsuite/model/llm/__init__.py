"""PyTorch Lightning Module Wrappers für End-to-End Training."""

from deepsuite.model.llm.centernet import CenterNetModule
from deepsuite.model.llm.deepseek import DeepSeekModule, DeepSeekV3
from deepsuite.model.llm.gpt import GPT, GPTModule

__all__ = [
    "GPT",
    "CenterNetModule",
    "DeepSeekModule",
    "DeepSeekV3",
    "GPTModule",
]
