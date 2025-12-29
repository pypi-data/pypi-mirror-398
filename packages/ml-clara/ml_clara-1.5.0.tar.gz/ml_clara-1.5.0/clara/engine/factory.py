"""
Inference engine factory.

This module selects the appropriate inference backend based on config:
- Transformers backend (default): uses `clara.models.load_model` + `InferenceEngine`
- GGUF backend (optional): uses `GGUFEngine` via `llama-cpp-python`
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .gguf import GGUFEngine, GGUFLoadConfig
from .inference import InferenceEngine
from ..models import load_model
from ..utils.checksums import verify_local_model_checksums

Backend = Literal["transformers", "gguf"]


@dataclass(frozen=True)
class EngineLoadResult:
    engine: Any
    backend: Backend
    model_path: str
    adapter_name: str | None = None


def _model_config(config: dict[str, Any]) -> dict[str, Any]:
    model = config.get("model", {})
    return model if isinstance(model, dict) else {}


def _gguf_path_from_config(config: dict[str, Any]) -> str | None:
    model = _model_config(config)

    backend = (model.get("backend") or "").strip().lower()
    if backend in {"gguf", "llama.cpp", "llama_cpp", "llama-cpp"}:
        path = model.get("local_path") or model.get("hf_id")
        return str(path) if path else None

    local_path = model.get("local_path")
    if isinstance(local_path, str) and local_path.strip():
        p = Path(local_path).expanduser()
        if p.is_file() and p.suffix.lower() == ".gguf":
            return str(p)

    hf_id = model.get("hf_id")
    if isinstance(hf_id, str) and hf_id.strip():
        p = Path(hf_id).expanduser()
        if p.is_file() and p.suffix.lower() == ".gguf":
            return str(p)

    return None


def load_engine(config: dict[str, Any]) -> EngineLoadResult:
    """
    Load an inference engine based on config.

    For GGUF models, set `model.local_path` to a `.gguf` file (or `model.backend: gguf`).
    For Transformers models, use `model.hf_id` or `model.local_path` (directory).
    """
    gguf_path = _gguf_path_from_config(config)
    if gguf_path:
        model = _model_config(config)
        gguf_file = Path(gguf_path).expanduser()
        if not gguf_file.exists() or not gguf_file.is_file():
            raise FileNotFoundError(str(gguf_file))

        # Optional local-only checksum verification
        verify_local_model_checksums(gguf_file, model)

        gguf_cfg = model.get("gguf", {}) if isinstance(model.get("gguf"), dict) else {}

        def pick(key: str, default: Any) -> Any:
            return gguf_cfg.get(key, model.get(key, default))

        cfg = GGUFLoadConfig(
            model_path=str(gguf_file),
            n_ctx=int(pick("n_ctx", 4096)),
            n_threads=pick("n_threads", None),
            n_gpu_layers=int(pick("n_gpu_layers", 0)),
            seed=pick("seed", None),
            verbose=bool(pick("verbose", False)),
        )
        engine = GGUFEngine(cfg)
        return EngineLoadResult(
            engine=engine,
            backend="gguf",
            model_path=str(Path(cfg.model_path).expanduser()),
            adapter_name=None,
        )

    result = load_model(config)
    engine = InferenceEngine(result.model, result.tokenizer)
    return EngineLoadResult(
        engine=engine,
        backend="transformers",
        model_path=result.model_path,
        adapter_name=result.adapter_name,
    )
