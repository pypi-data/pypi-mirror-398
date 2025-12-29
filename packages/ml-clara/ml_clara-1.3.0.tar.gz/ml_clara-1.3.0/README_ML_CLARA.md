# ML-Clara

ML-Clara is a small, config-driven CLI + Python API for:

- Local LLM inference with streaming (`clara run`)
- Lightweight benchmarking (`clara eval`)
- LoRA fine-tuning (`clara train`) and adapter merging (`clara export`)
- Device auto-detection (MPS/CUDA/CPU)

This repository also contains Apple’s **CLaRa** research codebase; ML-Clara lives in the `clara/` package.

---

## Install

```bash
pip install ml-clara
clara info
```

If your platform needs a specific PyTorch build, install PyTorch first, then install ML-Clara.

---

## Quickstart

### Run

```bash
clara run "Explain LoRA in one paragraph" --model gpt2
clara run "Write a haiku about debugging" --model gpt2 --stream
```

### Create a config (recommended)

```bash
clara init-config --type default -o config.yaml
clara run "Hello" --config config.yaml
```

### Eval

```bash
clara eval --model gpt2 --benchmarks perplexity --samples 50
```

### Fine-tune (LoRA)

```bash
clara init-config --type finetune -o finetune.yaml
clara train --config finetune.yaml
```

### Web UI (FastAPI)

```bash
pip install "ml-clara[server]"
clara serve --model gpt2
```

Then open `http://127.0.0.1:8000`.

### Export (merge adapter)

```bash
clara export outputs/my-adapter/final --output models/merged
```

---

## Docs

- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Full repository README (CLaRa research + ML-Clara section): `README.md`
