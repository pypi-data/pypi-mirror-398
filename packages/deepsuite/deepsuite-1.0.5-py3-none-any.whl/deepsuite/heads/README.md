# Heads

Ausgabe-Köpfe (Output Heads) für verschiedene Deep Learning Tasks.

## Module

### Language Models

- **`lm_head.py`** - Language Modeling Head mit optionaler Gewichtsteilung
- **`mtp_head.py`** - Multi-Token Prediction (MTP) Head für DeepSeek-V3

### Computer Vision

- **`classification.py`** - Klassifizierungs-Head für Image Classification
- **`box.py`** - Bounding Box Regression für Object Detection
- **`centernet.py`** - CenterNet Detection Head mit Heatmaps
- **`heatmap.py`** - Generische Heatmap-Ausgabe für Keypoint Detection

## Verwendung

### Language Model Head

```python
from deepsuite.heads import LMHead

lm_head = LMHead(
    d_model=2048,
    vocab_size=50000,
    tie_weights=True  # Gewichte mit Embedding teilen
)

logits = lm_head(hidden_states)  # (batch, seq_len, vocab_size)
```

### Multi-Token Prediction Head

```python
from deepsuite.heads import MTPHead

mtp_head = MTPHead(
    d_model=2048,
    vocab_size=50000,
    mtp_depth=3  # 1, 2, 3 Tokens voraus
)

logits_list = mtp_head(hidden_states)  # Liste von (batch, seq_len, vocab_size)
```

### Classification Head

```python
from deepsuite.heads import ClassificationHead

clf_head = ClassificationHead(
    in_features=2048,
    num_classes=1000,
    dropout=0.1
)

logits = clf_head(features)  # (batch, num_classes)
```

### CenterNet Head

```python
from deepsuite.heads import CenterNetHead

head = CenterNetHead(
    in_channels=256,
    num_classes=80,
    head_conv=64
)

outputs = head(features)  # Dict mit 'heatmap', 'wh', 'reg'
```

## Features

- ✅ Modulare Architektur für verschiedene Tasks
- ✅ Einfache Integration in PyTorch Lightning Module
- ✅ Unterstützung für Gewichtsteilung (LM Head)
- ✅ Konfigurierbare Dropout-Raten
- ✅ Optimierte Implementierungen

## Head-Loss Paarungen

| Head                 | Passende Loss-Funktion          | Task                    |
| -------------------- | ------------------------------- | ----------------------- |
| `LMHead`             | `CrossEntropyLoss`              | Language Modeling       |
| `MTPHead`            | `MTPLoss`                       | Multi-Token Prediction  |
| `ClassificationHead` | `CrossEntropyLoss`, `FocalLoss` | Image Classification    |
| `CenterNetHead`      | `CenterNetLoss`                 | Object Detection        |
| `BoxHead`            | `GIoULoss`, `DIoULoss`          | Bounding Box Regression |

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- LLM Heads: [docs/llm_loss_head.md](../../../docs/llm_loss_head.md)
