"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_cli_version(self, runner):
        """Test version command."""
        from clara.cli.main import cli
        from clara import __version__

        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_cli_help(self, runner):
        """Test help output."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ML-Clara" in result.output
        assert "run" in result.output
        assert "eval" in result.output
        assert "info" in result.output

    def test_run_help(self, runner):
        """Test run command help."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--config" in result.output
        assert "--max-tokens" in result.output
        assert "--temperature" in result.output
        assert "--stream" in result.output

    def test_eval_help(self, runner):
        """Test eval command help."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["eval", "--help"])
        assert result.exit_code == 0
        assert "--benchmarks" in result.output
        assert "--samples" in result.output
        assert "--output" in result.output

    def test_info_command(self, runner):
        """Test info command."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "ML-Clara" in result.output
        assert "Python" in result.output
        assert "Device" in result.output
        assert "PyTorch" in result.output

    def test_validate_missing_config(self, runner):
        """Test validate with missing config."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["validate", "--config", "/nonexistent/path.yaml"])
        assert result.exit_code != 0

    def test_validate_valid_config(self, runner, tmp_path):
        """Test validate with valid config."""
        from clara.cli.main import cli

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
model:
  hf_id: gpt2
  dtype: float32
""")

        result = runner.invoke(cli, ["validate", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "Config valid" in result.output

    def test_adapters_no_config(self, runner):
        """Test adapters command without config."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["adapters"])
        assert result.exit_code == 1
        assert "No config file specified" in result.output

    def test_adapters_empty_config(self, runner, tmp_path):
        """Test adapters with config having no adapters."""
        from clara.cli.main import cli

        config_file = tmp_path / "empty_adapters.yaml"
        config_file.write_text("""
model:
  hf_id: gpt2
""")

        result = runner.invoke(cli, ["adapters", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "No adapters configured" in result.output

    def test_adapters_with_adapters(self, runner, tmp_path):
        """Test adapters command with configured adapters."""
        from clara.cli.main import cli

        # Create real adapter directories so they pass path validation
        adapter1_dir = tmp_path / "adapter1"
        adapter1_dir.mkdir()
        adapter2_dir = tmp_path / "adapter2"
        adapter2_dir.mkdir()

        config_file = tmp_path / "multi_adapter.yaml"
        config_file.write_text(f"""
model:
  hf_id: gpt2

adapters:
  available:
    - name: adapter1
      path: {adapter1_dir}
      description: Test adapter 1
    - name: adapter2
      path: {adapter2_dir}
      rank: 16
  active: adapter1
""")

        result = runner.invoke(cli, ["adapters", "--config", str(config_file)])
        assert result.exit_code == 0
        assert "adapter1" in result.output
        assert "adapter2" in result.output
        assert "Available adapters (2)" in result.output

    def test_verbose_flag(self, runner):
        """Test verbose flag."""
        from clara.cli.main import cli

        result = runner.invoke(cli, ["-v", "info"])
        assert result.exit_code == 0

    def test_init_config_writes_file_and_overwrite_guard(self, runner, tmp_path):
        """`clara init-config` writes templates and protects existing files."""
        from clara.cli.main import cli

        out = tmp_path / "config.yaml"

        result = runner.invoke(cli, ["init-config", "--type", "default", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        contents = out.read_text()
        assert "model:" in contents
        assert "hf_id:" in contents

        # Refuse overwrite without --force
        result2 = runner.invoke(cli, ["init-config", "--type", "default", "-o", str(out)])
        assert result2.exit_code != 0
        assert "Refusing to overwrite" in result2.output

        # Allow overwrite with --force
        result3 = runner.invoke(cli, ["init-config", "--type", "default", "-o", str(out), "--force"])
        assert result3.exit_code == 0
