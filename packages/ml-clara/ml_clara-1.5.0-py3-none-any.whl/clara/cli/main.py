"""
CLI entry point for ML-Clara.

Provides commands for inference, evaluation, and system info.
"""

import click

from clara import __version__


@click.group()
@click.version_option(version=__version__, prog_name="clara")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """ML-Clara: Local LLM inference engine."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        import logging

        logging.getLogger("clara").setLevel(logging.DEBUG)


@cli.command()
@click.argument("prompt")
@click.option(
    "--model",
    "-m",
    type=str,
    help="Model name / HuggingFace ID / local path (dir or .gguf file)",
)
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option(
    "--max-tokens", "-n", type=int, default=256, help="Max tokens to generate"
)
@click.option("--temperature", "-t", type=float, default=0.7, help="Sampling temperature")
@click.option("--stream", "-s", is_flag=True, help="Stream output token by token")
@click.pass_context
def run(ctx, prompt, model, config, max_tokens, temperature, stream):
    """
    Generate text from a prompt.

    Examples:

        clara run "Explain quantum computing"

        clara run "Write a haiku" --model gpt2 --stream

        clara run "Hello" --config config.yaml --max-tokens 100
    """
    from pathlib import Path

    from clara import GenerationConfig
    from clara.config import load_config
    from clara.engine.factory import load_engine
    from clara.utils.errors import format_cli_error, print_cli_traceback

    verbose = bool((ctx.obj or {}).get("verbose"))

    try:
        # Load config
        if config:
            cfg = load_config(config)
        else:
            cfg = {
                "model": {
                    "hf_id": model or "mistralai/Mistral-7B-Instruct-v0.2",
                    "dtype": "auto",
                }
            }

        # Optional CLI override
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

        click.echo("Loading model...", err=True)
        loaded = load_engine(cfg)

        click.echo(f"Model loaded: {loaded.model_path} ({loaded.backend})", err=True)

        engine = loaded.engine
        gen_config = GenerationConfig(
            max_new_tokens=max_tokens,
            temperature=temperature,
        )

        prompt_tokens = 0
        if verbose:
            if hasattr(engine, "count_tokens"):
                try:
                    prompt_tokens = int(engine.count_tokens(prompt))
                except Exception:
                    prompt_tokens = 0
            elif hasattr(engine, "tokenizer"):
                try:
                    prompt_tokens = len(engine.tokenizer.encode(prompt, return_tensors=None))
                except Exception:
                    prompt_tokens = 0

        if stream:
            chunks: list[str] = []
            for chunk in engine.generate_stream(prompt, gen_config):
                click.echo(chunk, nl=False)
                if verbose:
                    chunks.append(chunk)
            click.echo()

            if verbose:
                completion_tokens = 0
                if hasattr(engine, "count_tokens"):
                    try:
                        completion_tokens = int(engine.count_tokens("".join(chunks)))
                    except Exception:
                        completion_tokens = 0
                elif hasattr(engine, "tokenizer"):
                    try:
                        completion_tokens = len(
                            engine.tokenizer.encode(
                                "".join(chunks),
                                return_tensors=None,
                                add_special_tokens=False,
                            )
                        )
                    except Exception:
                        completion_tokens = 0

                total_tokens = prompt_tokens + completion_tokens
                click.echo(
                    f"\n[prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}]",
                    err=True,
                )
        else:
            output = engine.generate(prompt, gen_config)
            click.echo(output.text)
            if verbose:
                total_tokens = prompt_tokens + output.num_tokens
                click.echo(
                    f"\n[prompt={prompt_tokens}, completion={output.num_tokens}, total={total_tokens}, "
                    f"{output.tokens_per_second:.1f} tok/s]",
                    err=True,
                )
            else:
                click.echo(
                    f"\n[{output.num_tokens} tokens, {output.tokens_per_second:.1f} tok/s]",
                    err=True,
                )
    except SystemExit:
        raise
    except Exception as e:
        click.echo(format_cli_error(e), err=True)
        if verbose:
            print_cli_traceback(e)
        raise SystemExit(1) from e


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option(
    "--model",
    "-m",
    type=str,
    help="Model name / HuggingFace ID / local model dir (Transformers only)",
)
@click.option(
    "--prompt",
    "-p",
    type=str,
    default="Explain LoRA in one paragraph.",
    show_default=True,
    help="Prompt to benchmark",
)
@click.option("--trials", type=int, default=3, show_default=True, help="Measured runs")
@click.option("--warmup", type=int, default=1, show_default=True, help="Warmup runs (not measured)")
@click.option("--max-new-tokens", type=int, default=256, show_default=True)
@click.option("--temperature", type=float, default=0.7, show_default=True)
@click.option("--top-p", type=float, default=0.9, show_default=True)
@click.option("--top-k", type=int, default=50, show_default=True)
@click.option("--repetition-penalty", type=float, default=1.1, show_default=True)
@click.option("--seed", type=int, default=None, help="Seed for reproducibility")
@click.option("--output-json", type=click.Path(dir_okay=False), help="Write results to JSON")
@click.pass_context
def bench(
    ctx,
    config: str | None,
    model: str | None,
    prompt: str,
    trials: int,
    warmup: int,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    top_k: int,
    repetition_penalty: float,
    seed: int | None,
    output_json: str | None,
) -> None:
    """
    Benchmark inference performance (Transformers backend).

    Measures:
    - TTFT (time to first token)
    - end-to-end tokens/sec (streaming)
    - best-effort memory snapshots
    """
    import json
    import statistics
    import time
    from pathlib import Path

    from clara import GenerationConfig
    from clara.config import load_config
    from clara.engine.factory import load_engine
    from clara.utils.errors import format_cli_error, print_cli_traceback
    from clara.utils.memory import get_memory_stats

    verbose = bool((ctx.obj or {}).get("verbose"))

    try:
        if trials <= 0:
            raise SystemExit("--trials must be >= 1")
        if warmup < 0:
            raise SystemExit("--warmup must be >= 0")

        # Load config
        if config:
            cfg = load_config(config)
        else:
            cfg = {
                "model": {
                    "hf_id": model or "gpt2",
                    "dtype": "auto",
                }
            }

        # Optional CLI override
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

        click.echo("Loading model...", err=True)
        loaded = load_engine(cfg)
        if loaded.backend != "transformers":
            raise SystemExit("`clara bench` currently supports Transformers models only.")

        engine = loaded.engine

        gen_cfg = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            seed=seed,
        )

        prompt_tokens = 0
        if hasattr(engine, "tokenizer"):
            try:
                prompt_tokens = len(engine.tokenizer.encode(prompt, return_tensors=None))
            except Exception:
                prompt_tokens = 0

        click.echo(f"Model: {loaded.model_path}", err=True)
        click.echo(f"Prompt tokens: {prompt_tokens}", err=True)
        click.echo(f"Warmup: {warmup} | Trials: {trials}", err=True)

        def run_once() -> dict[str, float]:
            start = time.perf_counter()
            first_token_at: float | None = None
            chunks: list[str] = []
            for chunk in engine.generate_stream(prompt, gen_cfg):
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                chunks.append(chunk)
            end = time.perf_counter()

            ttft_s = (first_token_at - start) if first_token_at is not None else (end - start)
            total_s = end - start
            text = "".join(chunks)

            completion_tokens = 0
            if hasattr(engine, "tokenizer"):
                try:
                    completion_tokens = len(
                        engine.tokenizer.encode(text, return_tensors=None, add_special_tokens=False)
                    )
                except Exception:
                    completion_tokens = 0

            tps = (completion_tokens / total_s) if total_s > 0 else 0.0

            stats = get_memory_stats()
            return {
                "ttft_s": float(ttft_s),
                "total_s": float(total_s),
                "completion_tokens": float(completion_tokens),
                "tokens_per_second": float(tps),
                "allocated_mb": float(stats.allocated_mb),
                "reserved_mb": float(stats.reserved_mb),
            }

        # Warmup
        for _ in range(warmup):
            _ = run_once()

        results: list[dict[str, float]] = []
        for i in range(trials):
            click.echo(f"Trial {i+1}/{trials}...", err=True)
            results.append(run_once())

        ttfts = [r["ttft_s"] for r in results]
        tps = [r["tokens_per_second"] for r in results]
        totals = [r["total_s"] for r in results]

        summary = {
            "model_path": loaded.model_path,
            "prompt_tokens": prompt_tokens,
            "trials": trials,
            "warmup": warmup,
            "generation": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty,
                "seed": seed,
            },
            "results": results,
            "aggregate": {
                "ttft_s_mean": statistics.fmean(ttfts),
                "ttft_s_p50": statistics.median(ttfts),
                "tokens_per_second_mean": statistics.fmean(tps),
                "tokens_per_second_p50": statistics.median(tps),
                "total_s_mean": statistics.fmean(totals),
            },
        }

        click.echo("", err=True)
        click.echo("=== Bench Summary ===", err=True)
        click.echo(f"TTFT (p50): {summary['aggregate']['ttft_s_p50']:.3f}s", err=True)
        click.echo(
            f"Tokens/sec (p50): {summary['aggregate']['tokens_per_second_p50']:.2f}", err=True
        )
        click.echo(f"Total time (mean): {summary['aggregate']['total_s_mean']:.3f}s", err=True)

        if output_json:
            out_path = Path(output_json)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(summary, indent=2))
            click.echo(f"Wrote: {out_path}", err=True)

        # Print machine-readable summary to stdout
        click.echo(json.dumps(summary["aggregate"]))
    except SystemExit:
        raise
    except Exception as e:
        click.echo(format_cli_error(e), err=True)
        if verbose:
            print_cli_traceback(e)
        raise SystemExit(1) from e


@cli.command("eval")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option("--model", "-m", type=str, help="Model name or HuggingFace ID")
@click.option(
    "--benchmarks",
    "-b",
    type=str,
    default="all",
    help="Comma-separated benchmarks: perplexity,hellaswag,arc_easy",
)
@click.option("--samples", "-n", type=int, help="Limit samples per benchmark")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="results/eval.json",
    help="Output JSON path",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress bars")
def evaluate(config, model, benchmarks, samples, output, quiet):
    """
    Run model evaluation benchmarks.

    Examples:

        clara eval --model gpt2 --benchmarks perplexity --samples 50

        clara eval --config config.yaml --benchmarks all

        clara eval -m mistralai/Mistral-7B -b hellaswag,arc_easy -n 100
    """
    from clara import load_model
    from clara.config import load_config
    from clara.eval import EvaluationHarness

    # Load config
    if config:
        cfg = load_config(config)
    else:
        cfg = {
            "model": {
                "hf_id": model or "mistralai/Mistral-7B-Instruct-v0.2",
                "dtype": "auto",
            }
        }

    click.echo("Loading model...", err=True)
    result = load_model(cfg)

    bench_list = [b.strip() for b in benchmarks.split(",")]

    harness = EvaluationHarness(
        model=result.model,
        tokenizer=result.tokenizer,
        model_name=result.model_path,
        adapter_name=result.adapter_name,
    )

    click.echo(f"Running benchmarks: {', '.join(bench_list)}", err=True)
    harness.run(
        benchmarks=bench_list,
        num_samples=samples,
        show_progress=not quiet,
    )

    harness.print_results()
    harness.save(output)
    click.echo(f"Results saved to: {output}", err=True)


@cli.command()
def info():
    """Show system information and available devices."""
    import torch

    from clara import __version__
    from clara.utils.device import get_device
    from clara.utils.memory import get_memory_stats

    click.echo(f"ML-Clara v{__version__}")
    click.echo()

    # Python info
    import sys

    click.echo(f"Python: {sys.version.split()[0]}")

    # Device info
    device = get_device()
    click.echo(f"Device: {device}")

    if torch.cuda.is_available():
        click.echo(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        click.echo(f"CUDA Version: {torch.version.cuda}")
    elif torch.backends.mps.is_available():
        click.echo("MPS: Available (Apple Silicon)")
    else:
        click.echo("GPU: Not available (using CPU)")

    click.echo(f"PyTorch: {torch.__version__}")

    # Memory
    try:
        stats = get_memory_stats()
        if stats.allocated_mb > 0:
            click.echo(f"GPU Memory: {stats.allocated_mb:.1f}MB allocated")
    except Exception:
        pass

    # Transformers version
    try:
        import transformers

        click.echo(f"Transformers: {transformers.__version__}")
    except ImportError:
        pass


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), required=True)
def validate(config):
    """
    Validate a configuration file.

    Example:

        clara validate --config config.yaml
    """
    from clara.config import load_config

    try:
        cfg = load_config(config)
        click.echo(f"Config valid: {config}")

        # Show key settings
        model_cfg = cfg.get("model", {})
        if model_cfg.get("local_path"):
            click.echo(f"  Model: {model_cfg['local_path']} (local)")
        elif model_cfg.get("hf_id"):
            click.echo(f"  Model: {model_cfg['hf_id']} (HuggingFace)")
        else:
            click.echo("  Model: Not specified")

        # Adapter info
        adapters = cfg.get("adapters", {})
        if adapters.get("available"):
            click.echo(f"  Adapters: {len(adapters['available'])} configured")
            if adapters.get("active"):
                click.echo(f"  Active: {adapters['active']}")
        elif cfg.get("adapter", {}).get("enabled"):
            click.echo("  Adapter: enabled (legacy format)")

    except Exception as e:
        click.echo(f"Config invalid: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
def adapters(config):
    """
    List available adapters from configuration.

    Example:

        clara adapters --config configs/multi_adapter.yaml
    """
    from clara.adapters import AdapterRegistry
    from clara.config import load_config

    if not config:
        click.echo("No config file specified. Use --config to specify one.", err=True)
        raise SystemExit(1)

    cfg = load_config(config)
    from pathlib import Path

    base_path = None
    config_dir = cfg.get("config_dir")
    if isinstance(config_dir, str) and config_dir:
        base_path = Path(config_dir)

    registry = AdapterRegistry.from_config(cfg, base_path=base_path)

    if len(registry) == 0:
        click.echo("No adapters configured.")
        return

    click.echo(f"Available adapters ({len(registry)}):")
    click.echo()

    active = registry.get_active()
    for adapter in registry:
        marker = "*" if active and adapter.name == active.name else " "
        click.echo(f"  {marker} {adapter.name}")
        click.echo(f"      Path: {adapter.path}")
        if adapter.rank:
            click.echo(f"      Rank: {adapter.rank}")
        if adapter.description:
            click.echo(f"      Desc: {adapter.description}")
        click.echo()


@cli.command("init-config")
@click.option(
    "--type",
    "template_type",
    type=click.Choice(["default", "finetune", "multi-adapter", "test-train"], case_sensitive=False),
    default="default",
    show_default=True,
    help="Which template to write",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    help="Output path (defaults to config.yaml or <type>.yaml)",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite if the file exists")
def init_config(template_type: str, output: str | None, force: bool) -> None:
    """
    Write a starter config template to disk.

    Examples:

        clara init-config

        clara init-config --type finetune -o finetune.yaml
    """
    from pathlib import Path

    from clara.config.templates import write_template

    template_type = template_type.lower()
    if output is None:
        output = "config.yaml" if template_type == "default" else f"{template_type.replace('-', '_')}.yaml"

    try:
        written = write_template(template_type, Path(output), force=force)
    except FileExistsError:
        click.echo(f"Refusing to overwrite existing file: {output} (use --force)", err=True)
        raise SystemExit(1)

    click.echo(f"Wrote {template_type} config to: {written}")


@cli.command()
@click.option("--host", type=str, default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=8000, show_default=True)
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option(
    "--model",
    "-m",
    type=str,
    help="Model name / HuggingFace ID / local path (dir or .gguf) (overrides config)",
)
@click.option("--reload", is_flag=True, help="Auto-reload on code changes (dev only)")
def serve(host: str, port: int, config: str | None, model: str | None, reload: bool) -> None:
    """
    Start the local FastAPI web UI + JSON API.

    Examples:

        clara serve --model gpt2

        clara init-config --type default -o config.yaml
        clara serve --config config.yaml
    """
    import os

    try:
        import uvicorn  # type: ignore
    except Exception as e:
        raise SystemExit(
            "uvicorn is required for `clara serve`. Install with: pip install 'ml-clara[server]'"
        ) from e

    if config:
        os.environ["CLARA_SERVER_CONFIG"] = str(config)
    else:
        os.environ.pop("CLARA_SERVER_CONFIG", None)

    if model:
        os.environ["CLARA_SERVER_MODEL"] = str(model)
    else:
        os.environ.pop("CLARA_SERVER_MODEL", None)

    click.echo(f"Starting server on http://{host}:{port}", err=True)
    click.echo("Press Ctrl+C to stop.", err=True)

    uvicorn.run(
        "clara.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@cli.command()
@click.option(
    "--config", "-c", type=click.Path(exists=True), required=True, help="Training config file"
)
@click.option("--model", "-m", type=str, help="Base model (overrides config)")
@click.option("--dataset", "-d", type=str, help="Dataset path (overrides config)")
@click.option("--output", "-o", type=str, help="Output directory (overrides config)")
@click.option("--resume", type=click.Path(exists=True), help="Resume from checkpoint")
@click.pass_context
def train(ctx, config, model, dataset, output, resume):
    """
    Fine-tune a model with LoRA.

    Example:

        clara train --config configs/finetune.yaml --dataset data/train.jsonl
    """
    from clara.data import DatasetConfig, load_dataset, prepare_dataset
    from clara.models import load_model
    from clara.training import LoggingCallback, Trainer, TrainingConfig

    # Load training config
    train_cfg = TrainingConfig.from_yaml(config)

    # Override from CLI
    if model:
        train_cfg.model_path = model
    if dataset:
        train_cfg.dataset_path = dataset
    if output:
        train_cfg.output_dir = output
    if resume:
        train_cfg.resume_from_checkpoint = resume

    click.echo("Loading base model...", err=True)

    # Load model
    model_cfg = {"model": {"hf_id": train_cfg.model_path}}
    result = load_model(model_cfg)

    click.echo("Loading dataset...", err=True)

    # Load dataset
    ds_config = DatasetConfig(path=train_cfg.dataset_path)
    full_dataset = load_dataset(ds_config, result.tokenizer, train_cfg.max_length)
    train_ds, eval_ds = prepare_dataset(full_dataset, val_split=train_cfg.val_split)

    click.echo(f"Training samples: {len(train_ds)}", err=True)
    if eval_ds:
        click.echo(f"Validation samples: {len(eval_ds)}", err=True)

    # Setup trainer
    trainer = Trainer(
        model=result.model,
        tokenizer=result.tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        config=train_cfg,
        callbacks=[LoggingCallback(train_cfg.report_to)],
    )

    click.echo("Starting training...", err=True)
    state = trainer.train()

    click.echo(
        f"Training complete! Final checkpoint: {train_cfg.output_dir}/final", err=True
    )


@cli.command()
@click.argument("adapter_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=str, required=True, help="Output path for merged model")
@click.option("--model", "-m", type=str, help="Base model (if not in adapter config)")
@click.option("--push-to-hub", is_flag=True, help="Push to HuggingFace Hub")
@click.option("--hub-name", type=str, help="HuggingFace repo name")
def export(adapter_path, output, model, push_to_hub, hub_name):
    """
    Export adapter by merging with base model.

    Example:

        clara export outputs/final --output models/merged-model
    """
    from peft import PeftConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    click.echo("Loading adapter config...", err=True)

    # Get base model from adapter config
    peft_config = PeftConfig.from_pretrained(adapter_path)
    base_model_name = model or peft_config.base_model_name_or_path

    click.echo(f"Loading base model: {base_model_name}", err=True)

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    click.echo("Loading adapter...", err=True)
    peft_model = PeftModel.from_pretrained(base_model, adapter_path)

    click.echo("Merging adapter with base model...", err=True)
    merged = peft_model.merge_and_unload()

    click.echo(f"Saving merged model to: {output}", err=True)
    merged.save_pretrained(output)
    tokenizer.save_pretrained(output)

    if push_to_hub:
        if not hub_name:
            click.echo("--hub-name required for push-to-hub", err=True)
            raise SystemExit(1)

        click.echo(f"Pushing to HuggingFace Hub: {hub_name}", err=True)
        merged.push_to_hub(hub_name)
        tokenizer.push_to_hub(hub_name)

    click.echo("Export complete!", err=True)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
