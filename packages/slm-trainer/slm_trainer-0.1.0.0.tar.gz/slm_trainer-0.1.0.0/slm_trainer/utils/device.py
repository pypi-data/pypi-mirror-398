"""
Device management utilities for CPU/GPU detection and configuration.
"""

import torch
from typing import Optional


def get_device(device: Optional[str] = None) -> torch.device:
    """
    Get the appropriate PyTorch device.

    Args:
        device: Device string ('cpu', 'cuda', 'cuda:0', etc.) or None for auto-detection

    Returns:
        torch.device object

    Example:
        >>> device = get_device()  # Auto-detect
        >>> device = get_device('cuda')  # Force CUDA
        >>> device = get_device('cpu')  # Force CPU
    """
    if device is None or device == 'auto':
        # Auto-detect: use CUDA if available, otherwise CPU
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        return torch.device(device)


def is_cuda_available() -> bool:
    """
    Check if CUDA is available.

    Returns:
        True if CUDA is available, False otherwise
    """
    return torch.cuda.is_available()


def get_device_info() -> dict:
    """
    Get detailed device information.

    Returns:
        Dictionary with device information
    """
    info = {
        'cuda_available': torch.cuda.is_available(),
        'device_count': 0,
        'current_device': None,
        'device_name': None,
        'device_capability': None,
        'memory_allocated': None,
        'memory_reserved': None,
    }

    if torch.cuda.is_available():
        info['device_count'] = torch.cuda.device_count()
        info['current_device'] = torch.cuda.current_device()
        info['device_name'] = torch.cuda.get_device_name(0)
        info['device_capability'] = torch.cuda.get_device_capability(0)

        # Memory info (in MB)
        info['memory_allocated'] = torch.cuda.memory_allocated(0) / 1024 / 1024
        info['memory_reserved'] = torch.cuda.memory_reserved(0) / 1024 / 1024

    return info


def print_device_info():
    """Print device information in a readable format."""
    info = get_device_info()

    print("=" * 50)
    print("Device Information")
    print("=" * 50)

    if info['cuda_available']:
        print(f"CUDA Available: Yes")
        print(f"Number of GPUs: {info['device_count']}")
        print(f"Current Device: {info['current_device']}")
        print(f"Device Name: {info['device_name']}")
        print(f"Device Capability: {info['device_capability']}")
        print(f"Memory Allocated: {info['memory_allocated']:.2f} MB")
        print(f"Memory Reserved: {info['memory_reserved']:.2f} MB")
    else:
        print(f"CUDA Available: No")
        print(f"Using CPU")

    print("=" * 50)


def move_to_device(obj, device: torch.device):
    """
    Move a PyTorch object (model, tensor, etc.) to a device.

    Args:
        obj: PyTorch model, tensor, or other object
        device: Target device

    Returns:
        Object moved to the device
    """
    if hasattr(obj, 'to'):
        return obj.to(device)
    return obj


def empty_cache():
    """
    Empty CUDA cache to free up memory.

    This can help when you're running into CUDA out of memory errors.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
