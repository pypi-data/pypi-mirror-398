"""
Tokenizer wrapper module.

Provides a wrapper around HuggingFace tokenizers with:
- Automatic BOS/EOS insertion
- Streaming decode support
- Chat template application
- Consistent padding/truncation
"""

from __future__ import annotations

from typing import Iterator, Any

import torch
from transformers import PreTrainedTokenizer

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TokenizerWrapper:
    """
    Wrapper around HuggingFace tokenizer with convenience methods.

    Features:
    - Automatic BOS/EOS insertion
    - Streaming decode support
    - Chat template application
    - Consistent padding/truncation
    - Stop token detection

    Example:
        >>> from transformers import AutoTokenizer
        >>> base_tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
        >>> tokenizer = TokenizerWrapper(base_tokenizer)
        >>> tokens = tokenizer.encode("Hello, world!")
        >>> text = tokenizer.decode(tokens)
    """

    def __init__(
        self,
        tokenizer: PreTrainedTokenizer,
        add_bos: bool = True,
        add_eos: bool = False,
        max_length: int | None = None,
    ):
        """
        Initialize wrapper.

        Args:
            tokenizer: Base HuggingFace tokenizer
            add_bos: Automatically add BOS token
            add_eos: Automatically add EOS token (usually False for generation)
            max_length: Max sequence length (from tokenizer if None)
        """
        self._tokenizer = tokenizer
        self._add_bos = add_bos
        self._add_eos = add_eos

        # Get max_length with sanity check (some tokenizers have absurd values like 10^30)
        if max_length:
            self._max_length = max_length
        else:
            model_max = getattr(tokenizer, "model_max_length", 4096)
            # Cap at reasonable value to avoid overflow issues
            self._max_length = min(model_max, 32768) if model_max else 4096

        # Cache special token IDs
        self._bos_token_id = tokenizer.bos_token_id
        self._eos_token_id = tokenizer.eos_token_id
        self._pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id

        # For streaming decode
        self._decode_buffer: list[int] = []

        logger.debug(
            f"TokenizerWrapper initialized: "
            f"vocab_size={self.vocab_size}, "
            f"max_length={self._max_length}, "
            f"add_bos={add_bos}, add_eos={add_eos}"
        )

    @property
    def base_tokenizer(self) -> PreTrainedTokenizer:
        """Access the underlying HuggingFace tokenizer."""
        return self._tokenizer

    @property
    def bos_token_id(self) -> int | None:
        """BOS token ID."""
        return self._bos_token_id

    @property
    def eos_token_id(self) -> int | None:
        """EOS token ID."""
        return self._eos_token_id

    @property
    def pad_token_id(self) -> int | None:
        """Pad token ID (defaults to EOS if not set)."""
        return self._pad_token_id

    @property
    def vocab_size(self) -> int:
        """Vocabulary size."""
        return len(self._tokenizer)

    @property
    def max_length(self) -> int:
        """Maximum sequence length."""
        return self._max_length

    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        return_tensors: str | None = "pt",
        truncation: bool = True,
        max_length: int | None = None,
    ) -> list[int] | torch.Tensor:
        """
        Encode text to token IDs.

        Handles BOS/EOS based on wrapper settings.

        Args:
            text: Input text
            add_special_tokens: Add special tokens (respects wrapper settings)
            return_tensors: "pt" for PyTorch tensor, None for list
            truncation: Truncate to max_length
            max_length: Override max length

        Returns:
            Token IDs as list or tensor
        """
        max_len = max_length or self._max_length

        # Encode without special tokens first
        token_ids = self._tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=truncation,
            max_length=max_len - 2,  # Reserve space for BOS/EOS
        )

        # Add BOS/EOS based on settings
        if add_special_tokens:
            if self._add_bos and self._bos_token_id is not None:
                token_ids = [self._bos_token_id] + token_ids
            if self._add_eos and self._eos_token_id is not None:
                token_ids = token_ids + [self._eos_token_id]

        if return_tensors == "pt":
            return torch.tensor([token_ids], dtype=torch.long)

        return token_ids

    def decode(
        self,
        token_ids: list[int] | torch.Tensor,
        skip_special_tokens: bool = True,
        clean_up_tokenization_spaces: bool = True,
    ) -> str:
        """
        Decode token IDs to text.

        Args:
            token_ids: Token IDs (list or tensor)
            skip_special_tokens: Skip special tokens in output
            clean_up_tokenization_spaces: Clean up tokenization spaces

        Returns:
            Decoded text
        """
        if isinstance(token_ids, torch.Tensor):
            # Handle batch dimension
            if token_ids.dim() > 1:
                token_ids = token_ids[0]
            token_ids = token_ids.tolist()

        return self._tokenizer.decode(
            token_ids,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
        )

    def decode_stream(
        self,
        token_ids: Iterator[int],
        skip_special_tokens: bool = True,
    ) -> Iterator[str]:
        """
        Streaming decode for real-time output.

        Yields text chunks as tokens arrive.
        Handles multi-byte UTF-8 sequences correctly.

        Args:
            token_ids: Iterator of token IDs
            skip_special_tokens: Skip special tokens

        Yields:
            Text chunks as they become decodable
        """
        buffer: list[int] = []
        prev_text = ""

        for token_id in token_ids:
            # Skip special tokens if requested
            if skip_special_tokens:
                if token_id in [self._bos_token_id, self._eos_token_id, self._pad_token_id]:
                    continue

            buffer.append(token_id)

            # Try to decode the buffer
            try:
                text = self._tokenizer.decode(
                    buffer,
                    skip_special_tokens=skip_special_tokens,
                    clean_up_tokenization_spaces=False,
                )

                # Yield new characters
                if len(text) > len(prev_text):
                    new_text = text[len(prev_text):]
                    # Only yield if we have valid characters (handles partial UTF-8)
                    if new_text and not new_text.endswith("�"):
                        yield new_text
                        prev_text = text

            except Exception:
                # Buffer might contain partial multi-byte sequence
                continue

        # Flush any remaining buffer
        if buffer:
            try:
                text = self._tokenizer.decode(
                    buffer,
                    skip_special_tokens=skip_special_tokens,
                    clean_up_tokenization_spaces=True,
                )
                if len(text) > len(prev_text):
                    yield text[len(prev_text):]
            except Exception:
                pass

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        add_generation_prompt: bool = True,
        tokenize: bool = False,
    ) -> str | list[int]:
        """
        Apply chat template to messages.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts
            add_generation_prompt: Add assistant prompt for generation
            tokenize: Return token IDs instead of string

        Returns:
            Formatted prompt string or token IDs

        Example:
            >>> messages = [
            ...     {"role": "user", "content": "Hello!"},
            ... ]
            >>> prompt = tokenizer.apply_chat_template(messages)
        """
        if hasattr(self._tokenizer, "apply_chat_template"):
            return self._tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=add_generation_prompt,
                tokenize=tokenize,
            )
        else:
            # Fallback for tokenizers without chat template
            logger.warning(
                "Tokenizer does not support chat templates, using basic formatting"
            )
            formatted = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted += f"<|{role}|>\n{content}\n"

            if add_generation_prompt:
                formatted += "<|assistant|>\n"

            if tokenize:
                return self.encode(formatted, return_tensors=None)  # type: ignore

            return formatted

    def detect_stop(
        self,
        token_id: int,
        stop_token_ids: list[int] | None = None,
    ) -> bool:
        """
        Check if a token is a stop token.

        Args:
            token_id: Token ID to check
            stop_token_ids: Additional stop token IDs

        Returns:
            True if token is a stop token
        """
        # Check EOS
        if token_id == self._eos_token_id:
            return True

        # Check additional stop tokens
        if stop_token_ids and token_id in stop_token_ids:
            return True

        return False

    def get_stop_token_ids(
        self,
        stop_tokens: list[str] | None = None,
    ) -> list[int]:
        """
        Convert stop token strings to IDs.

        Args:
            stop_tokens: List of stop token strings

        Returns:
            List of stop token IDs
        """
        stop_ids: list[int] = []

        # Always include EOS
        if self._eos_token_id is not None:
            stop_ids.append(self._eos_token_id)

        # Convert string tokens to IDs
        if stop_tokens:
            for token in stop_tokens:
                token_ids = self._tokenizer.encode(token, add_special_tokens=False)
                if token_ids:
                    # Use the last token ID for multi-token strings
                    stop_ids.append(token_ids[-1])

        return list(set(stop_ids))

    def truncate_to_max_length(
        self,
        token_ids: list[int] | torch.Tensor,
        max_length: int | None = None,
        keep_end: bool = False,
    ) -> list[int] | torch.Tensor:
        """
        Truncate token sequence to max length.

        Args:
            token_ids: Token IDs
            max_length: Max length (uses wrapper default if None)
            keep_end: Keep end of sequence instead of start

        Returns:
            Truncated token IDs
        """
        max_len = max_length or self._max_length

        is_tensor = isinstance(token_ids, torch.Tensor)
        if is_tensor:
            if token_ids.dim() > 1:
                token_ids = token_ids[0]
            ids = token_ids.tolist()
        else:
            ids = list(token_ids)

        if len(ids) > max_len:
            if keep_end:
                ids = ids[-max_len:]
            else:
                ids = ids[:max_len]

        if is_tensor:
            return torch.tensor([ids], dtype=torch.long)

        return ids

    def __len__(self) -> int:
        """Return vocabulary size."""
        return self.vocab_size

    def __repr__(self) -> str:
        return (
            f"TokenizerWrapper("
            f"vocab_size={self.vocab_size}, "
            f"max_length={self._max_length}, "
            f"add_bos={self._add_bos}, "
            f"add_eos={self._add_eos})"
        )
