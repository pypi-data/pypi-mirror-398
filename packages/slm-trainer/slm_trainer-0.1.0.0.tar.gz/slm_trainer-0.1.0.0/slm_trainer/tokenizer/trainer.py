"""
SentencePiece tokenizer training utilities.
"""

import sentencepiece as spm
import os
from typing import Optional, List


def train_sentencepiece_tokenizer(
    input_file: str,
    model_prefix: str,
    vocab_size: int = 8000,
    model_type: str = 'bpe',
    character_coverage: float = 0.9995,
    pad_id: int = 0,
    unk_id: int = 1,
    bos_id: int = 2,
    eos_id: int = 3,
    user_defined_symbols: Optional[List[str]] = None
) -> None:
    """
    Train a SentencePiece tokenizer with sensible defaults.

    Args:
        input_file: Path to input text file for training
        model_prefix: Prefix for output model files (will create .model and .vocab files)
        vocab_size: Vocabulary size (default: 8000)
        model_type: Tokenization algorithm ('bpe' or 'unigram')
        character_coverage: Character coverage for handling rare characters
                           (1.0 for languages like English, 0.9995 for languages with many chars)
        pad_id: ID for padding token
        unk_id: ID for unknown token
        bos_id: ID for beginning-of-sequence token
        eos_id: ID for end-of-sequence token
        user_defined_symbols: Optional list of user-defined symbols to include in vocabulary

    Raises:
        ValueError: If input_file doesn't exist or model_type is invalid
        RuntimeError: If SentencePiece training fails

    Example:
        >>> train_sentencepiece_tokenizer(
        ...     input_file='data.txt',
        ...     model_prefix='my_tokenizer',
        ...     vocab_size=16000
        ... )
        # This creates my_tokenizer.model and my_tokenizer.vocab
    """
    # Validate input file
    if not os.path.exists(input_file):
        raise ValueError(f"Input file not found: {input_file}")

    # Validate model type
    if model_type not in ['bpe', 'unigram']:
        raise ValueError(f"model_type must be 'bpe' or 'unigram', got: {model_type}")

    # Build training command
    train_args = [
        f'--input={input_file}',
        f'--model_prefix={model_prefix}',
        f'--vocab_size={vocab_size}',
        f'--model_type={model_type}',
        f'--character_coverage={character_coverage}',
        f'--pad_id={pad_id}',
        f'--unk_id={unk_id}',
        f'--bos_id={bos_id}',
        f'--eos_id={eos_id}',
        '--pad_piece=<pad>',
        '--unk_piece=<unk>',
        '--bos_piece=<bos>',
        '--eos_piece=<eos>',
        '--normalization_rule_name=nmt_nfkc',  # Normalize text
        '--remove_extra_whitespaces=true',     # Clean up whitespace
        '--max_sentence_length=16384',         # Max sentence length
    ]

    # Add user-defined symbols if provided
    if user_defined_symbols:
        symbols_str = ','.join(user_defined_symbols)
        train_args.append(f'--user_defined_symbols={symbols_str}')

    # Train the model
    try:
        spm.SentencePieceTrainer.Train(' '.join(train_args))
        print(f"Tokenizer trained successfully!")
        print(f"Model saved to: {model_prefix}.model")
        print(f"Vocabulary saved to: {model_prefix}.vocab")
    except Exception as e:
        raise RuntimeError(f"Failed to train SentencePiece tokenizer: {e}")


def train_tokenizer_from_text(
    text_data: List[str],
    model_prefix: str,
    vocab_size: int = 8000,
    model_type: str = 'bpe',
    temp_file: str = 'temp_train_data.txt'
) -> None:
    """
    Train a SentencePiece tokenizer from a list of text strings.

    This is a convenience function that writes text to a temporary file
    and then trains the tokenizer.

    Args:
        text_data: List of text strings
        model_prefix: Prefix for output model files
        vocab_size: Vocabulary size
        model_type: Tokenization algorithm ('bpe' or 'unigram')
        temp_file: Temporary file to write text data

    Example:
        >>> texts = ["Hello world", "This is a test", "Training tokenizer"]
        >>> train_tokenizer_from_text(texts, 'my_tokenizer', vocab_size=1000)
    """
    # Write text to temporary file
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            for text in text_data:
                f.write(text + '\n')

        # Train tokenizer from file
        train_sentencepiece_tokenizer(
            input_file=temp_file,
            model_prefix=model_prefix,
            vocab_size=vocab_size,
            model_type=model_type
        )

    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
