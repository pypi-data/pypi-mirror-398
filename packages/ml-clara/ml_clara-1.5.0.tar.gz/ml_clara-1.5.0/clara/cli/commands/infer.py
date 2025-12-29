"""Inference CLI command."""

from argparse import Namespace
from clara.config import load_config
from clara.engine import InferenceEngine
from clara.utils.logging import get_logger


def run_inference(args: Namespace):
    """Run inference command."""
    logger = get_logger()

    # Load config
    config = load_config(config_path=args.config) if args.config else None

    # Create engine
    engine = InferenceEngine(
        model_path=args.model,
        device=args.device,
        config=config,
    )

    # Generate
    if args.stream:
        for token in engine.generate(
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            stream=True,
        ):
            print(token, end="", flush=True)
        print()  # Newline after streaming
    else:
        result = engine.generate(
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print(result)

