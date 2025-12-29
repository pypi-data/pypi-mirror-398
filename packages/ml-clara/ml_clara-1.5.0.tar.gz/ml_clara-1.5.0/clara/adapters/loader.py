"""Adapter loading and merging operations."""

from __future__ import annotations

from transformers import PreTrainedModel

from .exceptions import AdapterCompatibilityError
from .registry import AdapterMetadata, AdapterRegistry
from ..utils.logging import get_logger

logger = get_logger(__name__)


def validate_adapter_compatibility(
    adapter: AdapterMetadata,
    model: PreTrainedModel,
    strict: bool = True,
) -> None:
    """
    Validate that adapter is compatible with base model.

    Checks:
    - Target modules exist in model
    - Base model name matches (if specified in adapter)

    Args:
        adapter: Adapter metadata
        model: Base model to check against
        strict: If True, raise on any mismatch. If False, warn only.

    Raises:
        AdapterCompatibilityError: Adapter incompatible with model
    """
    model_modules = set(name for name, _ in model.named_modules())

    # Check target modules exist
    if adapter.target_modules:
        missing = []
        for target in adapter.target_modules:
            # Target modules can be partial names
            # e.g., "q_proj" matches "model.layers.0.self_attn.q_proj"
            found = any(target in module for module in model_modules)
            if not found:
                missing.append(target)

        if missing:
            msg = f"Target modules not found in model: {missing}"
            if strict:
                raise AdapterCompatibilityError(
                    adapter.name,
                    msg,
                    adapter_info={"target_modules": adapter.target_modules},
                    model_info={"sample_modules": list(model_modules)[:10]},
                )
            else:
                logger.warning(f"Adapter '{adapter.name}': {msg}")

    # Check base model name if specified
    if adapter.base_model_name:
        # This is a soft check - model configs vary
        model_name = getattr(model.config, "_name_or_path", None)
        if model_name and adapter.base_model_name not in model_name:
            msg = (
                f"Adapter was trained on '{adapter.base_model_name}', "
                f"but loading into '{model_name}'"
            )
            if strict:
                logger.warning(f"Adapter '{adapter.name}': {msg}")
            else:
                logger.info(f"Adapter '{adapter.name}': {msg}")


def merge_adapter(
    model: PreTrainedModel,
    adapter: AdapterMetadata,
    validate: bool = True,
) -> PreTrainedModel:
    """
    Merge adapter into base model.

    Uses PEFT's merge_and_unload for clean merged weights.

    Args:
        model: Base model
        adapter: Adapter metadata with path
        validate: Run compatibility checks before merge

    Returns:
        Merged model (original model is modified)

    Raises:
        AdapterCompatibilityError: Adapter cannot be merged
    """
    logger.info(f"Merging adapter: {adapter.name} from {adapter.path}")

    try:
        from peft import PeftModel
    except ImportError:
        raise AdapterCompatibilityError(
            adapter.name,
            "PEFT library not installed. Install with: pip install peft",
        )

    # Validate compatibility
    if validate:
        validate_adapter_compatibility(adapter, model, strict=False)

    try:
        # Load adapter
        model = PeftModel.from_pretrained(model, str(adapter.path))

        # Merge and unload for clean inference
        model = model.merge_and_unload()

        logger.info(f"Successfully merged adapter: {adapter.name}")

    except Exception as e:
        raise AdapterCompatibilityError(
            adapter.name,
            f"Failed to merge: {e}",
            adapter_info={
                "path": str(adapter.path),
                "type": adapter.type,
                "rank": adapter.rank,
            },
        )

    return model


def load_adapter_from_registry(
    model: PreTrainedModel,
    registry: AdapterRegistry,
    adapter_name: str | None = None,
    validate: bool = True,
) -> tuple[PreTrainedModel, AdapterMetadata | None]:
    """
    Load and merge an adapter from the registry.

    Args:
        model: Base model
        registry: Adapter registry
        adapter_name: Name of adapter to load (uses active if None)
        validate: Run compatibility checks

    Returns:
        (merged_model, adapter_metadata) tuple
        adapter_metadata is None if no adapter was loaded
    """
    # Determine which adapter to use
    if adapter_name:
        adapter = registry.get(adapter_name)
    else:
        adapter = registry.get_active()

    if adapter is None:
        logger.info("No adapter to load")
        return model, None

    # Merge adapter
    merged_model = merge_adapter(model, adapter, validate=validate)

    return merged_model, adapter
