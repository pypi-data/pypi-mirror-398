# Utils

Utility-Funktionen und Helper für verschiedene Tasks.

## Module

### Model Utilities

- **`teacher.py`** - Teacher Model Management für Knowledge Distillation
- **`device.py`** - Device Management (CPU/GPU/TPU)
- **`autocast.py`** - Mixed Precision Utilities
- **`summery.py`** - Model Summary und Parameter Counting

### Data Processing

- **`bbox.py`** - Bounding Box Operationen (IoU, NMS, etc.)
- **`image.py`** - Bildverarbeitung und Augmentation
- **`tensor.py`** - Tensor-Manipulationen
- **`xy.py`** - Koordinaten-Transformationen

### Audio Processing

- **`tsignal.py`** - Time-Series Signal Processing
- **`complex.py`** - Complex-valued Tensor Operations
- **`array_calibration.py`** - Microphone Array Calibration

### Architecture Utilities

- **`anchor.py`** - Anchor Generation für Object Detection
- **`head_expansion.py`** - Dynamische Head-Expansion
- **`search_space.py`** - Neural Architecture Search Spaces
- **`rnn.py`** - RNN Helper Functions

### Mathematical Operations

- **`hermite.py`** - Hermite Polynomial Functions
- **`laguerre.py`** - Laguerre Polynomial Functions

### Training Utilities

- **`taskAlignedAssigner.py`** - Task-Aligned Sample Assignment (TOOD)
- **`hw.py`** - Hardware Detection und Optimization

## Verwendung

### Bounding Box Utilities

```python
from deepsuite.utils import bbox

# IoU Berechnung
iou = bbox.box_iou(boxes1, boxes2)  # (N, M)

# Non-Maximum Suppression
keep = bbox.nms(boxes, scores, iou_threshold=0.45)

# Box Format Conversion
boxes_xyxy = bbox.xywh2xyxy(boxes_xywh)
boxes_cxcywh = bbox.xyxy2cxcywh(boxes_xyxy)

# Box Area
areas = bbox.box_area(boxes)
```

### Image Processing

```python
from deepsuite.utils import image

# Resize mit Aspect Ratio
img_resized, scale = image.letterbox(img, new_shape=(640, 640))

# Mosaic Augmentation (YOLO)
mosaic = image.mosaic_augmentation(images, labels)

# Mixup
mixed_img, mixed_label = image.mixup(img1, label1, img2, label2, alpha=0.5)

# Color Jittering
img_aug = image.random_color_jitter(img, brightness=0.2, contrast=0.2)
```

### Tensor Operations

```python
from deepsuite.utils import tensor

# Select Top-K
values, indices = tensor.select_topk(scores, k=5)

# Gather by Index
gathered = tensor.gather_by_index(features, indices)

# Masked Operations
masked_mean = tensor.masked_mean(tensor, mask)

# Smooth Labels
smoothed = tensor.label_smoothing(labels, smoothing=0.1)
```

### Device Management

```python
from deepsuite.utils import device

# Auto-detect beste Device
dev = device.get_device()  # 'cuda', 'mps', 'cpu'

# Model auf Device
model = device.to_device(model, dev)

# Memory Info
memory = device.get_memory_info()
print(f"Used: {memory['used']} / {memory['total']} MB")

# Multi-GPU Setup
devices = device.get_available_devices()
```

### Anchor Generation

```python
from deepsuite.utils import anchor

# Generate Anchors für YOLO
anchors = anchor.generate_anchors(
    feature_sizes=[(80, 80), (40, 40), (20, 20)],
    anchor_scales=[10, 16, 33],
    anchor_ratios=[1.0, 2.0, 0.5],
    image_size=640
)

# Assign Anchors zu Ground Truth
assigned = anchor.assign_anchors(
    anchors=anchors,
    gt_boxes=gt_boxes,
    iou_threshold=0.5
)
```

### Task-Aligned Assigner

```python
from deepsuite.utils import TaskAlignedAssigner

assigner = TaskAlignedAssigner(
    topk=13,
    alpha=1.0,
    beta=6.0
)

# Dynamic Label Assignment
target_labels, target_boxes, target_scores = assigner(
    pred_scores=pred_scores,
    pred_boxes=pred_boxes,
    anchor_points=anchor_points,
    gt_labels=gt_labels,
    gt_boxes=gt_boxes
)
```

