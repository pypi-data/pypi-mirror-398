"""
Checkpoint utilities for saving and loading models.
"""

import torch
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path


def save_checkpoint(
    model: torch.nn.Module,
    save_path: str,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[Any] = None,
    epoch: Optional[int] = None,
    global_step: Optional[int] = None,
    metrics: Optional[Dict[str, float]] = None,
    config: Optional[Any] = None
) -> None:
    """
    Save a model checkpoint with optional training state.

    Args:
        model: PyTorch model to save
        save_path: Directory path to save the checkpoint
        optimizer: Optional optimizer state
        scheduler: Optional learning rate scheduler state
        epoch: Current epoch number
        global_step: Current global step
        metrics: Optional dictionary of metrics
        config: Optional model configuration

    Example:
        >>> save_checkpoint(
        ...     model=model,
        ...     save_path='./checkpoints/step_1000',
        ...     optimizer=optimizer,
        ...     epoch=5,
        ...     metrics={'loss': 0.5}
        ... )
    """
    # Create directory if it doesn't exist
    os.makedirs(save_path, exist_ok=True)

    # Prepare checkpoint dictionary
    checkpoint = {
        'model_state_dict': model.state_dict(),
    }

    # Add optional components
    if optimizer is not None:
        checkpoint['optimizer_state_dict'] = optimizer.state_dict()

    if scheduler is not None:
        checkpoint['scheduler_state_dict'] = scheduler.state_dict()

    if epoch is not None:
        checkpoint['epoch'] = epoch

    if global_step is not None:
        checkpoint['global_step'] = global_step

    if metrics is not None:
        checkpoint['metrics'] = metrics

    # Save checkpoint
    checkpoint_path = os.path.join(save_path, 'pytorch_model.bin')
    torch.save(checkpoint, checkpoint_path)

    # Save config if provided
    if config is not None:
        save_config(config, save_path)

    print(f"Checkpoint saved to {save_path}")


def load_checkpoint(
    model: torch.nn.Module,
    load_path: str,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[Any] = None,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Load a model checkpoint and optionally restore training state.

    Args:
        model: PyTorch model to load weights into
        load_path: Directory path containing the checkpoint
        optimizer: Optional optimizer to restore state
        scheduler: Optional scheduler to restore state
        device: Device to load the checkpoint on

    Returns:
        Dictionary containing checkpoint metadata (epoch, step, metrics, etc.)

    Example:
        >>> info = load_checkpoint(
        ...     model=model,
        ...     load_path='./checkpoints/step_1000',
        ...     optimizer=optimizer
        ... )
        >>> print(f"Resumed from epoch {info['epoch']}")
    """
    checkpoint_path = os.path.join(load_path, 'pytorch_model.bin')

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")

    # Load checkpoint
    if device is None:
        checkpoint = torch.load(checkpoint_path)
    else:
        checkpoint = torch.load(checkpoint_path, map_location=device)

    # Load model weights
    model.load_state_dict(checkpoint['model_state_dict'])

    # Load optimizer state if provided
    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    # Load scheduler state if provided
    if scheduler is not None and 'scheduler_state_dict' in checkpoint:
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

    # Prepare metadata
    metadata = {}
    if 'epoch' in checkpoint:
        metadata['epoch'] = checkpoint['epoch']
    if 'global_step' in checkpoint:
        metadata['global_step'] = checkpoint['global_step']
    if 'metrics' in checkpoint:
        metadata['metrics'] = checkpoint['metrics']

    print(f"Checkpoint loaded from {load_path}")

    return metadata


def save_config(config: Any, save_path: str, filename: str = 'config.json') -> None:
    """
    Save a configuration object as JSON.

    Args:
        config: Configuration object (dataclass, dict, or any object with __dict__)
        save_path: Directory path to save the config
        filename: Filename for the config file

    Example:
        >>> from slm_trainer.config.model_configs import SMALL_CONFIG
        >>> save_config(SMALL_CONFIG, './my_model')
    """
    os.makedirs(save_path, exist_ok=True)

    # Convert config to dict if it's a dataclass or object
    if hasattr(config, '__dict__'):
        config_dict = {
            k: v for k, v in config.__dict__.items()
            if not k.startswith('_')
        }
    elif isinstance(config, dict):
        config_dict = config
    else:
        raise TypeError("Config must be a dataclass, dict, or object with __dict__")

    # Save as JSON
    config_path = os.path.join(save_path, filename)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2)

    print(f"Config saved to {config_path}")


def load_config(load_path: str, filename: str = 'config.json') -> Dict[str, Any]:
    """
    Load a configuration from JSON.

    Args:
        load_path: Directory path containing the config
        filename: Filename of the config file

    Returns:
        Dictionary containing configuration

    Example:
        >>> config_dict = load_config('./my_model')
        >>> print(config_dict['d_model'])
    """
    config_path = os.path.join(load_path, filename)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)

    return config_dict


def get_latest_checkpoint(checkpoints_dir: str) -> Optional[str]:
    """
    Get the path to the latest checkpoint in a directory.

    Assumes checkpoints are named with step numbers (e.g., 'step_1000', 'step_2000').

    Args:
        checkpoints_dir: Directory containing checkpoints

    Returns:
        Path to the latest checkpoint, or None if no checkpoints found
    """
    if not os.path.exists(checkpoints_dir):
        return None

    # Find all checkpoint directories
    checkpoints = []
    for item in os.listdir(checkpoints_dir):
        item_path = os.path.join(checkpoints_dir, item)
        if os.path.isdir(item_path):
            checkpoint_file = os.path.join(item_path, 'pytorch_model.bin')
            if os.path.exists(checkpoint_file):
                checkpoints.append(item_path)

    if not checkpoints:
        return None

    # Sort by modification time (most recent last)
    checkpoints.sort(key=lambda x: os.path.getmtime(x))

    return checkpoints[-1]


def cleanup_old_checkpoints(
    checkpoints_dir: str,
    keep_last_n: int = 5
) -> None:
    """
    Remove old checkpoints, keeping only the most recent ones.

    Args:
        checkpoints_dir: Directory containing checkpoints
        keep_last_n: Number of recent checkpoints to keep

    Example:
        >>> cleanup_old_checkpoints('./checkpoints', keep_last_n=3)
    """
    if not os.path.exists(checkpoints_dir):
        return

    # Find all checkpoint directories
    checkpoints = []
    for item in os.listdir(checkpoints_dir):
        item_path = os.path.join(checkpoints_dir, item)
        if os.path.isdir(item_path):
            checkpoint_file = os.path.join(item_path, 'pytorch_model.bin')
            if os.path.exists(checkpoint_file):
                checkpoints.append(item_path)

    if len(checkpoints) <= keep_last_n:
        return  # Nothing to cleanup

    # Sort by modification time (oldest first)
    checkpoints.sort(key=lambda x: os.path.getmtime(x))

    # Remove old checkpoints
    for checkpoint_path in checkpoints[:-keep_last_n]:
        import shutil
        shutil.rmtree(checkpoint_path)
        print(f"Removed old checkpoint: {checkpoint_path}")
