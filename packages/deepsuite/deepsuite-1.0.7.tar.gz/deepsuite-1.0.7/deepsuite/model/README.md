# Models

Model architectures for various deep learning tasks.

## Modules

### Language Models

- **`gpt.py`** - GPT-2/GPT-3 Transformer
- **`deepseek.py`** - DeepSeek-V3 with MLA and MoE

### Computer Vision

#### Object Detection

- **`detection/`**
  - `yolo.py` - YOLO (v3/v4/v5)
  - `centernet.py` - CenterNet anchor-free detection
  - `detection.py` - Base detection architecture
  - `efficient.py` - EfficientDet
  - `darknet.py` - DarkNet backbone
  - `resnet.py` - ResNet detection
  - `mobile.py` - MobileNet-based detectors
  - `head.py` - Detection heads

#### Feature Extraction

- **`feature/`**
  - `resnet.py` - ResNet-18/34/50/101/152
  - `efficientnet.py` - EfficientNet B0-B7
  - `darknet.py` - DarkNet-53/CSPDarkNet
  - `mobile.py` - MobileNetV2/V3
  - `fpn.py` - Feature Pyramid Network
  - `wavenet.py` - WaveNet für Audio

### Audio Processing

- **`beamforming/`** - Multi-Channel Audio Beamforming
  - `beamforming.py` - Delay-and-Sum, MVDR, GCC-PHAT
- **`doa.py`** - Direction of Arrival Estimation
- **`complex.py`** - Complex-valued Neural Networks
- **`rnn.py`** - RNN-basierte Sequenzmodelle

### Specialized

- **`tracking.py`** - Multi-Object Tracking
- **`polynomial.py`** - Polynomial Feature Networks
- **`residual.py`** - Residual Connections
- **`conv.py`** - Konventionelle CNN-Architekturen
- **`backend_adapter.py`** - Export-Adapter für verschiedene Backends

## Verwendung

### GPT Model

```python
from deepsuite.model import GPT

model = GPT(
    vocab_size=50000,
    d_model=768,
    n_layers=12,
    n_heads=12,
    d_ff=3072,
    max_seq_len=1024,
    dropout=0.1
)

output = model(input_ids, attention_mask)
```

### DeepSeek-V3 Model

```python
from deepsuite.model import DeepSeekV3

model = DeepSeekV3(
    vocab_size=50000,
    d_model=2048,
    n_layers=24,
    n_heads=16,
    # MLA
    d_h_c=256,
    d_h_r=64,
    # MoE
    n_shared_experts=1,
    n_routed_experts=256,
    n_expert_per_token=8
)

logits = model(input_ids)
```

### YOLO Model

```python
from deepsuite.model.detection import YOLO

model = YOLO(
    num_classes=80,
    model_size='s',  # 's', 'm', 'l', 'x'
    img_size=640
)

predictions = model(images)  # (batch, num_detections, 85)
```

### CenterNet Model

```python
from deepsuite.model.detection import CenterNet

model = CenterNet(
    num_classes=80,
    backbone='resnet50',
    head_conv=64
)

outputs = model(images)  # Dict: 'heatmap', 'wh', 'reg'
```

### ResNet Feature Extractor

```python
from deepsuite.model.feature import ResNet50

backbone = ResNet50(pretrained=True)

# Multi-scale Features
features = backbone(images)
# Returns: [C2, C3, C4, C5] - verschiedene Auflösungen
```

### Feature Pyramid Network

```python
from deepsuite.model.feature import FPN

fpn = FPN(
    in_channels=[256, 512, 1024, 2048],  # ResNet outputs
    out_channels=256
)

# Einheitliche Feature-Maps
pyramid = fpn(features)  # [P2, P3, P4, P5]
```

### Beamforming

```python
from deepsuite.model.beamforming import Beamformer

beamformer = Beamformer(
    n_channels=4,
    algorithm='mvdr',  # 'das', 'mvdr', 'gccphat'
    sample_rate=16000
)

# Multi-channel Input: (batch, channels, time)
enhanced = beamformer(multichannel_audio)
```

### Direction of Arrival