### Complex Operations

```python
from deepsuite.utils import complex as cplx

# Complex Multiplication
result = cplx.complex_mul(a, b)

# Complex Convolution
conv_out = cplx.complex_conv2d(x_complex, weight_complex)

# Magnitude and Phase
magnitude = cplx.magnitude(x_complex)
phase = cplx.phase(x_complex)

# STFT
stft = cplx.stft(audio, n_fft=512, hop_length=160)
```

### Signal Processing

```python
from deepsuite.utils import tsignal

# Apply Window Function
windowed = tsignal.apply_window(signal, window='hamming')

# Compute Spectrogram
spec = tsignal.spectrogram(audio, n_fft=512, hop_length=160)

# Mel-Scale Conversion
mel_spec = tsignal.mel_spectrogram(audio, sr=16000, n_mels=80)

# Voice Activity Detection
vad_mask = tsignal.vad(audio, threshold=0.05)
```

### Model Summary

```python
from deepsuite.utils import summery

# Parameter Count
total, trainable = summery.count_parameters(model)
print(f"Total: {total:,} | Trainable: {trainable:,}")

# Layer-wise Summary
summery.print_summary(model, input_size=(1, 3, 224, 224))

# FLOPs Estimation
flops = summery.estimate_flops(model, input_size=(1, 3, 224, 224))
print(f"FLOPs: {flops / 1e9:.2f}G")
```

### Mixed Precision

```python
from deepsuite.utils import autocast

# Automatic Mixed Precision Context
with autocast.autocast_context(device_type='cuda', dtype=torch.float16):
    output = model(input)
    loss = criterion(output, target)

# Gradient Scaling
scaler = autocast.get_scaler()
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### Polynomial Functions

```python
from deepsuite.utils import hermite, laguerre

# Hermite Polynomials
H_n = hermite.hermite_polynomial(x, n=5)

# Laguerre Polynomials
L_n = laguerre.laguerre_polynomial(x, n=5)

# Feature Expansion
features_expanded = hermite.hermite_feature_expansion(features, max_order=3)
```

## Utility-Kategorien

### Bounding Box Operationen

| Funktion    | Beschreibung            |
| ----------- | ----------------------- |
| `box_iou`   | Intersection over Union |
| `box_giou`  | Generalized IoU         |
| `box_diou`  | Distance IoU            |
| `box_ciou`  | Complete IoU            |
| `nms`       | Non-Maximum Suppression |
| `soft_nms`  | Soft NMS                |
| `xywh2xyxy` | Format Conversion       |
| `xyxy2xywh` | Format Conversion       |

### Image Processing

| Funktion              | Beschreibung             |
| --------------------- | ------------------------ |
| `letterbox`           | Resize mit Padding       |
| `mosaic_augmentation` | 4-Image Mosaic           |
| `mixup`               | Image Mixing             |
| `random_color_jitter` | Color Augmentation       |
| `random_flip`         | Horizontal/Vertical Flip |
| `random_crop`         | Random Cropping          |

### Tensor Operations

| Funktion          | Beschreibung     |
| ----------------- | ---------------- |
| `select_topk`     | Top-K Selection  |
| `gather_by_index` | Indexing         |
| `masked_mean`     | Masked Averaging |
| `label_smoothing` | Label Smoothing  |
| `one_hot`         | One-Hot Encoding |

## Best Practices

### Efficient Bounding Box Processing

```python
from deepsuite.utils import bbox

# Vectorized IoU (viel schneller als Loop)
ious = bbox.box_iou(pred_boxes, gt_boxes)  # (N, M)

# NMS mit konfigurierbarem Threshold
keep = bbox.nms(boxes, scores, iou_threshold=0.45)
filtered_boxes = boxes[keep]
```

### Memory-Efficient Image Augmentation

```python
from deepsuite.utils import image

# In-place Operations wo möglich
image.random_flip_inplace(img, p=0.5)

# Batch Processing
batch_imgs = image.batch_letterbox(imgs, new_shape=(640, 640))
```

### Device-Agnostic Code

```python
from deepsuite.utils import device

# Automatische Device-Auswahl
dev = device.get_device()
model = model.to(dev)
data = data.to(dev)

# Graceful Fallback
try:
    dev = device.get_device(prefer='cuda')
except:
    dev = torch.device('cpu')
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- Beispiele: [examples/](../../../examples/)
