"""Tests for evaluation harness."""

import pytest
import torch


class TestBenchmarkResults:
    """Tests for BenchmarkResult dataclass."""

    def test_result_to_dict(self):
        """Test result serialization."""
        from clara.eval import BenchmarkResult

        result = BenchmarkResult(
            benchmark="perplexity",
            score=15.5,
            metric_name="perplexity",
            num_samples=100,
            metadata={"dataset": "wikitext"},
        )

        d = result.to_dict()
        assert d["benchmark"] == "perplexity"
        assert d["score"] == 15.5
        assert d["metric_name"] == "perplexity"
        assert d["num_samples"] == 100
        assert d["metadata"]["dataset"] == "wikitext"


class TestEvaluationReport:
    """Tests for EvaluationReport."""

    def test_empty_report(self):
        """Test empty report creation."""
        from clara.eval import EvaluationReport

        report = EvaluationReport.create(
            model_name="test-model",
            adapter_name=None,
        )

        assert report.model_name == "test-model"
        assert len(report.results) == 0

    def test_report_add_result(self):
        """Test adding results to report."""
        from clara.eval import BenchmarkResult, EvaluationReport

        report = EvaluationReport.create(
            model_name="mistral-7b",
            adapter_name="lora-v1",
        )

        result = BenchmarkResult(
            benchmark="ppl",
            score=10.0,
            metric_name="perplexity",
            num_samples=100,
        )

        report.add_result(result)
        assert len(report.results) == 1
        assert report.model_name == "mistral-7b"
        assert report.adapter_name == "lora-v1"
        assert report.timestamp is not None


class TestPerplexity:
    """Tests for perplexity computation."""

    def test_compute_perplexity_basic(self, device):
        """Test basic perplexity computation."""
        from clara.eval.perplexity import compute_perplexity

        # Create mock model with parameters
        class MockModel(torch.nn.Module):
            def __init__(self, dev):
                super().__init__()
                self.dummy = torch.nn.Parameter(torch.zeros(1, device=dev))

            def forward(self, input_ids, labels=None, **kwargs):
                # Return mock loss
                class Output:
                    loss = torch.tensor(2.0, device=input_ids.device)

                return Output()

        class MockTokenizer:
            pad_token_id = 0
            eos_token_id = 2

            def encode(self, text, **kwargs):
                return list(range(50))

            def __call__(self, text, **kwargs):
                class Encoding:
                    input_ids = torch.tensor([[1, 2, 3] * 20])

                return Encoding()

        model = MockModel(device)
        tokenizer = MockTokenizer()

        result = compute_perplexity(
            model, tokenizer, ["test text"], max_length=64, stride=32
        )
        assert result.score > 0
        assert result.benchmark == "perplexity"


class TestHarnessIntegration:
    """Integration tests for EvaluationHarness."""

    def test_harness_creation(self):
        """Test harness initialization."""
        from clara.eval import EvaluationHarness

        class MockModel:
            device = torch.device("cpu")

            def __call__(self, *args, **kwargs):
                class Output:
                    loss = torch.tensor(1.0)
                    logits = torch.randn(1, 10, 1000)

                return Output()

        class MockTokenizer:
            pad_token_id = 0
            eos_token_id = 2
            model_max_length = 512

            def encode(self, text, **kwargs):
                return [1, 2, 3, 4, 5]

            def __call__(self, texts, **kwargs):
                class Encoding:
                    input_ids = torch.tensor([[1, 2, 3, 4, 5]])

                    def to(self, device):
                        return self

                return Encoding()

        harness = EvaluationHarness(
            model=MockModel(),
            tokenizer=MockTokenizer(),
            model_name="test-model",
        )

        assert harness.model_name == "test-model"
        assert harness.adapter_name is None
