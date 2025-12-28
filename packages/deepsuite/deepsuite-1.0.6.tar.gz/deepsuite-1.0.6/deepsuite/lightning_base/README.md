# Lightning Base

Basis-Komponenten für PyTorch Lightning Integration.

## Module

### Core Components

- **`module.py`** - Basis Lightning Module mit gemeinsamer Funktionalität
- **`trainer.py`** - Trainer-Konfiguration und Utilities
- **`continual_learning_manager.py`** - Continual Learning und Knowledge Distillation

### Datasets

- **`dataset/`** - Datenloader für verschiedene Modalitäten
  - `text_loader.py` - Text-Datasets für Language Models
  - `image_loader.py` - Bild-Datasets für Vision Tasks
  - `audio_loader.py` - Audio-Datasets für Audio Processing
  - `universal_set.py` - Flexible Dataset-Abstraktion
  - `base_loader.py` - Basis-Klasse für alle Loader

## Verwendung

### Lightning Module Basis

```python
from deepsuite.lightning_base import BaseLightningModule

class CustomModule(BaseLightningModule):
    def __init__(self, model, learning_rate=1e-4):
        super().__init__(learning_rate=learning_rate)
        self.model = model

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.cross_entropy(y_hat, y)
        self.log('train/loss', loss)
        return loss
```

### Text DataLoader

```python
from deepsuite.lightning_base.dataset import TextDataLoader

datamodule = TextDataLoader(
    train_data_path="train.txt",
    val_data_path="val.txt",
    tokenizer=tokenizer,
    max_seq_len=512,
    batch_size=32,
    num_workers=4,
    # Optional: MTP
    return_mtp=True,
    mtp_depth=3,
    # Optional: Sliding Window
    stride=256
)

# Automatisches Setup
datamodule.setup(stage='fit')
train_loader = datamodule.train_dataloader()
val_loader = datamodule.val_dataloader()
```

### Image DataLoader

```python
from deepsuite.lightning_base.dataset import ImageDataLoader

datamodule = ImageDataLoader(
    train_dir="data/train",
    val_dir="data/val",
    img_size=224,
    batch_size=64,
    num_workers=8,
    augmentation=True
)
```

### Audio DataLoader

```python
from deepsuite.lightning_base.dataset import AudioDataLoader

datamodule = AudioDataLoader(
    train_dir="data/audio/train",
    val_dir="data/audio/val",
    sample_rate=16000,
    n_fft=512,
    hop_length=160,
    batch_size=32
)
```

### Continual Learning

```python
from deepsuite.lightning_base import ContinualLearningManager

manager = ContinualLearningManager(
    model=current_model,
    teacher_model=previous_model,
    distillation_alpha=0.5,
    temperature=2.0
)

# Training mit Knowledge Distillation
trainer = pl.Trainer()
trainer.fit(manager, datamodule)
```

## Features

### BaseLightningModule

- ✅ Automatische Optimizer-Konfiguration (Adam/AdamW)
- ✅ Learning Rate Scheduler (Cosine, Linear, etc.)
- ✅ Gradient Clipping
- ✅ Mixed Precision Training (AMP)
- ✅ Logging Integration (TensorBoard, WandB)
- ✅ Checkpoint Management

### Dataset Loaders

- ✅ **Text**: .txt, .jsonl, .pt mit Tokenizer-Support
- ✅ **Images**: Standard Image Augmentation, Multi-Scale Training
- ✅ **Audio**: STFT, Mel-Spectrogram, Multi-Channel Support
- ✅ **Universal**: Flexibles Format für Custom Data

### Continual Learning

- ✅ Knowledge Distillation
- ✅ Learning without Forgetting (LwF)
- ✅ Elastic Weight Consolidation (EWC)
- ✅ Task Incremental Learning

## Dataset-Format-Übersicht

### Text Datasets

| Format   | Beschreibung                     | Verwendung           |
| -------- | -------------------------------- | -------------------- |
| `.txt`   | Raw text                         | Language Modeling    |
| `.jsonl` | JSON Lines mit `{"text": "..."}` | Structured Data      |
| `.pt`    | Pre-tokenized PyTorch Tensor     | Optimiertes Training |

### Image Datasets

| Format         | Struktur               | Task                  |
| -------------- | ---------------------- | --------------------- |
| Classification | `class_name/image.jpg` | Image Classification  |
| Detection      | COCO/YOLO Annotation   | Object Detection      |
| Segmentation   | Image + Mask Pairs     | Semantic Segmentation |

### Audio Datasets

| Format  | Beschreibung | Task            |
| ------- | ------------ | --------------- |
| `.wav`  | Raw Audio    | Speech, Music   |
| `.flac` | Lossless     | High Quality    |
| `.mp3`  | Compressed   | General Purpose |

## Beispiel: Multi-Modal Training

```python
from deepsuite.lightning_base.dataset import TextDataLoader, ImageDataLoader

# Text Branch
text_dm = TextDataLoader(
    train_data_path="text_train.txt",
    tokenizer=tokenizer,
    max_seq_len=512,
    batch_size=32
)

# Vision Branch
image_dm = ImageDataLoader(
    train_dir="images/train",
    img_size=224,
    batch_size=64
)

# Combined Training
class MultiModalModule(BaseLightningModule):
    def __init__(self):
        super().__init__()
        self.text_encoder = ...
        self.image_encoder = ...

    def training_step(self, batch, batch_idx):
        if isinstance(batch, dict):
            # Text batch
            text_loss = self.text_forward(batch['text'])
        else:
            # Image batch
            image_loss = self.image_forward(batch)
        return loss
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- Text Datasets: [docs/text_dataset.md](../../../docs/text_dataset.md)
- Beispiele: [examples/text_dataset_simple.py](../../../examples/text_dataset_simple.py)
