"""HellaSwag commonsense reasoning benchmark."""

from __future__ import annotations

import time
from typing import Any

import torch
from tqdm import tqdm

from ..utils.logging import get_logger
from .results import BenchmarkResult

logger = get_logger(__name__)


def evaluate_hellaswag(
    model: Any,
    tokenizer: Any,
    num_samples: int | None = None,
    batch_size: int = 1,
    device: torch.device | None = None,
    show_progress: bool = True,
) -> BenchmarkResult:
    """
    Evaluate model on HellaSwag benchmark.

    HellaSwag tests commonsense reasoning by asking the model
    to select the most plausible continuation of a scenario.

    Args:
        model: Language model
        tokenizer: Tokenizer
        num_samples: Limit number of samples (None = all)
        batch_size: Batch size (currently unused, single sample eval)
        device: Device for computation
        show_progress: Show progress bar

    Returns:
        BenchmarkResult with accuracy score
    """
    from datasets import load_dataset

    if device is None:
        device = next(model.parameters()).device

    # Get base tokenizer
    base_tokenizer = getattr(tokenizer, "base_tokenizer", tokenizer)

    logger.info("Loading HellaSwag dataset")
    dataset = load_dataset("Rowan/hellaswag", split="validation")

    if num_samples:
        dataset = dataset.select(range(min(num_samples, len(dataset))))

    model.eval()
    correct = 0
    total = 0

    start_time = time.time()
    iterator = tqdm(dataset, desc="HellaSwag", disable=not show_progress)

    with torch.no_grad():
        for example in iterator:
            # Get context and endings
            ctx = example["ctx"]
            endings = example["endings"]
            label = int(example["label"])

            # Score each ending
            scores = []
            for ending in endings:
                # Combine context and ending
                text = ctx + " " + ending

                # Tokenize
                inputs = base_tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                ).to(device)

                # Get loss (lower is better)
                outputs = model(**inputs, labels=inputs.input_ids)
                scores.append(-outputs.loss.item())  # Negate: higher = better

            # Prediction is highest scoring ending
            pred = scores.index(max(scores))

            if pred == label:
                correct += 1
            total += 1

            # Update progress bar
            iterator.set_postfix(acc=f"{correct/total:.1%}")

    elapsed = time.time() - start_time
    accuracy = correct / total if total > 0 else 0.0

    logger.info(f"HellaSwag accuracy: {accuracy:.1%} ({correct}/{total})")

    return BenchmarkResult(
        benchmark="hellaswag",
        score=accuracy,
        metric_name="accuracy",
        num_samples=total,
        correct=correct,
        duration_seconds=elapsed,
    )
