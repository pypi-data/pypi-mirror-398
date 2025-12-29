"""
Evaluation toolkit for ML-Clara.

Provides:
- Perplexity evaluation
- HellaSwag benchmark
- ARC-Easy benchmark
- Unified evaluation harness

Usage:
    from clara.eval import EvaluationHarness

    harness = EvaluationHarness(model, tokenizer, model_name="Mistral-7B")
    report = harness.run(["perplexity", "hellaswag", "arc_easy"])
    harness.print_results()
    harness.save("results/eval.json")
"""

from .arc import evaluate_arc
from .harness import EvaluationHarness
from .hellaswag import evaluate_hellaswag
from .perplexity import compute_perplexity, evaluate_perplexity_dataset
from .results import BenchmarkResult, EvaluationReport, print_results_table

__all__ = [
    # Results
    "BenchmarkResult",
    "EvaluationReport",
    "print_results_table",
    # Benchmarks
    "compute_perplexity",
    "evaluate_perplexity_dataset",
    "evaluate_hellaswag",
    "evaluate_arc",
    # Harness
    "EvaluationHarness",
]
