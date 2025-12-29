"""
Model loading module.

Provides unified model loading from local paths or HuggingFace,
with support for both standard HF architectures and CLaRa models.

Resolution order:
1. config["model"]["local_path"] — if exists, load from local
2. config["model"]["hf_id"] — download from HuggingFace
3. Raise ModelNotFoundError if neither specified

Architecture detection:
- First attempts AutoModelForCausalLM (generic HF)
- Falls back to ClaraForCausalLM if HF load fails or config indicates CLaRa
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Any

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoConfig,
    PreTrainedModel,
    PreTrainedTokenizer,
    BitsAndBytesConfig,
)

from .exceptions import ModelNotFoundError, ModelLoadError, AdapterIncompatibleError
from ..utils.device import get_device
from ..utils.logging import get_logger

logger = get_logger(__name__)


# Type aliases
Architecture = Literal["hf", "clara"]
Source = Literal["local", "huggingface"]
DtypeStr = Literal["float32", "float16", "bfloat16", "auto"]


@dataclass
class ModelLoadResult:
    """Result of model loading operation."""

    model: PreTrainedModel
    tokenizer: PreTrainedTokenizer
    architecture: Architecture
    device: torch.device
    dtype: torch.dtype
    model_path: str
    source: Source
    adapter_merged: bool = False
    adapter_name: str | None = None  # Name of merged adapter (if any)

    def __repr__(self) -> str:
        return (
            f"ModelLoadResult("
            f"architecture={self.architecture!r}, "
            f"device={self.device}, "
            f"dtype={self.dtype}, "
            f"source={self.source!r}, "
            f"adapter_merged={self.adapter_merged}, "
            f"adapter_name={self.adapter_name!r})"
        )


def resolve_dtype(
    config: dict[str, Any],
    device: torch.device,
) -> torch.dtype:
    """
    Resolve dtype from config with device-aware defaults.

    Args:
        config: Configuration dict
        device: Target device

    Returns:
        Resolved torch dtype
    """
    dtype_str = config.get("model", {}).get("dtype", "auto")

    dtype_map = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "fp32": torch.float32,
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
    }

    if dtype_str in dtype_map:
        return dtype_map[dtype_str]

    # Auto-detect based on device
    if dtype_str == "auto":
        if device.type == "cuda":
            # Check if GPU supports bfloat16
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        elif device.type == "mps":
            # MPS works best with float16
            return torch.float16
        else:
            # CPU default
            return torch.float32

    # Default fallback
    logger.warning(f"Unknown dtype '{dtype_str}', defaulting to float32")
    return torch.float32


def resolve_model_source(
    config: dict[str, Any],
) -> tuple[str, Source]:
    """
    Determine model path and source from config.

    Resolution order:
    1. local_path if exists on filesystem
    2. hf_id for HuggingFace download
    3. Raise ModelNotFoundError

    Args:
        config: Configuration dict

    Returns:
        (path, source) tuple

    Raises:
        ModelNotFoundError: Neither local_path nor hf_id specified
    """
    model_config = config.get("model", {})
    local_path = model_config.get("local_path")
    hf_id = model_config.get("hf_id")

    # Check local path first
    if local_path:
        path = Path(local_path).expanduser()
        if path.exists():
            logger.info(f"Using local model: {path}")
            return str(path), "local"
        else:
            logger.warning(f"Local path not found: {path}, falling back to HF")

    # Try HuggingFace ID
    if hf_id:
        logger.info(f"Using HuggingFace model: {hf_id}")
        return hf_id, "huggingface"

    raise ModelNotFoundError(
        "No model specified. Provide 'model.local_path' or 'model.hf_id' in config."
    )


def _detect_architecture(
    model_path: str,
    config: dict[str, Any],
) -> Architecture:
    """
    Detect if model is CLaRa or standard HF architecture.

    Detection methods:
    1. Explicit config["model"]["architecture"] override
    2. Check for clara-specific keys in model config.json
    3. Check model class in config.json

    Args:
        model_path: Path to model (local or HF ID)
        config: User configuration

    Returns:
        "hf" or "clara"
    """
    # Check for explicit override
    arch_override = config.get("model", {}).get("architecture")
    if arch_override:
        if arch_override.lower() in ["clara", "hf"]:
            return arch_override.lower()  # type: ignore
        logger.warning(f"Unknown architecture '{arch_override}', auto-detecting")

    # Try to read model config.json
    try:
        path = Path(model_path)
        if path.exists():
            config_file = path / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    model_cfg = json.load(f)

                # Check for CLaRa-specific keys
                if "clara_config" in model_cfg or model_cfg.get("model_type") == "clara":
                    logger.info("Detected CLaRa architecture from config")
                    return "clara"

                # Check architectures field
                archs = model_cfg.get("architectures", [])
                for arch in archs:
                    if "clara" in arch.lower():
                        logger.info(f"Detected CLaRa architecture: {arch}")
                        return "clara"
    except Exception as e:
        logger.debug(f"Could not read model config: {e}")

    # Default to HF
    return "hf"


def _load_hf_model(
    model_path: str,
    device: torch.device,
    dtype: torch.dtype,
    trust_remote_code: bool = False,
    quantization_config: BitsAndBytesConfig | None = None,
) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Load model using AutoModelForCausalLM.

    Args:
        model_path: Local path or HuggingFace ID
        device: Target device
        dtype: Model dtype
        trust_remote_code: Trust remote code in model
        quantization_config: Optional quantization config

    Returns:
        (model, tokenizer) tuple
    """
    logger.info(f"Loading HuggingFace model: {model_path}")

    load_kwargs: dict[str, Any] = {
        "torch_dtype": dtype,
        "trust_remote_code": trust_remote_code,
        "low_cpu_mem_usage": True,
    }

    # Device mapping
    if device.type == "cuda":
        load_kwargs["device_map"] = "auto"
    elif device.type == "mps":
        # MPS doesn't support device_map, load to CPU first then move
        load_kwargs["device_map"] = None
    else:
        load_kwargs["device_map"] = None

    if quantization_config:
        load_kwargs["quantization_config"] = quantization_config

    try:
        model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=trust_remote_code,
        )
    except Exception as e:
        raise ModelLoadError(f"Failed to load HuggingFace model from {model_path}", e)

    return model, tokenizer


