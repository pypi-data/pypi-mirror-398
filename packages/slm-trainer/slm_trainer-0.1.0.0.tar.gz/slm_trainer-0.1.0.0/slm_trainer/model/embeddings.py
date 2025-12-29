"""
Token and positional embedding layers for the transformer model.
"""

import torch
import torch.nn as nn
import math


class TokenEmbedding(nn.Module):
    """
    Token embedding layer with proper initialization.
    """

    def __init__(self, vocab_size: int, d_model: int):
        """
        Initialize token embedding.

        Args:
            vocab_size: Size of the vocabulary
            d_model: Embedding dimension
        """
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model

        self.embedding = nn.Embedding(vocab_size, d_model)
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using normal distribution."""
        nn.init.normal_(self.embedding.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            input_ids: Token IDs of shape (batch_size, seq_len)

        Returns:
            Embeddings of shape (batch_size, seq_len, d_model)
        """
        return self.embedding(input_ids)


class PositionalEmbedding(nn.Module):
    """
    Learnable positional embeddings (GPT-style).

    This uses learned position embeddings rather than sinusoidal encodings,
    following the GPT architecture.
    """

    def __init__(self, max_seq_len: int, d_model: int):
        """
        Initialize positional embedding.

        Args:
            max_seq_len: Maximum sequence length
            d_model: Embedding dimension
        """
        super().__init__()
        self.max_seq_len = max_seq_len
        self.d_model = d_model

        self.embedding = nn.Embedding(max_seq_len, d_model)
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using normal distribution."""
        nn.init.normal_(self.embedding.weight, mean=0.0, std=0.02)

    def forward(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """
        Forward pass.

        Args:
            seq_len: Actual sequence length
            device: Device to create positions on

        Returns:
            Positional embeddings of shape (1, seq_len, d_model)
        """
        if seq_len > self.max_seq_len:
            raise ValueError(
                f"Sequence length {seq_len} exceeds maximum {self.max_seq_len}"
            )

        # Create position indices [0, 1, 2, ..., seq_len-1]
        positions = torch.arange(0, seq_len, dtype=torch.long, device=device)

        # Get embeddings (seq_len, d_model)
        pos_embeddings = self.embedding(positions)

        # Add batch dimension (1, seq_len, d_model)
        return pos_embeddings.unsqueeze(0)


class CombinedEmbedding(nn.Module):
    """
    Combined token and positional embeddings with dropout.

    This module combines token embeddings and positional embeddings,
    then applies dropout.
    """

    def __init__(
        self,
        vocab_size: int,
        max_seq_len: int,
        d_model: int,
        dropout: float = 0.1
    ):
        """
        Initialize combined embeddings.

        Args:
            vocab_size: Size of the vocabulary
            max_seq_len: Maximum sequence length
            d_model: Embedding dimension
            dropout: Dropout rate
        """
        super().__init__()
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.d_model = d_model

        self.token_emb = TokenEmbedding(vocab_size, d_model)
        self.pos_emb = PositionalEmbedding(max_seq_len, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass combining token and positional embeddings.

        Args:
            input_ids: Token IDs of shape (batch_size, seq_len)

        Returns:
            Combined embeddings of shape (batch_size, seq_len, d_model)
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device

        # Get token embeddings (batch_size, seq_len, d_model)
        token_embeddings = self.token_emb(input_ids)

        # Get positional embeddings (1, seq_len, d_model)
        pos_embeddings = self.pos_emb(seq_len, device)

        # Combine embeddings (broadcasting handles batch dimension)
        embeddings = token_embeddings + pos_embeddings

        # Apply dropout
        embeddings = self.dropout(embeddings)

        return embeddings

    def get_token_embedding_weight(self) -> torch.nn.Parameter:
        """
        Get the token embedding weight matrix for weight tying.

        Returns:
            Token embedding weights of shape (vocab_size, d_model)
        """
        return self.token_emb.embedding.weight
