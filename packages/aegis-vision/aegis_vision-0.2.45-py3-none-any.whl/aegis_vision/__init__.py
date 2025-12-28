"""
Aegis Vision - Computer Vision Training Utilities

A Python package for training computer vision models on cloud platforms like Kaggle.
Focused on YOLO object detection with support for multiple model variants and export formats.
"""

# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
import os
from .headless_utils import setup_headless_environment
setup_headless_environment()

# Dynamically read version from pyproject.toml to ensure consistency
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        tomllib = None

if tomllib:
    from pathlib import Path
    _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    if _pyproject_path.exists():
        with open(_pyproject_path, "rb") as f:
            _pyproject_data = tomllib.load(f)
            __version__ = _pyproject_data.get("project", {}).get("version", "0.0.0")
    else:
        __version__ = "0.0.0"  # Fallback if pyproject.toml not found
else:
    # Fallback: hardcoded version (should match pyproject.toml manually)
    __version__ = "0.2.x"

__author__ = "Aegis AI Team"
__license__ = "MIT"

# Optional training and converter modules
try:
    from .trainer import YOLOTrainer
    TRAINING_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    YOLOTrainer = None
    TRAINING_AVAILABLE = False

try:
    from .converters import COCOConverter, DatasetMerger, AdvancedCOCOtoYOLOMerger
    CONVERTERS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    COCOConverter = None
    DatasetMerger = None
    AdvancedCOCOtoYOLOMerger = None
    CONVERTERS_AVAILABLE = False

# Core utilities (should always work)
from .dataset_utils import discover_datasets, preprocess_datasets, preprocess_coco_standard
from .utils import (
    setup_logging,
    get_device_info,
    detect_environment,
    format_size,
    format_time,
)

# Optional cloud and export modules
try:
    from .kaggle_uploader import KaggleModelUploader, upload_trained_model
    KAGGLE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    KaggleModelUploader = None
    upload_trained_model = None
    KAGGLE_AVAILABLE = False

try:
    from .export_coreml_standalone import export_to_coreml
    COREML_EXPORT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    # Dummy function for when dependencies are missing
    def export_to_coreml(*args, **kwargs):
        raise RuntimeError("Export dependencies (ultralytics/coremltools) not found. Install with: pip install 'aegis-vision[training]'")
    COREML_EXPORT_AVAILABLE = False

__all__ = [
    "YOLOTrainer",
    "COCOConverter",
    "DatasetMerger",
    "AdvancedCOCOtoYOLOMerger",
    "discover_datasets",
    "preprocess_datasets",
    "preprocess_coco_standard",
    "setup_logging",
    "get_device_info",
    "detect_environment",
    "format_size",
    "format_time",
    "KaggleModelUploader",
    "upload_trained_model",
    "export_to_coreml",
    "COREML_EXPORT_AVAILABLE",
]
