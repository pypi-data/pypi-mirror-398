"""
Checksum helpers (local-only).

Used to verify local model artifacts (directories or single files like `.gguf`)
against user-provided SHA256 hashes.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from clara.models.exceptions import ChecksumConfigError, ChecksumMismatchError


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """
    Compute SHA256 for a file.

    Reads in chunks to support very large files.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_sha256(value: str) -> str:
    v = value.strip().lower()
    if v.startswith("sha256:"):
        v = v.split(":", 1)[1].strip()
    if not _SHA256_RE.match(v):
        raise ChecksumConfigError(f"Invalid sha256: {value!r}")
    return v


def _checksum_spec(model_cfg: dict[str, Any]) -> Any:
    for key in ("sha256", "checksum", "checksums"):
        if key in model_cfg:
            return model_cfg.get(key)
    return None


def verify_local_model_checksums(local_path: str | Path, model_cfg: dict[str, Any]) -> None:
    """
    Verify local model artifacts based on `model` config.

    Supported config shapes:

    - Single file:
      model:
        local_path: /path/to/model.gguf
        sha256: "<hex>"

    - Directory (verify specific files):
      model:
        local_path: /path/to/model_dir
        sha256:
          config.json: "<hex>"
          model.safetensors: "<hex>"
    """
    spec = _checksum_spec(model_cfg)
    if spec is None:
        return

    path = Path(local_path).expanduser()
    if not path.exists():
        raise ChecksumConfigError(f"Local path does not exist: {path}")

    if isinstance(spec, str):
        expected = _normalize_sha256(spec)
        if path.is_dir():
            raise ChecksumConfigError(
                "model.sha256 is a string but model.local_path is a directory; "
                "provide a mapping of relative file paths to sha256 values."
            )
        actual = sha256_file(path)
        if actual != expected:
            raise ChecksumMismatchError(str(path), expected, actual)
        return

    if not isinstance(spec, dict):
        raise ChecksumConfigError("model.sha256 must be a string or mapping")

    mapping: dict[str, str] = {}
    for k, v in spec.items():
        if v is None:
            continue
        mapping[str(k)] = _normalize_sha256(str(v))

    if path.is_file():
        expected = mapping.get("__self__") or mapping.get(path.name) or mapping.get(str(path))
        if not expected:
            raise ChecksumConfigError(
                f"No checksum provided for file {path.name!r}. "
                f"Use model.sha256: \"<sha256>\" or model.sha256: {{\"{path.name}\": \"<sha256>\"}}"
            )
        actual = sha256_file(path)
        if actual != expected:
            raise ChecksumMismatchError(str(path), expected, actual)
        return

    # Directory
    if not mapping:
        raise ChecksumConfigError("model.sha256 mapping is empty")

    if "__self__" in mapping and len(mapping) == 1:
        raise ChecksumConfigError(
            "model.sha256 mapping only contains '__self__' but model.local_path is a directory; "
            "provide file entries like {'config.json': '<sha256>'}."
        )

    for rel, expected in mapping.items():
        if rel == "__self__":
            continue
        rel_path = Path(rel)
        target = rel_path if rel_path.is_absolute() else (path / rel_path)
        if not target.exists() or not target.is_file():
            raise ChecksumConfigError(f"Checksum entry does not exist: {target}")
        actual = sha256_file(target)
        if actual != expected:
            raise ChecksumMismatchError(str(target), expected, actual)

