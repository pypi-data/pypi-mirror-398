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
@click.option("--model", "-m", type=str, help="Model name or HuggingFace ID")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option(
    "--max-tokens", "-n", type=int, default=256, help="Max tokens to generate"
)
@click.option("--temperature", "-t", type=float, default=0.7, help="Sampling temperature")
@click.option("--stream", "-s", is_flag=True, help="Stream output token by token")
def run(prompt, model, config, max_tokens, temperature, stream):
    """
    Generate text from a prompt.

    Examples:

        clara run "Explain quantum computing"

        clara run "Write a haiku" --model gpt2 --stream

        clara run "Hello" --config config.yaml --max-tokens 100
    """
    from clara import GenerationConfig, InferenceEngine, load_model
    from clara.config import load_config

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
    click.echo(f"Model loaded: {result.model_path}", err=True)

    engine = InferenceEngine(result.model, result.tokenizer)
    gen_config = GenerationConfig(
        max_new_tokens=max_tokens,
        temperature=temperature,
    )

    if stream:
        for chunk in engine.generate_stream(prompt, gen_config):
            click.echo(chunk, nl=False)
        click.echo()
    else:
        output = engine.generate(prompt, gen_config)
        click.echo(output.text)
        click.echo(
            f"\n[{output.num_tokens} tokens, {output.tokens_per_second:.1f} tok/s]",
            err=True,
        )


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
@click.option("--model", "-m", type=str, help="Model name or HuggingFace ID (overrides config)")
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
