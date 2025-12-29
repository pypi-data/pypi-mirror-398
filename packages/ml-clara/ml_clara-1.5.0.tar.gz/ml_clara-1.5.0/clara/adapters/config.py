"""Adapter configuration schema and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Any

from .exceptions import AdapterConfigError


AdapterType = Literal["lora", "qlora", "adalora", "prefix", "ia3"]


@dataclass
class AdapterConfig:
    """Configuration for a single adapter."""

    name: str
    path: str
    type: AdapterType = "lora"
    description: str = ""

    # Resolved absolute path (set during validation)
    resolved_path: Path | None = field(default=None, repr=False)

    def validate(self, base_path: Path | None = None) -> None:
        """
        Validate adapter configuration.

        Args:
            base_path: Base path for resolving relative adapter paths

        Raises:
            AdapterConfigError: Invalid configuration
        """
        if not self.name:
            raise AdapterConfigError("Adapter name cannot be empty")

        if not self.path:
            raise AdapterConfigError(f"Adapter '{self.name}' has no path")

        # Resolve path
        path = Path(self.path).expanduser()
        if not path.is_absolute() and base_path:
            path = base_path / path

        self.resolved_path = path.resolve()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdapterConfig:
        """Create AdapterConfig from dictionary."""
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            type=data.get("type", "lora"),
            description=data.get("description", ""),
        )


@dataclass
class AdapterSettings:
    """Global adapter settings."""

    validate_compatibility: bool = True
    merge_weights: bool = True  # Always true for v1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdapterSettings:
        """Create AdapterSettings from dictionary."""
        return cls(
            validate_compatibility=data.get("validate_compatibility", True),
            merge_weights=data.get("merge_weights", True),
        )


@dataclass
class AdaptersConfig:
    """Complete adapters configuration."""

    available: list[AdapterConfig] = field(default_factory=list)
    active: str | None = None
    settings: AdapterSettings = field(default_factory=AdapterSettings)

    def get_active_adapter(self) -> AdapterConfig | None:
        """Get the currently active adapter config."""
        if not self.active:
            return None

        for adapter in self.available:
            if adapter.name == self.active:
                return adapter

        return None

    def list_names(self) -> list[str]:
        """List all available adapter names."""
        return [a.name for a in self.available]

    def validate(self, base_path: Path | None = None) -> None:
        """
        Validate complete adapter configuration.

        Raises:
            AdapterConfigError: Invalid configuration
        """
        # Check for duplicate names
        names = [a.name for a in self.available]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise AdapterConfigError(
                f"Duplicate adapter names: {list(set(duplicates))}"
            )

        # Validate each adapter
        for adapter in self.available:
            adapter.validate(base_path)

        # Check active adapter exists
        if self.active and self.active not in names:
            raise AdapterConfigError(
                f"Active adapter '{self.active}' not in available adapters: {names}"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdaptersConfig:
        """Create AdaptersConfig from dictionary."""
        available = [AdapterConfig.from_dict(a) for a in data.get("available", [])]

        return cls(
            available=available,
            active=data.get("active"),
            settings=AdapterSettings.from_dict(data.get("settings", {})),
        )

    @classmethod
    def from_legacy(cls, data: dict[str, Any]) -> AdaptersConfig:
        """
        Create AdaptersConfig from legacy Phase 1 format.

        Legacy format:
            adapter:
              enabled: true
              path: "/path/to/adapter"
              type: "lora"
        """
        if not data.get("enabled", False):
            return cls()  # No adapter

        adapter = AdapterConfig(
            name="default",
            path=data.get("path", ""),
            type=data.get("type", "lora"),
            description="Legacy adapter",
        )

        return cls(
            available=[adapter],
            active="default",
        )


def parse_adapter_config(config: dict[str, Any]) -> AdaptersConfig:
    """
    Parse adapter configuration from full config dict.

    Handles both new and legacy formats.

    Args:
        config: Full configuration dictionary

    Returns:
        AdaptersConfig instance
    """
    # Check for new format first
    if "adapters" in config:
        adapters_data = config["adapters"]
        if isinstance(adapters_data, dict) and "available" in adapters_data:
            return AdaptersConfig.from_dict(adapters_data)

    # Check for legacy format
    if "adapter" in config:
        return AdaptersConfig.from_legacy(config["adapter"])

    # No adapter configuration
    return AdaptersConfig()
