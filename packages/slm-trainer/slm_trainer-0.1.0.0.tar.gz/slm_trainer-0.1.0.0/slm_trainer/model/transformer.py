"""
Transformer block with attention and feed-forward network.
"""

import torch
import torch.nn as nn


class FeedForward(nn.Module):
    """
    Feed-forward network (MLP) used in transformer blocks.

    Architecture: Linear -> GELU -> Linear -> Dropout
    Expands to d_ff (typically 4 * d_model) then projects back to d_model.
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        """
        Initialize feed-forward network.

        Args:
            d_model: Model dimension
            d_ff: Feed-forward hidden dimension (typically 4 * d_model)
            dropout: Dropout rate
        """
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

        self._init_weights()

    def _init_weights(self):
        """Initialize weights using normal distribution."""
        nn.init.normal_(self.fc1.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.fc2.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.fc1.bias)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)
        x = self.dropout(x)
        return x


class TransformerBlock(nn.Module):
    """
    Transformer block with pre-normalization (GPT-2 style).

    Architecture:
        x = x + Attention(LayerNorm(x))
        x = x + FeedForward(LayerNorm(x))

    This is the "pre-norm" variant which applies layer normalization
    before the sub-layers, which is more stable for training.
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        max_seq_len: int,
        attn_dropout: float = 0.1,
        dropout: float = 0.1
    ):
        """
        Initialize transformer block.

        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward hidden dimension
            max_seq_len: Maximum sequence length
            attn_dropout: Dropout rate for attention
            dropout: Dropout rate for residual connections
        """
        super().__init__()

        # Import here to avoid circular dependency
        from .attention import MultiHeadCausalAttention

        # Layer normalization (before attention and FFN)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

        # Multi-head attention
        self.attn = MultiHeadCausalAttention(
            d_model=d_model,
            n_heads=n_heads,
            max_seq_len=max_seq_len,
            attn_dropout=attn_dropout,
            resid_dropout=dropout
        )

        # Feed-forward network
        self.ffn = FeedForward(d_model=d_model, d_ff=d_ff, dropout=dropout)

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: torch.Tensor = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            attention_mask: Optional attention mask of shape (batch_size, seq_len)

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Pre-norm: Apply layer norm before attention
        # Then add residual connection
        x = x + self.attn(self.ln1(x), attention_mask=attention_mask)

        # Pre-norm: Apply layer norm before feed-forward
        # Then add residual connection
        x = x + self.ffn(self.ln2(x))

        return x
