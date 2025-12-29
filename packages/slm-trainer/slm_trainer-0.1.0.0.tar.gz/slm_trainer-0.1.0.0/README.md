# SLM-Trainer: Train Private Small Language Models

A simple Python library for training Small Language Models (SLMs) from scratch using PyTorch, SentencePiece, and GPT-style transformer architecture.

## Why SLM-Trainer?

With the rapid adoption of Generative AI, organizations increasingly face challenges related to:
- **Data Privacy**: Sensitive data leaving internal systems
- **High Costs**: Ongoing API and infrastructure expenses
- **Complexity**: Vector databases, RAG pipelines, fine-tuning large models
- **Latency**: Slower responses due to retrieval and external APIs
- **Limited Control**: Dependency on external models

SLM-Trainer solves these problems by enabling you to:
- Train domain-specific language models from scratch
- Use only your own private text data
- Run models offline or on-premises
- Avoid external APIs and complex infrastructure
- Deploy cost-efficient, secure AI models

## Features

- **Simple API**: Scikit-learn-like interface for training language models
- **Three Model Sizes**: Tiny (10-30M params), Small (50-125M params), Medium (200-300M params)
- **CPU & GPU Support**: Tiny and Small models can train on CPU
- **Private & Secure**: Train on your own data, no external dependencies
- **Text Generation**: Built-in autoregressive generation with temperature, top-k, and top-p sampling
- **Easy to Use**: Just 3-5 lines of code to train a model

## Installation

```bash
pip install slm-trainer
```

## Quick Start

```python
from slm_trainer import SLMTrainer

# Initialize trainer with desired model size
trainer = SLMTrainer(model_size="small")

# Train on your text data
trainer.train("data.txt", epochs=10)

# Save the trained model
trainer.save("./my_slm")

# Load and use the model
loaded = SLMTrainer.load("./my_slm")
text = loaded.generate("Once upon a time", max_new_tokens=50)
print(text)
```

That's it! You now have a custom language model trained on your data.

## Model Sizes

| Model Size | Parameters | Context Length | CPU Training | GPU Training | Use Case |
|-----------|------------|----------------|--------------|--------------|----------|
| Tiny | 10-30M | 512 tokens | ✅ | ✅ | Quick prototyping, limited resources |
| Small | 50-125M | 1024 tokens | ✅(slow) | ✅ | General purpose, balanced performance |
| Medium | 200-300M | 2048 tokens | ❌ | ✅ | Best quality, requires GPU |

## API Reference

### SLMTrainer

Main class for training and using small language models.

#### `__init__(model_size='small', vocab_size=None, device=None, **kwargs)`

Initialize the trainer.

**Parameters:**
- `model_size` (str): One of 'tiny', 'small', 'medium'
- `vocab_size` (int, optional): Override default vocabulary size
- `device` (str, optional): 'cpu', 'cuda', or None for auto-detection
- `**kwargs`: Additional model configuration overrides

**Example:**
```python
trainer = SLMTrainer(model_size="small", vocab_size=16000)
```

#### `train(data, epochs=10, val_data=None, learning_rate=None, batch_size=None, **kwargs)`

Train the model on text data.

**Parameters:**
- `data` (str or list): Path to text file or list of strings
- `epochs` (int): Number of training epochs
- `val_data` (str or list, optional): Validation data
- `learning_rate` (float, optional): Override default learning rate
- `batch_size` (int, optional): Override default batch size
- `**kwargs`: Additional training configuration overrides

**Example:**
```python
trainer.train("data.txt", epochs=10, batch_size=32, learning_rate=1e-4)
```

#### `save(path)`

Save model, tokenizer, and configurations.

**Parameters:**
- `path` (str): Directory path to save the model

**Example:**
```python
trainer.save("./my_model")
```

#### `load(path, device=None)` (classmethod)

Load a trained model from directory.

**Parameters:**
- `path` (str): Directory containing the saved model
- `device` (str, optional): Device to load model on

**Returns:**
- `SLMTrainer`: Loaded trainer instance

**Example:**
```python
trainer = SLMTrainer.load("./my_model")
```

#### `generate(prompt, max_new_tokens=100, temperature=1.0, top_k=None, top_p=None)`

Generate text given a prompt.

**Parameters:**
- `prompt` (str): Input text to continue
- `max_new_tokens` (int): Maximum tokens to generate
- `temperature` (float): Sampling temperature (higher = more random)
- `top_k` (int, optional): Keep only top k tokens for sampling
- `top_p` (float, optional): Nucleus sampling threshold

**Returns:**
- `str`: Generated text

**Example:**
```python
text = trainer.generate(
    "Once upon a time",
    max_new_tokens=50,
    temperature=0.8,
    top_p=0.9
)
```

## Advanced Usage

### Custom Model Configuration

```python
from slm_trainer import SLMTrainer

# Start with a base size and customize
trainer = SLMTrainer(
    model_size="small",
    d_model=768,        # Override embedding dimension
    n_layers=10,        # Override number of layers
    max_seq_len=2048    # Override context length
)
```

### Training with Validation Data

```python
trainer = SLMTrainer(model_size="small")

trainer.train(
    data="train.txt",
    val_data="val.txt",  # Provide separate validation data
    epochs=20
)
```

### Using Pre-trained Tokenizer

```python
from slm_trainer import SLMTokenizer

# Train tokenizer separately
tokenizer = SLMTokenizer()
tokenizer.train(
    input_file="data.txt",
    model_prefix="my_tokenizer",
    vocab_size=32000
)
tokenizer.save("./tokenizer")

# Use with trainer
trainer = SLMTrainer(model_size="small")
trainer.tokenizer = SLMTokenizer.from_pretrained("./tokenizer")
trainer.train("data.txt", epochs=10)
```

## Requirements

- Python >= 3.8
- PyTorch >= 2.0.0
- SentencePiece >= 0.1.99
- NumPy >= 1.21.0
- tqdm >= 4.65.0

## Hardware Requirements

### Tiny Model (10-30M parameters)
- **CPU**: 4GB RAM, any modern CPU
- **GPU**: 2GB VRAM (optional)
- **Training Time**: ~1-2 hours for 10M tokens on CPU

### Small Model (50-125M parameters)
- **CPU**: 8GB RAM, modern multi-core CPU
- **GPU**: 4GB VRAM (recommended)
- **Training Time**: ~4-8 hours for 10M tokens on GPU

### Medium Model (200-300M parameters)
- **CPU**: Not recommended
- **GPU**: 8GB+ VRAM (required)
- **Training Time**: ~8-16 hours for 10M tokens on GPU


## Technical Details

### Architecture

- **Model Type**: GPT-style transformer (decoder-only)
- **Tokenizer**: BPE tokenization via SentencePiece
- **Attention**: Multi-head causal self-attention
- **Normalization**: Pre-normalization (GPT-2 style)
- **Activation**: GELU
- **Weight Tying**: Token embeddings and LM head share weights

### Training

- **Optimizer**: AdamW with weight decay
- **Learning Rate Schedule**: Linear warmup + cosine decay
- **Gradient Clipping**: max_norm=1.0
- **Mixed Precision**: Automatic mixed precision (AMP) support
- **Regularization**: Dropout, label smoothing (optional)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.



## Acknowledgments

- Built with [PyTorch](https://pytorch.org/)
- Tokenization powered by [SentencePiece](https://github.com/google/sentencepiece)
