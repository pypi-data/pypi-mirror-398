<p align="center">
    <img src="docs/logo.png" alt="DeepSuite" width="140" />
</p>

# DeepSuite

DeepSuite is a comprehensive deep learning framework based on [PyTorch Lightning](https://www.pytorchlightning.ai/).
It provides production-ready implementations of modern architectures: language models (GPT, DeepSeek‑V3 with MLA/MoE),
object detection (YOLO, CenterNet), and specialized audio/vision models. Docstrings and examples follow Google‑Style.

## 🚀 Features

### Language Models & NLP

- ✅ **GPT-2/GPT-3 Architecture**: Full transformer implementation with configurable layers
- ✅ **DeepSeek-V3**: State-of-the-art LLM with Multi-Head Latent Attention (MLA) and Mixture-of-Experts (MoE)
  - Multi-Head Latent Attention with KV-Compression
  - Auxiliary-Loss-Free Load Balancing
  - Multi-Token Prediction (MTP)
  - Rotary Position Embeddings (RoPE)
- ✅ **Text Dataset Loaders**: Support for .txt, .jsonl, pre-tokenized data with sliding window

### Computer Vision

- ✅ **Object Detection**: YOLO (v3/v4/v5), CenterNet, EfficientDet
- ✅ **Feature Extractors**: ResNet, DarkNet, EfficientNet, MobileNet, FPN
- ✅ **Tracking**: RNN-based object tracking with ReID

### Audio Processing

- ✅ **Beamforming**: Multi-channel audio processing
- ✅ **Direction of Arrival (DOA)**: Acoustic source localization
- ✅ **Feature Networks**: WaveNet, Complex-valued networks

### Training & Optimization

- 🧠 **Continual Learning**: Built-in knowledge distillation and LwF (Learning without Forgetting)
- 🧩 **Pluggable Callbacks**: TorchScript export, TensorRT optimization, t-SNE visualization
- ⚙️ **Modular Design**: Composable heads, losses, layers, and metrics
- 📊 **Visualization Tools**: Embedding analysis, training metrics, model profiling
- 🗂️ **Flexible Dataset Loaders**: Image, audio, text with augmentation support

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/afeldman/deepsuite.git
cd deepsuite

# Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Installation (CPU)
uv sync --extra cpu --extra dev

# Installation (CUDA 12.4)
uv sync --extra cu124 --extra dev

# Documentation build dependencies
brew install graphviz             # macOS
sudo apt-get install libgraphviz-dev  # Linux
```

## 🎯 Quick Start

### Language Model Training (DeepSeek‑V3)

```python
import pytorch_lightning as pl
from deepsuite.model.llm.deepseek import DeepSeekV3Module
from deepsuite.lightning_base.dataset.text_loader import TextDataLoader

# Prepare dataset
datamodule = TextDataLoader(
    train_data_path="data/train.txt",
    val_data_path="data/val.txt",
    tokenizer=tokenizer,
    max_seq_len=512,
    batch_size=32,
    return_mtp=True,  # Enable Multi-Token Prediction
)

# Create model
model = DeepSeekV3Module(
    vocab_size=50000,
    d_model=2048,
    n_layers=24,
    n_heads=16,
    use_moe=True,           # Mixture-of-Experts
    use_mtp=True,           # Multi-Token Prediction
    n_routed_experts=256,
    n_expert_per_token=8,
)

# Training
trainer = pl.Trainer(max_steps=100000, accelerator="gpu")
trainer.fit(model, datamodule)
```

### Object Detection (YOLO)

````python
import pytorch_lightning as pl
from deepsuite.model.feature.yolo import YOLOLightningModule

model = YOLOLightningModule(
    num_classes=80,
    backbone="cspdarknet",
    use_rotated_loss=False,
)

trainer = pl.Trainer(max_epochs=100, accelerator="gpu")
trainer.fit(model, datamodule)

### Pluggable Heads & Global Registry

DeepSuite provides a global head registry and trainer helpers to compose multi-head models across projects.

```python
from deepsuite.registry import HeadRegistry
from deepsuite.lightning_base.trainer import train_heads_with_registry

# Register your head class in your project
@HeadRegistry.register("my_head")
class MyHead:
    ...

# Build and train via registry
trainer = train_heads_with_registry(
    head_cfgs=[{"name": "my_head", "args": {"param": 123}}],
    module_builder=MyMultiHeadLightningModule,  # accepts heads, share_backbone
    datamodule=my_data_module,
    trainer_cfg={"max_epochs": 10, "accelerator": "gpu"},
    share_backbone=True,
)
````

````

### Feature Matching (LoFTR)

```python
from deepsuite.model.loftr.loftr import LoFTR

loftr = LoFTR(d_model=256, nhead=8)
matches = loftr(img1, img2)
````

### Spatial Transformer Networks (STN)

```python
from deepsuite.model.stn import AffineSTN

stn = AffineSTN(in_channels=3)
warped = stn(images)
```

## 📚 Documentation

### Core Modules

#### Language Models

- **[LLM Modules](docs/llm_modules.md)**: GPT and DeepSeek-V3 architecture documentation
- **[LLM Loss & Heads](docs/llm_loss_head.md)**: Language modeling losses and output heads
- **[Mixture-of-Experts](docs/moe.md)**: DeepSeek-V3 MoE implementation
- **[Text Datasets](docs/text_dataset.md)**: Text data loading and preprocessing

#### Computer Vision

- Detection models (YOLO, CenterNet, EfficientDet)
- Feature extractors (ResNet, DarkNet, EfficientNet, FPN)
- Object tracking systems

#### Audio Processing

- Beamforming algorithms
- DOA estimation
- Complex-valued neural networks

### Examples

```bash
# Language Models
python examples/llm_modules_example.py      # GPT & DeepSeek-V3
python examples/llm_loss_head_example.py    # Loss functions & heads
python examples/moe_example.py              # Mixture-of-Experts
python examples/text_dataset_simple.py      # Text data loading

# View all examples
ls examples/
```

### Build Documentation Locally

```bash
cd docs
make html
# Open docs/_build/html/index.html
```

## 🏗️ Project Structure

```bash
deepsuite/
├── src/deepsuite/                      # Core source code
│   ├── callbacks/                 # Training callbacks (TensorRT, t-SNE, etc.)
│   ├── heads/                     # Output heads (classification, detection, LM)
│   ├── layers/                    # Neural network layers
│   │   ├── attention/             # Attention mechanisms (MLA, RoPE, KV-Compression)
│   │   └── moe.py                 # Mixture-of-Experts
│   ├── lightning_base/            # Lightning modules and utilities
│   │   └── dataset/               # Dataset loaders (image, audio, text)
│   ├── loss/                      # Loss functions
│   ├── metric/                    # Evaluation metrics
│   ├── model/                     # Model architectures
│   │   ├── beamforming/           # Audio beamforming
│   │   └── detection/             # Object detection
│   ├── modules/                   # Lightning modules
│   │   ├── deepseek.py            # DeepSeek-V3 module
│   │   ├── gpt.py                 # GPT module
│   │   ├── yolo.py                # YOLO module
│   │   └── ...
│   └── utils/                     # Utility functions
├── examples/                      # Usage examples
│   ├── llm_modules_example.py     # Language model examples
│   ├── moe_example.py             # MoE examples
│   └── text_dataset_simple.py     # Dataset examples
├── tests/                         # Unit tests
├── docs/                          # Sphinx documentation
│   ├── llm_modules.md             # LLM documentation
│   ├── moe.md                     # MoE documentation
│   └── text_dataset.md            # Dataset documentation
├── pyproject.toml                 # Project configuration
├── README.md                      # This file
#
```

## 🎓 Key Concepts

### Multi-Head Latent Attention (MLA)

DeepSeek-V3's efficient attention mechanism with low-rank KV-compression:

```python
from deepsuite.layers.attention.mla import MultiHeadLatentAttention

attention = MultiHeadLatentAttention(
    d=2048,  # Model dimension
    n_h=16,  # Number of heads
    d_h_c=256,  # Compressed KV dimension
    d_h_r=64,  # Per-head RoPE dimension
)
```

### Mixture-of-Experts (MoE)

Sparse expert activation with auxiliary-loss-free load balancing:

```python
from deepsuite.layers.moe import DeepSeekMoE

moe = DeepSeekMoE(
    d_model=2048,
    n_shared_experts=1,  # Always active
    n_routed_experts=256,  # Selectively activated
    n_expert_per_token=8,  # Top-K experts per token
)
```

### Multi-Token Prediction (MTP)

Predict multiple future tokens simultaneously:

```python
# Dataset mit MTP-Zielen
dataset = TextDataset(
    data_path="train.txt",
    tokenizer=tokenizer,
    return_mtp=True,
    mtp_depth=3,  # Predict 1, 2, 3 tokens ahead
)

# Model with MTP loss
model = DeepSeekV3Module(
    vocab_size=50000,
    use_mtp=True,
    mtp_lambda=0.3,  # MTP loss weight
)
```

## 📊 Model Zoo

### Language Models

| Model          | Parameters | Config                                       | Performance    |
| -------------- | ---------- | -------------------------------------------- | -------------- |
| GPT-Small      | 124M       | \`d_model=768, n_layers=12\`                 | GPT-2 baseline |
| DeepSeek-Small | 51M        | \`d_model=512, n_layers=4, use_moe=True\`    | Demo config    |
| DeepSeek-Base  | 1.3B       | \`d_model=2048, n_layers=24, n_experts=256\` | Production     |
| DeepSeek-V3    | 685B       | \`d_model=7168, n_layers=60, n_experts=256\` | Full scale     |

### Object Detection

| Model     | Backbone   | mAP  | FPS |
| --------- | ---------- | ---- | --- |
| YOLOv5s   | CSPDarknet | 37.4 | 140 |
| YOLOv5m   | CSPDarknet | 45.4 | 100 |
| CenterNet | ResNet-50  | 42.1 | 45  |

## 🧪 Testing

```bash
# All tests
pytest

# Single test
pytest tests/test_tensor_rt_export_callback.py

# With coverage
pytest --cov=deepsuite
```

## 🛠️ Development

### Code Quality (Google‑Style, Ruff, MyPy)

Docstrings follow Google-Style and are verified via Ruff (pydocstyle=google).

```bash
# Format code
ruff format .

# Linting (Auto-Fix)
ruff check . --fix

# Type checking
mypy src/deepsuite
```

Optional: Set up pre-commit hooks.

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type checking
mypy src/deepsuite
```

### Pre‑commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📖 Citation

If you use DeepSuite in your research, please cite:

```bibtex
@software{deepsuite2025,
title = {DeepSuite},
author = {Anton Feldmann},
year = {2025},
url = {https://github.com/afeldman/deepsuite}
}
```

For DeepSeek-V3:

```bibtex
@article{deepseekai2024deepseekv3,
title={DeepSeek-V3 Technical Report},
author={DeepSeek-AI},
journal={arXiv preprint arXiv:2412.19437},
year={2024}
}
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/amazing-feature\`)
3. Commit your changes (\`git commit -m 'Add amazing feature'\`)
4. Push to the branch (\`git push origin feature/amazing-feature\`)
5. Open a Pull Request

Please ensure:

- Code follows the style guide (Ruff + MyPy)
- Tests pass (pytest)
- Documentation is updated

## 🙏 Acknowledgments

- [PyTorch Lightning](https://www.pytorchlightning.ai/) for the training framework
- [DeepSeek-AI](https://github.com/deepseek-ai) for the DeepSeek-V3 architecture
- [Ultralytics](https://github.com/ultralytics/yolov5) for YOLO implementations
- The open-source community for various model implementations

## 📧 Contact

Anton Feldmann - anton.feldmann@gmail.com

Project Link: [https://github.com/afeldman/deepsuite](https://github.com/afeldman/deepsuite)

---

**Version:** 1.0.1 | **Python:** >=3.11 | **PyTorch:** >=2.6.0 | **Lightning:** >=2.5.1 | **License:** Apache 2.0
