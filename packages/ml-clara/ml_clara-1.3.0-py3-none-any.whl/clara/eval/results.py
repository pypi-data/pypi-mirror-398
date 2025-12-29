"""Evaluation results storage and display."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """Result from a single benchmark evaluation."""

    benchmark: str  # "perplexity", "hellaswag", "arc_easy"
    score: float  # Primary metric (PPL or accuracy)
    metric_name: str  # "perplexity" or "accuracy"
    num_samples: int
    correct: int | None = None  # For accuracy-based benchmarks
    total_tokens: int | None = None  # For perplexity
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class EvaluationReport:
    """Complete evaluation report."""

    model_name: str
    adapter_name: str | None
    timestamp: str
    results: list[BenchmarkResult] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def save(self, path: Path) -> None:
        """Save report to JSON file."""
        data = {
            "model_name": self.model_name,
            "adapter_name": self.adapter_name,
            "timestamp": self.timestamp,
            "config": self.config,
            "results": [r.to_dict() for r in self.results],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> EvaluationReport:
        """Load report from JSON file."""
        with open(path) as f:
            data = json.load(f)
        report = cls(
            model_name=data["model_name"],
            adapter_name=data.get("adapter_name"),
            timestamp=data["timestamp"],
            config=data.get("config", {}),
        )
        for r in data.get("results", []):
            report.results.append(BenchmarkResult(**r))
        return report

    @classmethod
    def create(
        cls,
        model_name: str,
        adapter_name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> EvaluationReport:
        """Create a new evaluation report."""
        return cls(
            model_name=model_name,
            adapter_name=adapter_name,
            timestamp=datetime.now().isoformat(),
            config=config or {},
        )


def print_results_table(report: EvaluationReport) -> None:
    """Print results as a formatted CLI table."""
    print()
    print("=" * 65)
    print(f" Model: {report.model_name}")
    if report.adapter_name:
        print(f" Adapter: {report.adapter_name}")
    print(f" Timestamp: {report.timestamp}")
    print("=" * 65)
    print()
    print(f"{'Benchmark':<15} {'Metric':<12} {'Score':>10} {'Samples':>10} {'Time':>10}")
    print("-" * 65)

    for result in report.results:
        if result.metric_name == "perplexity":
            score_str = f"{result.score:.2f}"
        else:
            score_str = f"{result.score:.1%}"

        time_str = f"{result.duration_seconds:.1f}s"

        print(
            f"{result.benchmark:<15} "
            f"{result.metric_name:<12} "
            f"{score_str:>10} "
            f"{result.num_samples:>10} "
            f"{time_str:>10}"
        )

    print("-" * 65)
    print()
