"""Universal dataset module with auto-download and extraction capabilities.

This module provides a flexible PyTorch Dataset implementation that supports
automatic downloading and extracting datasets from URLs. It integrates seamlessly
with PyTorch DataLoaders and supports custom transforms.

Example:
    Basic usage with auto-download::

        from deepsuite.lightning_base.dataset.universal_set import UniversalDataset

        dataset = UniversalDataset(
            download_url="https://example.com/dataset.zip", root_dir="./data", auto_download=True
        )

    Using with custom data and transforms::

        import torch
        from torchvision import transforms

        data = [torch.randn(3, 224, 224) for _ in range(100)]
        labels = [i % 10 for i in range(100)]
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5])])

        dataset = UniversalDataset(data=data, labels=labels, transform=transform)
"""

import logging
from pathlib import Path
import shutil
from typing import Any
import urllib.request

from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class UniversalDataset(Dataset[tuple[Any, Any]]):
    """PyTorch Dataset with optional auto-download and archive extraction.

    This dataset class extends torch.utils.data.Dataset to provide:
    - Automatic dataset downloading from URLs
    - Support for multiple archive formats (zip, tar.gz, tar, tgz)
    - Intelligent caching to avoid re-downloading
    - Optional transform pipeline support
    - Full type hints for better IDE support and mypy compatibility

    Attributes:
        data: List of data samples.
        labels: List of corresponding labels.
        transform: Optional callable to transform samples.
        download_url: URL to download dataset from.
        root_dir: Root directory for storing downloaded files.
    """

    def __init__(
        self,
        data: list[Any] | None = None,
        labels: list[Any] | None = None,
        transform: Any | None = None,
        download_url: str | None = None,
        root_dir: str | None = None,
        auto_download: bool = False,
    ) -> None:
        """Initialize UniversalDataset with optional auto-download functionality.

        Args:
            data: List of data samples. If None and auto_download is True with
                a download_url, the dataset will be downloaded. Defaults to None.
            labels: List of corresponding labels matching the data length.
                Defaults to None.
            transform: Optional callable to apply to each sample during
                __getitem__. Should accept and return a single sample.
                Defaults to None.
            download_url: URL to download the dataset archive from. Supports
                .zip, .tar, .tar.gz, and .tgz formats. Defaults to None.
            root_dir: Directory to store downloaded files. Created if it doesn't
                exist. Defaults to ./datasets in current working directory.
            auto_download: If True and download_url is provided, automatically
                download and extract the dataset if not already present.
                Defaults to False.

        Raises:
            RuntimeError: If download or extraction fails.
            ValueError: If archive format is unsupported.

        Example:
            >>> dataset = UniversalDataset(
            ...     download_url="https://example.com/dataset.zip", auto_download=True
            ... )
            >>> len(dataset)  # Returns number of samples
            >>> x, y = dataset[0]  # Gets first sample and label
        """
        self.download_url = download_url
        self.root_dir = Path(root_dir) if root_dir else Path.cwd() / "datasets"
        self.root_dir.mkdir(parents=True, exist_ok=True)

        # Auto-download if URL provided and data is empty
        if auto_download and download_url and (data is None or len(data) == 0):
            self._download_and_extract()

        self.data = data if data is not None else []
        self.labels = labels if labels is not None else []
        self.transform = transform

    @staticmethod
    def _raise_unsupported_format(message: str) -> None:
        """Raise ValueError for unsupported archive format.

        Args:
            message: Error message.

        Raises:
            ValueError: Always raised with the given message.
        """
        raise ValueError(message)

    def _download_and_extract(self) -> None:
        """Download and extract dataset if not already present.

        This method handles the complete download and extraction workflow:
        1. Extracts filename from the URL
        2. Checks if dataset is already extracted
        3. Downloads the file if not present
        4. Extracts the archive to the appropriate directory

        Supported formats:
            - .zip: ZIP archives
            - .tar.gz, .tgz: Gzipped TAR archives
            - .tar: TAR archives
            - .7z: Not supported (requires py7zr)

        Raises:
            RuntimeError: If download fails or extraction encounters an error.
            ValueError: If archive format is not supported.

        Note:
            Uses logging for informational messages instead of print statements
            for better integration with production environments.
        """
        if not self.download_url:
            return

        # Extract filename from URL
        filename = self.download_url.split("/")[-1]
        filepath = self.root_dir / filename
        extract_dir = self.root_dir / filename.rsplit(".", 1)[0]

        # Check if already extracted
        if extract_dir.exists():
            logger.info(f"Dataset already exists at {extract_dir}")
            return

        # Download if not present
        if not filepath.exists():
            logger.info(f"Downloading dataset from {self.download_url}...")
            try:
                urllib.request.urlretrieve(self.download_url, str(filepath))  # noqa: S310
                logger.info(f"Downloaded to {filepath}")
            except Exception as exc:
                msg = f"Failed to download dataset: {exc}"
                logger.exception(msg)
                raise RuntimeError(msg) from exc

        # Extract archive
        logger.info(f"Extracting {filename}...")
        try:
            if filename.endswith(".zip"):
                shutil.unpack_archive(str(filepath), str(extract_dir), "zip")
            elif filename.endswith((".tar.gz", ".tgz")):
                shutil.unpack_archive(str(filepath), str(extract_dir), "gztar")
            elif filename.endswith(".tar"):
                shutil.unpack_archive(str(filepath), str(extract_dir), "tar")
            elif filename.endswith(".7z"):
                self._raise_unsupported_format("7z format requires py7zr library")
            else:
                self._raise_unsupported_format(f"Unsupported archive format: {filename}")
            logger.info(f"Extracted to {extract_dir}")
        except Exception as exc:
            msg = f"Failed to extract dataset: {exc}"
            logger.exception(msg)
            raise RuntimeError(msg) from exc

    def __len__(self) -> int:
        """Return the number of samples in the dataset.

        Returns:
            int: Number of samples in the dataset.

        Example:
            >>> dataset = UniversalDataset(data=[1, 2, 3], labels=[0, 1, 0])
            >>> len(dataset)
            3
        """
        return len(self.data)

    def __getitem__(self, idx: int) -> tuple[Any, Any]:
        """Get a sample and its label by index.

        Retrieves the sample and label at the specified index and optionally
        applies the transform if configured.

        Args:
            idx: Index of the sample to retrieve.

        Returns:
            tuple: A tuple of (sample, label) where sample is potentially
                transformed by the configured transform callable.

        Raises:
            IndexError: If idx is out of bounds.

        Example:
            >>> dataset = UniversalDataset(data=[[1, 2], [3, 4]], labels=[0, 1])
            >>> sample, label = dataset[0]
            >>> sample
            [1, 2]
            >>> label
            0
        """
        x = self.data[idx]
        y = self.labels[idx]

        if self.transform:
            x = self.transform(x)

        return x, y
