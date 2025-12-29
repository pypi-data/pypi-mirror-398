"""Unified evaluation harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from ..utils.logging import get_logger
from .arc import evaluate_arc
from .hellaswag import evaluate_hellaswag
from .perplexity import evaluate_perplexity_dataset
from .results import BenchmarkResult, EvaluationReport, print_results_table

logger = get_logger(__name__)


BenchmarkName = Literal["perplexity", "hellaswag", "arc_easy", "arc_challenge", "all"]


class EvaluationHarness:
    """
    Unified evaluation harness for running benchmarks.

    Usage:
        harness = EvaluationHarness(model, tokenizer)
        report = harness.run(["perplexity", "hellaswag", "arc_easy"])
        harness.print_results()
        harness.save("results/eval.json")
    """

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        model_name: str = "unknown",
        adapter_name: str | None = None,
    ):
        """
        Initialize evaluation harness.

        Args:
            model: Language model
            tokenizer: Tokenizer
            model_name: Name for reporting
            adapter_name: Adapter name if using one
        """
        self.model = model
        self.tokenizer = tokenizer
        self.model_name = model_name
        self.adapter_name = adapter_name
        self.report: EvaluationReport | None = None

    def run(
        self,
        benchmarks: list[BenchmarkName] | BenchmarkName = "all",
        num_samples: int | None = None,
        show_progress: bool = True,
        **kwargs,
    ) -> EvaluationReport:
        """
        Run specified benchmarks.

        Args:
            benchmarks: List of benchmark names or "all"
            num_samples: Limit samples per benchmark
            show_progress: Show progress bars
            **kwargs: Additional benchmark-specific args

        Returns:
            EvaluationReport with all results
        """
        if benchmarks == "all":
            benchmarks = ["perplexity", "hellaswag", "arc_easy"]
        elif isinstance(benchmarks, str):
            benchmarks = [benchmarks]

        self.report = EvaluationReport.create(
            model_name=self.model_name,
            adapter_name=self.adapter_name,
            config={"benchmarks": benchmarks, "num_samples": num_samples},
        )

        for benchmark in benchmarks:
            logger.info(f"Running benchmark: {benchmark}")
            result = self._run_benchmark(
                benchmark,
                num_samples=num_samples,
                show_progress=show_progress,
                **kwargs,
            )
            self.report.add_result(result)

        return self.report

    def _run_benchmark(
        self,
        name: str,
        num_samples: int | None = None,
        show_progress: bool = True,
        **kwargs,
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        if name == "perplexity":
            return evaluate_perplexity_dataset(
                self.model,
                self.tokenizer,
                num_samples=num_samples,
                show_progress=show_progress,
                **kwargs,
            )
        elif name == "hellaswag":
            return evaluate_hellaswag(
                self.model,
                self.tokenizer,
                num_samples=num_samples,
                show_progress=show_progress,
            )
        elif name == "arc_easy":
            return evaluate_arc(
                self.model,
                self.tokenizer,
                difficulty="easy",
                num_samples=num_samples,
                show_progress=show_progress,
            )
        elif name == "arc_challenge":
            return evaluate_arc(
                self.model,
                self.tokenizer,
                difficulty="challenge",
                num_samples=num_samples,
                show_progress=show_progress,
            )
        else:
            raise ValueError(f"Unknown benchmark: {name}")

    def print_results(self) -> None:
        """Print results table to console."""
        if self.report:
            print_results_table(self.report)

    def save(self, path: str | Path) -> None:
        """Save results to JSON file."""
        if self.report:
            self.report.save(Path(path))
            logger.info(f"Results saved to: {path}")

    def get_results(self) -> dict[str, float]:
        """Get results as simple dict."""
        if not self.report:
            return {}
        return {r.benchmark: r.score for r in self.report.results}
