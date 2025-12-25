"""Tsne Laplace Callback module."""

import os

import matplotlib.pyplot as plt
import numpy as np
from pytorch_lightning import Callback
from sklearn.manifold import TSNE
import torch


class TSNELaplaceCallback(Callback):
    def __init__(
        self,
        dataloader,
        num_classes: int = 4000,
        every_n_epochs: int = 5,
        save_dir: str = "tsne_plots",
        tensorboard_logger=None,
    ) -> None:
        super().__init__()
        self.dataloader = dataloader
        self.num_classes = num_classes
        self.every_n_epochs = every_n_epochs
        self.save_dir = save_dir
        self.logger = tensorboard_logger

        os.makedirs(save_dir, exist_ok=True)

    def on_epoch_end(self, trainer, pl_module):
        epoch = trainer.current_epoch
        if epoch % self.every_n_epochs != 0:
            return

        pl_module.eval()
        all_embeddings = []
        all_labels = []

        with torch.no_grad():
            for batch in self.dataloader:
                inputs, targets = batch
                inputs = inputs.to(pl_module.device)
                targets = targets.to(pl_module.device)

                # 🔥 define `extract_features` in your model
                features = pl_module.extract_features(inputs)
                all_embeddings.append(features.cpu())
                all_labels.append(targets.cpu())

        embeddings_np = torch.cat(all_embeddings).numpy()
        labels_np = torch.cat(all_labels).numpy()

        self._plot_tsne_laplace(embeddings_np, labels_np, epoch)

    def _plot_tsne_laplace(self, embeddings, labels, epoch):
        tsne = TSNE(
            n_components=2, init="random", learning_rate="auto", perplexity=30, ithubrandom_state=42
        )
        reduced = tsne.fit_transform(embeddings)

        angles = np.linspace(0, 2 * np.pi, self.num_classes, endpoint=False)
        class_pos = np.stack([np.cos(angles), np.sin(angles)], axis=1)

        plt.figure(figsize=(10, 10))
        plt.scatter(reduced[:, 0], reduced[:, 1], c=labels, cmap="hsv", s=2, alpha=0.7)

        for i in range(0, self.num_classes, max(1, self.num_classes // 100)):
            x, y = class_pos[i] * 100
            plt.text(x, y, str(i), fontsize=5, ha="center", va="center", color="gray")

        plt.title(f"t-SNE Laplace-Scheibe - Epoch {epoch}")
        plt.axis("off")

        save_path = f"{self.save_dir}/tsne_epoch_{epoch:03d}.png"
        plt.savefig(save_path, dpi=300)
        plt.close()

        if self.logger:
            from PIL import Image

            img = Image.open(save_path).convert("RGB")
            img_tensor = torch.from_numpy(np.array(img)).permute(2, 0, 1).float() / 255.0
            self.logger.experiment.add_image("tSNE_Laplace", img_tensor, global_step=epoch)
