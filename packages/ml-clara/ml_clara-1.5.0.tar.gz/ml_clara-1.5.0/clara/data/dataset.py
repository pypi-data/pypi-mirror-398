"""Dataset loading and preprocessing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetConfig:
    """Dataset configuration."""

    path: str  # HF dataset name or local path
    split: str = "train"
    text_field: str = "text"  # Field containing text
    max_samples: int | None = None
    streaming: bool = False

    # For instruction datasets
    instruction_field: str | None = None
    input_field: str | None = None
    output_field: str | None = None

    # Chat template
    apply_chat_template: bool = False


class FinetuneDataset(Dataset):
    """
    Dataset for fine-tuning.

    Supports:
    - Plain text (completion training)
    - Instruction format (instruction/input/output)
    - Chat format (messages array)
    """

    def __init__(
        self,
        data: list[dict[str, Any]],
        tokenizer: Any,
        max_length: int = 2048,
        config: DatasetConfig | None = None,
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.config = config or DatasetConfig(path="")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        item = self.data[idx]
        text = self._format_example(item)

        # Get base tokenizer if wrapped
        base_tokenizer = getattr(self.tokenizer, "base_tokenizer", self.tokenizer)

        # Tokenize
        encoding = base_tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None,
        )

        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": encoding["input_ids"].copy(),  # For causal LM
        }

    def _format_example(self, item: dict[str, Any]) -> str:
        """Format a single example based on config."""
        cfg = self.config

        # Plain text
        if cfg.text_field in item:
            return item[cfg.text_field]

        # Instruction format
        if cfg.instruction_field and cfg.instruction_field in item:
            instruction = item[cfg.instruction_field]
            inp = item.get(cfg.input_field, "") if cfg.input_field else ""
            output = item.get(cfg.output_field, "") if cfg.output_field else ""

            if inp:
                return f"### Instruction:\n{instruction}\n\n### Input:\n{inp}\n\n### Response:\n{output}"
            else:
                return f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

        # Fallback: concatenate all string fields
        parts = [str(v) for v in item.values() if isinstance(v, str)]
        return " ".join(parts)


def load_dataset(
    config: DatasetConfig,
    tokenizer: Any,
    max_length: int = 2048,
) -> FinetuneDataset:
    """
    Load dataset from HuggingFace or local path.

    Args:
        config: Dataset configuration
        tokenizer: Tokenizer for preprocessing
        max_length: Maximum sequence length

    Returns:
        FinetuneDataset ready for training
    """
    from datasets import load_dataset as hf_load_dataset

    path = Path(config.path)

    if path.exists():
        # Local file
        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
        elif path.suffix == ".jsonl":
            data = []
            with open(path) as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    else:
        # HuggingFace dataset
        ds = hf_load_dataset(
            config.path,
            split=config.split,
            streaming=config.streaming,
        )

        if config.max_samples and not config.streaming:
            ds = ds.select(range(min(config.max_samples, len(ds))))

        data = list(ds)

    logger.info(f"Loaded {len(data)} examples from {config.path}")

    return FinetuneDataset(
        data=data,
        tokenizer=tokenizer,
        max_length=max_length,
        config=config,
    )


def prepare_dataset(
    dataset: FinetuneDataset,
    val_split: float = 0.1,
    seed: int = 42,
) -> tuple[FinetuneDataset, FinetuneDataset | None]:
    """
    Split dataset into train/val.

    Args:
        dataset: Full dataset
        val_split: Validation split ratio
        seed: Random seed

    Returns:
        (train_dataset, val_dataset) tuple
    """
    if val_split <= 0:
        return dataset, None

    import random

    random.seed(seed)

    indices = list(range(len(dataset)))
    random.shuffle(indices)

    split_idx = int(len(indices) * (1 - val_split))
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]

    train_data = [dataset.data[i] for i in train_indices]
    val_data = [dataset.data[i] for i in val_indices]

    train_ds = FinetuneDataset(
        data=train_data,
        tokenizer=dataset.tokenizer,
        max_length=dataset.max_length,
        config=dataset.config,
    )

    val_ds = FinetuneDataset(
        data=val_data,
        tokenizer=dataset.tokenizer,
        max_length=dataset.max_length,
        config=dataset.config,
    )

    logger.info(f"Split: {len(train_ds)} train, {len(val_ds)} val")

    return train_ds, val_ds
