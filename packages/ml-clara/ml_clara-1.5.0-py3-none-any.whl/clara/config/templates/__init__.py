"""Config templates shipped with ML-Clara.

These templates are used by the `clara init-config` CLI command so that users can
generate working starter configs even when ML-Clara is installed via pip (i.e.
without a cloned repo containing `configs/`).
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

_TEMPLATE_FILES: dict[str, str] = {
    "default": "default.yaml",
    "finetune": "finetune.yaml",
    "multi-adapter": "multi_adapter.yaml",
    "test-train": "test_train.yaml",
}


def list_templates() -> list[str]:
    """Return supported template names."""
    return sorted(_TEMPLATE_FILES.keys())


def get_template(name: str) -> str:
    """
    Load a template by name.

    Args:
        name: Template name (see `list_templates()`).
    """
    key = name.strip().lower()
    if key not in _TEMPLATE_FILES:
        raise KeyError(f"Unknown template '{name}'. Available: {', '.join(list_templates())}")

    return files(__package__).joinpath(_TEMPLATE_FILES[key]).read_text(encoding="utf-8")


def write_template(name: str, output_path: str | Path, *, force: bool = False) -> Path:
    """
    Write a template to disk.

    Args:
        name: Template name (see `list_templates()`).
        output_path: Where to write the YAML.
        force: Overwrite if the file exists.
    """
    path = Path(output_path).expanduser()
    if path.exists() and not force:
        raise FileExistsError(str(path))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(get_template(name), encoding="utf-8")
    return path

