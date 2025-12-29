from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from clara.config import load_config
from clara.engine import GenerationConfig
from clara.engine.factory import load_engine
from clara.utils.errors import OpenAIErrorSpec, openai_error_from_exception


DEFAULT_MODEL = "gpt2"


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)

    # Config resolution:
    # - if config_path provided, load that file
    # - else use base_config from server startup (if any)
    # - else build a tiny config from `model`
    config_path: str | None = None
    model: str | None = None

    # Generation overrides
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1


class GenerateResponse(BaseModel):
    text: str
    num_tokens: int
    tokens_per_second: float
    model_path: str
    adapter_name: str | None = None


class OpenAIChatMessage(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class OpenAIChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str | None = None
    messages: list[OpenAIChatMessage] = Field(default_factory=list)
    stream: bool = False

    # OpenAI-ish generation params
    max_tokens: int | None = None
    temperature: float = 0.7
    top_p: float = 0.9
    stop: str | list[str] | None = None
    seed: int | None = None

    # ML-Clara extensions (optional)
    config_path: str | None = None
    top_k: int = 50
    repetition_penalty: float = 1.1


@dataclass(frozen=True)
class EngineBundle:
    engine: Any
    model_path: str
    adapter_name: str | None


class EngineProvider(Protocol):
    def get(self, config: dict[str, Any]) -> EngineBundle: ...


def _config_key(config: dict[str, Any]) -> tuple[Any, ...]:
    model = config.get("model", {}) if isinstance(config.get("model"), dict) else {}
    adapters = config.get("adapters", {}) if isinstance(config.get("adapters"), dict) else {}
    legacy_adapter = config.get("adapter", {}) if isinstance(config.get("adapter"), dict) else {}
    gguf = model.get("gguf", {}) if isinstance(model.get("gguf"), dict) else {}

    def pick_gguf(key: str) -> Any:
        return gguf.get(key, model.get(key))

    return (
        model.get("local_path") or model.get("hf_id"),
        model.get("backend"),
        pick_gguf("n_ctx"),
        pick_gguf("n_threads"),
        pick_gguf("n_gpu_layers"),
        model.get("dtype"),
        model.get("architecture"),
        bool(model.get("trust_remote_code")),
        adapters.get("active"),
        json.dumps(adapters.get("available", []), sort_keys=True, default=str),
        bool(legacy_adapter.get("enabled")),
        legacy_adapter.get("path"),
    )


class DefaultEngineProvider:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cached_key: tuple[Any, ...] | None = None
        self._cached_bundle: EngineBundle | None = None

    def get(self, config: dict[str, Any]) -> EngineBundle:
        key = _config_key(config)
        if self._cached_bundle is not None and key == self._cached_key:
            return self._cached_bundle

        with self._lock:
            if self._cached_bundle is not None and key == self._cached_key:
                return self._cached_bundle

            loaded = load_engine(config)
            bundle = EngineBundle(
                engine=loaded.engine,
                model_path=loaded.model_path,
                adapter_name=loaded.adapter_name,
            )

            self._cached_key = key
            self._cached_bundle = bundle
            return bundle


def _resolve_config(
    request: GenerateRequest,
    base_config: dict[str, Any] | None,
) -> dict[str, Any]:
    return _resolve_config_from_inputs(request.config_path, request.model, base_config)


def _resolve_config_from_inputs(
    config_path: str | None,
    model: str | None,
    base_config: dict[str, Any] | None,
) -> dict[str, Any]:
    if config_path:
        cfg = load_config(config_path)
    elif base_config is not None:
        cfg = json.loads(json.dumps(base_config))  # cheap deep copy for primitives
    else:
        cfg = {"model": {"hf_id": model or DEFAULT_MODEL, "dtype": "auto"}}

    if model:
        cfg.setdefault("model", {})
        if not isinstance(cfg["model"], dict):
            cfg["model"] = {}

        candidate = Path(model).expanduser()
        if candidate.exists():
            cfg["model"]["local_path"] = str(candidate)
            cfg["model"].pop("hf_id", None)
        else:
            cfg["model"]["hf_id"] = model
            cfg["model"].pop("local_path", None)

    # Ensure config provenance exists when a config file is used
    if config_path and "config_path" not in cfg:
        path = Path(config_path).expanduser().resolve()
        cfg["config_path"] = str(path)
        cfg["config_dir"] = str(path.parent)

    return cfg


def _openai_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _openai_finish_reason(stop_reason: str) -> str:
    if stop_reason == "max_tokens":
        return "length"
    return "stop"


def _normalize_stop(stop: str | list[str] | None) -> list[str] | None:
    if stop is None:
        return None
    if isinstance(stop, str):
        return [stop]
    return [s for s in stop if s]


def _openai_error_response(spec: OpenAIErrorSpec) -> JSONResponse:
    return JSONResponse(
        status_code=spec.status_code,
        content={"error": {"message": spec.message, "type": spec.type, "code": spec.code}},
    )


def _validation_error_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid request"

    first = errors[0]
    loc = first.get("loc") or []
    msg = first.get("msg") or "Invalid request"

    loc_str = ".".join(str(p) for p in loc if p != "body")
    return f"{loc_str}: {msg}" if loc_str else str(msg)


def _ui_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ML-Clara</title>
  <style>
    :root {
      --bg: #0b0f17;
      --panel: #121a27;
      --panel2: #0f1622;
      --text: #e8eefc;
      --muted: #9bb0d1;
      --border: rgba(255,255,255,0.08);
      --accent: #6aa6ff;
      --accent2: #9f7bff;
      --danger: #ff6a6a;
      --ok: #53d18a;
      --shadow: 0 18px 60px rgba(0,0,0,0.45);
      --radius: 16px;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background:
        radial-gradient(1200px 600px at 10% 0%, rgba(106,166,255,0.18), transparent 55%),
        radial-gradient(900px 500px at 90% 10%, rgba(159,123,255,0.14), transparent 55%),
        radial-gradient(700px 500px at 50% 90%, rgba(83,209,138,0.10), transparent 60%),
        var(--bg);
    }
    header {
      max-width: 1100px;
      margin: 28px auto 14px;
      padding: 0 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .brand { display: flex; flex-direction: column; gap: 4px; }
    .brand h1 { font-size: 18px; margin: 0; letter-spacing: 0.2px; }
    .brand p { margin: 0; color: var(--muted); font-size: 13px; }
    .pill {
      font-family: var(--mono);
      font-size: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: rgba(255,255,255,0.04);
    }
    main {
      max-width: 1100px;
      margin: 0 auto 40px;
      padding: 0 18px;
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 14px;
    }
    @media (max-width: 980px) { main { grid-template-columns: 1fr; } }
    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .card .hd {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      background: rgba(255,255,255,0.03);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .card .hd h2 { margin: 0; font-size: 14px; letter-spacing: 0.2px; }
    .card .bd { padding: 14px 16px; }
    label { display: block; font-size: 12px; color: var(--muted); margin: 10px 0 6px; }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.25);
      color: var(--text);
      border-radius: 12px;
      padding: 10px 12px;
      outline: none;
    }
    textarea { min-height: 170px; resize: vertical; font-family: var(--sans); }
    input { font-family: var(--mono); font-size: 13px; }
    select { font-family: var(--mono); font-size: 13px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .btns { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
    button {
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      border-radius: 12px;
      padding: 10px 12px;
      font-weight: 600;
      cursor: pointer;
    }
    button.primary {
      border-color: rgba(106,166,255,0.35);
      background: linear-gradient(135deg, rgba(106,166,255,0.30), rgba(159,123,255,0.18));
    }
    button.danger { border-color: rgba(255,106,106,0.35); background: rgba(255,106,106,0.08); }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .meta {
      font-family: var(--mono);
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: var(--mono);
      font-size: 13px;
      line-height: 1.5;
      color: var(--text);
      background: rgba(0,0,0,0.22);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      min-height: 290px;
    }
    .status { display: inline-flex; align-items: center; gap: 8px; }
    .dot { width: 8px; height: 8px; border-radius: 999px; background: var(--muted); }
    .dot.ok { background: var(--ok); }
    .dot.bad { background: var(--danger); }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>ML-Clara</h1>
      <p>Local web UI for <span class="pill">clara</span> inference (FastAPI)</p>
    </div>
    <div class="status meta" id="health">
      <span class="dot" id="healthDot"></span>
      <span id="healthText">Checking…</span>
    </div>
  </header>

  <main>
    <section class="card">
      <div class="hd">
        <h2>Request</h2>
        <span class="pill">/api/generate</span>
      </div>
      <div class="bd">
        <label>Model (optional)</label>
        <select id="modelPreset">
          <option value="gpt2" selected>gpt2 (tiny / fast)</option>
          <option value="meta-llama/Meta-Llama-3.1-8B-Instruct">meta-llama/Meta-Llama-3.1-8B-Instruct</option>
          <option value="mistralai/Mistral-7B-Instruct-v0.2">mistralai/Mistral-7B-Instruct-v0.2</option>
          <option value="mistralai/Mistral-7B-Instruct-v0.3">mistralai/Mistral-7B-Instruct-v0.3</option>
          <option value="google/gemma-2-9b-it">google/gemma-2-9b-it</option>
          <option value="custom">Custom…</option>
        </select>
        <input id="modelCustom" placeholder="e.g. meta-llama/Meta-Llama-3.1-8B-Instruct" style="display:none; margin-top: 8px;" />

        <label>Config file path (optional)</label>
        <input id="configPath" placeholder="e.g. ./config.yaml" />

        <div class="row">
          <div>
            <label>Max new tokens</label>
            <input id="maxNewTokens" value="256" />
          </div>
          <div>
            <label>Temperature</label>
            <input id="temperature" value="0.7" />
          </div>
        </div>

        <div class="row">
          <div>
            <label>Top-p</label>
            <input id="topP" value="0.9" />
          </div>
          <div>
            <label>Top-k</label>
            <input id="topK" value="50" />
          </div>
        </div>

        <label>Prompt</label>
        <textarea id="prompt" placeholder="Ask something…">Explain LoRA in one paragraph.</textarea>

        <div class="btns">
          <button class="primary" id="btnRun">Run</button>
          <button id="btnStream">Stream</button>
          <button class="danger" id="btnStop" disabled>Stop</button>
        </div>

        <div class="meta" style="margin-top: 12px;">
          Tip: generate a config template with <span class="pill">clara init-config</span>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="hd">
        <h2>Output</h2>
        <span class="pill">text</span>
      </div>
      <div class="bd">
        <pre id="out"></pre>
        <div class="meta" id="meta" style="margin-top: 10px;"></div>
      </div>
    </section>
  </main>

  <script>
    const el = (id) => document.getElementById(id);
    const out = el("out");
    const meta = el("meta");
    const btnRun = el("btnRun");
    const btnStream = el("btnStream");
    const btnStop = el("btnStop");
    let aborter = null;

    const modelPreset = el("modelPreset");
    const modelCustom = el("modelCustom");

    function resolvedModel() {
      const preset = (modelPreset && modelPreset.value) ? modelPreset.value : "";
      if (preset === "custom") return (modelCustom.value || "").trim() || null;
      return preset || null;
    }

    function syncModelUI() {
      if (!modelPreset || !modelCustom) return;
      const showCustom = modelPreset.value === "custom";
      modelCustom.style.display = showCustom ? "block" : "none";
      if (showCustom) modelCustom.focus();
    }

    function setBusy(busy) {
      btnRun.disabled = busy;
      btnStream.disabled = busy;
      btnStop.disabled = !busy;
    }

    function payload() {
      return {
        prompt: el("prompt").value,
        model: resolvedModel(),
        config_path: el("configPath").value || null,
        max_new_tokens: Number(el("maxNewTokens").value || 256),
        temperature: Number(el("temperature").value || 0.7),
        top_p: Number(el("topP").value || 0.9),
        top_k: Number(el("topK").value || 50),
        repetition_penalty: 1.1,
      };
    }

    async function health() {
      try {
        const r = await fetch("/api/health");
        const j = await r.json();
        el("healthDot").className = "dot ok";
        el("healthText").textContent = "Ready";
      } catch (e) {
        el("healthDot").className = "dot bad";
        el("healthText").textContent = "Server error";
      }
    }

    btnStop.addEventListener("click", () => {
      if (aborter) aborter.abort();
    });

    btnRun.addEventListener("click", async () => {
      out.textContent = "";
      meta.textContent = "";
      setBusy(true);
      aborter = new AbortController();

      try {
        const r = await fetch("/api/generate", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload()),
          signal: aborter.signal,
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || "Request failed");
        out.textContent = j.text || "";
        meta.textContent = `model: ${j.model_path} • tokens: ${j.num_tokens} • speed: ${j.tokens_per_second.toFixed(1)} tok/s` + (j.adapter_name ? ` • adapter: ${j.adapter_name}` : "");
      } catch (e) {
        out.textContent = String(e);
      } finally {
        setBusy(false);
        aborter = null;
      }
    });

    btnStream.addEventListener("click", async () => {
      out.textContent = "";
      meta.textContent = "";
      setBusy(true);
      aborter = new AbortController();

      try {
        const r = await fetch("/api/stream", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload()),
          signal: aborter.signal,
        });
        if (!r.ok) {
          const j = await r.json();
          throw new Error(j.detail || "Request failed");
        }

        const reader = r.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const {value, done} = await reader.read();
          if (done) break;
          out.textContent += decoder.decode(value, {stream: true});
        }
      } catch (e) {
        out.textContent = String(e);
      } finally {
        setBusy(false);
        aborter = null;
      }
    });

    if (modelPreset) modelPreset.addEventListener("change", syncModelUI);
    syncModelUI();

    health();
  </script>
