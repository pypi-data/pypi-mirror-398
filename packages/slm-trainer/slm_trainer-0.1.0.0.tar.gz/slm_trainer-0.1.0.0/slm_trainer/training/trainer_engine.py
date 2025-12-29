"""
Training engine with optimization, learning rate scheduling, and training loop.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, List
import math

from ..config.training_configs import TrainingConfig
from ..utils.checkpoint import save_checkpoint
from ..utils.logging import MetricsTracker
from .callbacks import CallbackList, Callback


class TrainingEngine:
    """
    Core training engine with optimization loop, mixed precision, and callbacks.
    """

    def __init__(
        self,
        model: nn.Module,
        train_config: TrainingConfig,
        device: torch.device,
        callbacks: Optional[List[Callback]] = None
    ):
        """
        Initialize training engine.

        Args:
            model: PyTorch model to train
            train_config: Training configuration
            device: Device to train on
            callbacks: Optional list of callbacks
        """
        self.model = model
        self.config = train_config
        self.device = device
        self.callbacks = CallbackList(callbacks or [])

        # Move model to device
        self.model.to(device)

        # Setup optimizer
        self.optimizer = self._create_optimizer()

        # Learning rate scheduler (will be initialized in train())
        self.scheduler = None

        # Mixed precision scaler
        self.scaler = torch.cuda.amp.GradScaler() if train_config.mixed_precision else None

        # Metrics tracker
        self.metrics = MetricsTracker()

        # Global step counter
        self.global_step = 0

    def _create_optimizer(self) -> torch.optim.Optimizer:
        """
        Create AdamW optimizer with weight decay.

        Returns:
            AdamW optimizer
        """
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            betas=(self.config.beta1, self.config.beta2),
            eps=self.config.epsilon,
            weight_decay=self.config.weight_decay
        )
        return optimizer

    def _create_scheduler(self, num_training_steps: int):
        """
        Create learning rate scheduler with linear warmup and cosine decay.

        Args:
            num_training_steps: Total number of training steps
        """
        def lr_lambda(current_step):
            # Linear warmup
            if current_step < self.config.warmup_steps:
                return float(current_step) / float(max(1, self.config.warmup_steps))

            # Cosine decay
            progress = float(current_step - self.config.warmup_steps) / float(
                max(1, num_training_steps - self.config.warmup_steps)
            )
            return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))

        self.scheduler = torch.optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> dict:
        """
        Train for one epoch.

        Args:
            train_loader: Training data loader
            epoch: Current epoch number

        Returns:
            Dictionary of average metrics for the epoch
        """
        self.model.train()
        self.metrics.reset()

        # Notify callbacks
        self.callbacks.on_epoch_begin(epoch, {'total_steps': len(train_loader)})

        for batch_idx, batch in enumerate(train_loader):
            # Notify callbacks
            self.callbacks.on_batch_begin(batch_idx)

            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Forward and backward pass
            loss = self.train_step(batch)

            # Update metrics
            self.metrics.update(loss=loss)

            # Create logs
            logs = {
                'loss': loss,
                'lr': self.optimizer.param_groups[0]['lr'],
                'step': self.global_step
            }

            # Notify callbacks
            self.callbacks.on_batch_end(batch_idx, logs)
            self.callbacks.on_step_end(self.global_step, logs)

            # Check if callbacks want to save checkpoint
            if logs.get('save_checkpoint', False):
                self._save_checkpoint(
                    logs['checkpoint_path'],
                    epoch,
                    logs.get('is_best', False)
                )

        # Get epoch metrics
        epoch_metrics = self.metrics.get_all_averages()

        # Notify callbacks
        self.callbacks.on_epoch_end(epoch, epoch_metrics)

        return epoch_metrics

    def train_step(self, batch: dict) -> float:
        """
        Perform a single training step.

        Args:
            batch: Dictionary containing 'input_ids', 'labels', and optionally 'attention_mask'

        Returns:
            Loss value
        """
        # Extract batch data
        input_ids = batch['input_ids']
        labels = batch['labels']
        attention_mask = batch.get('attention_mask', None)

        # Mixed precision context
        if self.config.mixed_precision:
            with torch.cuda.amp.autocast():
                # Forward pass
                logits, loss = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
        else:
            # Forward pass
            logits, loss = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

        # Scale loss for gradient accumulation
        loss = loss / self.config.gradient_accumulation_steps

        # Backward pass
        if self.config.mixed_precision:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()

        # Update weights if gradient accumulation is complete
        if (self.global_step + 1) % self.config.gradient_accumulation_steps == 0:
            # Gradient clipping
            if self.config.mixed_precision:
                self.scaler.unscale_(self.optimizer)

            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.max_grad_norm
            )

            # Optimizer step
            if self.config.mixed_precision:
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.optimizer.step()

            # Scheduler step
            if self.scheduler is not None:
                self.scheduler.step()

            # Zero gradients
            self.optimizer.zero_grad()

        # Increment global step
        self.global_step += 1

        # Return unscaled loss
        return loss.item() * self.config.gradient_accumulation_steps

    @torch.no_grad()
    def evaluate(self, eval_loader: DataLoader) -> dict:
        """
        Evaluate the model on validation data.

        Args:
            eval_loader: Evaluation data loader

        Returns:
            Dictionary of evaluation metrics
        """
        self.model.eval()
        eval_metrics = MetricsTracker()

        for batch in eval_loader:
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Extract batch data
            input_ids = batch['input_ids']
            labels = batch['labels']
            attention_mask = batch.get('attention_mask', None)

            # Forward pass
            logits, loss = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            # Update metrics
            eval_metrics.update(val_loss=loss.item())

        # Get average metrics
        avg_metrics = eval_metrics.get_all_averages()

        # Calculate perplexity
        if 'val_loss' in avg_metrics:
            avg_metrics['perplexity'] = math.exp(avg_metrics['val_loss'])

        return avg_metrics

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        epochs: Optional[int] = None
    ) -> dict:
        """
        Main training loop.

        Args:
            train_loader: Training data loader
            val_loader: Optional validation data loader
            epochs: Number of epochs (overrides config if provided)

        Returns:
            Dictionary with training history
        """
        epochs = epochs or self.config.epochs

        # Calculate total training steps
        steps_per_epoch = len(train_loader)
        total_steps = epochs * steps_per_epoch

        # Create learning rate scheduler
        self._create_scheduler(total_steps)

        # Training history
        history = {
            'train_loss': [],
            'val_loss': [],
            'perplexity': []
        }

        # Notify callbacks
        self.callbacks.on_train_begin({'epochs': epochs, 'total_steps': total_steps})

        try:
            for epoch in range(epochs):
                # Train for one epoch
                train_metrics = self.train_epoch(train_loader, epoch)
                history['train_loss'].append(train_metrics['loss'])

                # Evaluate on validation set
                if val_loader is not None:
                    val_metrics = self.evaluate(val_loader)
                    history['val_loss'].append(val_metrics['val_loss'])
                    history['perplexity'].append(val_metrics['perplexity'])

                    print(f"\nValidation - Loss: {val_metrics['val_loss']:.4f}, "
                          f"Perplexity: {val_metrics['perplexity']:.4f}")

                    # Notify callbacks with validation metrics
                    combined_metrics = {**train_metrics, **val_metrics}
                    self.callbacks.on_epoch_end(epoch, combined_metrics)

        except KeyboardInterrupt:
            print("\n\nTraining interrupted by user")

        # Notify callbacks
        self.callbacks.on_train_end({'history': history})

        return history

    def _save_checkpoint(
        self,
        checkpoint_path: str,
        epoch: int,
        is_best: bool = False
    ):
        """
        Save model checkpoint.

        Args:
            checkpoint_path: Path to save checkpoint
            epoch: Current epoch
            is_best: Whether this is the best model so far
        """
        metrics = self.metrics.get_all_averages()

        save_checkpoint(
            model=self.model,
            save_path=checkpoint_path,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
            epoch=epoch,
            global_step=self.global_step,
            metrics=metrics,
            config=self.config
        )

        if is_best:
            print(f"Best model saved to {checkpoint_path}")
        else:
            print(f"Checkpoint saved to {checkpoint_path}")
