"""
Logging and debugging suite.

Provides colored terminal logs, verbosity modes, and exception pretty-printing.
"""

import sys
import traceback
from enum import Enum
from typing import Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.traceback import Traceback
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import logging


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ClaraLogger:
    """Structured logger for ML-Clara."""

    def __init__(
        self,
        name: str = "clara",
        level: LogLevel = LogLevel.INFO,
        use_colors: bool = True,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add handler
        if RICH_AVAILABLE and use_colors:
            handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
        else:
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, exc_info=None):
        """Log exception with traceback."""
        self.logger.exception(message, exc_info=exc_info)

    def device_detected(self, device_type: str, device_str: str):
        """Log device detection."""
        device_names = {
            "mps": "Apple Metal Performance Shaders",
            "cuda": "NVIDIA CUDA",
            "cpu": "CPU (no GPU acceleration)",
        }
        name = device_names.get(device_str, device_str)
        self.info(f"Using device: {device_str} ({name})")

    def model_loading(self, model_path: str):
        """Log model loading."""
        self.info(f"Loading model from: {model_path}")

    def adapter_loading(self, adapter_path: str):
        """Log adapter loading."""
        self.info(f"Loading adapter from: {adapter_path}")

    def generation_start(self, prompt_length: int, max_tokens: int):
        """Log generation start."""
        self.debug(f"Generating {max_tokens} tokens from {prompt_length} token prompt")

    def generation_complete(self, tokens_generated: int, time_taken: float):
        """Log generation completion."""
        self.info(
            f"Generated {tokens_generated} tokens in {time_taken:.2f}s "
            f"({tokens_generated/time_taken:.1f} tokens/s)"
        )


# Global logger instance
_logger: Optional[ClaraLogger] = None


def get_logger(
    name: str = "clara",
    level: Optional[LogLevel] = None,
    verbosity: Optional[int] = None,
) -> ClaraLogger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name
        level: Log level (overrides verbosity if set)
        verbosity: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3+=DEBUG)

    Returns:
        ClaraLogger instance
    """
    global _logger

    if level is None and verbosity is not None:
        level_map = {
            0: LogLevel.ERROR,
            1: LogLevel.WARNING,
            2: LogLevel.INFO,
        }
        level = level_map.get(verbosity, LogLevel.DEBUG)
    elif level is None:
        level = LogLevel.INFO

    if _logger is None:
        _logger = ClaraLogger(name=name, level=level)

    return _logger


def set_verbosity(verbosity: int):
    """Set global verbosity level."""
    logger = get_logger(verbosity=verbosity)
    level_map = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
    }
    logger.logger.setLevel(level_map.get(verbosity, logging.DEBUG))

