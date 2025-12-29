"""Memory profiling utilities."""

from __future__ import annotations

import gc
from dataclasses import dataclass

import torch

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryStats:
    """Memory statistics."""

    allocated_mb: float
    reserved_mb: float
    max_allocated_mb: float
    device: str


def get_memory_stats(device: torch.device | None = None) -> MemoryStats:
    """
    Get current memory statistics.

    Args:
        device: Device to check (auto-detect if None)

    Returns:
        MemoryStats with current memory usage
    """
    if device is None:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

    if device.type == "cuda":
        allocated = torch.cuda.memory_allocated(device) / 1024**2
        reserved = torch.cuda.memory_reserved(device) / 1024**2
        max_allocated = torch.cuda.max_memory_allocated(device) / 1024**2
    elif device.type == "mps":
        # MPS memory tracking
        try:
            allocated = torch.mps.current_allocated_memory() / 1024**2
        except AttributeError:
            # Older PyTorch versions
            allocated = 0.0
        reserved = allocated  # MPS doesn't distinguish
        max_allocated = allocated
    else:
        # CPU - use process memory
        try:
            import psutil

            process = psutil.Process()
            mem_info = process.memory_info()
            allocated = mem_info.rss / 1024**2
        except ImportError:
            allocated = 0.0
        reserved = allocated
        max_allocated = allocated

    return MemoryStats(
        allocated_mb=allocated,
        reserved_mb=reserved,
        max_allocated_mb=max_allocated,
        device=str(device),
    )


def clear_memory(device: torch.device | None = None) -> None:
    """
    Clear GPU/MPS memory cache.

    Args:
        device: Device to clear
    """
    gc.collect()

    if device is None:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            try:
                torch.mps.empty_cache()
            except AttributeError:
                pass  # Older PyTorch
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    elif device.type == "mps":
        try:
            torch.mps.empty_cache()
        except AttributeError:
            pass

    logger.debug("Memory cache cleared")


def log_memory_stats(prefix: str = "") -> None:
    """Log current memory statistics."""
    stats = get_memory_stats()
    msg = f"{prefix}Memory: {stats.allocated_mb:.1f}MB allocated"
    if stats.device not in ["cpu", "cpu:0"]:
        msg += f", {stats.reserved_mb:.1f}MB reserved"
    logger.info(msg)
