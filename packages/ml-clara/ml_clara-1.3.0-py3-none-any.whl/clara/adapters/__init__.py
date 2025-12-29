"""
Adapter management for ML-Clara.

Provides:
- AdapterRegistry: Named adapter management
- AdapterConfig: Adapter configuration parsing
- merge_adapter: Adapter merging operations

Usage:
    from clara.adapters import AdapterRegistry, merge_adapter

    registry = AdapterRegistry.from_config(config)
    adapter = registry.get_active()
    model = merge_adapter(model, adapter)
"""

from .config import (
    AdapterConfig,
    AdapterSettings,
    AdaptersConfig,
    parse_adapter_config,
)
from .exceptions import (
    AdapterCompatibilityError,
    AdapterConfigError,
    AdapterError,
    AdapterNotFoundError,
    AdapterPathError,
)
from .loader import (
    load_adapter_from_registry,
    merge_adapter,
    validate_adapter_compatibility,
)
from .registry import AdapterMetadata, AdapterRegistry

__all__ = [
    # Registry
    "AdapterRegistry",
    "AdapterMetadata",
    # Config
    "AdapterConfig",
    "AdaptersConfig",
    "AdapterSettings",
    "parse_adapter_config",
    # Loader
    "merge_adapter",
    "validate_adapter_compatibility",
    "load_adapter_from_registry",
    # Exceptions
    "AdapterError",
    "AdapterNotFoundError",
    "AdapterPathError",
    "AdapterCompatibilityError",
    "AdapterConfigError",
]
