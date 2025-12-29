from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from clara.config import load_config
from clara.engine import GenerationConfig, InferenceEngine
from clara.models import ModelLoadResult, load_model


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


@dataclass(frozen=True)
class EngineBundle:
    engine: InferenceEngine
    model_path: str
    adapter_name: str | None


class EngineProvider(Protocol):
    def get(self, config: dict[str, Any]) -> EngineBundle: ...


def _config_key(config: dict[str, Any]) -> tuple[Any, ...]:
    model = config.get("model", {}) if isinstance(config.get("model"), dict) else {}
    adapters = config.get("adapters", {}) if isinstance(config.get("adapters"), dict) else {}
    legacy_adapter = config.get("adapter", {}) if isinstance(config.get("adapter"), dict) else {}

    return (
        model.get("local_path") or model.get("hf_id"),
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

            result: ModelLoadResult = load_model(config)
            engine = InferenceEngine(result.model, result.tokenizer)
            bundle = EngineBundle(engine=engine, model_path=result.model_path, adapter_name=result.adapter_name)

            self._cached_key = key
            self._cached_bundle = bundle
            return bundle


def _resolve_config(
    request: GenerateRequest,
    base_config: dict[str, Any] | None,
) -> dict[str, Any]:
    if request.config_path:
        cfg = load_config(request.config_path)
    elif base_config is not None:
        cfg = json.loads(json.dumps(base_config))  # cheap deep copy for primitives
    else:
        cfg = {"model": {"hf_id": request.model or DEFAULT_MODEL, "dtype": "auto"}}

    if request.model:
        cfg.setdefault("model", {})
        if isinstance(cfg["model"], dict):
            cfg["model"]["hf_id"] = request.model
        else:
            cfg["model"] = {"hf_id": request.model}

    # Ensure config provenance exists when a config file is used
    if request.config_path and "config_path" not in cfg:
        path = Path(request.config_path).expanduser().resolve()
        cfg["config_path"] = str(path)
        cfg["config_dir"] = str(path.parent)

    return cfg


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
    input, textarea {
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
        <input id="model" value="gpt2" placeholder="e.g. gpt2 or mistralai/Mistral-7B-Instruct-v0.2" />

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

    function setBusy(busy) {
      btnRun.disabled = busy;
      btnStream.disabled = busy;
      btnStop.disabled = !busy;
    }

    function payload() {
      return {
        prompt: el("prompt").value,
        model: el("model").value || null,
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

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _ui_html()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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
        cfg = {"model": {"hf_id": model_override, "dtype": "auto"}}

    if cfg is not None and model_override:
        cfg.setdefault("model", {})
        if isinstance(cfg["model"], dict):
            cfg["model"]["hf_id"] = model_override
        else:
            cfg["model"] = {"hf_id": model_override}

    return cfg


# For `uvicorn clara.server.app:app`
app = create_app(base_config=_base_config_from_env())
