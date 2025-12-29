"""
SLMTokenizer: A wrapper around SentencePiece tokenizer with save/load functionality.
"""

import sentencepiece as spm
import os
from typing import List, Union, Optional
import shutil


class SLMTokenizer:
    """
    Tokenizer wrapper for SentencePiece with encode/decode functionality.

    This class provides a simple interface for tokenizing text using SentencePiece,
    with support for saving and loading trained tokenizers.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize tokenizer.

        Args:
            model_path: Path to trained SentencePiece model file (.model)
                       If None, tokenizer must be trained before use.
        """
        self.sp = None
        self.model_path = model_path

        if model_path is not None:
            self.load(model_path)

    def load(self, model_path: str) -> None:
        """
        Load a trained SentencePiece model.

        Args:
            model_path: Path to .model file

        Raises:
            ValueError: If model file doesn't exist
        """
        if not os.path.exists(model_path):
            raise ValueError(f"Model file not found: {model_path}")

        self.sp = spm.SentencePieceProcessor()
        self.sp.Load(model_path)
        self.model_path = model_path

    def train(
        self,
        input_file: str,
        model_prefix: str,
        vocab_size: int = 8000,
        model_type: str = 'bpe'
    ) -> None:
        """
        Train a new SentencePiece tokenizer.

        Args:
            input_file: Path to input text file
            model_prefix: Prefix for output model files
            vocab_size: Vocabulary size
            model_type: Tokenization algorithm ('bpe' or 'unigram')
        """
        from .trainer import train_sentencepiece_tokenizer

        train_sentencepiece_tokenizer(
            input_file=input_file,
            model_prefix=model_prefix,
            vocab_size=vocab_size,
            model_type=model_type
        )

        # Load the trained model
        self.load(f"{model_prefix}.model")

    def encode(
        self,
        text: Union[str, List[str]],
        add_bos: bool = False,
        add_eos: bool = False
    ) -> Union[List[int], List[List[int]]]:
        """
        Encode text to token IDs.

        Args:
            text: Text string or list of text strings
            add_bos: Whether to add beginning-of-sequence token
            add_eos: Whether to add end-of-sequence token

        Returns:
            List of token IDs, or list of lists if input is a list

        Raises:
            RuntimeError: If tokenizer is not loaded
        """
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded. Call load() or train() first.")

        # Handle single string
        if isinstance(text, str):
            ids = self.sp.EncodeAsIds(text)
            if add_bos:
                ids = [self.bos_token_id] + ids
            if add_eos:
                ids = ids + [self.eos_token_id]
            return ids

        # Handle list of strings
        encoded = []
        for t in text:
            ids = self.sp.EncodeAsIds(t)
            if add_bos:
                ids = [self.bos_token_id] + ids
            if add_eos:
                ids = ids + [self.eos_token_id]
            encoded.append(ids)
        return encoded

    def decode(
        self,
        ids: Union[List[int], List[List[int]]],
        skip_special_tokens: bool = True
    ) -> Union[str, List[str]]:
        """
        Decode token IDs to text.

        Args:
            ids: List of token IDs, or list of lists for batch decoding
            skip_special_tokens: Whether to skip special tokens in output

        Returns:
            Decoded text string, or list of strings if input is a list of lists

        Raises:
            RuntimeError: If tokenizer is not loaded
        """
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded. Call load() or train() first.")

        # Handle single list of IDs
        if isinstance(ids[0], int):
            if skip_special_tokens:
                # Filter out special tokens
                ids = [
                    id for id in ids
                    if id not in [self.pad_token_id, self.bos_token_id, self.eos_token_id]
                ]
            return self.sp.DecodeIds(ids)

        # Handle batch (list of lists)
        decoded = []
        for id_list in ids:
            if skip_special_tokens:
                id_list = [
                    id for id in id_list
                    if id not in [self.pad_token_id, self.bos_token_id, self.eos_token_id]
                ]
            decoded.append(self.sp.DecodeIds(id_list))
        return decoded

    def encode_batch(
        self,
        texts: List[str],
        max_length: Optional[int] = None,
        padding: bool = True,
        add_bos: bool = False,
        add_eos: bool = False
    ) -> dict:
        """
        Encode a batch of texts with optional padding.

        Args:
            texts: List of text strings
            max_length: Maximum sequence length (will truncate or pad)
            padding: Whether to pad sequences to same length
            add_bos: Whether to add beginning-of-sequence token
            add_eos: Whether to add end-of-sequence token

        Returns:
            Dictionary with 'input_ids' and 'attention_mask' keys
        """
        # Encode all texts
        encoded = self.encode(texts, add_bos=add_bos, add_eos=add_eos)

        # Determine max length
        if max_length is None:
            max_length = max(len(ids) for ids in encoded)

        # Truncate and/or pad
        input_ids = []
        attention_mask = []

        for ids in encoded:
            # Truncate if needed
            if len(ids) > max_length:
                ids = ids[:max_length]

            # Create attention mask (1 for real tokens, 0 for padding)
            mask = [1] * len(ids)

            # Pad if needed
            if padding and len(ids) < max_length:
                padding_length = max_length - len(ids)
                ids = ids + [self.pad_token_id] * padding_length
                mask = mask + [0] * padding_length

            input_ids.append(ids)
            attention_mask.append(mask)

        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask
        }

    def save(self, save_path: str) -> None:
        """
        Save the tokenizer to a directory.

        Args:
            save_path: Directory path to save the tokenizer
        """
        if self.sp is None:
            raise RuntimeError("No tokenizer to save. Train or load a tokenizer first.")

        os.makedirs(save_path, exist_ok=True)

        # Copy model and vocab files
        if self.model_path:
            model_filename = os.path.basename(self.model_path)
            vocab_filename = model_filename.replace('.model', '.vocab')

            # Copy .model file
            shutil.copy(self.model_path, os.path.join(save_path, 'tokenizer.model'))

            # Copy .vocab file if it exists
            vocab_path = self.model_path.replace('.model', '.vocab')
            if os.path.exists(vocab_path):
                shutil.copy(vocab_path, os.path.join(save_path, 'tokenizer.vocab'))

    @classmethod
    def from_pretrained(cls, load_path: str) -> 'SLMTokenizer':
        """
        Load a tokenizer from a directory.

        Args:
            load_path: Directory path containing the tokenizer

        Returns:
            Loaded tokenizer instance
        """
        model_path = os.path.join(load_path, 'tokenizer.model')
        if not os.path.exists(model_path):
            raise ValueError(f"Tokenizer model not found in {load_path}")

        return cls(model_path=model_path)

    @property
    def vocab_size(self) -> int:
        """Get vocabulary size."""
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded.")
        return self.sp.GetPieceSize()

    @property
    def pad_token_id(self) -> int:
        """Get padding token ID."""
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded.")
        return self.sp.pad_id()

    @property
    def unk_token_id(self) -> int:
        """Get unknown token ID."""
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded.")
        return self.sp.unk_id()

    @property
    def bos_token_id(self) -> int:
        """Get beginning-of-sequence token ID."""
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded.")
        return self.sp.bos_id()

    @property
    def eos_token_id(self) -> int:
        """Get end-of-sequence token ID."""
        if self.sp is None:
            raise RuntimeError("Tokenizer not loaded.")
        return self.sp.eos_id()

    def __len__(self) -> int:
        """Return vocabulary size."""
        return self.vocab_size

    def __repr__(self) -> str:
        """String representation."""
        if self.sp is None:
            return "SLMTokenizer(not loaded)"
        return f"SLMTokenizer(vocab_size={self.vocab_size})"
