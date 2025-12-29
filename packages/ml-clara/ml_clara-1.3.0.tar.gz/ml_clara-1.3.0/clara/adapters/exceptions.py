"""Adapter-specific exceptions."""

from __future__ import annotations


class AdapterError(Exception):
    """Base exception for adapter operations."""

    pass


class AdapterNotFoundError(AdapterError):
    """Requested adapter not found in registry."""

    def __init__(self, adapter_name: str, available: list[str]):
        self.adapter_name = adapter_name
        self.available = available
        super().__init__(
            f"Adapter '{adapter_name}' not found. "
            f"Available adapters: {', '.join(available) or 'none'}"
        )


class AdapterPathError(AdapterError):
    """Adapter path does not exist or is invalid."""

    def __init__(self, adapter_name: str, path: str):
        self.adapter_name = adapter_name
        self.path = path
        super().__init__(f"Adapter '{adapter_name}' path not found: {path}")


class AdapterCompatibilityError(AdapterError):
    """Adapter is incompatible with base model."""

    def __init__(
        self,
        adapter_name: str,
        reason: str,
        adapter_info: dict | None = None,
        model_info: dict | None = None,
    ):
        self.adapter_name = adapter_name
        self.reason = reason
        self.adapter_info = adapter_info or {}
        self.model_info = model_info or {}
        super().__init__(
            f"Adapter '{adapter_name}' incompatible with base model: {reason}"
        )


class AdapterConfigError(AdapterError):
    """Invalid adapter configuration."""

    def __init__(self, message: str, config_path: str | None = None):
        self.config_path = config_path
        super().__init__(message)
