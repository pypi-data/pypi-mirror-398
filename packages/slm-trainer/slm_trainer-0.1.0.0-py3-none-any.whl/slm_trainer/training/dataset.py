"""
Dataset and data loading utilities for text data.
"""

import torch
from torch.utils.data import Dataset
from typing import List, Dict, Optional
import os


class TextDataset(Dataset):
    """
    Dataset for loading and preprocessing text data for language modeling.

    Uses a sliding window approach to create training examples from long text.
    """

    def __init__(
        self,
        file_path: str,
        tokenizer,
        max_length: int = 512,
        stride: Optional[int] = None
    ):
        """
        Initialize text dataset.

        Args:
            file_path: Path to text file
            tokenizer: Tokenizer instance with encode method
            max_length: Maximum sequence length
            stride: Stride for sliding window (if None, uses max_length for non-overlapping)

        Example:
            >>> from slm_trainer.tokenizer import SLMTokenizer
            >>> tokenizer = SLMTokenizer.from_pretrained('./tokenizer')
            >>> dataset = TextDataset('data.txt', tokenizer, max_length=512)
        """
        self.file_path = file_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.stride = stride if stride is not None else max_length

        # Read and tokenize the entire file
        self.examples = self._load_and_tokenize()

    def _load_and_tokenize(self) -> List[List[int]]:
        """
        Load text file and create training examples using sliding window.

        Returns:
            List of token ID sequences
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Read text
        with open(self.file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Tokenize entire text
        token_ids = self.tokenizer.encode(text, add_bos=True, add_eos=True)

        # Create sliding window examples
        examples = []
        for i in range(0, len(token_ids), self.stride):
            # Extract window
            window = token_ids[i:i + self.max_length]

            # Only keep windows that are long enough
            if len(window) > 1:  # Need at least 2 tokens (input + target)
                examples.append(window)

            # Stop if we've processed all tokens
            if i + self.max_length >= len(token_ids):
                break

        print(f"Loaded {len(examples)} examples from {self.file_path}")
        return examples

    def __len__(self) -> int:
        """Return number of examples."""
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get a single example.

        Args:
            idx: Index of the example

        Returns:
            Dictionary with 'input_ids' and 'labels' tensors
        """
        token_ids = self.examples[idx]

        # For language modeling, input and labels are the same (shifted during loss computation)
        input_ids = torch.tensor(token_ids, dtype=torch.long)
        labels = torch.tensor(token_ids, dtype=torch.long)

        return {
            'input_ids': input_ids,
            'labels': labels
        }


class DataCollator:
    """
    Collate function for batching variable-length sequences.

    Handles padding and creates attention masks.
    """

    def __init__(self, pad_token_id: int = 0):
        """
        Initialize data collator.

        Args:
            pad_token_id: Token ID to use for padding
        """
        self.pad_token_id = pad_token_id

    def __call__(self, batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """
        Collate a batch of examples.

        Args:
            batch: List of dictionaries with 'input_ids' and 'labels'

        Returns:
            Dictionary with batched tensors:
                - input_ids: (batch_size, max_seq_len)
                - labels: (batch_size, max_seq_len)
                - attention_mask: (batch_size, max_seq_len)
        """
        # Find max length in batch
        max_length = max(len(example['input_ids']) for example in batch)

        # Prepare batched tensors
        input_ids_batch = []
        labels_batch = []
        attention_mask_batch = []

        for example in batch:
            input_ids = example['input_ids']
            labels = example['labels']
            seq_len = len(input_ids)

            # Create attention mask (1 for real tokens, 0 for padding)
            attention_mask = torch.ones(seq_len, dtype=torch.long)

            # Pad if necessary
            if seq_len < max_length:
                padding_length = max_length - seq_len

                # Pad input_ids
                input_ids = torch.cat([
                    input_ids,
                    torch.full((padding_length,), self.pad_token_id, dtype=torch.long)
                ])

                # Pad labels (use -100 for padding so it's ignored in loss)
                labels = torch.cat([
                    labels,
                    torch.full((padding_length,), -100, dtype=torch.long)
                ])

                # Pad attention mask
                attention_mask = torch.cat([
                    attention_mask,
                    torch.zeros(padding_length, dtype=torch.long)
                ])

            input_ids_batch.append(input_ids)
            labels_batch.append(labels)
            attention_mask_batch.append(attention_mask)

        # Stack into batch
        return {
            'input_ids': torch.stack(input_ids_batch),
            'labels': torch.stack(labels_batch),
            'attention_mask': torch.stack(attention_mask_batch)
        }


def split_dataset(
    dataset: TextDataset,
    val_split: float = 0.1,
    seed: int = 42
) -> tuple:
    """
    Split dataset into train and validation sets.

    Args:
        dataset: Dataset to split
        val_split: Fraction of data for validation
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_dataset, val_dataset)

    Example:
        >>> dataset = TextDataset('data.txt', tokenizer)
        >>> train_ds, val_ds = split_dataset(dataset, val_split=0.1)
    """
    from torch.utils.data import random_split

    # Calculate sizes
    total_size = len(dataset)
    val_size = int(total_size * val_split)
    train_size = total_size - val_size

    # Split dataset
    generator = torch.Generator().manual_seed(seed)
    train_dataset, val_dataset = random_split(
        dataset,
        [train_size, val_size],
        generator=generator
    )

    return train_dataset, val_dataset
