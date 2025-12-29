"""ARC (AI2 Reasoning Challenge) benchmark."""

from __future__ import annotations

import time
from typing import Any

import torch
from tqdm import tqdm

from ..utils.logging import get_logger
from .results import BenchmarkResult

logger = get_logger(__name__)


def evaluate_arc(
    model: Any,
    tokenizer: Any,
    difficulty: str = "easy",
    num_samples: int | None = None,
    device: torch.device | None = None,
    show_progress: bool = True,
) -> BenchmarkResult:
    """
    Evaluate model on ARC benchmark.

    ARC tests basic reasoning and science knowledge through
    multiple choice questions.

    Args:
        model: Language model
        tokenizer: Tokenizer
        difficulty: "easy" or "challenge"
        num_samples: Limit number of samples
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

    # Load appropriate split
    config = "ARC-Easy" if difficulty == "easy" else "ARC-Challenge"
    logger.info(f"Loading ARC dataset: {config}")
    dataset = load_dataset("allenai/ai2_arc", config, split="test")

    if num_samples:
        dataset = dataset.select(range(min(num_samples, len(dataset))))

    model.eval()
    correct = 0
    total = 0

    start_time = time.time()
    iterator = tqdm(
        dataset, desc=f"ARC-{difficulty.title()}", disable=not show_progress
    )

    with torch.no_grad():
        for example in iterator:
            question = example["question"]
            choices = example["choices"]
            answer_key = example["answerKey"]

            # Map answer key to index
            labels = choices["label"]
            texts = choices["text"]

            try:
                answer_idx = labels.index(answer_key)
            except ValueError:
                # Some answers are numeric
                answer_idx = int(answer_key) - 1 if answer_key.isdigit() else 0

            # Score each choice
            scores = []
            for choice_text in texts:
                # Format as Q&A
                prompt = f"Question: {question}\nAnswer: {choice_text}"

                inputs = base_tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                ).to(device)

                outputs = model(**inputs, labels=inputs.input_ids)
                scores.append(-outputs.loss.item())

            # Prediction is highest scoring choice
            pred = scores.index(max(scores))

            if pred == answer_idx:
                correct += 1
            total += 1

            iterator.set_postfix(acc=f"{correct/total:.1%}")

    elapsed = time.time() - start_time
    accuracy = correct / total if total > 0 else 0.0

    benchmark_name = f"arc_{difficulty}"
    logger.info(f"ARC-{difficulty.title()} accuracy: {accuracy:.1%} ({correct}/{total})")

    return BenchmarkResult(
        benchmark=benchmark_name,
        score=accuracy,
        metric_name="accuracy",
        num_samples=total,
        correct=correct,
        duration_seconds=elapsed,
    )
