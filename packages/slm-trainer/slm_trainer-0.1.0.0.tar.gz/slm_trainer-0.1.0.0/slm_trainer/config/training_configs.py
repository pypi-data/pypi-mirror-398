"""
Training configuration presets for different model sizes.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TrainingConfig:
    """Configuration for training hyperparameters."""

    # Optimization
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    epsilon: float = 1e-8

    # Learning rate schedule
    warmup_steps: int = 500
    max_steps: Optional[int] = None      # If None, will be calculated from epochs
    lr_decay_factor: float = 0.1         # For cosine decay

    # Training
    batch_size: int = 32
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0           # Gradient clipping
    epochs: int = 10

    # Regularization
    label_smoothing: float = 0.0

    # System
    mixed_precision: bool = True
    num_workers: int = 0                 # DataLoader workers (0 for Windows compatibility)

    # Checkpointing
    save_every_n_steps: int = 1000
    eval_every_n_steps: int = 500

    # Validation
    val_split: float = 0.1               # Fraction of data for validation

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")

        if not 0.0 <= self.weight_decay <= 1.0:
            raise ValueError("weight_decay must be between 0.0 and 1.0")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive")

        if self.max_grad_norm <= 0:
            raise ValueError("max_grad_norm must be positive")

        if not 0.0 <= self.val_split < 1.0:
            raise ValueError("val_split must be between 0.0 and 1.0")

    def effective_batch_size(self) -> int:
        """Calculate effective batch size with gradient accumulation."""
        return self.batch_size * self.gradient_accumulation_steps


# Predefined training configurations for each model size

TINY_TRAINING_CONFIG = TrainingConfig(
    # Optimization
    learning_rate=3e-4,
    weight_decay=0.1,
    beta1=0.9,
    beta2=0.95,
    epsilon=1e-8,

    # LR schedule
    warmup_steps=500,
    max_steps=None,         # Will be set based on epochs
    lr_decay_factor=0.1,

    # Training
    batch_size=64,
    gradient_accumulation_steps=1,
    max_grad_norm=1.0,
    epochs=10,

    # Regularization
    label_smoothing=0.0,

    # System
    mixed_precision=True,
    num_workers=0,

    # Checkpointing
    save_every_n_steps=1000,
    eval_every_n_steps=500,

    # Validation
    val_split=0.1
)
# Effective batch size: 64

SMALL_TRAINING_CONFIG = TrainingConfig(
    # Optimization
    learning_rate=2e-4,
    weight_decay=0.1,
    beta1=0.9,
    beta2=0.95,
    epsilon=1e-8,

    # LR schedule
    warmup_steps=2000,
    max_steps=None,
    lr_decay_factor=0.1,

    # Training
    batch_size=32,
    gradient_accumulation_steps=2,
    max_grad_norm=1.0,
    epochs=10,

    # Regularization
    label_smoothing=0.0,

    # System
    mixed_precision=True,
    num_workers=0,

    # Checkpointing
    save_every_n_steps=2000,
    eval_every_n_steps=1000,

    # Validation
    val_split=0.1
)
# Effective batch size: 64

MEDIUM_TRAINING_CONFIG = TrainingConfig(
    # Optimization
    learning_rate=1.5e-4,
    weight_decay=0.1,
    beta1=0.9,
    beta2=0.95,
    epsilon=1e-8,

    # LR schedule
    warmup_steps=5000,
    max_steps=None,
    lr_decay_factor=0.1,

    # Training
    batch_size=16,
    gradient_accumulation_steps=4,
    max_grad_norm=1.0,
    epochs=10,

    # Regularization
    label_smoothing=0.0,

    # System
    mixed_precision=True,
    num_workers=0,

    # Checkpointing
    save_every_n_steps=5000,
    eval_every_n_steps=2000,

    # Validation
    val_split=0.1
)
# Effective batch size: 64


# Training config mapping
TRAINING_SIZE_MAP = {
    'tiny': TINY_TRAINING_CONFIG,
    'small': SMALL_TRAINING_CONFIG,
    'medium': MEDIUM_TRAINING_CONFIG
}


def get_training_config(model_size: str, **overrides) -> TrainingConfig:
    """
    Get a training configuration by model size, with optional parameter overrides.

    Args:
        model_size: One of 'tiny', 'small', 'medium'
        **overrides: Parameters to override in the base config

    Returns:
        TrainingConfig: Configuration object

    Raises:
        ValueError: If model_size is not recognized

    Example:
        >>> config = get_training_config('small', learning_rate=1e-4, epochs=20)
    """
    if model_size not in TRAINING_SIZE_MAP:
        raise ValueError(
            f"Unknown model size: {model_size}. "
            f"Choose from: {list(TRAINING_SIZE_MAP.keys())}"
        )

    base_config = TRAINING_SIZE_MAP[model_size]

    # Apply overrides
    if overrides:
        config_dict = {
            'learning_rate': base_config.learning_rate,
            'weight_decay': base_config.weight_decay,
            'beta1': base_config.beta1,
            'beta2': base_config.beta2,
            'epsilon': base_config.epsilon,
            'warmup_steps': base_config.warmup_steps,
            'max_steps': base_config.max_steps,
            'lr_decay_factor': base_config.lr_decay_factor,
            'batch_size': base_config.batch_size,
            'gradient_accumulation_steps': base_config.gradient_accumulation_steps,
            'max_grad_norm': base_config.max_grad_norm,
            'epochs': base_config.epochs,
            'label_smoothing': base_config.label_smoothing,
            'mixed_precision': base_config.mixed_precision,
            'num_workers': base_config.num_workers,
            'save_every_n_steps': base_config.save_every_n_steps,
            'eval_every_n_steps': base_config.eval_every_n_steps,
            'val_split': base_config.val_split
        }
        config_dict.update(overrides)
        return TrainingConfig(**config_dict)

    return base_config
