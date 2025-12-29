"""Perplexity evaluation."""

from __future__ import annotations

import time
from typing import Any, Iterator

import torch
from tqdm import tqdm

from ..utils.logging import get_logger
from .results import BenchmarkResult

logger = get_logger(__name__)


def compute_perplexity(
    model: Any,
    tokenizer: Any,
    texts: list[str] | Iterator[str],
    batch_size: int = 1,
    max_length: int = 512,
    stride: int = 256,
    device: torch.device | None = None,
    show_progress: bool = True,
) -> BenchmarkResult:
    """
    Compute perplexity on a list of texts.

    Uses sliding window approach for long sequences.

    Args:
        model: Language model
        tokenizer: Tokenizer (or TokenizerWrapper)
        texts: Input texts
        batch_size: Batch size for evaluation
        max_length: Maximum sequence length per chunk
        stride: Stride for sliding window
        device: Device for computation
        show_progress: Show progress bar

    Returns:
        BenchmarkResult with perplexity score
    """
    if device is None:
        device = next(model.parameters()).device

    # Get base tokenizer if wrapped
    base_tokenizer = getattr(tokenizer, "base_tokenizer", tokenizer)

    model.eval()
    total_loss = 0.0
    total_tokens = 0
    num_samples = 0

    start_time = time.time()

    # Convert to list if iterator
    if not isinstance(texts, list):
        texts = list(texts)

    iterator = tqdm(texts, desc="Perplexity", disable=not show_progress)

    with torch.no_grad():
        for text in iterator:
            if not text.strip():
                continue

            # Tokenize
            encodings = base_tokenizer(
                text,
                return_tensors="pt",
                truncation=False,
                padding=False,
            )
            input_ids = encodings.input_ids.to(device)
            seq_len = input_ids.size(1)

            if seq_len == 0:
                continue

            # Sliding window for long sequences
            prev_end = 0
            for begin in range(0, seq_len, stride):
                end = min(begin + max_length, seq_len)
                trg_len = end - prev_end  # Tokens to score

                input_chunk = input_ids[:, begin:end]
                target_chunk = input_chunk.clone()

                # Only compute loss on new tokens (after stride)
                if begin > 0:
                    target_chunk[:, :-trg_len] = -100

                outputs = model(input_chunk, labels=target_chunk)
                loss = outputs.loss

                # Accumulate
                total_loss += loss.item() * trg_len
                total_tokens += trg_len

                prev_end = end
                if end == seq_len:
                    break

            num_samples += 1

    elapsed = time.time() - start_time

    if total_tokens == 0:
        perplexity = float("inf")
    else:
        perplexity = torch.exp(torch.tensor(total_loss / total_tokens)).item()

    logger.info(f"Perplexity: {perplexity:.2f} ({total_tokens} tokens)")

    return BenchmarkResult(
        benchmark="perplexity",
        score=perplexity,
        metric_name="perplexity",
        num_samples=num_samples,
        total_tokens=total_tokens,
        duration_seconds=elapsed,
    )


def evaluate_perplexity_dataset(
    model: Any,
    tokenizer: Any,
    dataset_name: str = "wikitext",
    dataset_config: str = "wikitext-2-raw-v1",
    split: str = "test",
    num_samples: int | None = None,
    **kwargs,
) -> BenchmarkResult:
    """
    Evaluate perplexity on a HuggingFace dataset.

    Args:
        model: Language model
        tokenizer: Tokenizer
        dataset_name: HuggingFace dataset name
        dataset_config: Dataset configuration
        split: Dataset split
        num_samples: Limit number of samples
        **kwargs: Additional args for compute_perplexity

    Returns:
        BenchmarkResult
    """
    from datasets import load_dataset

    logger.info(f"Loading dataset: {dataset_name}/{dataset_config}")
    dataset = load_dataset(dataset_name, dataset_config, split=split)

    # Extract text field
    if "text" in dataset.column_names:
        texts = dataset["text"]
    elif "content" in dataset.column_names:
        texts = dataset["content"]
    else:
        raise ValueError(f"No text column found in dataset: {dataset.column_names}")

    # Filter empty strings
    texts = [t for t in texts if t.strip()]

    if num_samples:
        texts = texts[:num_samples]

    return compute_perplexity(model, tokenizer, texts, **kwargs)