```python
from deepsuite.model import DOAEstimator

doa = DOAEstimator(
    n_channels=4,
    n_fft=512,
    method='music'  # 'music', 'esprit', 'srp-phat'
)

angles = doa.estimate(multichannel_audio)  # (batch, n_sources)
```

## Model-Hierarchie

```
model/
├── Language Models
│   ├── gpt.py              # GPT-2/GPT-3
│   └── deepseek.py         # DeepSeek-V3
│
├── detection/              # Object Detection
│   ├── yolo.py
│   ├── centernet.py
│   ├── efficient.py
│   ├── darknet.py
│   ├── resnet.py
│   ├── mobile.py
│   └── head.py
│
├── feature/                # Feature Extraction
│   ├── resnet.py
│   ├── efficientnet.py
│   ├── darknet.py
│   ├── mobile.py
│   ├── fpn.py
│   └── wavenet.py
│
├── beamforming/            # Audio Processing
│   └── beamforming.py
│
└── Specialized
    ├── tracking.py         # Object Tracking
    ├── doa.py             # DOA Estimation
    ├── complex.py         # Complex Networks
    ├── rnn.py             # RNN Models
    └── polynomial.py      # Polynomial Networks
```

## Model Zoo

### Language Models

| Model       | Size   | Parameters | Config                           |
| ----------- | ------ | ---------- | -------------------------------- |
| GPT-Small   | Small  | 124M       | `d_model=768, n_layers=12`       |
| GPT-Medium  | Medium | 350M       | `d_model=1024, n_layers=24`      |
| GPT-Large   | Large  | 774M       | `d_model=1280, n_layers=36`      |
| DeepSeek-V3 | Base   | 1.3B       | `d_model=2048, n_layers=24, MoE` |
| DeepSeek-V3 | Large  | 685B       | `d_model=7168, n_layers=60, MoE` |

### Computer Vision

| Model           | Backbone        | Parameters | mAP  | FPS |
| --------------- | --------------- | ---------- | ---- | --- |
| YOLOv5s         | CSPDarknet      | 7.2M       | 37.4 | 140 |
| YOLOv5m         | CSPDarknet      | 21M        | 45.4 | 100 |
| YOLOv5l         | CSPDarknet      | 46M        | 49.0 | 70  |
| CenterNet       | ResNet-50       | 32M        | 42.1 | 45  |
| EfficientDet-D0 | EfficientNet-B0 | 3.9M       | 33.8 | 98  |

### Feature Extractors

| Backbone        | Parameters | ImageNet Top-1 | Use Case         |
| --------------- | ---------- | -------------- | ---------------- |
| ResNet-18       | 11M        | 69.8%          | Lightweight      |
| ResNet-50       | 25M        | 76.1%          | Standard         |
| ResNet-101      | 44M        | 77.4%          | High Accuracy    |
| EfficientNet-B0 | 5.3M       | 77.3%          | Mobile           |
| EfficientNet-B4 | 19M        | 82.9%          | High Performance |
| DarkNet-53      | 41M        | -              | YOLO Backbone    |
| MobileNetV3     | 5.4M       | 75.2%          | Edge Devices     |

## Features

### Alle Models bieten

- ✅ Pre-trained weights (ImageNet, COCO, etc.)
- ✅ Easy export (ONNX, TorchScript, TensorRT)
- ✅ Batch inference support
- ✅ Mixed precision (FP16/BF16)
- ✅ Modular design for custom heads

### Export Example

```python
from deepsuite.model import ResNet50
from deepsuite.model.backend_adapter import ONNXAdapter, TensorRTAdapter

model = ResNet50(pretrained=True)

# ONNX Export
onnx_adapter = ONNXAdapter(model)
onnx_adapter.export("resnet50.onnx", input_shape=(1, 3, 224, 224))

# TensorRT Export
trt_adapter = TensorRTAdapter(model)
trt_adapter.export("resnet50.engine", precision="fp16")
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- LLM Models: [docs/llm_modules.md](../../../docs/llm_modules.md)
- MoE: [docs/moe.md](../../../docs/moe.md)
- Beispiele: [examples/](../../../examples/)
