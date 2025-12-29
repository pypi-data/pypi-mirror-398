"""Data collator for causal language modeling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch


@dataclass
class DataCollatorForCausalLM:
    """
    Data collator for causal LM training.

    Handles padding and label masking.
    """

    tokenizer: Any
    max_length: int = 2048
    pad_to_multiple_of: int | None = 8
    label_pad_token_id: int = -100

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        """Collate batch of features."""
        # Find max length in batch
        max_len = max(len(f["input_ids"]) for f in features)

        # Round up to multiple
        if self.pad_to_multiple_of:
            max_len = (
                (max_len + self.pad_to_multiple_of - 1)
                // self.pad_to_multiple_of
                * self.pad_to_multiple_of
            )

        max_len = min(max_len, self.max_length)

        batch = {
            "input_ids": [],
            "attention_mask": [],
            "labels": [],
        }

        # Get pad token
        base_tokenizer = getattr(self.tokenizer, "base_tokenizer", self.tokenizer)
        pad_token_id = getattr(base_tokenizer, "pad_token_id", None)
        if pad_token_id is None:
            pad_token_id = getattr(base_tokenizer, "eos_token_id", 0)

        for feature in features:
            input_ids = feature["input_ids"][:max_len]
            attention_mask = feature["attention_mask"][:max_len]
            labels = feature["labels"][:max_len]

            # Pad
            pad_len = max_len - len(input_ids)

            input_ids = list(input_ids) + [pad_token_id] * pad_len
            attention_mask = list(attention_mask) + [0] * pad_len
            labels = list(labels) + [self.label_pad_token_id] * pad_len

            batch["input_ids"].append(input_ids)
            batch["attention_mask"].append(attention_mask)
            batch["labels"].append(labels)

        return {k: torch.tensor(v, dtype=torch.long) for k, v in batch.items()}
