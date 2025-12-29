"""
Configuration loader with support for YAML/JSON, environment variables, and CLI overrides.

Priority order:
1. CLI arguments
2. Environment variables
3. Config file (YAML/JSON)
4. Defaults
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class InferenceConfig:
    """Inference configuration."""
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    stop_tokens: list[str] = field(default_factory=list)
    do_sample: bool = True


@dataclass
class ModelConfig:
    """Model configuration."""
    hf_id: str | None = "mistralai/Mistral-7B-Instruct-v0.2"
    local_path: str | None = None
    dtype: str = "auto"  # float32 | float16 | bfloat16 | auto
    trust_remote_code: bool = False
    architecture: str | None = None  # "hf" | "clara" | None


@dataclass
class DeviceConfig:
    """Device configuration."""
    device: Optional[str] = None  # Auto-detect if None
    prefer_mps: bool = True
    prefer_cuda: bool = True


@dataclass
class AdapterConfig:
    """Legacy single-adapter configuration (Phase 1 format)."""

    enabled: bool = False
    path: str | None = None
    type: str | None = None  # Auto-detect if None


@dataclass
class Config:
    """Main configuration class."""
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    adapter: AdapterConfig = field(default_factory=AdapterConfig)
    logging: Dict[str, Any] = field(default_factory=lambda: {"level": "INFO", "verbosity": 2})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()

        if "inference" in data:
            config.inference = InferenceConfig(**data["inference"])
        if "model" in data:
            config.model = ModelConfig(**data["model"])
        if "device" in data:
            config.device = DeviceConfig(**data["device"])
        if "adapter" in data:
            config.adapter = AdapterConfig(**data["adapter"])
        if "logging" in data:
            config.logging = data["logging"]

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "inference": {
                "max_new_tokens": self.inference.max_new_tokens,
                "temperature": self.inference.temperature,
                "top_p": self.inference.top_p,
                "top_k": self.inference.top_k,
                "repetition_penalty": self.inference.repetition_penalty,
                "stop_tokens": self.inference.stop_tokens,
                "do_sample": self.inference.do_sample,
            },
            "model": {
                "hf_id": self.model.hf_id,
                "local_path": self.model.local_path,
                "dtype": self.model.dtype,
                "trust_remote_code": self.model.trust_remote_code,
                "architecture": self.model.architecture,
            },
            "device": {
                "device": self.device.device,
                "prefer_mps": self.device.prefer_mps,
                "prefer_cuda": self.device.prefer_cuda,
            },
            "adapter": {
                "enabled": self.adapter.enabled,
                "path": self.adapter.path,
                "type": self.adapter.type,
            },
            "logging": self.logging,
        }


def load_config(
    config_path: Optional[str] = None,
    env_overrides: bool = True,
) -> Dict[str, Any]:
    """
    Load configuration from file, environment variables, and defaults.

    Args:
        config_path: Path to YAML/JSON config file
        env_overrides: Whether to apply environment variable overrides

    Returns:
        Configuration dict (raw dict for compatibility with model loader)
    """
    config: Dict[str, Any] = {}

    # Load raw dict from file
    if config_path:
        path = Path(config_path).expanduser()
        if path.exists():
            file_data = _load_config_file(str(path))

            if file_data is None:
                config = {}
            elif not isinstance(file_data, dict):
                raise ValueError(
                    f"Config file must contain a mapping at the top level: {path}"
                )
            else:
                config = file_data.copy()

            # Include provenance for downstream path resolution (e.g., relative adapters)
            config.setdefault("config_path", str(path.resolve()))
            config.setdefault("config_dir", str(path.resolve().parent))

    # Apply environment overrides (keeps unknown keys intact)
    if env_overrides:
        config = _apply_env_overrides_dict(config)

    return config


def _load_config_file(config_path: str) -> Optional[Dict[str, Any]]:
    """Load config from YAML or JSON file."""
    path = Path(config_path)

    if not path.exists():
        return None

    if path.suffix in [".yaml", ".yml"]:
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML required for YAML config files. Install with: pip install pyyaml")
        with open(path, "r") as f:
            return yaml.safe_load(f)
    elif path.suffix == ".json":
        with open(path, "r") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported config file format: {path.suffix}")

    return None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _apply_env_overrides_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to a raw config dict.

    This intentionally avoids rewriting the full config (so unknown keys like
    `adapters:` remain intact).
    """
    model = config.setdefault("model", {})
    device = config.setdefault("device", {})
    inference = config.setdefault("inference", {})
    adapter = config.setdefault("adapter", {})
    logging_cfg = config.setdefault("logging", {})

    # Model overrides
    model_hf_id = (
        os.getenv("CLARA_MODEL_HF_ID")
        or os.getenv("CLARA_MODEL")
        or os.getenv("CLARA_MODEL_ID")  # legacy
    )
    if model_hf_id:
        model["hf_id"] = model_hf_id

    if os.getenv("CLARA_LOCAL_MODEL_PATH"):
        model["local_path"] = os.getenv("CLARA_LOCAL_MODEL_PATH")

    if os.getenv("CLARA_MODEL_DTYPE"):
        model["dtype"] = os.getenv("CLARA_MODEL_DTYPE")

    if os.getenv("CLARA_TRUST_REMOTE_CODE"):
        model["trust_remote_code"] = _parse_bool(os.getenv("CLARA_TRUST_REMOTE_CODE", ""))

    # Device overrides
    if os.getenv("CLARA_DEVICE"):
        device["device"] = os.getenv("CLARA_DEVICE")

    # Adapter overrides (legacy single adapter)
    if os.getenv("CLARA_ADAPTER_PATH"):
        adapter["enabled"] = True
        adapter["path"] = os.getenv("CLARA_ADAPTER_PATH")

    # Inference overrides
    if os.getenv("CLARA_MAX_TOKENS"):
        inference["max_new_tokens"] = int(os.getenv("CLARA_MAX_TOKENS", "0"))
    if os.getenv("CLARA_TEMPERATURE"):
        inference["temperature"] = float(os.getenv("CLARA_TEMPERATURE", "0"))

    # Logging overrides
    if os.getenv("CLARA_VERBOSITY"):
        logging_cfg["verbosity"] = int(os.getenv("CLARA_VERBOSITY", "0"))
    if os.getenv("CLARA_LOG_LEVEL"):
        logging_cfg["level"] = os.getenv("CLARA_LOG_LEVEL")

    return config


def _get_default_config_path() -> Path:
    """Get path to default config file."""
    # Check for configs/default.yaml in repo root
    repo_root = Path(__file__).parent.parent.parent
    default_path = repo_root / "configs" / "default.yaml"
    if default_path.exists():
        return default_path

    return default_path
