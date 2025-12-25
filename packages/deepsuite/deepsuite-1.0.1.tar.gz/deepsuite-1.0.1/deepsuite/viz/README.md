# Visualization

Visualisierungs-Tools für Training, Embeddings und Modell-Analyse.

## Module

- **`embedding.py`** - Embedding-Visualisierung (t-SNE, UMAP, PCA)

## Verwendung

### Embedding Visualization

```python
from deepsuite.viz import EmbeddingVisualizer

viz = EmbeddingVisualizer(
    method='tsne',  # 'tsne', 'umap', 'pca'
    perplexity=30,
    n_components=2
)

# Visualize Embeddings
viz.plot(
    embeddings=features,
    labels=labels,
    save_path='embeddings.png',
    title='Feature Space Visualization'
)
```

### t-SNE Visualization

```python
from deepsuite.viz import TSNEVisualizer

tsne_viz = TSNEVisualizer(
    perplexity=30,
    n_iter=1000,
    random_state=42
)

# 2D Projection
projection = tsne_viz.fit_transform(embeddings)

# Plot
tsne_viz.plot(
    projection=projection,
    labels=labels,
    save_path='tsne.png'
)
```

### UMAP Visualization

```python
from deepsuite.viz import UMAPVisualizer

umap_viz = UMAPVisualizer(
    n_neighbors=15,
    min_dist=0.1,
    metric='cosine'
)

# Faster than t-SNE
projection = umap_viz.fit_transform(embeddings)
umap_viz.plot(projection, labels, save_path='umap.png')
```

### PCA Visualization

```python
from deepsuite.viz import PCAVisualizer

pca_viz = PCAVisualizer(n_components=2)

# Linear projection
projection = pca_viz.fit_transform(embeddings)
explained_var = pca_viz.explained_variance_ratio_

print(f"Explained variance: {explained_var}")
```

## Features

- ✅ **Multiple Methods**: t-SNE, UMAP, PCA
- ✅ **Interactive Plots**: Matplotlib, Plotly
- ✅ **Color Coding**: Automatische Farbzuweisung für Klassen
- ✅ **3D Visualization**: Optional 3D-Projektionen
- ✅ **Animation**: Zeitliche Entwicklung von Embeddings

## Integration mit PyTorch Lightning

```python
import pytorch_lightning as pl
from deepsuite.viz import EmbeddingVisualizer

class ModelWithVisualization(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.viz = EmbeddingVisualizer(method='tsne')

    def validation_epoch_end(self, outputs):
        # Sammle Embeddings
        embeddings = torch.cat([o['embeddings'] for o in outputs])
        labels = torch.cat([o['labels'] for o in outputs])

        # Visualize
        self.viz.plot(
            embeddings=embeddings.cpu().numpy(),
            labels=labels.cpu().numpy(),
            save_path=f'embeddings_epoch_{self.current_epoch}.png'
        )
```

## Erweiterte Verwendung

### Animation über Epochen

```python
from deepsuite.viz import EmbeddingAnimator

animator = EmbeddingAnimator(method='tsne')

# Während Training sammeln
for epoch in range(100):
    embeddings = model.get_embeddings(val_data)
    animator.add_frame(embeddings, labels, epoch)

# Animation erstellen
animator.save('embedding_evolution.gif', fps=10)
```

### Interactive 3D Plot

```python
from deepsuite.viz import Interactive3DVisualizer

viz = Interactive3DVisualizer()

# 3D Plotly Visualization
fig = viz.plot_3d(
    embeddings=features,
    labels=labels,
    hover_text=sample_names
)

fig.show()  # Öffnet im Browser
```

### Clustering Visualization

```python
from deepsuite.viz import ClusterVisualizer

cluster_viz = ClusterVisualizer(
    clustering_method='kmeans',
    n_clusters=10
)

# Automatisches Clustering + Visualization
cluster_viz.fit_plot(
    embeddings=features,
    save_path='clusters.png'
)
```

## Visualisierungs-Typen

### Embedding Space

```python
# t-SNE für komplexe Manifolds
tsne = TSNEVisualizer(perplexity=30)
tsne.plot(embeddings, labels)

# UMAP für große Datasets (schneller)
umap = UMAPVisualizer(n_neighbors=15)
umap.plot(embeddings, labels)

# PCA für lineare Struktur
pca = PCAVisualizer(n_components=2)
pca.plot(embeddings, labels)
```

### Confusion Matrix

```python
from deepsuite.viz import ConfusionMatrixVisualizer

cm_viz = ConfusionMatrixVisualizer(class_names=class_names)

cm_viz.plot(
    y_true=true_labels,
    y_pred=predicted_labels,
    normalize=True,
    save_path='confusion_matrix.png'
)
```

### Training Curves

```python
from deepsuite.viz import TrainingVisualizer

train_viz = TrainingVisualizer()

train_viz.plot_metrics(
    train_loss=train_losses,
    val_loss=val_losses,
    train_acc=train_accs,
    val_acc=val_accs,
    save_path='training_curves.png'
)
```

### Attention Weights

```python
from deepsuite.viz import AttentionVisualizer

attn_viz = AttentionVisualizer()

# Visualize Transformer Attention
attn_viz.plot_attention(
    attention_weights=attn_weights,  # (n_heads, seq_len, seq_len)
    tokens=tokens,
    layer=5,
    save_path='attention_layer5.png'
)
```

## Beispiel: Complete Visualization Pipeline

```python
from deepsuite.viz import VisualizationPipeline

pipeline = VisualizationPipeline(
    output_dir='visualizations/',
    methods=['tsne', 'umap', 'pca']
)

# Training Callback
class VizCallback(pl.Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        embeddings = pl_module.val_embeddings
        labels = pl_module.val_labels

        pipeline.visualize_all(
            embeddings=embeddings,
            labels=labels,
            epoch=trainer.current_epoch
        )
```

## Best Practices

### Performance

```python
# Für große Datasets: Sample reduzieren
indices = torch.randperm(len(embeddings))[:5000]
embeddings_sample = embeddings[indices]
labels_sample = labels[indices]

viz.plot(embeddings_sample, labels_sample)
```

### Reproduzierbarkeit

```python
# Seed setzen
viz = EmbeddingVisualizer(
    method='tsne',
    random_state=42
)
```

### High-Quality Plots

```python
# DPI erhöhen
viz.plot(
    embeddings=features,
    labels=labels,
    save_path='high_res.png',
    dpi=300,
    figsize=(12, 10)
)
```

## Weitere Informationen

- Hauptdokumentation: [docs/modules_overview.md](../../../docs/modules_overview.md)
- Beispiele: [examples/](../../../examples/)
