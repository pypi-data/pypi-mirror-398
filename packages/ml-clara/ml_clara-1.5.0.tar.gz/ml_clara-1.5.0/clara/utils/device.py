"""
Device detection and management module.

Provides automatic device detection (MPS, CUDA, CPU) with configuration overrides.
"""

import os
from enum import Enum
from typing import Optional, Literal
import torch


class DeviceType(str, Enum):
    """Supported device types."""
    MPS = "mps"  # Apple Silicon GPU
    CUDA = "cuda"  # NVIDIA GPU
    CPU = "cpu"  # CPU fallback


def detect_device(
    override: Optional[str] = None,
    prefer_mps: bool = True,
    prefer_cuda: bool = True,
) -> tuple[DeviceType, str]:
    """
    Automatically detect the best available device.

    Args:
        override: Force a specific device ("mps", "cuda", "cpu")
        prefer_mps: Prefer MPS over CUDA if both available (default: True)
        prefer_cuda: Prefer CUDA over CPU if available (default: True)

    Returns:
        Tuple of (DeviceType enum, device string)

    Example:
        >>> device_type, device_str = detect_device()
        >>> print(f"Using {device_type}")
    """
    # Check for override (env var or parameter)
    if override is None:
        override = os.environ.get("CLARA_DEVICE")

    if override:
        override = override.lower()
        if override in ["mps", "cuda", "cpu"]:
            device_str = override
            device_type = DeviceType(override)

            # Validate device is actually available
            if device_type == DeviceType.MPS:
                if not (torch.backends.mps.is_available() and torch.backends.mps.is_built()):
                    raise RuntimeError(
                        "MPS requested but not available. "
                        "PyTorch MPS support requires macOS 12.3+ and PyTorch 1.12+"
                    )
            elif device_type == DeviceType.CUDA:
                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "CUDA requested but not available. "
                        "Install PyTorch with CUDA support."
                    )

            return device_type, device_str

    # Automatic detection with priority
    if prefer_mps and torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return DeviceType.MPS, "mps"

    if prefer_cuda and torch.cuda.is_available():
        return DeviceType.CUDA, "cuda"

    # CPU fallback
    return DeviceType.CPU, "cpu"


def get_device_info(device: str) -> dict:
    """
    Get detailed information about a device.

    Args:
        device: Device string ("mps", "cuda", "cpu")

    Returns:
        Dictionary with device information
    """
    info = {
        "device": device,
        "type": device,
    }

    if device == "cuda" and torch.cuda.is_available():
        info.update({
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(0),
            "memory_total": torch.cuda.get_device_properties(0).total_memory,
            "memory_allocated": torch.cuda.memory_allocated(0),
            "memory_reserved": torch.cuda.memory_reserved(0),
        })
    elif device == "mps" and torch.backends.mps.is_available():
        info.update({
            "available": True,
            "built": torch.backends.mps.is_built(),
        })

    return info


# Convenience function matching PRD requirement
def get_device(override: Optional[str] = None) -> str:
    """
    Get device string (simplified interface).

    Args:
        override: Optional device override

    Returns:
        Device string ("mps", "cuda", or "cpu")
    """
    _, device_str = detect_device(override=override)
    return device_str

