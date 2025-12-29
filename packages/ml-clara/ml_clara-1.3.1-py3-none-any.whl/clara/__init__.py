"""
ML-Clara: Local LLM Inference Platform

A production-ready inference system for Mistral-7B-Instruct and adapters
with support for MPS (Apple Silicon), CUDA, and CPU.

Usage:
    from clara import load_model, InferenceEngine, GenerationConfig

    result = load_model({"model": {"hf_id": "mistralai/Mistral-7B"}})
    engine = InferenceEngine(result.model, result.tokenizer)
    output = engine.generate("Hello, world!")
"""

__version__ = "1.3.1"
__author__ = "ML-Clara Team"

# Core imports
from clara.config import load_config
from clara.engine import (
    BatchGenerationResult,
    GenerationConfig,
    GenerationResult,
    InferenceEngine,
    generate_batch,
)
from clara.models import ModelLoadResult, load_model
from clara.tokenizer import TokenizerWrapper
from clara.utils.device import DeviceType, get_device

__all__ = [
    # Version
    "__version__",
    # Model loading
    "load_model",
    "ModelLoadResult",
    # Inference
    "InferenceEngine",
    "GenerationConfig",
    "GenerationResult",
    "generate_batch",
    "BatchGenerationResult",
    # Tokenizer
    "TokenizerWrapper",
    # Device
    "get_device",
    "DeviceType",
    # Config
    "load_config",
]
