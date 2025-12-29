"""Tests for dataset utilities."""

import json
import pytest
import torch


class TestDatasetConfig:
    """Tests for DatasetConfig."""

    def test_default_config(self):
        """Test default dataset config."""
        from clara.data import DatasetConfig

        config = DatasetConfig(path="test/path")
        assert config.path == "test/path"
        assert config.split == "train"
        assert config.text_field == "text"
        assert config.max_samples is None

    def test_instruction_config(self):
        """Test instruction dataset config."""
        from clara.data import DatasetConfig

        config = DatasetConfig(
            path="alpaca",
            instruction_field="instruction",
            input_field="input",
            output_field="output",
        )
        assert config.instruction_field == "instruction"
        assert config.output_field == "output"


class TestFinetuneDataset:
    """Tests for FinetuneDataset."""

    def test_plain_text_format(self):
        """Test plain text formatting."""
        from clara.data import DatasetConfig, FinetuneDataset

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {
                    "input_ids": list(range(len(text.split()))),
                    "attention_mask": [1] * len(text.split()),
                }

        data = [{"text": "Hello world"}, {"text": "Test input"}]
        config = DatasetConfig(path="", text_field="text")

        dataset = FinetuneDataset(
            data=data,
            tokenizer=MockTokenizer(),
            max_length=512,
            config=config,
        )

        assert len(dataset) == 2
        item = dataset[0]
        assert "input_ids" in item
        assert "attention_mask" in item
        assert "labels" in item

    def test_instruction_format(self):
        """Test instruction formatting."""
        from clara.data import DatasetConfig, FinetuneDataset

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {
                    "input_ids": list(range(10)),
                    "attention_mask": [1] * 10,
                }

        data = [
            {
                "instruction": "Summarize this",
                "input": "Long text here",
                "output": "Short summary",
            }
        ]

        config = DatasetConfig(
            path="",
            instruction_field="instruction",
            input_field="input",
            output_field="output",
        )

        dataset = FinetuneDataset(
            data=data,
            tokenizer=MockTokenizer(),
            max_length=512,
            config=config,
        )

        # Check that formatting includes instruction markers
        text = dataset._format_example(data[0])
        assert "### Instruction:" in text
        assert "### Input:" in text
        assert "### Response:" in text


class TestDataCollator:
    """Tests for DataCollatorForCausalLM."""

    def test_collation(self):
        """Test batch collation."""
        from clara.data import DataCollatorForCausalLM

        class MockTokenizer:
            pad_token_id = 0
            eos_token_id = 2

        collator = DataCollatorForCausalLM(
            tokenizer=MockTokenizer(),
            max_length=512,
            pad_to_multiple_of=8,
        )

        features = [
            {"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1], "labels": [1, 2, 3]},
            {
                "input_ids": [1, 2, 3, 4, 5],
                "attention_mask": [1, 1, 1, 1, 1],
                "labels": [1, 2, 3, 4, 5],
            },
        ]

        batch = collator(features)

        assert batch["input_ids"].shape[0] == 2
        assert batch["input_ids"].shape[1] == 8  # Padded to multiple of 8
        assert batch["attention_mask"].shape == batch["input_ids"].shape
        assert batch["labels"].shape == batch["input_ids"].shape

    def test_label_padding(self):
        """Test that labels are padded with -100."""
        from clara.data import DataCollatorForCausalLM

        class MockTokenizer:
            pad_token_id = 0

        collator = DataCollatorForCausalLM(
            tokenizer=MockTokenizer(),
            max_length=512,
            pad_to_multiple_of=None,
        )

        features = [
            {"input_ids": [1, 2], "attention_mask": [1, 1], "labels": [1, 2]},
            {"input_ids": [1, 2, 3, 4], "attention_mask": [1, 1, 1, 1], "labels": [1, 2, 3, 4]},
        ]

        batch = collator(features)

        # First sequence should have -100 padding in labels
        assert batch["labels"][0, 2].item() == -100
        assert batch["labels"][0, 3].item() == -100


class TestPrepareDataset:
    """Tests for prepare_dataset."""

    def test_split(self):
        """Test train/val split."""
        from clara.data import DatasetConfig, FinetuneDataset, prepare_dataset

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}

        data = [{"text": f"example {i}"} for i in range(100)]
        config = DatasetConfig(path="")

        dataset = FinetuneDataset(
            data=data,
            tokenizer=MockTokenizer(),
            max_length=512,
            config=config,
        )

        train_ds, val_ds = prepare_dataset(dataset, val_split=0.2, seed=42)

        assert len(train_ds) == 80
        assert len(val_ds) == 20
        assert len(train_ds) + len(val_ds) == 100

    def test_no_split(self):
        """Test with val_split=0."""
        from clara.data import DatasetConfig, FinetuneDataset, prepare_dataset

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [1], "attention_mask": [1]}

        data = [{"text": "test"}]
        config = DatasetConfig(path="")

        dataset = FinetuneDataset(
            data=data,
            tokenizer=MockTokenizer(),
            max_length=512,
            config=config,
        )

        train_ds, val_ds = prepare_dataset(dataset, val_split=0)

        assert train_ds is dataset
        assert val_ds is None


class TestLoadDataset:
    """Tests for load_dataset."""

    def test_load_jsonl(self, tmp_path):
        """Test loading JSONL file."""
        from clara.data import DatasetConfig, load_dataset

        # Create test file
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, "w") as f:
            f.write('{"text": "Line 1"}\n')
            f.write('{"text": "Line 2"}\n')
            f.write('{"text": "Line 3"}\n')

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [1, 2], "attention_mask": [1, 1]}

        config = DatasetConfig(path=str(jsonl_file))
        dataset = load_dataset(config, MockTokenizer(), max_length=512)

        assert len(dataset) == 3

    def test_load_json(self, tmp_path):
        """Test loading JSON file."""
        from clara.data import DatasetConfig, load_dataset

        # Create test file
        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump([{"text": "Example 1"}, {"text": "Example 2"}], f)

        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [1], "attention_mask": [1]}

        config = DatasetConfig(path=str(json_file))
        dataset = load_dataset(config, MockTokenizer(), max_length=512)

        assert len(dataset) == 2
