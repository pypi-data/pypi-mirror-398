"""Text/LLM Dataset Loader für Language Modeling.

Unterstützt verschiedene Text-Datasets für Pre-Training und Fine-Tuning
von Language Models wie GPT und DeepSeek-V3.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pytorch_lightning import LightningDataModule
import torch
from torch.utils.data import DataLoader, Dataset

if TYPE_CHECKING:
    from deepsuite.typing import Tensor


class TextDataset(Dataset):
    """Dataset für Language Modeling mit Tokenization.

    Unterstützt verschiedene Formate:
    - Raw text files (.txt)
    - JSONL files ({"text": "..."})
    - Pre-tokenized files (.pt)

    Args:
        data_path: Path zu Daten (file oder directory).
        tokenizer: Tokenizer mit encode/decode methods.
        max_seq_len: Maximale Sequenzlänge. Defaults to 512.
        stride: Sliding window stride für lange Texte. Defaults to 256.
        return_mtp: Return Multi-Token Prediction targets. Defaults to False.
        mtp_depth: MTP lookahead depth. Defaults to 1.

    Examples:
        >>> from tokenizers import Tokenizer
        >>> tokenizer = Tokenizer.from_file("tokenizer.json")
        >>> dataset = TextDataset(
        ...     data_path="data/train.txt",
        ...     tokenizer=tokenizer,
        ...     max_seq_len=512,
        ... )
        >>> sample = dataset[0]
        >>> print(sample["input_ids"].shape)
        torch.Size([512])
    """

    def __init__(
        self,
        data_path: str | Path,
        tokenizer: Any,
        max_seq_len: int = 512,
        stride: int | None = None,
        return_mtp: bool = False,
        mtp_depth: int = 1,
    ) -> None:
        """Initialize text dataset."""
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.stride = stride or max_seq_len
        self.return_mtp = return_mtp
        self.mtp_depth = mtp_depth

        # Load data
        self.samples: list[dict[str, Tensor]] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load and tokenize data."""
        if self.data_path.is_file():
            if self.data_path.suffix == ".txt":
                self._load_txt_file(self.data_path)
            elif self.data_path.suffix == ".jsonl":
                self._load_jsonl_file(self.data_path)
            elif self.data_path.suffix == ".pt":
                self._load_pt_file(self.data_path)
            else:
                msg = f"Unsupported file format: {self.data_path.suffix}"
                raise ValueError(msg)
        elif self.data_path.is_dir():
            # Load all files in directory
            for txt_file in self.data_path.glob("*.txt"):
                self._load_txt_file(txt_file)
            for jsonl_file in self.data_path.glob("*.jsonl"):
                self._load_jsonl_file(jsonl_file)
            for pt_file in self.data_path.glob("*.pt"):
                self._load_pt_file(pt_file)
        else:
            msg = f"Path not found: {self.data_path}"
            raise ValueError(msg)

    def _load_txt_file(self, path: Path) -> None:
        """Load raw text file and tokenize."""
        with path.open(encoding="utf-8") as f:
            text = f.read()

        # Tokenize
        if hasattr(self.tokenizer, "encode"):
            encoded = self.tokenizer.encode(text)
            # Check if result has .ids attribute (HuggingFace tokenizers)
            if hasattr(encoded, "ids"):
                token_ids = encoded.ids
            else:
                # Direct list of IDs
                token_ids = encoded
        else:
            # Fallback: assume tokenizer is callable
            token_ids = self.tokenizer(text)

        # Split into chunks with sliding window
        self._create_samples_from_tokens(token_ids)

    def _load_jsonl_file(self, path: Path) -> None:
        """Load JSONL file (one JSON per line)."""
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    text = data.get("text", "")

                    if hasattr(self.tokenizer, "encode"):
                        encoded = self.tokenizer.encode(text)
                        if hasattr(encoded, "ids"):
                            token_ids = encoded.ids
                        else:
                            token_ids = encoded
                    else:
                        token_ids = self.tokenizer(text)

                    self._create_samples_from_tokens(token_ids)

    def _load_pt_file(self, path: Path) -> None:
        """Load pre-tokenized PyTorch tensor file."""
        token_ids = torch.load(path, weights_only=True)
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()
        self._create_samples_from_tokens(token_ids)

    def _create_samples_from_tokens(self, token_ids: list[int]) -> None:
        """Create samples from token IDs using sliding window.

        Args:
            token_ids: List of token IDs.
        """
        # Need at least max_seq_len + 1 tokens (input + target)
        if len(token_ids) < self.max_seq_len + 1:
            # Pad if too short
            token_ids = token_ids + [0] * (self.max_seq_len + 1 - len(token_ids))

        # Sliding window
        for i in range(0, len(token_ids) - self.max_seq_len, self.stride):
            # Input: [i : i + max_seq_len]
            # Target: [i+1 : i + max_seq_len + 1]
            input_ids = token_ids[i : i + self.max_seq_len]
            labels = token_ids[i + 1 : i + self.max_seq_len + 1]

            sample = {
                "input_ids": torch.tensor(input_ids, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long),
            }

            # Multi-Token Prediction targets
            if self.return_mtp:
                mtp_labels = []
                for d in range(1, self.mtp_depth + 1):
                    # Lookahead d positions
                    end_idx = min(i + self.max_seq_len + d + 1, len(token_ids))
                    mtp_target = token_ids[i + d + 1 : end_idx]

                    # Pad to max_seq_len
                    if len(mtp_target) < self.max_seq_len:
                        mtp_target = mtp_target + [0] * (self.max_seq_len - len(mtp_target))

                    mtp_labels.append(mtp_target)

                # Stack: (mtp_depth, max_seq_len)
                sample["mtp_labels"] = torch.tensor(mtp_labels, dtype=torch.long)

            self.samples.append(sample)

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Tensor]:
        """Get sample by index.

        Args:
            idx: Sample index.

        Returns:
            Dict with:
                - input_ids: (max_seq_len,)
                - labels: (max_seq_len,)
                - mtp_labels: (mtp_depth, max_seq_len) [optional]
        """
        return self.samples[idx]


