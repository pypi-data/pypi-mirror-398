"""
Main SLMTrainer API - Simple interface for training small language models.
"""

import torch
from torch.utils.data import DataLoader
from typing import Optional, Union, List
import os

from .config.model_configs import get_model_config, ModelConfig
from .config.training_configs import get_training_config, TrainingConfig
from .model.gpt import GPTModel
from .tokenizer.tokenizer import SLMTokenizer
from .training.dataset import TextDataset, DataCollator, split_dataset
from .training.trainer_engine import TrainingEngine
from .training.callbacks import LoggingCallback, CheckpointCallback, ProgressCallback
from .utils.device import get_device
from .utils.checkpoint import save_checkpoint, load_checkpoint, save_config, load_config


class SLMTrainer:
    """
    Main API class for training Small Language Models.

    This class provides a simple, scikit-learn-like interface for training
    GPT-style transformer models from scratch using only text data.

    Example:
        >>> from slm_trainer import SLMTrainer
        >>>
        >>> # Initialize trainer
        >>> trainer = SLMTrainer(model_size="small")
        >>>
        >>> # Train on text file
        >>> trainer.train("data.txt", epochs=10)
        >>>
        >>> # Save model
        >>> trainer.save("./my_slm")
        >>>
        >>> # Load model
        >>> loaded = SLMTrainer.load("./my_slm")
        >>>
        >>> # Generate text
        >>> text = loaded.generate("Once upon a time")
        >>> print(text)
    """

    def __init__(
        self,
        model_size: str = "small",
        vocab_size: Optional[int] = None,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize SLM Trainer.

        Args:
            model_size: One of 'tiny', 'small', 'medium'
            vocab_size: Override default vocabulary size
            device: Device to use ('cpu', 'cuda', or None for auto-detect)
            **kwargs: Additional model config overrides

        Example:
            >>> trainer = SLMTrainer(model_size="small", vocab_size=16000)
        """
        self.model_size = model_size
        self.device = get_device(device)

        # Get model configuration
        model_config_overrides = {}
        if vocab_size is not None:
            model_config_overrides['vocab_size'] = vocab_size
        model_config_overrides.update(kwargs)

        self.model_config = get_model_config(model_size, **model_config_overrides)

        # Initialize components (lazy loading)
        self.tokenizer = None
        self.model = None
        self.training_engine = None

        print(f"Initialized SLMTrainer with model size: {model_size}")
        print(f"Device: {self.device}")
        print(f"Estimated parameters: {self.model_config.total_params_millions():.2f}M")

    def train(
        self,
        data: Union[str, List[str]],
        epochs: int = 10,
        val_data: Optional[Union[str, List[str]]] = None,
        learning_rate: Optional[float] = None,
        batch_size: Optional[int] = None,
        **kwargs
    ):
        """
        Train the model on text data.

        Args:
            data: Path to text file or list of text strings
            epochs: Number of training epochs
            val_data: Optional validation data (file path or list of strings)
            learning_rate: Override default learning rate
            batch_size: Override default batch size
            **kwargs: Additional training config overrides

        Example:
            >>> trainer.train("data.txt", epochs=10, batch_size=32)
        """
        print("\n" + "=" * 70)
        print("Starting Training Process")
        print("=" * 70)

        # Step 1: Train or load tokenizer
        if self.tokenizer is None:
            print("\nStep 1: Training tokenizer...")
            self._train_tokenizer(data)
        else:
            print("\nStep 1: Using existing tokenizer")

        # Step 2: Update model config with actual vocab size
        if self.model_config.vocab_size != self.tokenizer.vocab_size:
            print(f"Updating vocab size: {self.model_config.vocab_size} -> {self.tokenizer.vocab_size}")
            self.model_config.vocab_size = self.tokenizer.vocab_size

        # Step 3: Initialize model
        if self.model is None:
            print("\nStep 2: Initializing model...")
            self._initialize_model()
        else:
            print("\nStep 2: Using existing model")

        # Step 4: Prepare datasets
        print("\nStep 3: Preparing datasets...")
        train_loader, val_loader = self._prepare_datasets(
            data, val_data, batch_size
        )

        # Step 5: Setup training
        print("\nStep 4: Setting up training...")
        train_config_overrides = {}
        if learning_rate is not None:
            train_config_overrides['learning_rate'] = learning_rate
        if batch_size is not None:
            train_config_overrides['batch_size'] = batch_size
        train_config_overrides.update(kwargs)

        train_config = get_training_config(self.model_size, **train_config_overrides)
        train_config.epochs = epochs

        # Create callbacks
        callbacks = [
            LoggingCallback(log_every_n_steps=100),
            CheckpointCallback(
                save_dir='./checkpoints',
                save_every_n_steps=train_config.save_every_n_steps
            ),
            ProgressCallback()
        ]

        # Create training engine
        self.training_engine = TrainingEngine(
            model=self.model,
            train_config=train_config,
            device=self.device,
            callbacks=callbacks
        )

        # Step 6: Train
        print("\nStep 5: Training model...")
        history = self.training_engine.train(
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=epochs
        )

        print("\nTraining completed successfully!")
        return history

    def save(self, path: str):
        """
        Save model, tokenizer, and configurations to directory.

        Args:
            path: Directory path to save the model

        Example:
            >>> trainer.save("./my_slm")
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("No model to save. Train a model first.")

        print(f"\nSaving model to {path}...")

        # Create directory
        os.makedirs(path, exist_ok=True)

        # Save model checkpoint
        save_checkpoint(
            model=self.model,
            save_path=path,
            config=self.model_config
        )

        # Save tokenizer
        self.tokenizer.save(path)

        # Save model config
        save_config(self.model_config, path, filename='model_config.json')

        print(f"Model saved successfully to {path}")

    @classmethod
    def load(cls, path: str, device: Optional[str] = None) -> "SLMTrainer":
        """
        Load a trained model from directory.

        Args:
            path: Directory path containing the saved model
            device: Device to load model on (None for auto-detect)

        Returns:
            Loaded SLMTrainer instance

        Example:
            >>> trainer = SLMTrainer.load("./my_slm")
        """
        print(f"Loading model from {path}...")

        # Load model config
        config_dict = load_config(path, filename='model_config.json')

        # Create trainer instance
        trainer = cls(
            model_size=config_dict['name'],
            device=device,
            **config_dict
        )

        # Load tokenizer
        trainer.tokenizer = SLMTokenizer.from_pretrained(path)

        # Update vocab size in config
        trainer.model_config.vocab_size = trainer.tokenizer.vocab_size

        # Initialize model
        trainer._initialize_model()

        # Load model weights
        load_checkpoint(
            model=trainer.model,
            load_path=path,
            device=trainer.device
        )

        print("Model loaded successfully!")

        return trainer

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> str:
        """
        Generate text given a prompt.

        Args:
            prompt: Input text to continue
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_k: Keep only top k tokens for sampling
            top_p: Nucleus sampling threshold

        Returns:
            Generated text

        Example:
            >>> text = trainer.generate("Once upon a time", max_new_tokens=50)
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("No model loaded. Train or load a model first.")

        # Encode prompt
        input_ids = self.tokenizer.encode(prompt, add_bos=True)
        input_ids = torch.tensor([input_ids], dtype=torch.long, device=self.device)

        # Generate
        self.model.eval()
        generated_ids = self.model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )

        # Decode
        generated_text = self.tokenizer.decode(
            generated_ids[0].tolist(),
            skip_special_tokens=True
        )

        return generated_text

    def _train_tokenizer(self, data: Union[str, List[str]]):
        """Train SentencePiece tokenizer on data."""
        # Determine if data is file path or text
        if isinstance(data, str) and os.path.isfile(data):
            input_file = data
        else:
            # Write to temporary file
            input_file = "temp_tokenizer_data.txt"
            if isinstance(data, str):
                data = [data]
            with open(input_file, 'w', encoding='utf-8') as f:
                for text in data:
                    f.write(text + '\n')

        # Train tokenizer
        self.tokenizer = SLMTokenizer()
        self.tokenizer.train(
            input_file=input_file,
            model_prefix='slm_tokenizer',
            vocab_size=self.model_config.vocab_size,
            model_type='bpe'
        )

        print(f"Tokenizer trained with vocab size: {self.tokenizer.vocab_size}")

    def _initialize_model(self):
        """Initialize the GPT model."""
        self.model = GPTModel(self.model_config)
        self.model.to(self.device)

    def _prepare_datasets(
        self,
        train_data: Union[str, List[str]],
        val_data: Optional[Union[str, List[str]]],
        batch_size: Optional[int]
    ):
        """Prepare training and validation data loaders."""
        # Ensure train_data is a file
        if isinstance(train_data, list):
            train_file = "temp_train_data.txt"
            with open(train_file, 'w', encoding='utf-8') as f:
                for text in train_data:
                    f.write(text + '\n')
            train_data = train_file

        # Create dataset
        dataset = TextDataset(
            file_path=train_data,
            tokenizer=self.tokenizer,
            max_length=self.model_config.max_seq_len
        )

        # Split into train/val if val_data not provided
        if val_data is None:
            train_config = get_training_config(self.model_size)
            train_dataset, val_dataset = split_dataset(
                dataset,
                val_split=train_config.val_split
            )
        else:
            train_dataset = dataset
            # Create validation dataset
            if isinstance(val_data, list):
                val_file = "temp_val_data.txt"
                with open(val_file, 'w', encoding='utf-8') as f:
                    for text in val_data:
                        f.write(text + '\n')
                val_data = val_file

            val_dataset = TextDataset(
                file_path=val_data,
                tokenizer=self.tokenizer,
                max_length=self.model_config.max_seq_len
            )

        # Create data loaders
        batch_size = batch_size or get_training_config(self.model_size).batch_size
        collator = DataCollator(pad_token_id=self.tokenizer.pad_token_id)

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collator,
            num_workers=0  # 0 for Windows compatibility
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=collator,
            num_workers=0
        )

        print(f"Train dataset: {len(train_dataset)} examples")
        print(f"Validation dataset: {len(val_dataset)} examples")

        return train_loader, val_loader