</body>
</html>"""


def create_app(
    *,
    base_config: dict[str, Any] | None = None,
    engine_provider: EngineProvider | None = None,
) -> FastAPI:
    app = FastAPI(title="ML-Clara")
    app.state.base_config = base_config
    app.state.engine_provider = engine_provider or DefaultEngineProvider()

    @app.exception_handler(RequestValidationError)
    async def openai_validation_handler(request: Request, exc: RequestValidationError):
        if request.url.path.startswith("/v1/"):
            return _openai_error_response(
                OpenAIErrorSpec(
                    message=_validation_error_message(exc),
                    code="invalid_request",
                    status_code=400,
                )
            )
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(StarletteHTTPException)
    async def openai_http_exception_handler(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/v1/"):
            detail = exc.detail
            message = detail if isinstance(detail, str) else json.dumps(detail)
            return _openai_error_response(
                OpenAIErrorSpec(
                    message=message,
                    code="http_error",
                    status_code=int(exc.status_code),
                )
            )
        return await http_exception_handler(request, exc)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _ui_html()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models")
    def openai_list_models() -> dict[str, Any]:
        model_id: str | None = None
        cfg = app.state.base_config
        if isinstance(cfg, dict) and isinstance(cfg.get("model"), dict):
            model_id = cfg["model"].get("local_path") or cfg["model"].get("hf_id")
        model_id = model_id or DEFAULT_MODEL

        created = int(time.time())
        return {
            "object": "list",
            "data": [
                {
                    "id": model_id,
                    "object": "model",
                    "created": created,
                    "owned_by": "ml-clara",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    def openai_chat_completions(req: OpenAIChatCompletionRequest):
        if not req.messages:
            return _openai_error_response(
                OpenAIErrorSpec(
                    message="messages must be non-empty",
                    code="invalid_request",
                    status_code=400,
                )
            )

        try:
            cfg = _resolve_config_from_inputs(req.config_path, req.model, app.state.base_config)
            bundle: EngineBundle = app.state.engine_provider.get(cfg)

            gen_cfg = GenerationConfig(
                max_new_tokens=req.max_tokens or 256,
                temperature=req.temperature,
                top_p=req.top_p,
                top_k=req.top_k,
                repetition_penalty=req.repetition_penalty,
                stop_tokens=_normalize_stop(req.stop),
                seed=req.seed,
            )

            messages = [m.model_dump() for m in req.messages]
            created = int(time.time())
            completion_id = _openai_id("chatcmpl")
            model_name = req.model or DEFAULT_MODEL

            if req.stream:

                def iterator() -> Iterable[bytes]:
                    # Initial chunk announces assistant role
                    yield (
                        f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': model_name, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
                    ).encode("utf-8")

                    try:
                        for chunk in bundle.engine.chat_stream(messages, gen_cfg):
                            payload = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model_name,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": chunk},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")

                        final_payload = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_name,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                        }
                        yield f"data: {json.dumps(final_payload)}\n\n".encode("utf-8")
                        yield b"data: [DONE]\n\n"
                    except Exception as e:
                        spec = openai_error_from_exception(e)
                        yield f"data: {json.dumps({'error': {'message': spec.message, 'type': spec.type, 'code': spec.code}})}\n\n".encode(
                            "utf-8"
                        )
                        yield b"data: [DONE]\n\n"

                return StreamingResponse(iterator(), media_type="text/event-stream")

            # Non-streaming response
            result = bundle.engine.chat(messages, gen_cfg)
            prompt_tokens = 0
            if hasattr(bundle.engine, "count_chat_prompt_tokens"):
                try:
                    prompt_tokens = int(bundle.engine.count_chat_prompt_tokens(messages))
                except Exception:
                    prompt_tokens = 0
            elif hasattr(bundle.engine, "tokenizer"):
                prompt = bundle.engine.tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=False,
                )
                prompt_tokens = len(bundle.engine.tokenizer.encode(prompt, return_tensors=None))
            completion_tokens = result.num_tokens

            return {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": result.text},
                        "finish_reason": _openai_finish_reason(result.stop_reason),
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            return _openai_error_response(openai_error_from_exception(e))

    @app.post("/api/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest) -> GenerateResponse:
        try:
            cfg = _resolve_config(req, app.state.base_config)
            bundle: EngineBundle = app.state.engine_provider.get(cfg)

            gen_cfg = GenerationConfig(
                max_new_tokens=req.max_new_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                top_k=req.top_k,
                repetition_penalty=req.repetition_penalty,
            )
            result = bundle.engine.generate(req.prompt, gen_cfg)

            return GenerateResponse(
                text=result.text,
                num_tokens=result.num_tokens,
                tokens_per_second=result.tokens_per_second,
                model_path=bundle.model_path,
                adapter_name=bundle.adapter_name,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/stream")
    def stream(req: GenerateRequest) -> StreamingResponse:
        try:
            cfg = _resolve_config(req, app.state.base_config)
            bundle: EngineBundle = app.state.engine_provider.get(cfg)

            gen_cfg = GenerationConfig(
                max_new_tokens=req.max_new_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                top_k=req.top_k,
                repetition_penalty=req.repetition_penalty,
            )

            def iterator() -> Iterable[bytes]:
                for chunk in bundle.engine.generate_stream(req.prompt, gen_cfg):
                    yield chunk.encode("utf-8")

            return StreamingResponse(iterator(), media_type="text/plain; charset=utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


def _base_config_from_env() -> dict[str, Any] | None:
    """
    Build an optional base config from environment variables.

    - `CLARA_SERVER_CONFIG`: path to a YAML/JSON config file
    - `CLARA_SERVER_MODEL`: Hugging Face model id override
    """
    cfg: dict[str, Any] | None = None

    config_path = os.getenv("CLARA_SERVER_CONFIG")
    model_override = os.getenv("CLARA_SERVER_MODEL")

    if config_path:
        cfg = load_config(config_path)

    if cfg is None and model_override:
        candidate = Path(model_override).expanduser()
        if candidate.exists():
            cfg = {"model": {"local_path": str(candidate), "dtype": "auto"}}
        else:
            cfg = {"model": {"hf_id": model_override, "dtype": "auto"}}

    if cfg is not None and model_override:
        cfg.setdefault("model", {})
        if not isinstance(cfg["model"], dict):
            cfg["model"] = {}

        candidate = Path(model_override).expanduser()
        if candidate.exists():
            cfg["model"]["local_path"] = str(candidate)
            cfg["model"].pop("hf_id", None)
        else:
            cfg["model"]["hf_id"] = model_override
            cfg["model"].pop("local_path", None)

    return cfg


# For `uvicorn clara.server.app:app`
app = create_app(base_config=_base_config_from_env())
