"""FastAPI server for ML-Clara.

This provides a small local web UI + JSON API for running `clara` without having
to use the CLI directly.
"""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]

