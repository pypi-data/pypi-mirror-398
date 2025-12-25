"""Universal Set module."""

from torch.utils.data import Dataset


class UniversalDataset(Dataset):
    def __init__(self, data=None, labels=None, transform=None) -> None:
        self.data = data if data is not None else []
        self.labels = labels if labels is not None else []
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x = self.data[idx]
        y = self.labels[idx]

        if self.transform:
            x = self.transform(x)

        return x, y
