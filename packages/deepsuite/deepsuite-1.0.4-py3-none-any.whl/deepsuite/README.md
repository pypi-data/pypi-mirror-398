# DeepSuite

This is the main directory for the DeepSuite source code.

## Module Overview

Each subdirectory contains its own README.md with detailed documentation.

### 🧠 Language Models & NLP

- **[layers/](layers/)** - Neural Network Layers

  - Attention Mechanisms (MLA, RoPE, KV-Compression)
  - Mixture-of-Experts (MoE)
  - Specialized Layers (Complex, Hermite, Laguerre)

- **[modules/](modules/)** - PyTorch Lightning Modules

  - GPT-2/GPT-3
  - DeepSeek-V3 with MLA and MoE
  - YOLO, CenterNet

- **[heads/](heads/)** - Output Heads

  - Language Model Head
  - Multi-Token Prediction Head
  - Classification, Detection, Heatmap Heads

- **[loss/](loss/)** - Loss Functions
  - Language Modeling Losses
  - Multi-Token Prediction Loss
  - Detection Losses (Focal, GIoU, DFL)
  - Knowledge Distillation

### 👁️ Computer Vision

- **[model/](model/)** - Model Architectures

  - Object Detection (YOLO, CenterNet, EfficientDet)
  - Feature Extraction (ResNet, EfficientNet, DarkNet, FPN)
  - Tracking

- **[tracker/](tracker/)** - Multi-Object Tracking

  - SORT, DeepSORT, ByteTrack
  - Re-Identification
  - Tracking Pipeline

- **[metric/](metric/)** - Evaluation Metrics
  - Mean Average Precision (mAP)
  - Detection Metrics
  - Confusion Matrix

### 🎵 Audio Processing

- **[model/beamforming/](model/beamforming/)** - Audio Beamforming
- See also: `model/complex.py`, `model/doa.py`, `model/rnn.py`

### ⚙️ Training & Utilities

- **[lightning_base/](lightning_base/)** - PyTorch Lightning Base

  - Base Lightning Module
  - Dataset Loaders (Text, Image, Audio)
  - Continual Learning Manager

- **[callbacks/](callbacks/)** - Training Callbacks

  - TorchScript, TensorRT Export
  - Embedding Logger
  - t-SNE Visualization

- **[utils/](utils/)** - Utility Functions

  - Bounding Box Operations
  - Image Processing
  - Tensor Utilities
  - Device Management

- **[viz/](viz/)** - Visualization
  - Embedding Visualization (t-SNE, UMAP, PCA)

### 🔧 Specialized

- **[config/](config/)** - Configuration Management
- **[svm/](svm/)** - Support Vector Machines
- **[conv/](conv/)** - Convolutional Neural Networks

## Quick Access

### Key Files

```
src/deepsuite/
├── modules/
│   ├── gpt.py              # GPT-2/GPT-3 Implementation
│   ├── deepseek.py         # DeepSeek-V3 Implementation
│   ├── yolo.py             # YOLO Object Detection
│   └── centernet.py        # CenterNet Detection
│
├── layers/
│   ├── attention/          # Attention Mechanisms
│   │   ├── mla.py          # Multi-Head Latent Attention
│   │   └── rope.py         # Rotary Position Embeddings
│   └── moe.py              # Mixture-of-Experts
│
├── lightning_base/dataset/
│   ├── text_loader.py      # Text Dataset for LLMs
│   ├── image_loader.py     # Image Dataset
│   └── audio_loader.py     # Audio Dataset
│
└── loss/
    ├── classification.py   # Cross-Entropy, Focal Loss
    ├── mtp_loss.py         # Multi-Token Prediction Loss
    └── detection.py        # Detection Losses
```

## Usage

### Import Examples

```python
# Language Models
from deepsuite.modules import GPTModule, DeepSeekModule
from deepsuite.layers.attention import MultiHeadLatentAttention
from deepsuite.layers import DeepSeekMoE

# Object Detection
from deepsuite.modules import YOLOModule, CenterNetModule
from deepsuite.model.detection import YOLO, CenterNet

# Datasets
from deepsuite.lightning_base.dataset import TextDataLoader, ImageDataLoader

# Losses
from deepsuite.loss import CrossEntropyLoss, MTPLoss, FocalLoss, GIoULoss

# Metrics
from deepsuite.metric import MeanAveragePrecision, DetectionMetrics

# Tracking
from deepsuite.tracker import ObjectTracker, DeepSORTTracker

# Utils
from deepsuite.utils import bbox, image, device

# Visualization
from deepsuite.viz import EmbeddingVisualizer
```

## Documentation

### READMEs

Each module has its own README.md:

- [callbacks/README.md](callbacks/README.md) - Training Callbacks
- [heads/README.md](heads/README.md) - Output Heads
- [layers/README.md](layers/README.md) - Neural Network Layers
- [lightning_base/README.md](lightning_base/README.md) - Lightning Base Components
- [loss/README.md](loss/README.md) - Loss Functions
- [metric/README.md](metric/README.md) - Evaluation Metrics
- [model/README.md](model/README.md) - Model Architectures
- [modules/README.md](modules/README.md) - Lightning Modules
- [tracker/README.md](tracker/README.md) - Object Tracking
- [utils/README.md](utils/README.md) - Utility Functions
- [viz/README.md](viz/README.md) - Visualization Tools

### Complete Documentation

See [docs/modules_overview.md](../../docs/modules_overview.md) for a complete overview of all modules.

### Specific Topics

- [docs/llm_modules.md](../../docs/llm_modules.md) - Language Models (GPT, DeepSeek-V3)
- [docs/llm_loss_head.md](../../docs/llm_loss_head.md) - LLM Losses & Heads
- [docs/moe.md](../../docs/moe.md) - Mixture-of-Experts
- [docs/text_dataset.md](../../docs/text_dataset.md) - Text Data Loading

## Development

### Code Style

```bash
# Format
ruff format src/deepsuite

# Lint
ruff check src/deepsuite

# Type Checking
mypy src/deepsuite
```

### Testing

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_tensor_rt_export_callback.py
```

## Architecture Principles

### 1. Modularity

Each component is independently usable:

```python
# Layer alone
from deepsuite.layers import DeepSeekMoE
moe = DeepSeekMoE(d_model=2048, ...)

# In custom model
class MyModel(nn.Module):
    def __init__(self):
        self.moe = DeepSeekMoE(...)
```

### 2. Lightning Integration

All main models are Lightning Modules:

```python
from deepsuite.modules import DeepSeekModule
import pytorch_lightning as pl

model = DeepSeekModule(...)
trainer = pl.Trainer(...)
trainer.fit(model, datamodule)
```

### 3. Composability

Components can be freely combined:

```python
from deepsuite.heads import LMHead
from deepsuite.loss import CrossEntropyLoss
from deepsuite.metric import Perplexity

class CustomModule(pl.LightningModule):
    def __init__(self):
        self.backbone = ...
        self.head = LMHead(...)
        self.loss_fn = CrossEntropyLoss(...)
        self.metric = Perplexity()
```

## More Information

- **Main Project**: [README.md](../../README.md)
- **Documentation**: [docs/](../../docs/)
- **Examples**: [examples/](../../examples/)
- **Tests**: [tests/](../../tests/)

---

**Version**: 0.2.0 | **License**: Apache 2.0
