"""Training configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass
class LoraConfig:
    """LoRA adapter configuration."""

    r: int = 16  # Rank
    lora_alpha: int = 32  # Scaling factor
    lora_dropout: float = 0.05
    target_modules: list[str] | None = None  # Auto-detect if None
    bias: Literal["none", "all", "lora_only"] = "none"
    task_type: str = "CAUSAL_LM"

    # QLoRA settings
    use_qlora: bool = False
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    def to_peft_config(self) -> Any:
        """Convert to PEFT LoraConfig."""
        from peft import LoraConfig as PeftLoraConfig, TaskType

        return PeftLoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            bias=self.bias,
            task_type=TaskType.CAUSAL_LM,
        )


@dataclass
class TrainingConfig:
    """Training configuration."""

    # Output
    output_dir: str = "outputs"
    run_name: str | None = None

    # Model
    model_path: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # Training hyperparameters
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    max_grad_norm: float = 1.0

    # Sequence length
    max_length: int = 2048

    # Optimizer
    optimizer: Literal["adamw", "adamw_8bit", "sgd"] = "adamw"
    lr_scheduler: Literal["cosine", "linear", "constant"] = "cosine"

    # Memory optimization
    gradient_checkpointing: bool = True
    fp16: bool = False
    bf16: bool = True  # Prefer bf16 on modern hardware

    # Checkpointing
    save_steps: int = 500
    save_total_limit: int = 3
    resume_from_checkpoint: str | None = None

    # Evaluation
    eval_steps: int = 500
    eval_strategy: Literal["steps", "epoch", "no"] = "steps"

    # Logging
    logging_steps: int = 10
    report_to: list[str] = field(default_factory=lambda: ["tensorboard"])

    # LoRA config
    lora: LoraConfig = field(default_factory=LoraConfig)

    # Dataset
    dataset_path: str = ""
    val_split: float = 0.1

    def effective_batch_size(self) -> int:
        """Calculate effective batch size with gradient accumulation."""
        return self.batch_size * self.gradient_accumulation_steps

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingConfig":
        """Create from dictionary with type coercion."""
        data = data.copy()
        lora_data = data.pop("lora", {})

        # Type coercion for numeric fields (YAML may load as strings)
        float_fields = [
            "learning_rate",
            "weight_decay",
            "warmup_ratio",
            "max_grad_norm",
            "val_split",
            "lora_dropout",
        ]
        int_fields = [
            "num_epochs",
            "batch_size",
            "gradient_accumulation_steps",
            "max_length",
            "save_steps",
            "save_total_limit",
            "eval_steps",
            "logging_steps",
            "r",
            "lora_alpha",
        ]

        for field in float_fields:
            if field in data and data[field] is not None:
                data[field] = float(data[field])
            if field in lora_data and lora_data[field] is not None:
                lora_data[field] = float(lora_data[field])

        for field in int_fields:
            if field in data and data[field] is not None:
                data[field] = int(data[field])
            if field in lora_data and lora_data[field] is not None:
                lora_data[field] = int(lora_data[field])

        config = cls(**data)
        if lora_data:
            config.lora = LoraConfig(**lora_data)
        return config

    @classmethod
    def from_yaml(cls, path: str | Path) -> "TrainingConfig":
        """Load from YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        # Support nested training: key or flat config
        if "training" in data:
            train_data = data["training"]
        else:
            train_data = data

        return cls.from_dict(train_data)
