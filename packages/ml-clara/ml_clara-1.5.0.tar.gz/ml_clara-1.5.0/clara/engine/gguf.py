"""
GGUF (llama.cpp) inference engine.

This module provides an optional GGUF backend via `llama-cpp-python`.

Design goals (v1.5 scope):
- Inference-only backend for `clara run` and `clara serve`
- No evaluation/training integration
- Optional dependency (import only when used)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, Iterator

from .inference import GenerationConfig, GenerationResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GGUFDependencyError(RuntimeError):
    """Raised when GGUF support is requested but dependencies are missing."""


@dataclass(frozen=True)
class GGUFLoadConfig:
    """
    Configuration for GGUF model loading.

    Notes:
    - `llama-cpp-python` must be installed (ideally with Metal/CUDA enabled).
    - `n_gpu_layers` controls offloading (Metal/CUDA depending on build).
    """

    model_path: str
    n_ctx: int = 4096
    n_threads: int | None = None
    n_gpu_layers: int = 0
    seed: int | None = None
    verbose: bool = False


def _map_finish_reason(finish_reason: str | None) -> str:
    if finish_reason == "length":
        return "max_tokens"
    if finish_reason in {"stop", "eos_token"}:
        return "stop_token"
    return "stop_token"


class GGUFEngine:
    """
    Minimal GGUF engine using llama.cpp via `llama-cpp-python`.

    The engine API mirrors `InferenceEngine` where possible:
    - generate / generate_stream
    - chat / chat_stream (simple formatting fallback)
    - count_tokens helpers for token accounting
    """

    def __init__(self, cfg: GGUFLoadConfig, **llama_kwargs: Any) -> None:
        self.cfg = cfg
        self.model_path = cfg.model_path

        try:
            from llama_cpp import Llama  # type: ignore
        except Exception as e:
            raise GGUFDependencyError(
                "GGUF backend requested but `llama-cpp-python` is not installed. "
                "Install with: pip install 'ml-clara[gguf]'"
            ) from e

        import inspect

        supported = set(inspect.signature(Llama.__init__).parameters)
        init_kwargs: dict[str, Any] = {}

        def set_if_supported(key: str, value: Any) -> None:
            if key in supported:
                init_kwargs[key] = value

        set_if_supported("model_path", cfg.model_path)
        set_if_supported("n_ctx", cfg.n_ctx)
        set_if_supported("verbose", cfg.verbose)
        if cfg.n_threads is not None:
            set_if_supported("n_threads", cfg.n_threads)
        if cfg.n_gpu_layers is not None:
            set_if_supported("n_gpu_layers", cfg.n_gpu_layers)
        if cfg.seed is not None:
            set_if_supported("seed", cfg.seed)

        init_kwargs.update(llama_kwargs)

        self._llm = Llama(**init_kwargs)
        logger.info(f"GGUFEngine initialized: {cfg.model_path}")

    def count_tokens(self, text: str) -> int:
        tokens = self._llm.tokenize(text.encode("utf-8"), add_bos=False, special=False)
        return len(tokens)

    def render_chat_prompt(self, messages: list[dict[str, str]]) -> str:
        lines: list[str] = []
        for msg in messages:
            role = (msg.get("role") or "user").strip()
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            if role == "system":
                lines.append(f"System: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            else:
                lines.append(f"User: {content}")
        lines.append("Assistant:")
        return "\n".join(lines).strip() + " "

    def count_chat_prompt_tokens(self, messages: list[dict[str, str]]) -> int:
        return self.count_tokens(self.render_chat_prompt(messages))

    def _merge_config(
        self,
        config: GenerationConfig | None,
        overrides: dict[str, Any],
    ) -> GenerationConfig:
        if config is None:
            config = GenerationConfig()
        if not overrides:
            return config
        data = {
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
        data.update(overrides)
        return GenerationConfig(**data)

    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        config = self._merge_config(config, kwargs)

        start = time.time()
        resp = self._llm.create_completion(
            prompt=prompt,
            max_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repetition_penalty,
            stop=config.stop_tokens or None,
            stream=False,
        )
        choice = (resp.get("choices") or [{}])[0]
        text = choice.get("text") or ""
        stop_reason = _map_finish_reason(choice.get("finish_reason"))

        token_ids = self._llm.tokenize(text.encode("utf-8"), add_bos=False, special=False)
        elapsed = time.time() - start
        tps = len(token_ids) / elapsed if elapsed > 0 else 0.0

        return GenerationResult(
            text=text,
            tokens=token_ids,
            num_tokens=len(token_ids),
            stop_reason=stop_reason,
            generation_time=elapsed,
            tokens_per_second=tps,
        )

    def generate_stream(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        config = self._merge_config(config, kwargs)
        stream = self._llm.create_completion(
            prompt=prompt,
            max_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repetition_penalty,
            stop=config.stop_tokens or None,
            stream=True,
        )
        for evt in stream:
            choice = (evt.get("choices") or [{}])[0]
            chunk = choice.get("text") or ""
            if chunk:
                yield chunk

    def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        return self.generate(self.render_chat_prompt(messages), config, **kwargs)

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> Iterable[str]:
        yield from self.generate_stream(self.render_chat_prompt(messages), config, **kwargs)
