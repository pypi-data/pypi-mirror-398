# Metrics

Evaluations-Metriken für verschiedene Deep Learning Tasks.

## Module

### Object Detection

- **`detection.py`** - Detection-Metriken (Precision, Recall, F1)
- **`map.py`** - Mean Average Precision (mAP)
- **`bbox_iou.py`** - Bounding Box IoU-Metriken
- **`probiou.py`** - Probabilistic IoU

### General

- **`confidence_matrix.py`** - Confusion Matrix und Class-wise Metriken
- **`norm.py`** - Normalisierungs-Metriken

## Verwendung

### Mean Average Precision

```python
from deepsuite.metric import MeanAveragePrecision

map_metric = MeanAveragePrecision(
    num_classes=80,
    iou_thresholds=[0.5, 0.55, 0.6, ..., 0.95]
)

# Während Training/Validation
for batch in dataloader:
    predictions = model(batch['images'])

    map_metric.update(
        preds=predictions,
        target=batch['targets']
    )

# Berechnung am Ende
map_50 = map_metric.compute()['map_50']
map_50_95 = map_metric.compute()['map']
```

### Detection Metrics

```python
from deepsuite.metric import DetectionMetrics

det_metrics = DetectionMetrics(
    num_classes=80,
    conf_threshold=0.25,
    iou_threshold=0.45
)

# Batch-wise Update
det_metrics.update(predictions, ground_truth)

# Ergebnisse
results = det_metrics.compute()
print(f"Precision: {results['precision']:.3f}")
print(f"Recall: {results['recall']:.3f}")
print(f"F1: {results['f1']:.3f}")
```

### Confusion Matrix

```python
from deepsuite.metric import ConfusionMatrix

cm = ConfusionMatrix(num_classes=80)

# Update
cm.update(predictions, targets)

# Visualisierung
import matplotlib.pyplot as plt
cm.plot(save_dir='results/', names=class_names)

# Class-wise Metriken
per_class_precision = cm.precision()
per_class_recall = cm.recall()
```

### Bounding Box IoU

```python
from deepsuite.metric import bbox_iou

# Standard IoU
iou = bbox_iou(pred_boxes, gt_boxes, format='xyxy')

# GIoU (Generalized IoU)
giou = bbox_iou(pred_boxes, gt_boxes, metric='giou')

# DIoU (Distance IoU)
diou = bbox_iou(pred_boxes, gt_boxes, metric='diou')

# CIoU (Complete IoU)
ciou = bbox_iou(pred_boxes, gt_boxes, metric='ciou')
```

### Probabilistic IoU

```python
from deepsuite.metric import ProbIoU

prob_iou = ProbIoU(
    num_samples=1000,
    uncertainty='gaussian'
)

# Mit Bounding Box Unsicherheit
iou_dist = prob_iou(
    pred_boxes=pred_boxes,
    pred_std=pred_std,  # Unsicherheit
    gt_boxes=gt_boxes
)
```

## Metrik-Übersicht

### Object Detection

| Metrik         | Beschreibung                       | Verwendung       |
| -------------- | ---------------------------------- | ---------------- |
| `mAP@0.5`      | Mean Average Precision bei IoU=0.5 | COCO, PASCAL VOC |
| `mAP@0.5:0.95` | mAP über IoU-Thresholds 0.5-0.95   | COCO Standard    |
| `Precision`    | TP / (TP + FP)                     | Genauigkeit      |
| `Recall`       | TP / (TP + FN)                     | Vollständigkeit  |
| `F1-Score`     | 2 _ (P _ R) / (P + R)              | Balance          |
| `IoU`          | Intersection over Union            | Box Overlap      |

### Confusion Matrix Metriken

| Metrik    | Formel            | Interpretation    |
| --------- | ----------------- | ----------------- |
| Accuracy  | (TP + TN) / Total | Gesamtgenauigkeit |
| Precision | TP / (TP + FP)    | Pro Klasse        |
| Recall    | TP / (TP + FN)    | Pro Klasse        |
| F1-Score  | 2PR / (P + R)     | Pro Klasse        |

## Features

- ✅ **Effiziente Berechnung**: Vektorisierte Operationen
- ✅ **Batch Processing**: Automatische Akkumulation über Batches
- ✅ **Multi-Class Support**: Bis zu tausende Klassen
- ✅ **COCO-kompatibel**: Standard-Metriken wie COCO
- ✅ **Visualisierung**: Confusion Matrix Plots
- ✅ **Class-wise Details**: Per-Class Performance

## PyTorch Lightning Integration

```python
import pytorch_lightning as pl
from deepsuite.metric import MeanAveragePrecision

class DetectionModule(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = ...
        self.map_metric = MeanAveragePrecision(num_classes=80)

    def validation_step(self, batch, batch_idx):
        predictions = self.model(batch['images'])

        # Automatische Metrik-Berechnung
        self.map_metric.update(predictions, batch['targets'])

    def on_validation_epoch_end(self):
        # Logging am Ende der Epoch
        results = self.map_metric.compute()
        self.log('val/map_50', results['map_50'])
        self.log('val/map', results['map'])

        # Reset für nächste Epoch
        self.map_metric.reset()
```

## Erweiterte Verwendung

### Custom Metric

```python
from deepsuite.metric.base import BaseMetric

class CustomMetric(BaseMetric):
    def __init__(self):
        super().__init__()
        self.add_state('correct', default=torch.tensor(0), dist_reduce_fx='sum')
        self.add_state('total', default=torch.tensor(0), dist_reduce_fx='sum')

    def update(self, preds, target):
        self.correct += (preds == target).sum()
        self.total += target.numel()

    def compute(self):
        return self.correct.float() / self.total
```

### Multi-Metric Tracking

```python
from deepsuite.metric import MetricCollection

metrics = MetricCollection({
    'map': MeanAveragePrecision(num_classes=80),
    'precision': DetectionMetrics(metric='precision'),
    'recall': DetectionMetrics(metric='recall'),
})

# Alle auf einmal updaten
metrics.update(predictions, targets)

# Alle auf einmal berechnen
results = metrics.compute()
for name, value in results.items():
    print(f"{name}: {value:.3f}")
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- Beispiele: [examples/](../../../examples/)
