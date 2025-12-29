"""Configuration module for model and training configurations."""

from .model_configs import ModelConfig, get_model_config, TINY_CONFIG, SMALL_CONFIG, MEDIUM_CONFIG
from .training_configs import TrainingConfig, get_training_config

__all__ = [
    "ModelConfig",
    "get_model_config",
    "TINY_CONFIG",
    "SMALL_CONFIG",
    "MEDIUM_CONFIG",
    "TrainingConfig",
    "get_training_config",
]
