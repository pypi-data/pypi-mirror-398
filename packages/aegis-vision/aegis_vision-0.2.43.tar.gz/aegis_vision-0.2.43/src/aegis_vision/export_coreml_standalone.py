# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
import os
from .headless_utils import setup_headless_environment
setup_headless_environment()

from typing import Any

import sys
from pathlib import Path

def export_to_coreml(
    model_path: str,
    output_dir: str = None,
    img_size: int = 640,
    format: str = "coreml",
    nms: bool = True,
    half: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Export PyTorch model to CoreML format
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        return {
            "success": False,
            "error": "ultralytics not installed. Please install with: pip install 'aegis-vision[training]'"
        }
    
    model_path = Path(model_path)
    
    if not model_path.exists():
        return {
            "success": False,
            "error": f"Model file not found: {model_path}"
        }
    
    if verbose:
        print(f"📦 Loading YOLO model from: {model_path}")
        # Debug: Verify torch is in sys.modules
        print(f"🔍 DEBUG: torch in sys.modules = {'torch' in sys.modules}")
    
    try:
        # Load YOLO model
        model: Any = YOLO(str(model_path))
        
        if verbose:
            print(f"✅ Model loaded successfully")
            print(f"🔄 Exporting to {format.upper()}...")
            print(f"   Parameters: imgsz={img_size}, nms={nms}, half={half}")

        if 'torch' not in sys.modules:
            raise RuntimeError("torch module not in sys.modules! This should never happen.")
        
        print(f"📦 Exporting to {format.upper()}...")

        # Export to specified format (default: CoreML)
        result = model.export(
            source='torch',
            format=format,
            imgsz=img_size,
            nms=nms,
            half=half,
        )
        
        result_path = Path(str(result))
        
        if verbose:
            print(f"✅ Export successful!")
            print(f"📦 Output: {result}")
        
        return {
            "success": True,
            "output_path": str(result_path),
            "exists": result_path.exists(),
        }
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        
        if verbose:
            print(f"❌ Export failed: {error_msg}")
            import traceback
            print(traceback.format_exc())
        
        return {
            "success": False,
            "error": error_msg,
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export PyTorch YOLO model to CoreML format"
    )
    parser.add_argument(
        "model_path",
        type=str,
        help="Path to .pt model file"
    )
    parser.add_argument(
        "--img-size",
        type=int,
        default=640,
        help="Input image size (default: 640)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="coreml",
        help="Export format (default: coreml)"
    )
    parser.add_argument(
        "--no-nms",
        action="store_true",
        help="Disable NMS (not recommended for Neural Engine)"
    )
    parser.add_argument(
        "--no-half",
        action="store_true",
        help="Disable FP16 precision"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧪 CoreML Export (Standalone Module)")
    print("=" * 80)
    print(f"🐍 Python: {sys.version}")
    print(f"📂 Model: {args.model_path}")
    print(f"📦 Format: {args.format}")
    print("=" * 80)
    
    result = export_to_coreml(
        model_path=args.model_path,
        img_size=args.img_size,
        format=args.format,
        nms=not args.no_nms,
        half=not args.no_half,
        verbose=True,
    )
    
    if result["success"]:
        print("\n" + "=" * 80)
        print("🎉 Export completed successfully!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Export failed!")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
