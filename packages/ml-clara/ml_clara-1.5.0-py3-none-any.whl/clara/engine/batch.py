"""Batch generation for improved throughput."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .inference import GenerationConfig, GenerationResult, InferenceEngine

logger = get_logger(__name__)


@dataclass
class BatchGenerationResult:
    """Results from batch generation."""

    results: list["GenerationResult"]
    total_tokens: int
    total_time: float
    tokens_per_second: float

    def __repr__(self) -> str:
        return (
            f"BatchGenerationResult("
            f"num_results={len(self.results)}, "
            f"total_tokens={self.total_tokens}, "
            f"tokens_per_second={self.tokens_per_second:.1f})"
        )


def generate_batch(
    engine: "InferenceEngine",
    prompts: list[str],
    config: "GenerationConfig | None" = None,
    show_progress: bool = True,
    **kwargs: Any,
) -> BatchGenerationResult:
    """
    Generate responses for multiple prompts.

    Currently processes sequentially with optimized KV cache reuse.
    Future versions may implement true batched generation with padding.

    Args:
        engine: InferenceEngine instance
        prompts: List of input prompts
        config: Generation configuration
        show_progress: Show progress bar
        **kwargs: Override config values

    Returns:
        BatchGenerationResult with all responses
    """
    from tqdm import tqdm

    from .inference import GenerationResult

    results: list[GenerationResult] = []
    total_tokens = 0
    start_time = time.time()

    iterator = tqdm(prompts, desc="Generating", disable=not show_progress)

    for prompt in iterator:
        result = engine.generate(prompt, config, **kwargs)
        results.append(result)
        total_tokens += result.num_tokens

        # Update progress bar
        elapsed = time.time() - start_time
        tps = total_tokens / elapsed if elapsed > 0 else 0
        iterator.set_postfix(tokens=total_tokens, tps=f"{tps:.1f}")

    elapsed = time.time() - start_time

    logger.info(
        f"Batch generation complete: {len(prompts)} prompts, "
        f"{total_tokens} tokens, {total_tokens/elapsed:.1f} tok/s"
    )

    return BatchGenerationResult(
        results=results,
        total_tokens=total_tokens,
        total_time=elapsed,
        tokens_per_second=total_tokens / elapsed if elapsed > 0 else 0,
    )
