## ML-Clara: Production-Ready CLI for Local LLMs

ML-Clara is a high-performance, config-driven CLI and Python API built to simplify local LLM inference, evaluation, and fine-tuning.

### 🚀 Key Features

- **Device Auto-Detection**: Optimized support for **Apple Silicon (MPS)**, NVIDIA CUDA, and CPU.
- **Fast Inference**: Token-by-token streaming with highly optimized engine.
- **Unified CLI**: Run, evaluate, and fine-tune models with a single command.
- **Multi-Adapter Support**: Load and merge PEFT/LoRA adapters on the fly.
- **Benchmark Suite**: Built-in Perplexity, HellaSwag, and ARC evaluation.
- **Web UI**: Built-in FastAPI server with a modern local web interface.

---

## 🛠️ Quick Start

### 1. Installation
```bash
pip install ml-clara
clara info
```

### 2. Generate Text
```bash
clara run "Explain quantum computing in simple terms" --stream
```

### 3. Start Web UI
```bash
pip install "ml-clara[server]"
clara serve --model gpt2 --port 9123
```
Open `http://127.0.0.1:9123`.

---

## 📚 Documentation

- **[Installation Guide](docs/getting_started.md)**: Setup and dependencies.
- **[CLI Reference](README_ML_CLARA.md)**: Full command list and examples.
- **[Benchmarking](docs/BENCHMARKING.md)**: Measure TTFT, throughput, and memory.
- **[Apple Silicon Setup](MAC_SETUP.md)**: Optimization for Mac users.
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and fixes.

---

## 🧪 Research & Methodology (CLaRa)

This repository also serves as the official open-source release for **CLaRa**, a state-of-the-art end-to-end RAG model.

<div align="center">
  <img src="figs/clara_logo.jpg" width="300"/>
</div>

### Motivation
Retrieval-Augmented Generation (RAG) suffers from long contexts and disjoint optimization. CLaRa introduces document compression techniques to improve RAG efficiency, achieving **32x-64x compression** while preserving semantic accuracy.

### Three-Stage Training
1. **Stage 1: Compression Pretraining**: Semantic preservation via SCP framework.
2. **Stage 2: Instruction Tuning**: Downstream QA optimization.
3. **Stage 3: End-to-End Fine-tuning**: Joint reranker and generator training.

[Read the full CLaRa paper on arXiv](https://arxiv.org/abs/2511.18659)

---

## 📊 Benchmark Results

CLaRa consistently outperforms baselines across different compression ratios on standard QA datasets (NQ, HotpotQA, MuSiQue, 2Wiki).

| Model | CR | Avg Score | Status |
|:---|:---:|:---:|:---|
| Mistral-7B w/ retrieval | - | 37.67 | Baseline |
| **CLaRa (CR=32)** | **32** | **38.82** | ✅ Superior |

---

## Citation

```bibtex
@misc{he2025clarabridgingretrievalgeneration,
      title={CLaRa: Bridging Retrieval and Generation with Continuous Latent Reasoning},
      author={Jie He and Richard He Bai and Sinead Williamson and Jeff Z. Pan and Navdeep Jaitly and Yizhe Zhang},
      year={2025},
      eprint={2511.18659},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2511.18659},
}
```
