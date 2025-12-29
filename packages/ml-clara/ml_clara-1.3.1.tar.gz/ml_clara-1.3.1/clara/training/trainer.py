"""Core training loop."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from ..utils.logging import get_logger
from ..utils.memory import clear_memory
from .callbacks import Callback
from .config import TrainingConfig

logger = get_logger(__name__)


@dataclass
class TrainingState:
    """Current training state."""

    epoch: int = 0
    global_step: int = 0
    best_loss: float = float("inf")
    total_tokens: int = 0


@dataclass
class TrainingMetrics:
    """Training metrics for a step/epoch."""

    loss: float
    learning_rate: float
    tokens_per_second: float
    grad_norm: float | None = None


class Trainer:
    """
    LoRA fine-tuning trainer.

    Features:
    - Gradient accumulation
    - Mixed precision (fp16/bf16)
    - Gradient checkpointing
    - Checkpoint save/resume
    - Callback system

    Usage:
        trainer = Trainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_ds,
            config=TrainingConfig(...),
        )
        trainer.train()
    """

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        train_dataset: Any,
        config: TrainingConfig,
        eval_dataset: Any | None = None,
        callbacks: list[Callback] | None = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.config = config
        self.callbacks = callbacks or []

        self.state = TrainingState()
        self.device = next(model.parameters()).device

        # These will be set up in train()
        self.optimizer = None
        self.scheduler = None
        self.scaler = None
        self.train_dataloader = None
        self.eval_dataloader = None
        self.num_warmup_steps = 0

    def _setup_model(self) -> None:
        """Setup model for training."""
        from peft import get_peft_model, prepare_model_for_kbit_training

        # Prepare for quantized training if needed
        if self.config.lora.use_qlora:
            self.model = prepare_model_for_kbit_training(
                self.model,
                use_gradient_checkpointing=self.config.gradient_checkpointing,
            )
        elif self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()

        # Add LoRA adapters
        peft_config = self.config.lora.to_peft_config()
        self.model = get_peft_model(self.model, peft_config)

        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())

        logger.info(
            f"LoRA setup: {trainable:,} trainable / {total:,} total "
            f"({100 * trainable / total:.2f}%)"
        )

    def _setup_optimizer(self) -> None:
        """Setup optimizer."""
        cfg = self.config

        # Get trainable parameters
        params = [p for p in self.model.parameters() if p.requires_grad]

        if cfg.optimizer == "adamw":
            self.optimizer = torch.optim.AdamW(
                params,
                lr=cfg.learning_rate,
                weight_decay=cfg.weight_decay,
            )
        elif cfg.optimizer == "adamw_8bit":
            try:
                import bitsandbytes as bnb

                self.optimizer = bnb.optim.AdamW8bit(
                    params,
                    lr=cfg.learning_rate,
                    weight_decay=cfg.weight_decay,
                )
            except ImportError:
                logger.warning("bitsandbytes not available, falling back to AdamW")
                self.optimizer = torch.optim.AdamW(
                    params,
                    lr=cfg.learning_rate,
                    weight_decay=cfg.weight_decay,
                )
        elif cfg.optimizer == "sgd":
            self.optimizer = torch.optim.SGD(
                params,
                lr=cfg.learning_rate,
                weight_decay=cfg.weight_decay,
                momentum=0.9,
            )

    def _setup_scheduler(self) -> None:
        """Setup learning rate scheduler."""
        cfg = self.config

        num_training_steps = (
            len(self.train_dataset)
            // cfg.batch_size
            // cfg.gradient_accumulation_steps
            * cfg.num_epochs
        )
        self.num_warmup_steps = int(num_training_steps * cfg.warmup_ratio)

        if cfg.lr_scheduler == "cosine":
            from torch.optim.lr_scheduler import CosineAnnealingLR

            self.scheduler = CosineAnnealingLR(
                self.optimizer,
                T_max=max(num_training_steps - self.num_warmup_steps, 1),
            )
        elif cfg.lr_scheduler == "linear":
            from torch.optim.lr_scheduler import LinearLR

            self.scheduler = LinearLR(
                self.optimizer,
                start_factor=1.0,
                end_factor=0.0,
                total_iters=num_training_steps,
            )
        else:
            self.scheduler = None

    def _setup_dataloaders(self) -> None:
        """Setup data loaders."""
        from ..data.collator import DataCollatorForCausalLM

        collator = DataCollatorForCausalLM(
            tokenizer=self.tokenizer,
            max_length=self.config.max_length,
        )

        self.train_dataloader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            collate_fn=collator,
            num_workers=0,  # Avoid multiprocessing issues
            pin_memory=True,
        )

        if self.eval_dataset:
            self.eval_dataloader = DataLoader(
                self.eval_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                collate_fn=collator,
                num_workers=0,
                pin_memory=True,
            )
        else:
            self.eval_dataloader = None

    def train(self) -> TrainingState:
        """
        Run training loop.

        Returns:
            Final training state
        """
        cfg = self.config

        # Setup
        self._setup_model()
        self._setup_optimizer()
        self._setup_scheduler()
        self._setup_dataloaders()

        # Mixed precision
        self.scaler = None
        if cfg.fp16 and self.device.type == "cuda":
            self.scaler = torch.cuda.amp.GradScaler()

        # Resume from checkpoint if specified
        if cfg.resume_from_checkpoint:
            self._load_checkpoint(cfg.resume_from_checkpoint)

        # Callbacks: training start
        for cb in self.callbacks:
            cb.on_train_begin(self)

        logger.info(f"Starting training for {cfg.num_epochs} epochs")
        logger.info(f"  Batch size: {cfg.batch_size}")
        logger.info(f"  Gradient accumulation: {cfg.gradient_accumulation_steps}")
        logger.info(f"  Effective batch size: {cfg.effective_batch_size()}")
        logger.info(f"  Learning rate: {cfg.learning_rate}")

        self.model.train()

        for epoch in range(self.state.epoch, cfg.num_epochs):
            self.state.epoch = epoch

            for cb in self.callbacks:
                cb.on_epoch_begin(self, epoch)

            epoch_loss = self._train_epoch(epoch)

            metrics = {"loss": epoch_loss}

            # Evaluation
            if self.eval_dataloader and cfg.eval_strategy == "epoch":
                eval_loss = self._evaluate()
                logger.info(f"Epoch {epoch + 1} - eval_loss: {eval_loss:.4f}")
                metrics["eval_loss"] = eval_loss

            for cb in self.callbacks:
                cb.on_epoch_end(self, epoch, metrics)

            # Save checkpoint
            self._save_checkpoint(f"checkpoint-epoch-{epoch + 1}")

        # Final save
        self._save_checkpoint("final")

        # Callbacks: training end
        for cb in self.callbacks:
            cb.on_train_end(self)

        return self.state

    def _train_epoch(self, epoch: int) -> float:
        """Train for one epoch."""
        cfg = self.config
        total_loss = 0.0
        num_steps = 0

        progress = tqdm(
            self.train_dataloader,
            desc=f"Epoch {epoch + 1}/{cfg.num_epochs}",
            leave=True,
        )

        self.optimizer.zero_grad()

        for step, batch in enumerate(progress):
            # Move to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Forward pass with mixed precision
            use_amp = cfg.fp16 or (cfg.bf16 and self.device.type == "cuda")

            if use_amp and self.device.type == "cuda":
                with torch.cuda.amp.autocast(dtype=torch.bfloat16 if cfg.bf16 else torch.float16):
                    outputs = self.model(**batch)
                    loss = outputs.loss / cfg.gradient_accumulation_steps
            else:
                outputs = self.model(**batch)
                loss = outputs.loss / cfg.gradient_accumulation_steps

            # Backward pass
            if self.scaler:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()

            total_loss += loss.item() * cfg.gradient_accumulation_steps
            num_steps += 1

            # Gradient accumulation step
            if (step + 1) % cfg.gradient_accumulation_steps == 0:
                # Gradient clipping
                if cfg.max_grad_norm > 0:
                    if self.scaler:
                        self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        cfg.max_grad_norm,
                    )

                # Optimizer step
                if self.scaler:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()

                # Scheduler step (after warmup)
                if self.scheduler and self.state.global_step >= self.num_warmup_steps:
                    self.scheduler.step()

                self.optimizer.zero_grad()
                self.state.global_step += 1

                # Logging
                if self.state.global_step % cfg.logging_steps == 0:
                    avg_loss = total_loss / num_steps
                    lr = self.optimizer.param_groups[0]["lr"]
                    progress.set_postfix(loss=f"{avg_loss:.4f}", lr=f"{lr:.2e}")

                    for cb in self.callbacks:
                        cb.on_log(self, {"loss": avg_loss, "lr": lr})

                # Evaluation during training
                if (
                    cfg.eval_strategy == "steps"
                    and self.eval_dataloader
                    and self.state.global_step % cfg.eval_steps == 0
                ):
                    eval_loss = self._evaluate()
                    logger.info(
                        f"Step {self.state.global_step} - eval_loss: {eval_loss:.4f}"
                    )
                    self.model.train()

                # Checkpoint
                if self.state.global_step % cfg.save_steps == 0:
                    self._save_checkpoint(f"checkpoint-{self.state.global_step}")

        return total_loss / max(num_steps, 1)

    @torch.no_grad()
    def _evaluate(self) -> float:
        """Run evaluation."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        for batch in tqdm(self.eval_dataloader, desc="Evaluating", leave=False):
            batch = {k: v.to(self.device) for k, v in batch.items()}
            outputs = self.model(**batch)
            total_loss += outputs.loss.item()
            num_batches += 1

        return total_loss / max(num_batches, 1)

    def _save_checkpoint(self, name: str) -> None:
        """Save training checkpoint."""
        output_dir = Path(self.config.output_dir) / name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save adapter weights
        self.model.save_pretrained(output_dir)

        # Save training state
        state_dict = {
            "epoch": self.state.epoch,
            "global_step": self.state.global_step,
            "best_loss": self.state.best_loss,
            "optimizer_state": self.optimizer.state_dict(),
        }
        if self.scheduler:
            state_dict["scheduler_state"] = self.scheduler.state_dict()

        torch.save(state_dict, output_dir / "training_state.pt")

        logger.info(f"Checkpoint saved: {output_dir}")

        # Manage checkpoint limit
        self._cleanup_checkpoints()

        for cb in self.callbacks:
            cb.on_save(self, output_dir)

    def _load_checkpoint(self, path: str) -> None:
        """Load training checkpoint."""
        checkpoint_dir = Path(path)

        # Load training state
        state_path = checkpoint_dir / "training_state.pt"
        if state_path.exists():
            state_dict = torch.load(state_path, map_location=self.device)
            self.state.epoch = state_dict["epoch"]
            self.state.global_step = state_dict["global_step"]
            self.state.best_loss = state_dict["best_loss"]
            self.optimizer.load_state_dict(state_dict["optimizer_state"])
            if self.scheduler and "scheduler_state" in state_dict:
                self.scheduler.load_state_dict(state_dict["scheduler_state"])

        logger.info(f"Resumed from checkpoint: {checkpoint_dir}")

    def _cleanup_checkpoints(self) -> None:
        """Remove old checkpoints beyond limit."""
        if self.config.save_total_limit <= 0:
            return

        output_dir = Path(self.config.output_dir)
        checkpoints = sorted(
            output_dir.glob("checkpoint-*"),
            key=lambda p: p.stat().st_mtime,
        )

        while len(checkpoints) > self.config.save_total_limit:
            oldest = checkpoints.pop(0)
            shutil.rmtree(oldest)
            logger.debug(f"Removed old checkpoint: {oldest}")
