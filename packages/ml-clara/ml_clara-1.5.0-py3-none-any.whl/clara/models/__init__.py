"""
Model loading and management module.

Provides unified model loading from local paths or HuggingFace,
with support for both standard HF architectures and CLaRa models.
"""

from .loader import (
    load_model,
    resolve_model_source,
    ModelLoadResult,
)
from .exceptions import (
    ModelNotFoundError,
    ModelLoadError,
    AdapterIncompatibleError,
)

__all__ = [
    "load_model",
    "resolve_model_source",
    "ModelLoadResult",
    "ModelNotFoundError",
    "ModelLoadError",
    "AdapterIncompatibleError",
]
