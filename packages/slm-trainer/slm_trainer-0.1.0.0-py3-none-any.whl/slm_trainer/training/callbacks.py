"""
Training callbacks for logging, checkpointing, and monitoring.
"""

from typing import Dict, Any, Optional
import os


class Callback:
    """
    Base callback class.

    All callbacks should inherit from this class and override the relevant methods.
    """

    def on_train_begin(self, logs: Optional[Dict[str, Any]] = None):
        """Called at the beginning of training."""
        pass

    def on_train_end(self, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of training."""
        pass

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the beginning of each epoch."""
        pass

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of each epoch."""
        pass

    def on_batch_begin(self, batch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the beginning of each batch."""
        pass

    def on_batch_end(self, batch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of each batch."""
        pass

    def on_step_end(self, step: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of each training step."""
        pass


class LoggingCallback(Callback):
    """
    Callback for logging training metrics to console.
    """

    def __init__(self, log_every_n_steps: int = 100):
        """
        Initialize logging callback.

        Args:
            log_every_n_steps: Log metrics every N steps
        """
        self.log_every_n_steps = log_every_n_steps

    def on_train_begin(self, logs: Optional[Dict[str, Any]] = None):
        """Called at the beginning of training."""
        print("\n" + "=" * 70)
        print("Starting Training")
        print("=" * 70)

    def on_train_end(self, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of training."""
        print("\n" + "=" * 70)
        print("Training Completed")
        print("=" * 70)

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the beginning of each epoch."""
        print(f"\nEpoch {epoch + 1}")
        print("-" * 70)

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of each epoch."""
        if logs:
            metrics_str = " | ".join([f"{k}: {v:.4f}" for k, v in logs.items()])
            print(f"Epoch {epoch + 1} completed - {metrics_str}")

    def on_step_end(self, step: int, logs: Optional[Dict[str, Any]] = None):
        """Called at the end of each training step."""
        if step % self.log_every_n_steps == 0 and logs:
            metrics_str = " | ".join([f"{k}: {v:.4f}" for k, v in logs.items()])
            print(f"Step {step}: {metrics_str}")


class CheckpointCallback(Callback):
    """
    Callback for saving model checkpoints during training.
    """

    def __init__(
        self,
        save_dir: str,
        save_every_n_steps: int = 1000,
        save_best: bool = True,
        metric: str = 'val_loss',
        mode: str = 'min'
    ):
        """
        Initialize checkpoint callback.

        Args:
            save_dir: Directory to save checkpoints
            save_every_n_steps: Save checkpoint every N steps
            save_best: Whether to save the best model based on metric
            metric: Metric to monitor for best model (e.g., 'val_loss')
            mode: 'min' or 'max' - whether lower or higher metric is better
        """
        self.save_dir = save_dir
        self.save_every_n_steps = save_every_n_steps
        self.save_best = save_best
        self.metric = metric
        self.mode = mode
        self.best_metric = float('inf') if mode == 'min' else float('-inf')

        # Create save directory
        os.makedirs(save_dir, exist_ok=True)

    def on_step_end(self, step: int, logs: Optional[Dict[str, Any]] = None):
        """Save checkpoint at regular intervals."""
        if step > 0 and step % self.save_every_n_steps == 0:
            # This will be called from the training engine
            # The engine will handle the actual saving
            if logs is not None:
                logs['save_checkpoint'] = True
                logs['checkpoint_path'] = os.path.join(self.save_dir, f'step_{step}')

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Save best model if metric improved."""
        if not self.save_best or logs is None or self.metric not in logs:
            return

        current_metric = logs[self.metric]

        # Check if this is the best model
        is_best = False
        if self.mode == 'min':
            is_best = current_metric < self.best_metric
        else:
            is_best = current_metric > self.best_metric

        if is_best:
            self.best_metric = current_metric
            logs['save_checkpoint'] = True
            logs['checkpoint_path'] = os.path.join(self.save_dir, 'best_model')
            logs['is_best'] = True
            print(f"New best model! {self.metric}: {current_metric:.4f}")


class ProgressCallback(Callback):
    """
    Callback for displaying training progress.

    Uses tqdm for progress bars.
    """

    def __init__(self):
        """Initialize progress callback."""
        self.pbar = None

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Create progress bar for epoch."""
        from tqdm import tqdm

        if logs and 'total_steps' in logs:
            self.pbar = tqdm(total=logs['total_steps'], desc=f"Epoch {epoch + 1}")

    def on_batch_end(self, batch: int, logs: Optional[Dict[str, Any]] = None):
        """Update progress bar."""
        if self.pbar:
            # Update progress
            self.pbar.update(1)

            # Update description with metrics
            if logs:
                desc_parts = []
                for key, value in logs.items():
                    if key not in ['total_steps', 'save_checkpoint', 'checkpoint_path', 'is_best']:
                        if isinstance(value, float):
                            desc_parts.append(f"{key}: {value:.4f}")

                if desc_parts:
                    self.pbar.set_postfix_str(" | ".join(desc_parts))

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()
            self.pbar = None


class CallbackList:
    """
    Container for managing multiple callbacks.
    """

    def __init__(self, callbacks: list):
        """
        Initialize callback list.

        Args:
            callbacks: List of callback instances
        """
        self.callbacks = callbacks

    def on_train_begin(self, logs: Optional[Dict[str, Any]] = None):
        """Call on_train_begin for all callbacks."""
        for callback in self.callbacks:
            callback.on_train_begin(logs)

    def on_train_end(self, logs: Optional[Dict[str, Any]] = None):
        """Call on_train_end for all callbacks."""
        for callback in self.callbacks:
            callback.on_train_end(logs)

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Call on_epoch_begin for all callbacks."""
        for callback in self.callbacks:
            callback.on_epoch_begin(epoch, logs)

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None):
        """Call on_epoch_end for all callbacks."""
        for callback in self.callbacks:
            callback.on_epoch_end(epoch, logs)

    def on_batch_begin(self, batch: int, logs: Optional[Dict[str, Any]] = None):
        """Call on_batch_begin for all callbacks."""
        for callback in self.callbacks:
            callback.on_batch_begin(batch, logs)

    def on_batch_end(self, batch: int, logs: Optional[Dict[str, Any]] = None):
        """Call on_batch_end for all callbacks."""
        for callback in self.callbacks:
            callback.on_batch_end(batch, logs)

    def on_step_end(self, step: int, logs: Optional[Dict[str, Any]] = None):
        """Call on_step_end for all callbacks."""
        for callback in self.callbacks:
            callback.on_step_end(step, logs)
