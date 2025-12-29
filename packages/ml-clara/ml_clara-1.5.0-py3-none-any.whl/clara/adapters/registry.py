"""Adapter registry for managing named adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .config import AdaptersConfig, parse_adapter_config
from .exceptions import AdapterNotFoundError, AdapterPathError
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AdapterMetadata:
    """Metadata about a registered adapter."""

    name: str
    path: Path
    type: str
    description: str

    # Extracted from adapter_config.json if available
    rank: int | None = None
    alpha: float | None = None
    target_modules: list[str] = field(default_factory=list)
    base_model_name: str | None = None

    def __repr__(self) -> str:
        return (
            f"AdapterMetadata(name={self.name!r}, type={self.type!r}, "
            f"rank={self.rank}, targets={len(self.target_modules)} modules)"
        )


class AdapterRegistry:
    """
    Registry for managing multiple named adapters.

    Provides:
    - Named adapter lookup
    - Adapter metadata extraction
    - Path validation
    - Active adapter selection

    Usage:
        registry = AdapterRegistry.from_config(config)
        adapter = registry.get("domain_expert")
        print(adapter.rank, adapter.target_modules)
    """

    def __init__(self) -> None:
        self._adapters: dict[str, AdapterMetadata] = {}
        self._active: str | None = None

    def register(
        self,
        name: str,
        path: Path,
        adapter_type: str = "lora",
        description: str = "",
    ) -> AdapterMetadata:
        """
        Register an adapter in the registry.

        Args:
            name: Unique adapter name
            path: Path to adapter files
            adapter_type: Type of adapter (lora, qlora, etc.)
            description: Human-readable description

        Returns:
            AdapterMetadata for the registered adapter

        Raises:
            AdapterPathError: Path does not exist
        """
        if not path.exists():
            raise AdapterPathError(name, str(path))

        # Extract metadata from adapter files
        metadata = self._extract_metadata(name, path, adapter_type, description)

        self._adapters[name] = metadata
        logger.info(f"Registered adapter: {name} ({adapter_type}) from {path}")

        return metadata

    def get(self, name: str) -> AdapterMetadata:
        """
        Get adapter metadata by name.

        Args:
            name: Adapter name

        Returns:
            AdapterMetadata

        Raises:
            AdapterNotFoundError: Adapter not in registry
        """
        if name not in self._adapters:
            raise AdapterNotFoundError(name, list(self._adapters.keys()))

        return self._adapters[name]

    def get_active(self) -> AdapterMetadata | None:
        """Get the currently active adapter, or None."""
        if self._active is None:
            return None
        return self._adapters.get(self._active)

    def set_active(self, name: str | None) -> None:
        """
        Set the active adapter.

        Args:
            name: Adapter name, or None to deactivate

        Raises:
            AdapterNotFoundError: Adapter not in registry
        """
        if name is not None and name not in self._adapters:
            raise AdapterNotFoundError(name, list(self._adapters.keys()))

        self._active = name
        if name:
            logger.info(f"Active adapter set to: {name}")
        else:
            logger.info("No active adapter")

    def list_adapters(self) -> list[str]:
        """List all registered adapter names."""
        return list(self._adapters.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._adapters

    def __len__(self) -> int:
        return len(self._adapters)

    def __iter__(self) -> Iterator[AdapterMetadata]:
        return iter(self._adapters.values())

    def _extract_metadata(
        self,
        name: str,
        path: Path,
        adapter_type: str,
        description: str,
    ) -> AdapterMetadata:
        """Extract metadata from adapter files."""
        metadata = AdapterMetadata(
            name=name,
            path=path,
            type=adapter_type,
            description=description,
        )

        # Try to read adapter_config.json (PEFT format)
        config_file = path / "adapter_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    adapter_cfg = json.load(f)

                metadata.rank = adapter_cfg.get("r") or adapter_cfg.get("rank")
                metadata.alpha = adapter_cfg.get("lora_alpha")
                metadata.target_modules = adapter_cfg.get("target_modules", [])
                metadata.base_model_name = adapter_cfg.get("base_model_name_or_path")

                logger.debug(
                    f"Extracted metadata for {name}: rank={metadata.rank}, "
                    f"targets={metadata.target_modules}"
                )
            except Exception as e:
                logger.warning(f"Could not read adapter config for {name}: {e}")

        return metadata

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        base_path: Path | None = None,
    ) -> AdapterRegistry:
        """
        Create registry from configuration.

        Args:
            config: Full configuration dict
            base_path: Base path for resolving relative adapter paths

        Returns:
            Populated AdapterRegistry
        """
        registry = cls()

        # Parse adapter configuration
        adapters_config = parse_adapter_config(config)
        adapters_config.validate(base_path)

        # Register each adapter
        for adapter_cfg in adapters_config.available:
            if adapter_cfg.resolved_path and adapter_cfg.resolved_path.exists():
                registry.register(
                    name=adapter_cfg.name,
                    path=adapter_cfg.resolved_path,
                    adapter_type=adapter_cfg.type,
                    description=adapter_cfg.description,
                )
            else:
                logger.warning(
                    f"Adapter '{adapter_cfg.name}' path not found, skipping: "
                    f"{adapter_cfg.resolved_path}"
                )

        # Set active adapter
        if adapters_config.active:
            if adapters_config.active in registry:
                registry.set_active(adapters_config.active)
            else:
                logger.warning(
                    f"Active adapter '{adapters_config.active}' not registered "
                    f"(path may not exist)"
                )

        return registry
