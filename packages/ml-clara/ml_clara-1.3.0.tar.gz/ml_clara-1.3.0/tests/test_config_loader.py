"""Tests for config loading and path resolution."""

from __future__ import annotations

from pathlib import Path


def test_load_config_includes_provenance(tmp_path: Path) -> None:
    from clara.config import load_config

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
model:
  hf_id: gpt2
""".lstrip()
    )

    cfg = load_config(str(config_file))
    assert cfg["config_path"] == str(config_file.resolve())
    assert cfg["config_dir"] == str(tmp_path.resolve())


def test_cli_adapters_resolves_relative_paths(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from clara.cli.main import cli

    adapter_dir = tmp_path / "adapter1"
    adapter_dir.mkdir()

    config_file = tmp_path / "adapters.yaml"
    config_file.write_text(
        f"""
model:
  hf_id: gpt2

adapters:
  available:
    - name: adapter1
      path: {adapter_dir.name}
      description: Relative path adapter
  active: adapter1
""".lstrip()
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["adapters", "--config", str(config_file)])
    assert result.exit_code == 0
    assert "adapter1" in result.output
    assert str(adapter_dir) in result.output

