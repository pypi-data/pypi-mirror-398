"""
Tokenizer module.

Provides a wrapper around HuggingFace tokenizers with
convenience methods for BOS/EOS handling, streaming decode,
and chat template application.
"""

from .wrapper import TokenizerWrapper

__all__ = ["TokenizerWrapper"]
