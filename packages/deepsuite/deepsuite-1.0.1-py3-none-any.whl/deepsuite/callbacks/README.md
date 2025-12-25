# Callbacks

PyTorch Lightning callbacks for export, optimization, and visualization.

## Modules

### Export & Optimization

- **`torchscript.py`** - TorchScript export for production deployment
- **`tensor_rt.py`** - TensorRT optimization for NVIDIA GPUs

### Logging & Visualization

- **`embedding_logger.py`** - Embedding visualization during training
- **`tsne_laplace_callback.py`** - t-SNE and Laplace eigenmap visualization

### Base

- **`base.py`** - Base callback class and shared functionality

## Usage

### TorchScript Export

```python
from deepsuite.callbacks import TorchScriptCallback

trainer = pl.Trainer(
    callbacks=[
        TorchScriptCallback(
            export_path="model.pt",
            method="script"  # oder "trace"
        )
    ]
)
```

### TensorRT Optimization

```python
from deepsuite.callbacks import TensorRTCallback

trainer = pl.Trainer(
    callbacks=[
        TensorRTCallback(
            export_path="model.engine",
            precision="fp16",
            workspace_size=1 << 30  # 1GB
        )
    ]
)
```

### Embedding Visualization

```python
from deepsuite.callbacks import EmbeddingLoggerCallback

trainer = pl.Trainer(
    callbacks=[
        EmbeddingLoggerCallback(
            log_every_n_epochs=5,
            num_samples=1000
        )
    ]
)
```

## Features

- ✅ Automatischer Export am Ende des Trainings
- ✅ Validierung der exportierten Modelle
- ✅ Integration mit TensorBoard und Weights & Biases
- ✅ Flexible Konfiguration per Callback-Parameter
- ✅ Fehlerbehandlung und Logging

## Weitere Informationen

Siehe Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
