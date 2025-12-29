"""Training callbacks."""

from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .trainer import Trainer


class Callback(ABC):
    """Base callback class."""

    def on_train_begin(self, trainer: "Trainer") -> None:
        """Called at the start of training."""
        pass

    def on_train_end(self, trainer: "Trainer") -> None:
        """Called at the end of training."""
        pass

    def on_epoch_begin(self, trainer: "Trainer", epoch: int) -> None:
        """Called at the start of each epoch."""
        pass

    def on_epoch_end(self, trainer: "Trainer", epoch: int, metrics: dict) -> None:
        """Called at the end of each epoch."""
        pass

    def on_step(self, trainer: "Trainer", step: int, metrics: dict) -> None:
        """Called after each optimizer step."""
        pass

    def on_log(self, trainer: "Trainer", logs: dict) -> None:
        """Called when logging metrics."""
        pass

    def on_save(self, trainer: "Trainer", output_dir: Path) -> None:
        """Called when saving checkpoint."""
        pass


class LoggingCallback(Callback):
    """Callback for logging to various backends."""

    def __init__(self, report_to: list[str] | None = None):
        self.report_to = report_to or ["tensorboard"]
        self.writers: dict[str, Any] = {}

    def on_train_begin(self, trainer: "Trainer") -> None:
        """Setup logging backends."""
        if "tensorboard" in self.report_to:
            try:
                from torch.utils.tensorboard import SummaryWriter

                log_dir = Path(trainer.config.output_dir) / "logs"
                self.writers["tensorboard"] = SummaryWriter(log_dir)
            except ImportError:
                pass

        if "wandb" in self.report_to:
            try:
                import wandb

                wandb.init(
                    project="clara-finetune",
                    name=trainer.config.run_name,
                    config=trainer.config.__dict__,
                )
                self.writers["wandb"] = wandb
            except ImportError:
                pass

    def on_log(self, trainer: "Trainer", logs: dict) -> None:
        """Log metrics."""
        step = trainer.state.global_step

        if "tensorboard" in self.writers:
            for key, value in logs.items():
                self.writers["tensorboard"].add_scalar(key, value, step)

        if "wandb" in self.writers:
            self.writers["wandb"].log(logs, step=step)

    def on_train_end(self, trainer: "Trainer") -> None:
        """Cleanup."""
        if "tensorboard" in self.writers:
            self.writers["tensorboard"].close()
        if "wandb" in self.writers:
            self.writers["wandb"].finish()


class CheckpointCallback(Callback):
    """Callback for checkpoint management."""

    def __init__(self, save_best: bool = True):
        self.save_best = save_best
        self.best_loss = float("inf")

    def on_epoch_end(self, trainer: "Trainer", epoch: int, metrics: dict) -> None:
        """Save best checkpoint."""
        if not self.save_best:
            return

        loss = metrics.get("eval_loss", metrics.get("loss", float("inf")))

        if loss < self.best_loss:
            self.best_loss = loss
            trainer._save_checkpoint("best")


class EarlyStoppingCallback(Callback):
    """Early stopping callback."""

    def __init__(self, patience: int = 3, min_delta: float = 0.01):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float("inf")
        self.counter = 0

    def on_epoch_end(self, trainer: "Trainer", epoch: int, metrics: dict) -> None:
        """Check for early stopping."""
        loss = metrics.get("eval_loss", metrics.get("loss", float("inf")))

        if loss < self.best_loss - self.min_delta:
            self.best_loss = loss
            self.counter = 0
        else:
            self.counter += 1

            if self.counter >= self.patience:
                trainer.state.epoch = trainer.config.num_epochs  # Stop training
