"""
SLM-Trainer: A Python library for training private Small Language Models.

Example usage:
    >>> from slm_trainer import SLMTrainer
    >>>
    >>> trainer = SLMTrainer(model_size="small")
    >>> trainer.train("data.txt", epochs=10)
    >>> trainer.save("./my_slm")
    >>>
    >>> loaded = SLMTrainer.load("./my_slm")
    >>> text = loaded.generate("Once upon a time")
"""

from .trainer import SLMTrainer
from .tokenizer.tokenizer import SLMTokenizer
from .config.model_configs import ModelConfig, TINY_CONFIG, SMALL_CONFIG, MEDIUM_CONFIG
from .config.training_configs import TrainingConfig

__version__ = "0.1.0"

__all__ = [
    "SLMTrainer",
    "SLMTokenizer",
    "ModelConfig",
    "TrainingConfig",
    "TINY_CONFIG",
    "SMALL_CONFIG",
    "MEDIUM_CONFIG",
]
