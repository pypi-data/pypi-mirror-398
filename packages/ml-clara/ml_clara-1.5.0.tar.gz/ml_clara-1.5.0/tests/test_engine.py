"""Tests for inference engine."""

import pytest
import torch


class TestGenerationConfig:
    """Tests for GenerationConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        from clara import GenerationConfig

        config = GenerationConfig()

        # Match actual defaults from inference.py
        assert config.max_new_tokens == 512
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 50
        assert config.do_sample is True

    def test_custom_config(self):
        """Test custom configuration."""
        from clara import GenerationConfig

        config = GenerationConfig(
            max_new_tokens=128,
            temperature=0.5,
            top_p=0.8,
            top_k=40,
        )

        assert config.max_new_tokens == 128
        assert config.temperature == 0.5
        assert config.top_p == 0.8
        assert config.top_k == 40

    def test_greedy_config(self):
        """Test greedy decoding configuration."""
        from clara import GenerationConfig

        config = GenerationConfig(
            temperature=0.0,
            do_sample=False,
        )

        assert config.temperature == 0.0
        assert config.do_sample is False

    def test_invalid_temperature(self):
        """Test that negative temperature raises error."""
        from clara import GenerationConfig

        with pytest.raises(ValueError, match="temperature"):
            GenerationConfig(temperature=-0.5)

    def test_invalid_top_p(self):
        """Test that invalid top_p raises error."""
        from clara import GenerationConfig

        with pytest.raises(ValueError, match="top_p"):
            GenerationConfig(top_p=1.5)


class TestGenerationResult:
    """Tests for GenerationResult."""

    def test_result_properties(self):
        """Test result properties."""
        from clara.engine import GenerationResult

        result = GenerationResult(
            text="Hello, world!",
            tokens=[1, 2, 3],
            num_tokens=3,
            stop_reason="eos",
            generation_time=0.5,
            tokens_per_second=6.0,
        )

        assert result.text == "Hello, world!"
        assert result.tokens == [1, 2, 3]
        assert result.num_tokens == 3
        assert result.stop_reason == "eos"
        assert result.tokens_per_second == 6.0


class TestBatchGeneration:
    """Tests for batch generation."""

    def test_batch_result_properties(self):
        """Test BatchGenerationResult properties."""
        from clara.engine import BatchGenerationResult, GenerationResult

        results = [
            GenerationResult("a", [1], 10, "eos", 1.0, 10.0),
            GenerationResult("b", [2], 20, "eos", 2.0, 10.0),
        ]

        batch = BatchGenerationResult(
            results=results,
            total_tokens=30,
            total_time=3.0,
            tokens_per_second=10.0,
        )

        assert len(batch.results) == 2
        assert batch.total_tokens == 30
        assert batch.tokens_per_second == 10.0

    def test_batch_iteration(self):
        """Test iterating over batch results."""
        from clara.engine import BatchGenerationResult, GenerationResult

        results = [
            GenerationResult("a", [1], 5, "eos", 0.5, 10.0),
            GenerationResult("b", [2], 5, "eos", 0.5, 10.0),
        ]

        batch = BatchGenerationResult(
            results=results,
            total_tokens=10,
            total_time=1.0,
            tokens_per_second=10.0,
        )

        texts = [r.text for r in batch.results]
        assert texts == ["a", "b"]


class TestMemoryManagement:
    """Tests for memory utilities."""

    def test_get_memory_stats(self, device):
        """Test memory stats retrieval."""
        from clara.utils.memory import get_memory_stats

        stats = get_memory_stats(device)

        assert hasattr(stats, "allocated_mb")
        assert hasattr(stats, "reserved_mb")
        assert hasattr(stats, "max_allocated_mb")
        assert stats.allocated_mb >= 0

    def test_clear_memory(self, device):
        """Test memory clearing."""
        from clara.utils.memory import clear_memory

        # Should not raise
        clear_memory(device)

    def test_memory_stats_cpu(self):
        """Test memory stats on CPU."""
        from clara.utils.memory import get_memory_stats

        stats = get_memory_stats(torch.device("cpu"))

        # CPU reports system memory or zero depending on implementation
        assert stats.allocated_mb >= 0
        assert stats.device == "cpu"


class TestEngineFactory:
    def test_load_engine_selects_gguf_for_gguf_file(self, tmp_path, monkeypatch):
        from pathlib import Path

        from clara.engine import factory

        gguf_path = tmp_path / "dummy.gguf"
        gguf_path.write_bytes(b"GGUF")

        class _DummyGGUFEngine:
            def __init__(self, cfg, **kwargs):
                self.cfg = cfg

        monkeypatch.setattr(factory, "GGUFEngine", _DummyGGUFEngine)

        loaded = factory.load_engine({"model": {"local_path": str(gguf_path)}})
        assert loaded.backend == "gguf"
        assert Path(loaded.model_path) == gguf_path
        assert loaded.adapter_name is None

    def test_load_engine_gguf_checksum_mismatch(self, tmp_path, monkeypatch):
        from clara.engine import factory
        from clara.models.exceptions import ChecksumMismatchError
        from clara.utils.checksums import sha256_file

        gguf_path = tmp_path / "dummy.gguf"
        gguf_path.write_bytes(b"GGUF")

        class _DummyGGUFEngine:
            def __init__(self, cfg, **kwargs):
                self.cfg = cfg

        monkeypatch.setattr(factory, "GGUFEngine", _DummyGGUFEngine)

        good = sha256_file(gguf_path)
        loaded = factory.load_engine({"model": {"local_path": str(gguf_path), "sha256": good}})
        assert loaded.backend == "gguf"

        with pytest.raises(ChecksumMismatchError):
            factory.load_engine({"model": {"local_path": str(gguf_path), "sha256": "0" * 64}})


class TestChecksums:
    def test_verify_local_model_checksums_file(self, tmp_path):
        from clara.models.exceptions import ChecksumMismatchError
        from clara.utils.checksums import sha256_file, verify_local_model_checksums

        p = tmp_path / "file.gguf"
        p.write_bytes(b"abc")
        good = sha256_file(p)

        verify_local_model_checksums(p, {"sha256": good})
        with pytest.raises(ChecksumMismatchError):
            verify_local_model_checksums(p, {"sha256": "f" * 64})

    def test_verify_local_model_checksums_dir(self, tmp_path):
        from clara.models.exceptions import ChecksumMismatchError
        from clara.utils.checksums import sha256_file, verify_local_model_checksums

        d = tmp_path / "model_dir"
        d.mkdir()
        cfg = d / "config.json"
        cfg.write_text('{"test": true}')
        good = sha256_file(cfg)

        verify_local_model_checksums(d, {"sha256": {"config.json": good}})
        with pytest.raises(ChecksumMismatchError):
            verify_local_model_checksums(d, {"sha256": {"config.json": "0" * 64}})
