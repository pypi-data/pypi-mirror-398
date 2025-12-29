"""
Core inference engine.

Provides the main InferenceEngine class for text generation with:
- Greedy and sampling-based decoding
- Temperature, top_p, top_k sampling
- Repetition penalty
- Stop token detection
- Streaming output
- Chat conversation support
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator, Any

import torch
from transformers import PreTrainedModel

from ..tokenizer import TokenizerWrapper
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.0
    stop_tokens: list[str] | None = None
    stop_token_ids: list[int] | None = None
    seed: int | None = None
    do_sample: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.temperature < 0:
            raise ValueError("temperature must be >= 0")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError("top_p must be between 0 and 1")
        if self.top_k < 0:
            raise ValueError("top_k must be >= 0")
        if self.repetition_penalty < 1:
            raise ValueError("repetition_penalty must be >= 1")


@dataclass
class GenerationResult:
    """Result of generation."""

    text: str
    tokens: list[int]
    num_tokens: int
    stop_reason: str  # "max_tokens", "stop_token", "eos"
    generation_time: float = 0.0
    tokens_per_second: float = 0.0

    def __repr__(self) -> str:
        return (
            f"GenerationResult("
            f"num_tokens={self.num_tokens}, "
            f"stop_reason={self.stop_reason!r}, "
            f"tokens_per_second={self.tokens_per_second:.1f})"
        )


class InferenceEngine:
    """
    Main inference engine for text generation.

    Usage:
        from clara.models import load_model
        from clara.engine import InferenceEngine

        result = load_model(config)
        engine = InferenceEngine(result.model, result.tokenizer)
        output = engine.generate("Hello, how are you?")
        print(output.text)

    Example with streaming:
        for chunk in engine.generate_stream("Write a poem:"):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: TokenizerWrapper | Any,
        device: torch.device | None = None,
        default_config: GenerationConfig | None = None,
    ):
        """
        Initialize inference engine.

        Args:
            model: Loaded model (already on device)
            tokenizer: TokenizerWrapper instance or raw tokenizer
            device: Device for generation (inferred from model if None)
            default_config: Default generation configuration
        """
        self.model = model
        self._default_config = default_config or GenerationConfig()

        # Wrap tokenizer if needed
        if isinstance(tokenizer, TokenizerWrapper):
            self.tokenizer = tokenizer
        else:
            self.tokenizer = TokenizerWrapper(tokenizer)

        # Infer device from model
        if device is None:
            try:
                device = next(model.parameters()).device
            except StopIteration:
                device = torch.device("cpu")
        self.device = device

        logger.info(f"InferenceEngine initialized on {self.device}")

    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate text from prompt.

        Args:
            prompt: Input text
            config: Generation configuration
            **kwargs: Override config values

        Returns:
            GenerationResult with generated text and metadata
        """
        config = self._merge_config(config, kwargs)

        # Set seed for reproducibility
        if config.seed is not None:
            torch.manual_seed(config.seed)
            if self.device.type == "cuda":
                torch.cuda.manual_seed(config.seed)

        start_time = time.time()

        # Tokenize input
        input_ids = self._prepare_inputs(prompt)
        input_length = input_ids.shape[1]

        # Generate
        generated_tokens: list[int] = []
        stop_reason = "max_tokens"

        # Get stop token IDs
        stop_ids = self.tokenizer.get_stop_token_ids(config.stop_tokens)
        if config.stop_token_ids:
            stop_ids.extend(config.stop_token_ids)

        for token_id in self._generation_loop(input_ids, config, stop_ids):
            generated_tokens.append(token_id)

            # Check stop conditions
            stop_check = self._check_stop_condition(
                token_id,
                generated_tokens,
                config,
                stop_ids,
            )
            if stop_check:
                stop_reason = stop_check
                break

            if len(generated_tokens) >= config.max_new_tokens:
                break

        # Decode
        text = self.tokenizer.decode(generated_tokens)

        elapsed = time.time() - start_time
        tokens_per_second = len(generated_tokens) / elapsed if elapsed > 0 else 0

        return GenerationResult(
            text=text,
            tokens=generated_tokens,
            num_tokens=len(generated_tokens),
            stop_reason=stop_reason,
            generation_time=elapsed,
            tokens_per_second=tokens_per_second,
        )

    def generate_stream(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """
        Stream generated text token by token.

        Yields text chunks as they're generated.

        Args:
            prompt: Input text
            config: Generation configuration
            **kwargs: Override config values

        Yields:
            Text chunks
        """
        config = self._merge_config(config, kwargs)

        # Set seed for reproducibility
        if config.seed is not None:
            torch.manual_seed(config.seed)

        # Tokenize input
        input_ids = self._prepare_inputs(prompt)

        # Get stop token IDs
        stop_ids = self.tokenizer.get_stop_token_ids(config.stop_tokens)
        if config.stop_token_ids:
            stop_ids.extend(config.stop_token_ids)

        # Generate tokens
        generated_tokens: list[int] = []

        def token_generator() -> Iterator[int]:
            nonlocal generated_tokens
            for token_id in self._generation_loop(input_ids, config, stop_ids):
                generated_tokens.append(token_id)

                # Check stop conditions
                stop_check = self._check_stop_condition(
                    token_id,
                    generated_tokens,
                    config,
                    stop_ids,
                )
                if stop_check:
                    break

                if len(generated_tokens) >= config.max_new_tokens:
                    break

                yield token_id

        # Stream decode
        yield from self.tokenizer.decode_stream(token_generator())

    def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate response for chat messages.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts
            config: Generation configuration
            **kwargs: Override config values

        Returns:
            GenerationResult with assistant response
        """
        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        return self.generate(prompt, config, **kwargs)

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """
        Stream chat response token by token.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts
            config: Generation configuration
            **kwargs: Override config values

        Yields:
            Text chunks
        """
        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        yield from self.generate_stream(prompt, config, **kwargs)

    def _prepare_inputs(
        self,
        prompt: str,
    ) -> torch.Tensor:
        """
        Tokenize and prepare input tensors.

        Args:
            prompt: Input text

        Returns:
            Input IDs tensor on device
        """
        input_ids = self.tokenizer.encode(
            prompt,
            return_tensors="pt",
            truncation=True,
        )

        if isinstance(input_ids, torch.Tensor):
            return input_ids.to(self.device)

        return torch.tensor([input_ids], device=self.device)

    def _generation_loop(
        self,
        input_ids: torch.Tensor,
        config: GenerationConfig,
        stop_ids: list[int],
    ) -> Iterator[int]:
        """
        Core generation loop.

        Implements:
        - Greedy decoding (temperature=0 or do_sample=False)
        - Sampling with temperature
        - Top-p (nucleus) sampling
        - Top-k sampling
        - Repetition penalty

        Args:
            input_ids: Input token IDs
            config: Generation configuration
            stop_ids: Stop token IDs

        Yields:
            Generated token IDs
        """
        # Track all tokens for repetition penalty
        all_token_ids = input_ids.clone()

        # KV cache for efficient generation
        past_key_values = None

        with torch.no_grad():
            for _ in range(config.max_new_tokens):
                # Forward pass
                if past_key_values is None:
                    outputs = self.model(
                        input_ids=all_token_ids,
                        use_cache=True,
                    )
                else:
                    # Use only last token with cached KV
                    outputs = self.model(
                        input_ids=all_token_ids[:, -1:],
                        past_key_values=past_key_values,
                        use_cache=True,
                    )

                past_key_values = outputs.past_key_values
                logits = outputs.logits[:, -1, :]

                # Apply repetition penalty
                if config.repetition_penalty != 1.0:
                    logits = self._apply_repetition_penalty(
                        logits,
                        all_token_ids,
                        config.repetition_penalty,
                    )

                # Sample next token
                next_token_id = self._sample_next_token(logits, config)

                # Append to sequence
                all_token_ids = torch.cat(
                    [all_token_ids, next_token_id.unsqueeze(0).unsqueeze(0)],
                    dim=1,
                )

                yield next_token_id.item()

                # Check for stop tokens
                if next_token_id.item() in stop_ids:
                    break

    def _apply_repetition_penalty(
        self,
        logits: torch.Tensor,
        input_ids: torch.Tensor,
        penalty: float,
    ) -> torch.Tensor:
        """
        Apply repetition penalty to logits.

        Args:
            logits: Logits tensor [batch, vocab]
            input_ids: All token IDs so far
            penalty: Penalty factor (> 1.0 discourages repetition)

        Returns:
            Modified logits
        """
        # Get unique tokens in the sequence
        unique_tokens = input_ids[0].unique()

        # Apply penalty
        for token_id in unique_tokens:
            if logits[0, token_id] > 0:
                logits[0, token_id] /= penalty
            else:
                logits[0, token_id] *= penalty

        return logits

    def _sample_next_token(
        self,
        logits: torch.Tensor,
        config: GenerationConfig,
    ) -> torch.Tensor:
        """
        Sample next token from logits.

        Args:
            logits: Logits tensor [batch, vocab]
            config: Generation configuration

        Returns:
            Sampled token ID
        """
        # Greedy decoding
        if not config.do_sample or config.temperature == 0:
            return logits.argmax(dim=-1)[0]

        # Apply temperature
        if config.temperature != 1.0:
            logits = logits / config.temperature

        # Top-k filtering
        if config.top_k > 0:
            top_k = min(config.top_k, logits.size(-1))
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = float("-inf")

        # Top-p (nucleus) filtering
        if config.top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(
                torch.softmax(sorted_logits, dim=-1), dim=-1
            )

            # Remove tokens with cumulative probability above threshold
            sorted_indices_to_remove = cumulative_probs > config.top_p
            # Keep at least one token
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = False

            indices_to_remove = sorted_indices_to_remove.scatter(
                dim=-1, index=sorted_indices, src=sorted_indices_to_remove
            )
            logits[indices_to_remove] = float("-inf")

        # Sample from distribution
        probs = torch.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)

        return next_token[0, 0]

    def _check_stop_condition(
        self,
        token_id: int,
        generated_tokens: list[int],
        config: GenerationConfig,
        stop_ids: list[int],
    ) -> str | None:
        """
        Check if generation should stop.

        Args:
            token_id: Last generated token
            generated_tokens: All generated tokens
            config: Generation configuration
            stop_ids: Stop token IDs

        Returns:
            Stop reason or None to continue
        """
        # Check EOS
        if token_id == self.tokenizer.eos_token_id:
            return "eos"

        # Check stop token IDs
        if token_id in stop_ids:
            return "stop_token"

        # Check stop strings in generated text
        if config.stop_tokens:
            text = self.tokenizer.decode(generated_tokens)
            for stop_str in config.stop_tokens:
                if stop_str in text:
                    return "stop_token"

        return None

    def _merge_config(
        self,
        config: GenerationConfig | None,
        overrides: dict[str, Any],
    ) -> GenerationConfig:
        """
        Merge config with overrides.

        Args:
            config: Base configuration
            overrides: Override values

        Returns:
            Merged configuration
        """
        if config is None:
            config = self._default_config

        if not overrides:
            return config

        # Create new config with overrides
        config_dict = {
            "max_new_tokens": config.max_new_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repetition_penalty": config.repetition_penalty,
            "stop_tokens": config.stop_tokens,
            "stop_token_ids": config.stop_token_ids,
            "seed": config.seed,
            "do_sample": config.do_sample,
        }
        config_dict.update(overrides)

        return GenerationConfig(**config_dict)
