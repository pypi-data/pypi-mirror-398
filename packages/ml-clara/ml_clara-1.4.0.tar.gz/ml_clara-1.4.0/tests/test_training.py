"""Tests for training infrastructure."""

import pytest
import torch


class TestLoraConfig:
    """Tests for LoraConfig."""

    def test_default_config(self):
        """Test default LoRA config."""
        from clara.training import LoraConfig

        config = LoraConfig()
        assert config.r == 16
        assert config.lora_alpha == 32
        assert config.lora_dropout == 0.05
        assert config.bias == "none"

    def test_to_peft_config(self):
        """Test conversion to PEFT config."""
        from clara.training import LoraConfig

        config = LoraConfig(r=8, lora_alpha=16)
        peft_config = config.to_peft_config()

        assert peft_config.r == 8
        assert peft_config.lora_alpha == 16


class TestTrainingConfig:
    """Tests for TrainingConfig."""

    def test_default_config(self):
        """Test default training config."""
        from clara.training import TrainingConfig

        config = TrainingConfig()
        assert config.num_epochs == 3
        assert config.batch_size == 4
        assert config.gradient_accumulation_steps == 4
        assert config.learning_rate == 2e-4

    def test_effective_batch_size(self):
        """Test effective batch size calculation."""
        from clara.training import TrainingConfig

        config = TrainingConfig(batch_size=4, gradient_accumulation_steps=8)
        assert config.effective_batch_size() == 32

    def test_from_dict(self):
        """Test creating config from dict."""
        from clara.training import TrainingConfig

        data = {
            "num_epochs": 5,
            "batch_size": 8,
            "learning_rate": 1e-4,
            "lora": {"r": 32, "lora_alpha": 64},
        }

        config = TrainingConfig.from_dict(data)
        assert config.num_epochs == 5
        assert config.batch_size == 8
        assert config.lora.r == 32
        assert config.lora.lora_alpha == 64

    def test_from_dict_type_coercion(self):
        """Test type coercion for string values from YAML."""
        from clara.training import TrainingConfig

        # Simulate YAML loading strings for scientific notation
        data = {
            "num_epochs": "5",  # string instead of int
            "batch_size": "8",
            "learning_rate": "1e-4",  # scientific notation as string
            "weight_decay": "0.01",
            "lora": {
                "r": "32",
                "lora_alpha": "64",
                "lora_dropout": "0.05",
            },
        }

        config = TrainingConfig.from_dict(data)
        assert config.num_epochs == 5
        assert isinstance(config.num_epochs, int)
        assert config.learning_rate == 1e-4
        assert isinstance(config.learning_rate, float)
        assert config.lora.r == 32
        assert isinstance(config.lora.r, int)

    def test_from_yaml(self, tmp_path):
        """Test loading config from YAML."""
        from clara.training import TrainingConfig

        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
num_epochs: 10
batch_size: 2
learning_rate: 5e-5
lora:
  r: 8
  lora_alpha: 16
""")

        config = TrainingConfig.from_yaml(yaml_file)
        assert config.num_epochs == 10
        assert config.batch_size == 2
        assert config.lora.r == 8


class TestTrainingState:
    """Tests for TrainingState."""

    def test_default_state(self):
        """Test default training state."""
        from clara.training import TrainingState

        state = TrainingState()
        assert state.epoch == 0
        assert state.global_step == 0
        assert state.best_loss == float("inf")


class TestCallbacks:
    """Tests for training callbacks."""

    def test_logging_callback(self):
        """Test logging callback."""
        from clara.training import LoggingCallback

        callback = LoggingCallback(report_to=["tensorboard"])
        assert "tensorboard" in callback.report_to

    def test_early_stopping_callback(self):
        """Test early stopping callback."""
        from clara.training import EarlyStoppingCallback

        callback = EarlyStoppingCallback(patience=3, min_delta=0.01)
        assert callback.patience == 3
        assert callback.min_delta == 0.01
        assert callback.counter == 0

    def test_checkpoint_callback(self):
        """Test checkpoint callback."""
        from clara.training import CheckpointCallback

        callback = CheckpointCallback(save_best=True)
        assert callback.save_best is True
        assert callback.best_loss == float("inf")


class TestCLITrainCommand:
    """Tests for CLI train command."""

    def test_train_help(self):
        """Test train command help."""
        from click.testing import CliRunner
        from clara.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["train", "--help"])

        assert result.exit_code == 0
        assert "--config" in result.output
        assert "--model" in result.output
        assert "--dataset" in result.output
        assert "--output" in result.output
        assert "--resume" in result.output

    def test_train_missing_config(self):
        """Test train command without config."""
        from click.testing import CliRunner
        from clara.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["train"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestCLIExportCommand:
    """Tests for CLI export command."""

    def test_export_help(self):
        """Test export command help."""
        from click.testing import CliRunner
        from clara.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])

        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--model" in result.output
        assert "--push-to-hub" in result.output
