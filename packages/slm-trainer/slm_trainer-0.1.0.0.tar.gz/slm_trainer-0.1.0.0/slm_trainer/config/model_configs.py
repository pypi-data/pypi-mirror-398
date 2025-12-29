"""
Model configuration presets for different model sizes.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for GPT model architecture."""

    # Model size identifier
    name: str

    # Architecture parameters
    vocab_size: int          # Vocabulary size
    max_seq_len: int         # Maximum sequence length (context window)
    d_model: int             # Embedding dimension
    n_layers: int            # Number of transformer blocks
    n_heads: int             # Number of attention heads
    d_ff: int                # Feed-forward network hidden dimension

    # Regularization
    dropout: float = 0.1
    attn_dropout: float = 0.1
    emb_dropout: float = 0.1

    # Computation
    device_type: str = 'auto'  # 'cpu', 'cuda', or 'auto'

    def __post_init__(self):
        """Validate configuration parameters."""
        # Ensure d_model is divisible by n_heads
        if self.d_model % self.n_heads != 0:
            raise ValueError(
                f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"
            )

        # Validate dropout rates
        for dropout_name in ['dropout', 'attn_dropout', 'emb_dropout']:
            dropout_val = getattr(self, dropout_name)
            if not 0.0 <= dropout_val <= 1.0:
                raise ValueError(f"{dropout_name} must be between 0.0 and 1.0")

        # Validate positive values
        for param_name in ['vocab_size', 'max_seq_len', 'd_model', 'n_layers', 'n_heads', 'd_ff']:
            param_val = getattr(self, param_name)
            if param_val <= 0:
                raise ValueError(f"{param_name} must be positive")

    def total_params(self) -> int:
        """
        Estimate total parameter count for this configuration.

        Returns:
            int: Estimated number of parameters in millions
        """
        # Token embeddings
        token_emb = self.vocab_size * self.d_model

        # Positional embeddings
        pos_emb = self.max_seq_len * self.d_model

        # Per transformer block parameters:
        # - Attention: 4 projections (Q, K, V, O) each of size d_model x d_model
        # - FFN: 2 linear layers (d_model -> d_ff -> d_model)
        # - Layer norms: 2 per block, each with 2*d_model params (gamma, beta)
        attention_params = 4 * (self.d_model * self.d_model)
        ffn_params = 2 * (self.d_model * self.d_ff)
        layer_norm_params = 4 * self.d_model  # 2 layer norms x 2 params each

        block_params = attention_params + ffn_params + layer_norm_params
        total_blocks = self.n_layers * block_params

        # Final layer normalization
        final_ln = 2 * self.d_model

        # LM head (weight tied with token embeddings, so no additional params)
        # If not weight tied, would add: vocab_size * d_model

        total = token_emb + pos_emb + total_blocks + final_ln

        return total

    def total_params_millions(self) -> float:
        """Return parameter count in millions."""
        return self.total_params() / 1_000_000


# Predefined model configurations

TINY_CONFIG = ModelConfig(
    name="tiny",
    vocab_size=8192,        # 8K vocabulary
    max_seq_len=512,        # 512 token context
    d_model=256,            # Small embedding dimension
    n_layers=6,             # 6 transformer blocks
    n_heads=4,              # 4 attention heads (head_dim = 64)
    d_ff=1024,              # 4 * d_model
    dropout=0.1,
    attn_dropout=0.1,
    emb_dropout=0.1,
    device_type='auto'      # Can run on CPU or GPU
)
# Estimated: ~17-20M parameters

SMALL_CONFIG = ModelConfig(
    name="small",
    vocab_size=16384,       # 16K vocabulary
    max_seq_len=1024,       # 1K token context
    d_model=512,            # Medium embedding dimension
    n_layers=8,             # 8 transformer blocks
    n_heads=8,              # 8 attention heads (head_dim = 64)
    d_ff=2048,              # 4 * d_model
    dropout=0.1,
    attn_dropout=0.1,
    emb_dropout=0.1,
    device_type='auto'      # Can run on CPU or GPU
)
# Estimated: ~89-95M parameters

MEDIUM_CONFIG = ModelConfig(
    name="medium",
    vocab_size=32768,       # 32K vocabulary (GPT-2 style)
    max_seq_len=2048,       # 2K token context
    d_model=768,            # Larger embedding dimension
    n_layers=12,            # 12 transformer blocks
    n_heads=12,             # 12 attention heads (head_dim = 64)
    d_ff=3072,              # 4 * d_model
    dropout=0.1,
    attn_dropout=0.1,
    emb_dropout=0.1,
    device_type='cuda'      # GPU only
)
# Estimated: ~243-250M parameters


# Model size mapping
MODEL_SIZE_MAP = {
    'tiny': TINY_CONFIG,
    'small': SMALL_CONFIG,
    'medium': MEDIUM_CONFIG
}


def get_model_config(model_size: str, **overrides) -> ModelConfig:
    """
    Get a model configuration by size, with optional parameter overrides.

    Args:
        model_size: One of 'tiny', 'small', 'medium'
        **overrides: Parameters to override in the base config

    Returns:
        ModelConfig: Configuration object

    Raises:
        ValueError: If model_size is not recognized

    Example:
        >>> config = get_model_config('small', d_model=768)
    """
    if model_size not in MODEL_SIZE_MAP:
        raise ValueError(
            f"Unknown model size: {model_size}. "
            f"Choose from: {list(MODEL_SIZE_MAP.keys())}"
        )

    base_config = MODEL_SIZE_MAP[model_size]

    # Apply overrides
    if overrides:
        config_dict = {
            'name': base_config.name,
            'vocab_size': base_config.vocab_size,
            'max_seq_len': base_config.max_seq_len,
            'd_model': base_config.d_model,
            'n_layers': base_config.n_layers,
            'n_heads': base_config.n_heads,
            'd_ff': base_config.d_ff,
            'dropout': base_config.dropout,
            'attn_dropout': base_config.attn_dropout,
            'emb_dropout': base_config.emb_dropout,
            'device_type': base_config.device_type
        }
        config_dict.update(overrides)
        return ModelConfig(**config_dict)

    return base_config
