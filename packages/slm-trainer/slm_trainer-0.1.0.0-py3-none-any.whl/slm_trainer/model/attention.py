"""
Multi-head causal self-attention mechanism.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadCausalAttention(nn.Module):
    """
    Multi-head causal self-attention with scaled dot-product attention.

    This implements the attention mechanism used in GPT models, with:
    - Causal masking (preventing attention to future tokens)
    - Multi-head attention
    - Scaled dot-product attention
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        max_seq_len: int,
        attn_dropout: float = 0.1,
        resid_dropout: float = 0.1
    ):
        """
        Initialize multi-head attention.

        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            max_seq_len: Maximum sequence length (for causal mask)
            attn_dropout: Dropout rate for attention weights
            resid_dropout: Dropout rate for output
        """
        super().__init__()

        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.max_seq_len = max_seq_len

        # Query, Key, Value projections for all heads (in one matrix for efficiency)
        self.qkv_proj = nn.Linear(d_model, 3 * d_model)

        # Output projection
        self.out_proj = nn.Linear(d_model, d_model)

        # Dropout layers
        self.attn_dropout = nn.Dropout(attn_dropout)
        self.resid_dropout = nn.Dropout(resid_dropout)

        # Causal mask (lower triangular matrix)
        # This mask prevents attending to future positions
        self.register_buffer(
            "causal_mask",
            torch.tril(torch.ones(max_seq_len, max_seq_len)).view(
                1, 1, max_seq_len, max_seq_len
            )
        )

        self._init_weights()

    def _init_weights(self):
        """Initialize weights using normal distribution."""
        nn.init.normal_(self.qkv_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.out_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.qkv_proj.bias)
        nn.init.zeros_(self.out_proj.bias)

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
                           where 1 indicates valid positions and 0 indicates padding

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        batch_size, seq_len, d_model = x.shape

        # Compute Q, K, V for all heads in batch
        # qkv shape: (batch_size, seq_len, 3 * d_model)
        qkv = self.qkv_proj(x)

        # Split into Q, K, V
        # Each has shape: (batch_size, seq_len, d_model)
        q, k, v = qkv.chunk(3, dim=-1)

        # Reshape for multi-head attention
        # (batch_size, seq_len, d_model) -> (batch_size, seq_len, n_heads, head_dim)
        # -> (batch_size, n_heads, seq_len, head_dim)
        q = q.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        # Q * K^T / sqrt(head_dim)
        # (batch_size, n_heads, seq_len, head_dim) @ (batch_size, n_heads, head_dim, seq_len)
        # -> (batch_size, n_heads, seq_len, seq_len)
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # Apply causal mask (prevent attending to future positions)
        # Slice the causal mask to match the current sequence length
        causal_mask = self.causal_mask[:, :, :seq_len, :seq_len]
        attn_scores = attn_scores.masked_fill(causal_mask == 0, float('-inf'))

        # Apply attention mask if provided (for padding)
        if attention_mask is not None:
            # Expand mask dimensions: (batch_size, seq_len) -> (batch_size, 1, 1, seq_len)
            attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
            attn_scores = attn_scores.masked_fill(attention_mask == 0, float('-inf'))

        # Softmax to get attention weights
        # (batch_size, n_heads, seq_len, seq_len)
        attn_weights = F.softmax(attn_scores, dim=-1)

        # Apply attention dropout
        attn_weights = self.attn_dropout(attn_weights)

        # Weighted sum of values
        # (batch_size, n_heads, seq_len, seq_len) @ (batch_size, n_heads, seq_len, head_dim)
        # -> (batch_size, n_heads, seq_len, head_dim)
        attn_output = torch.matmul(attn_weights, v)

        # Reshape back to (batch_size, seq_len, d_model)
        # (batch_size, n_heads, seq_len, head_dim) -> (batch_size, seq_len, n_heads, head_dim)
        # -> (batch_size, seq_len, d_model)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, d_model)

        # Output projection
        output = self.out_proj(attn_output)

        # Apply residual dropout
        output = self.resid_dropout(output)

        return output
