# Tracker

Multi-Object Tracking Implementierungen.

## Module

- **`tracker.py`** - Basis-Tracker-Klasse
- **`tracker_manager.py`** - Tracker Management und Orchestrierung
- **`rnn_tracker.py`** - RNN-basiertes Object Tracking
- **`reid_encoder.py`** - Re-Identification Feature Encoder
- **`inference.py`** - Tracking Inference Pipeline

## Verwendung

### Einfaches Tracking

```python
from deepsuite.tracker import ObjectTracker

tracker = ObjectTracker(
    max_age=30,        # Frames ohne Detection
    min_hits=3,        # Min. Detections vor Initialisierung
    iou_threshold=0.3  # IoU für Matching
)

# Frame-by-Frame
for frame in video:
    detections = detector(frame)  # Bounding Boxes + Scores

    tracks = tracker.update(detections)

    for track in tracks:
        print(f"ID: {track.id}, Box: {track.box}, Age: {track.age}")
```

### RNN-basiertes Tracking

```python
from deepsuite.tracker import RNNTracker

tracker = RNNTracker(
    feature_dim=512,
    hidden_dim=256,
    num_layers=2,
    max_age=30,
    reid_threshold=0.7
)

# Mit Feature Extraction
for frame in video:
    detections = detector(frame)
    features = reid_encoder(frame, detections)

    tracks = tracker.update(detections, features)
```

### Re-Identification Encoder

```python
from deepsuite.tracker import ReIDEncoder

reid = ReIDEncoder(
    backbone='resnet50',
    embedding_dim=512,
    pretrained=True
)

# Feature Extraction für Detections
features = reid.extract_features(image, bboxes)  # (N, 512)

# Feature Matching
similarity = reid.compute_similarity(features1, features2)
```

### Tracker Manager

```python
from deepsuite.tracker import TrackerManager

manager = TrackerManager(
    detector=yolo_model,
    tracker=rnn_tracker,
    reid_encoder=reid_encoder
)

# End-to-End Tracking
for frame in video:
    tracks = manager.track(frame)

    # Visualisierung
    annotated = manager.visualize(frame, tracks)
```

## Tracking-Algorithmen

### SORT (Simple Online Realtime Tracking)

```python
from deepsuite.tracker import SORTTracker

tracker = SORTTracker(
    max_age=30,
    min_hits=3,
    iou_threshold=0.3
)

# Verwendet Kalman Filter + IoU Matching
tracks = tracker.update(detections)
```

### DeepSORT

```python
from deepsuite.tracker import DeepSORTTracker

tracker = DeepSORTTracker(
    max_age=30,
    n_init=3,
    max_iou_distance=0.7,
    max_cosine_distance=0.2,
    reid_encoder=reid_encoder
)

# Kalman Filter + Deep Appearance Features
tracks = tracker.update(detections, features)
```

### ByteTrack

```python
from deepsuite.tracker import ByteTracker

tracker = ByteTracker(
    track_thresh=0.5,
    track_buffer=30,
    match_thresh=0.8
)

# Two-Stage Association mit Low-Confidence Detections
tracks = tracker.update(detections)
```

## Features

- ✅ **Multi-Algorithm Support**: SORT, DeepSORT, ByteTrack
- ✅ **Re-Identification**: Deep Feature Matching
- ✅ **Motion Models**: Kalman Filter, Constant Velocity
- ✅ **Occlusion Handling**: Track Recovery nach Verdeckung
- ✅ **Real-time Performance**: Optimiert für Live-Video
- ✅ **Multi-Class Tracking**: Verschiedene Objektklassen

## Track-Objekt

```python
class Track:
    id: int              # Eindeutige Track-ID
    box: Tensor          # Bounding Box [x1, y1, x2, y2]
    score: float         # Confidence Score
    class_id: int        # Objektklasse
    age: int             # Frames seit Initialisierung
    hits: int            # Anzahl erfolgreicher Matches
    time_since_update: int  # Frames ohne Update
    features: Tensor     # ReID Features
    velocity: Tensor     # Geschwindigkeit [vx, vy, vw, vh]
```

## Evaluation

### MOT Metrics

```python
from deepsuite.tracker import MOTMetrics

mot = MOTMetrics()

for frame_id, (gt_boxes, pred_tracks) in enumerate(dataset):
    mot.update(
        frame_id=frame_id,
        gt_boxes=gt_boxes,
        pred_boxes=[t.box for t in pred_tracks],
        gt_ids=gt_ids,
        pred_ids=[t.id for t in pred_tracks]
    )

results = mot.compute()
print(f"MOTA: {results['mota']:.3f}")
print(f"MOTP: {results['motp']:.3f}")
print(f"IDF1: {results['idf1']:.3f}")
```

## Tracking Pipeline

```python
from deepsuite.tracker import TrackingPipeline

pipeline = TrackingPipeline(
    detector_config={
        'model': 'yolov5s',
        'conf_thresh': 0.25,
    },
    tracker_config={
        'algorithm': 'deepsort',
        'max_age': 30,
    },
    reid_config={
        'backbone': 'resnet50',
        'embedding_dim': 512,
    }
)

# Video Processing
pipeline.process_video(
    input_path='input.mp4',
    output_path='output.mp4',
    visualize=True
)
```

## Visualisierung

```python
from deepsuite.tracker import TrackVisualizer

viz = TrackVisualizer(
    colors='rainbow',      # Farben für verschiedene IDs
    thickness=2,
    show_trajectory=True,  # Pfade zeichnen
    trajectory_length=30
)

# Annotated Frame
annotated = viz.draw_tracks(
    frame=frame,
    tracks=tracks,
    show_id=True,
    show_class=True,
    show_score=True
)
```

## Best Practices

### Optimierung für Geschwindigkeit

```python
# 1. Niedrigere Detector Confidence
detector.conf_thresh = 0.4  # Weniger False Positives

# 2. Kürzere Tracking History
tracker.max_age = 15  # Schneller Track-Abbruch

# 3. ReID nur für schwierige Fälle
tracker.use_reid_threshold = 0.5  # IoU-Matching bevorzugen
```

### Optimierung für Genauigkeit

```python
# 1. Strengere Initialisierung
tracker.min_hits = 5  # Mehr Bestätigungen

# 2. Längere Tracking History
tracker.max_age = 50  # Bessere Occlusion Handling

# 3. Immer ReID verwenden
tracker.use_reid = True
```

### Multi-Camera Tracking

```python
from deepsuite.tracker import MultiCameraTracker

mc_tracker = MultiCameraTracker(
    num_cameras=4,
    reid_encoder=reid_encoder,
    spatial_constraints=camera_geometry
)

# Synchronisierte Frames
tracks = mc_tracker.update({
    'cam1': detections1,
    'cam2': detections2,
    'cam3': detections3,
    'cam4': detections4,
})
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- Beispiele: [examples/](../../../examples/)
