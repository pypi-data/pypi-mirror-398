"""
GPT-style transformer language model.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import math

from .embeddings import CombinedEmbedding
from .transformer import TransformerBlock
from ..config.model_configs import ModelConfig


class GPTModel(nn.Module):
    """
    GPT-style transformer model for causal language modeling.

    Architecture:
    - Token + Positional embeddings
    - N stacked transformer blocks
    - Layer normalization
    - Linear head for next-token prediction (weight tied with embeddings)
    """

    def __init__(self, config: ModelConfig):
        """
        Initialize GPT model.

        Args:
            config: Model configuration
        """
        super().__init__()
        self.config = config

        # Combined token and positional embeddings
        self.embeddings = CombinedEmbedding(
            vocab_size=config.vocab_size,
            max_seq_len=config.max_seq_len,
            d_model=config.d_model,
            dropout=config.emb_dropout
        )

        # Stack of transformer blocks
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(
                d_model=config.d_model,
                n_heads=config.n_heads,
                d_ff=config.d_ff,
                max_seq_len=config.max_seq_len,
                attn_dropout=config.attn_dropout,
                dropout=config.dropout
            )
            for _ in range(config.n_layers)
        ])

        # Final layer normalization
        self.ln_f = nn.LayerNorm(config.d_model)

        # Language modeling head (projects to vocabulary)
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Weight tying: share weights between token embeddings and lm_head
        # This reduces parameters and often improves performance
        self.lm_head.weight = self.embeddings.get_token_embedding_weight()

        # Initialize weights
        self.apply(self._init_weights)

        # Report number of parameters
        n_params = sum(p.numel() for p in self.parameters())
        print(f"Number of parameters: {n_params / 1e6:.2f}M")

    def _init_weights(self, module):
        """
        Initialize weights for different module types.

        Args:
            module: PyTorch module to initialize
        """
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass.

        Args:
            input_ids: Input token IDs of shape (batch_size, seq_len)
            attention_mask: Optional attention mask of shape (batch_size, seq_len)
                           where 1 indicates valid positions and 0 indicates padding
            labels: Optional labels of shape (batch_size, seq_len) for computing loss

        Returns:
            Tuple of (logits, loss):
                - logits: Logits of shape (batch_size, seq_len, vocab_size)
                - loss: Language modeling loss (if labels provided), else None
        """
        # Get embeddings
        x = self.embeddings(input_ids)

        # Pass through transformer blocks
        for block in self.transformer_blocks:
            x = block(x, attention_mask=attention_mask)

        # Final layer normalization
        x = self.ln_f(x)

        # Project to vocabulary
        logits = self.lm_head(x)

        # Compute loss if labels are provided
        loss = None
        if labels is not None:
            # Flatten logits and labels for cross-entropy
            # logits: (batch_size * seq_len, vocab_size)
            # labels: (batch_size * seq_len,)
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                ignore_index=-100  # Ignore padding tokens in loss
            )

        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        pad_token_id: Optional[int] = None,
        eos_token_id: Optional[int] = None
    ) -> torch.Tensor:
        """
        Generate text autoregressively.

        Args:
            input_ids: Initial token IDs of shape (batch_size, seq_len)
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_k: Keep only top k tokens with highest probability (nucleus filtering)
            top_p: Keep top tokens with cumulative probability >= top_p (nucleus sampling)
            pad_token_id: Padding token ID (to create attention mask)
            eos_token_id: End-of-sequence token ID (to stop generation)

        Returns:
            Generated token IDs of shape (batch_size, seq_len + max_new_tokens)
        """
        self.eval()  # Set to evaluation mode

        # Clone input to avoid modifying original
        generated = input_ids.clone()

        for _ in range(max_new_tokens):
            # If sequence is longer than max_seq_len, use only the last max_seq_len tokens
            input_seq = generated
            if input_seq.size(1) > self.config.max_seq_len:
                input_seq = input_seq[:, -self.config.max_seq_len:]

            # Create attention mask if pad_token_id is provided
            attention_mask = None
            if pad_token_id is not None:
                attention_mask = (input_seq != pad_token_id).long()

            # Forward pass
            logits, _ = self.forward(input_seq, attention_mask=attention_mask)

            # Get logits for the last token
            # logits: (batch_size, vocab_size)
            logits = logits[:, -1, :]

            # Apply temperature
            if temperature != 1.0:
                logits = logits / temperature

            # Apply top-k filtering
            if top_k is not None:
                # Get top-k logits and indices
                top_k_logits, top_k_indices = torch.topk(logits, min(top_k, logits.size(-1)))

                # Set all other logits to -inf
                logits_filtered = torch.full_like(logits, float('-inf'))
                logits_filtered.scatter_(1, top_k_indices, top_k_logits)
                logits = logits_filtered

            # Apply top-p (nucleus) sampling
            if top_p is not None:
                # Sort logits in descending order
                sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)

                # Compute cumulative probabilities
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

                # Remove tokens with cumulative probability above the threshold
                sorted_indices_to_remove = cumulative_probs > top_p

                # Shift right to keep at least one token
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = False

                # Create mask and apply it
                indices_to_remove = sorted_indices_to_remove.scatter(
                    1, sorted_indices, sorted_indices_to_remove
                )
                logits = logits.masked_fill(indices_to_remove, float('-inf'))

            # Sample from the distribution
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)

            # Append to generated sequence
            generated = torch.cat([generated, next_token], dim=1)

            # Stop if EOS token is generated
            if eos_token_id is not None and (next_token == eos_token_id).all():
                break

        return generated

    def get_num_params(self, non_embedding: bool = False) -> int:
        """
        Get the number of parameters in the model.

        Args:
            non_embedding: If True, exclude embedding parameters

        Returns:
            Number of parameters
        """
        n_params = sum(p.numel() for p in self.parameters())
        if non_embedding:
            n_params -= self.embeddings.token_emb.embedding.weight.numel()
            n_params -= self.embeddings.pos_emb.embedding.weight.numel()
        return n_params