def _load_clara_model(
    model_path: str,
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Load model using ClaraForCausalLM from modeling_clara.py.

    Args:
        model_path: Local path or HuggingFace ID
        device: Target device
        dtype: Model dtype

    Returns:
        (model, tokenizer) tuple
    """
    logger.info(f"Loading CLaRa model: {model_path}")

    try:
        # Import CLaRa model class
        from openrlhf.models.modeling_clara import ClaraForCausalLM
    except ImportError:
        # Try relative import
        try:
            import sys
            repo_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(repo_root))
            from openrlhf.models.modeling_clara import ClaraForCausalLM
        except ImportError as e:
            raise ModelLoadError(
                "Could not import ClaraForCausalLM. "
                "Ensure openrlhf.models.modeling_clara is available.",
                e,
            )

    try:
        # Load base model config
        config = AutoConfig.from_pretrained(model_path)

        # Create CLaRa model
        model = ClaraForCausalLM.from_pretrained(
            model_path,
            config=config,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        )

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)

    except Exception as e:
        raise ModelLoadError(f"Failed to load CLaRa model from {model_path}", e)

    return model, tokenizer


def _merge_adapter(
    model: PreTrainedModel,
    adapter_config: dict[str, Any],
    model_path: str,
) -> PreTrainedModel:
    """
    Merge LoRA/adapter into base model.

    Validates:
    - Adapter exists at path
    - Uses PEFT for merging

    Args:
        model: Base model
        adapter_config: Adapter configuration
        model_path: Base model path (for error messages)

    Returns:
        Merged model

    Raises:
        AdapterIncompatibleError: Adapter incompatible with base
    """
    adapter_path = adapter_config.get("path")
    if not adapter_path:
        raise AdapterIncompatibleError("No adapter path specified")

    adapter_path = Path(adapter_path).expanduser()
    if not adapter_path.exists():
        raise AdapterIncompatibleError(
            f"Adapter path does not exist: {adapter_path}",
            adapter_path=str(adapter_path),
        )

    logger.info(f"Merging adapter: {adapter_path}")

    try:
        from peft import PeftModel

        # Load adapter
        model = PeftModel.from_pretrained(model, str(adapter_path))

        # Merge and unload
        model = model.merge_and_unload()

        logger.info("Adapter merged successfully")

    except ImportError:
        raise AdapterIncompatibleError(
            "PEFT library not installed. Install with: pip install peft",
            adapter_path=str(adapter_path),
            base_model=model_path,
        )
    except Exception as e:
        raise AdapterIncompatibleError(
            f"Failed to merge adapter: {e}",
            adapter_path=str(adapter_path),
            base_model=model_path,
        )

    return model


def _prepare_model(
    model: PreTrainedModel,
    device: torch.device,
    dtype: torch.dtype,
) -> PreTrainedModel:
    """
    Prepare model for inference.

    Operations:
    - Move to device (if not already)
    - Set eval mode
    - Enable KV cache
    - Disable gradients

    Args:
        model: Loaded model
        device: Target device
        dtype: Target dtype

    Returns:
        Prepared model
    """
    # Check if model is already on correct device
    model_device = next(model.parameters()).device

    if model_device != device:
        logger.info(f"Moving model to {device}")
        model = model.to(device=device, dtype=dtype)

    # Set eval mode
    model.eval()

    # Enable KV cache for generation
    if hasattr(model.config, "use_cache"):
        model.config.use_cache = True

    # Disable gradients for inference
    for param in model.parameters():
        param.requires_grad = False

    return model


def load_model(
    config: dict[str, Any],
    device: torch.device | str | None = None,
    dtype: torch.dtype | None = None,
) -> ModelLoadResult:
    """
    Load model and tokenizer from local path or HuggingFace.

    Resolution order:
    1. config["model"]["local_path"] — if exists, load from local
    2. config["model"]["hf_id"] — download from HuggingFace
    3. Raise ModelNotFoundError if neither specified

    Architecture detection:
    - First attempts AutoModelForCausalLM (generic HF)
    - Falls back to ClaraForCausalLM if HF load fails or config indicates CLaRa

    Adapter handling:
    - If config["adapter"]["enabled"], merges adapter at load time
    - Validates adapter compatibility before merge

    Args:
        config: Configuration dict with model/adapter settings
        device: Target device (auto-detected if None)
        dtype: Model dtype (from config or auto-detected if None)

    Returns:
        ModelLoadResult with loaded model, tokenizer, and metadata

    Raises:
        ModelNotFoundError: Neither local_path nor hf_id specified
        ModelLoadError: Failed to load model
        AdapterIncompatibleError: Adapter doesn't match base model

    Example:
        >>> config = {"model": {"hf_id": "mistralai/Mistral-7B-Instruct-v0.2"}}
        >>> result = load_model(config)
        >>> print(result.architecture)
        'hf'
    """
    # Resolve device
    if device is None:
        device_str = get_device()
        device = torch.device(device_str)
    elif isinstance(device, str):
        device = torch.device(device)

    # Resolve dtype
    if dtype is None:
        dtype = resolve_dtype(config, device)

    logger.info(f"Loading model with device={device}, dtype={dtype}")

    # Resolve model source
    model_path, source = resolve_model_source(config)

    # Detect architecture
    architecture = _detect_architecture(model_path, config)

    # Load model and tokenizer
    trust_remote_code = config.get("model", {}).get("trust_remote_code", False)

    if architecture == "clara":
        model, tokenizer = _load_clara_model(model_path, device, dtype)
    else:
        model, tokenizer = _load_hf_model(
            model_path,
            device,
            dtype,
            trust_remote_code=trust_remote_code,
        )

    # Handle adapter configuration (supports both new and legacy formats)
    adapter_merged = False
    adapter_name = None

    # Try new adapter registry system first
    try:
        from ..adapters import (
            AdapterRegistry,
            load_adapter_from_registry,
            parse_adapter_config,
        )

        # Determine base path for relative adapter paths
        base_path = None
        if "config_path" in config:
            base_path = Path(config["config_path"]).parent

        # Build adapter registry
        registry = AdapterRegistry.from_config(config, base_path)

        # Load active adapter if any
        if registry.get_active():
            adapters_config = parse_adapter_config(config)
            validate = adapters_config.settings.validate_compatibility

            model, adapter_meta = load_adapter_from_registry(
                model,
                registry,
                validate=validate,
            )

            if adapter_meta:
                adapter_merged = True
                adapter_name = adapter_meta.name
                logger.info(f"Adapter '{adapter_name}' merged successfully")

    except ImportError:
        # Fallback to legacy adapter handling
        logger.debug("Adapter registry not available, using legacy handling")
        adapter_config = config.get("adapter", {})
        if adapter_config.get("enabled", False):
            model = _merge_adapter(model, adapter_config, model_path)
            adapter_merged = True
            adapter_name = "default"

    # Prepare model for inference
    model = _prepare_model(model, device, dtype)

    # Ensure tokenizer has pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    return ModelLoadResult(
        model=model,
        tokenizer=tokenizer,
        architecture=architecture,
        device=device,
        dtype=dtype,
        model_path=model_path,
        source=source,
        adapter_merged=adapter_merged,
        adapter_name=adapter_name,
    )