class TextDataLoader(LightningDataModule):
    """LightningDataModule für Text/LLM Datasets.

    Lädt Train/Val/Test Datasets für Language Modeling.

    Args:
        train_data_path: Path zu Training Daten.
        val_data_path: Path zu Validation Daten. Defaults to None.
        test_data_path: Path zu Test Daten. Defaults to None.
        tokenizer: Tokenizer mit encode/decode methods.
        max_seq_len: Maximale Sequenzlänge. Defaults to 512.
        batch_size: Batch size. Defaults to 32.
        num_workers: DataLoader workers. Defaults to 4.
        stride: Sliding window stride. Defaults to None (=max_seq_len).
        return_mtp: Return MTP targets. Defaults to False.
        mtp_depth: MTP lookahead depth. Defaults to 1.

    Examples:
        >>> from tokenizers import Tokenizer
        >>> tokenizer = Tokenizer.from_file("tokenizer.json")
        >>> datamodule = TextDataLoader(
        ...     train_data_path="data/train.txt",
        ...     val_data_path="data/val.txt",
        ...     tokenizer=tokenizer,
        ...     max_seq_len=512,
        ...     batch_size=32,
        ... )
        >>> datamodule.setup()
        >>> train_loader = datamodule.train_dataloader()
    """

    def __init__(
        self,
        train_data_path: str | Path,
        val_data_path: str | Path | None = None,
        test_data_path: str | Path | None = None,
        tokenizer: Any | None = None,
        max_seq_len: int = 512,
        batch_size: int = 32,
        num_workers: int = 4,
        stride: int | None = None,
        return_mtp: bool = False,
        mtp_depth: int = 1,
    ) -> None:
        """Initialize text data loader."""
        super().__init__()
        self.train_data_path = train_data_path
        self.val_data_path = val_data_path
        self.test_data_path = test_data_path
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.stride = stride
        self.return_mtp = return_mtp
        self.mtp_depth = mtp_depth

        self.train_dataset: TextDataset | None = None
        self.val_dataset: TextDataset | None = None
        self.test_dataset: TextDataset | None = None

    def setup(self, stage: str | None = None) -> None:
        """Setup datasets.

        Args:
            stage: 'fit', 'validate', 'test', or 'predict'. Defaults to None.
        """
        if self.tokenizer is None:
            msg = "Tokenizer required for TextDataLoader"
            raise ValueError(msg)

        if stage == "fit" or stage is None:
            # Training dataset
            self.train_dataset = TextDataset(
                data_path=self.train_data_path,
                tokenizer=self.tokenizer,
                max_seq_len=self.max_seq_len,
                stride=self.stride,
                return_mtp=self.return_mtp,
                mtp_depth=self.mtp_depth,
            )

            # Validation dataset
            if self.val_data_path is not None:
                self.val_dataset = TextDataset(
                    data_path=self.val_data_path,
                    tokenizer=self.tokenizer,
                    max_seq_len=self.max_seq_len,
                    stride=self.max_seq_len,  # No overlap for validation
                    return_mtp=self.return_mtp,
                    mtp_depth=self.mtp_depth,
                )

        if stage == "test" and self.test_data_path is not None:
            self.test_dataset = TextDataset(
                data_path=self.test_data_path,
                tokenizer=self.tokenizer,
                max_seq_len=self.max_seq_len,
                stride=self.max_seq_len,
                return_mtp=self.return_mtp,
                mtp_depth=self.mtp_depth,
            )

    def train_dataloader(self) -> DataLoader:
        """Return training dataloader."""
        if self.train_dataset is None:
            msg = "Train dataset not initialized. Call setup() first."
            raise ValueError(msg)

        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def val_dataloader(self) -> DataLoader | None:
        """Return validation dataloader."""
        if self.val_dataset is None:
            return None

        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def test_dataloader(self) -> DataLoader | None:
        """Return test dataloader."""
        if self.test_dataset is None:
            return None

        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True,
        )
