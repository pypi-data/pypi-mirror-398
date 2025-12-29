"""FastAPI server tests (no real model loading)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

import pytest


@dataclass(frozen=True)
class _FakeGenerationResult:
    text: str
    tokens: list[int]
    num_tokens: int
    stop_reason: str
    tokens_per_second: float


class _FakeEngine:
    def generate(self, prompt: str, config: Any) -> _FakeGenerationResult:
        return _FakeGenerationResult(
            text=f"echo: {prompt}",
            tokens=[1, 2, 3],
            num_tokens=3,
            stop_reason="max_tokens",
            tokens_per_second=99.0,
        )

    def generate_stream(self, prompt: str, config: Any) -> Iterable[str]:
        yield "echo: "
        yield prompt

    def chat(self, messages: list[dict[str, str]], config: Any) -> _FakeGenerationResult:
        prompt = messages[-1].get("content", "")
        return self.generate(prompt, config)

    def chat_stream(self, messages: list[dict[str, str]], config: Any) -> Iterable[str]:
        prompt = messages[-1].get("content", "")
        yield from self.generate_stream(prompt, config)


class _FakeProvider:
    def __init__(self) -> None:
        self.engine = _FakeEngine()

    def get(self, config: dict[str, Any]):
        from clara.server.app import EngineBundle

        return EngineBundle(engine=self.engine, model_path="fake-model", adapter_name=None)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from clara.server.app import create_app

    app = create_app(base_config={"model": {"hf_id": "gpt2"}}, engine_provider=_FakeProvider())
    return TestClient(app)


def test_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ML-Clara" in r.text


def test_generate_json(client):
    r = client.post("/api/generate", json={"prompt": "hello"})
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "echo: hello"
    assert data["model_path"] == "fake-model"
    assert data["num_tokens"] == 3


def test_stream(client):
    with client.stream("POST", "/api/stream", json={"prompt": "hello"}) as r:
        assert r.status_code == 200
        text = "".join(r.iter_text())
        assert text == "echo: hello"


def test_openai_models(client):
    r = client.get("/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "list"
    assert data["data"][0]["id"]


def test_openai_chat_completions(client):
    r = client.post(
        "/v1/chat/completions",
        json={"model": "gpt2", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "echo: hello"
    assert data["choices"][0]["finish_reason"] in {"stop", "length"}


def test_openai_chat_completions_stream(client):
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={"model": "gpt2", "stream": True, "messages": [{"role": "user", "content": "hello"}]},
    ) as r:
        assert r.status_code == 200
        chunks: list[str] = []
        for line in r.iter_lines():
            if not line:
                continue
            assert line.startswith("data: ")
            payload = line.removeprefix("data: ")
            if payload == "[DONE]":
                break
            evt = json.loads(payload)
            delta = evt["choices"][0]["delta"]
            if "content" in delta:
                chunks.append(delta["content"])
        assert "".join(chunks) == "echo: hello"
