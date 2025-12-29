"""
User-facing error helpers.

This module centralizes error-to-message mapping for:
- CLI output (human-friendly guidance)
- OpenAI-compatible server errors (/v1/* endpoints)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clara.models.exceptions import (
    AdapterIncompatibleError,
    ChecksumConfigError,
    ChecksumMismatchError,
    ModelLoadError,
    ModelNotFoundError,
)


@dataclass(frozen=True)
class OpenAIErrorSpec:
    message: str
    type: str = "invalid_request_error"
    code: str | None = None
    status_code: int = 400


def _unwrap_cause(exc: Exception) -> Exception:
    """
    Best-effort unwrapping of nested exceptions.

    - `ModelLoadError` has a `.cause`
    - Python exceptions may have `__cause__` / `__context__`
    """
    if isinstance(exc, ModelLoadError) and exc.cause is not None:
        return _unwrap_cause(exc.cause)
    if getattr(exc, "__cause__", None) is not None:
        return _unwrap_cause(exc.__cause__)  # type: ignore[arg-type]
    if getattr(exc, "__context__", None) is not None:
        return _unwrap_cause(exc.__context__)  # type: ignore[arg-type]
    return exc


def openai_error_from_exception(exc: Exception) -> OpenAIErrorSpec:
    """
    Map an exception to an OpenAI-style error response spec.
    """
    root = _unwrap_cause(exc)

    # Optional dependency errors (GGUF backend)
    try:
        from clara.engine.gguf import GGUFDependencyError  # local import to keep optional
    except Exception:  # pragma: no cover
        GGUFDependencyError = None  # type: ignore

    if GGUFDependencyError is not None and isinstance(root, GGUFDependencyError):  # type: ignore[arg-type]
        return OpenAIErrorSpec(
            message=str(root),
            code="missing_dependency",
            status_code=400,
        )

    if isinstance(root, ChecksumMismatchError):
        return OpenAIErrorSpec(message=str(root), code="checksum_mismatch", status_code=400)

    if isinstance(root, ChecksumConfigError):
        return OpenAIErrorSpec(message=str(root), code="checksum_config_error", status_code=400)

    if isinstance(root, FileNotFoundError):
        msg = str(root)
        if not msg:
            msg = "File not found"
        return OpenAIErrorSpec(message=msg, code="file_not_found", status_code=400)

    if isinstance(root, ModelNotFoundError):
        return OpenAIErrorSpec(message=str(root), code="model_not_found", status_code=400)

    if isinstance(root, AdapterIncompatibleError):
        return OpenAIErrorSpec(message=str(root), code="adapter_incompatible", status_code=400)

    if isinstance(root, ModelLoadError):
        return OpenAIErrorSpec(message=str(root), code="model_load_error", status_code=400)

    # Fallback
    return OpenAIErrorSpec(message=str(exc) or "Internal error", type="internal_error", status_code=500)


def format_cli_error(exc: Exception) -> str:
    """
    Return a concise, actionable CLI error message.
    """
    spec = openai_error_from_exception(exc)
    msg = spec.message.strip() if spec.message else "Error"

    # Add actionable hints for common cases.
    root = _unwrap_cause(exc)
    try:
        from clara.engine.gguf import GGUFDependencyError  # type: ignore
    except Exception:  # pragma: no cover
        GGUFDependencyError = None  # type: ignore

    if GGUFDependencyError is not None and isinstance(root, GGUFDependencyError):  # type: ignore[arg-type]
        return (
            f"{msg}\n\n"
            "Hint: install GGUF support with `pip install \"ml-clara[gguf]\"` "
            "(or `pip install \"ml-clara[server,gguf]\"` for serving)."
        )

    if isinstance(root, ChecksumMismatchError):
        return f"{msg}\n\nHint: ensure you are using the correct file, or update `model.sha256` in your config."

    if isinstance(root, ChecksumConfigError):
        return f"{msg}\n\nHint: set `model.sha256` to a 64-char hex string (file) or a mapping (dir)."

    if isinstance(root, FileNotFoundError):
        return f"{msg}\n\nHint: check the path and permissions."

    if isinstance(root, ModelNotFoundError):
        return f"{msg}\n\nHint: pass `--model ...` or set `model.hf_id` / `model.local_path` in your config."

    return msg


def print_cli_traceback(exc: Exception) -> None:
    """
    Print a traceback for debugging (prefers Rich if available).

    Intended to be used when `--verbose` is enabled.
    """
    try:
        from rich.console import Console  # type: ignore
        from rich.traceback import Traceback  # type: ignore

        console = Console(stderr=True)
        tb = Traceback.from_exception(type(exc), exc, exc.__traceback__, show_locals=False)
        console.print(tb)
    except Exception:
        import traceback

        traceback.print_exception(type(exc), exc, exc.__traceback__)
