"""
Utility functions for Aegis Vision training
"""

import logging
import platform
import sys
import time
from typing import Dict, Any


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for training scripts
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_device_info() -> Dict[str, Any]:
    """
    Get information about the current compute device
    
    Returns:
        Dictionary with device information
    """
    device_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    
    try:
        import torch
        device_info["torch_version"] = torch.__version__
        
        if torch.cuda.is_available():
            device_info.update({
                "device": "cuda",
                "device_name": torch.cuda.get_device_name(0),
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
            })
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_info.update({
                "device": "mps",
                "device_name": "Apple Silicon (MPS)",
                "gpu_count": 1,
            })
        else:
            device_info.update({
                "device": "cpu",
                "device_name": "CPU",
            })
    except ImportError:
        device_info.update({
            "device": "unknown",
            "device_name": "CPU (Torch not installed)",
            "torch_version": "not installed"
        })
    
    return device_info


def detect_environment() -> str:
    """
    Detect the current execution environment
    
    Returns:
        Environment name (kaggle, colab, local, etc.)
    """
    import os
    from pathlib import Path
    
    if Path("/kaggle/input").exists():
        return "kaggle"
    elif Path("/content").exists() and "COLAB_GPU" in os.environ:
        return "colab"
    else:
        return "local"


def format_size(bytes_size: int) -> str:
    """
    Format bytes into human-readable size
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "10.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def log_progress(message: str, **kwargs):
    """
    Log training progress with structured format for backend parsing
    
    Args:
        message: Log message
        **kwargs: Additional metadata to include in log
    """
    import json
    
    log_entry = {
        "message": message,
        "timestamp": time.time(),
        **kwargs
    }
    print(f"TRAINING_LOG: {json.dumps(log_entry)}")
    
    logger = logging.getLogger(__name__)
    logger.info(message)
