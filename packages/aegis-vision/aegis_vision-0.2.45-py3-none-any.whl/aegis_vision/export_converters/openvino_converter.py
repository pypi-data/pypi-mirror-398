#!/usr/bin/env python3
"""
OpenVINO Conversion Wrapper
Uses isolated Python environment to avoid dependency conflicts
Based on AegisForge reference implementation
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_openvino_venv_path() -> Path:
    """Get the path to the OpenVINO virtual environment"""
    # Use ~/.aegis-vision/venv_openvino (consistent with project convention)
    home_dir = Path.home()
    venv_path = home_dir / ".aegis-vision" / "venv_openvino"
    return venv_path


def setup_openvino_environment(venv_path: Path, auto_install: bool = True) -> Dict[str, Any]:
    """
    Automatically setup OpenVINO environment if it doesn't exist
    
    Fully autonomous - no user interaction required.
    Suitable for remote agent deployment.
    
    Args:
        venv_path: Path where to create the virtual environment
        auto_install: Whether to automatically install (True) or just report error (False)
        
    Returns:
        Dictionary with setup results
    """
    import shutil
    
    if venv_path.exists():
        logger.info(f"✅ OpenVINO environment already exists: {venv_path}")
        return {"success": True, "message": "Environment already exists", "path": str(venv_path)}
    
    if not auto_install:
        return {
            "success": False,
            "error": "OpenVINO environment not found and auto_install=False",
            "path": str(venv_path),
            "help": "Run: bash aegis-vision/scripts/setup_openvino_env.sh"
        }
    
    logger.info(f"🔧 OpenVINO environment not found. Creating automatically (no user interaction)...")
    logger.info(f"📍 Location: {venv_path}")
    logger.info(f"⏳ This may take 2-5 minutes...")
    
    # Check for Python 3.11 (required for PyTorch 2.4.1)
    python_cmd = None
    python_paths = [
        shutil.which("python3.11"),
        "/usr/local/bin/python3.11",
        "/opt/homebrew/bin/python3.11",
        "/usr/bin/python3.11",
    ]
    
    for path in python_paths:
        if path and Path(path).exists():
            python_cmd = path
            break
    
    if not python_cmd:
        # Try to find any Python 3.11 installation
        try:
            result = subprocess.run(
                ['which', 'python3.11'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                python_cmd = result.stdout.strip()
        except:
            pass
    
    if not python_cmd:
        return {
            "success": False,
            "error": "Python 3.11 not found. OpenVINO requires Python 3.11 for PyTorch 2.4.1 compatibility.",
            "help": "Install with: brew install python@3.11 (macOS) or apt-get install python3.11 (Linux)",
            "autonomous_install": "Consider installing Python 3.11 in your agent setup script"
        }
    
    try:
        # Ensure parent directory exists
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create virtual environment
        logger.info(f"📦 Creating Python 3.11 virtual environment...")
        result = subprocess.run(
            [python_cmd, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=120  # Increased timeout for slow systems
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to create venv: {result.stderr}",
                "stdout": result.stdout
            }
        
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            # Windows path
            pip_path = venv_path / "Scripts" / "pip.exe"
        
        if not pip_path.exists():
            return {
                "success": False,
                "error": f"pip not found in venv: {venv_path}"
            }
        
        # Upgrade pip (non-interactive)
        logger.info(f"📦 Upgrading pip...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel", "--quiet"],
            capture_output=True,
            timeout=180
        )
        
        # Find requirements file
        requirements_paths = [
            Path(__file__).parent.parent.parent.parent / "requirements" / "openvino.txt",
            Path(__file__).parent / "requirements" / "openvino.txt",
        ]
        
        requirements_file = None
        for req_path in requirements_paths:
            if req_path.exists():
                requirements_file = req_path
                break
        
        if not requirements_file:
            return {
                "success": False,
                "error": "Requirements file not found",
                "searched_paths": [str(p) for p in requirements_paths]
            }
        
        # Install requirements (non-interactive, with progress suppression)
        logger.info(f"📦 Installing OpenVINO dependencies from {requirements_file}...")
        logger.info(f"⏳ This may take 2-5 minutes (running in background)...")
        
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file), "--quiet", "--no-input"],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minutes max for slow connections
            env={**os.environ, "PIP_NO_INPUT": "1"}  # Force non-interactive
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to install requirements: {result.stderr}",
                "stdout": result.stdout,
                "autonomous_note": "This is a network or dependency issue, not user interaction"
            }
        
        logger.info(f"✅ OpenVINO environment created successfully (autonomous)!")
        logger.info(f"📍 Path: {venv_path}")
        logger.info(f"🤖 No user interaction was required")
        
        return {
            "success": True,
            "message": "OpenVINO environment created automatically (autonomous)",
            "path": str(venv_path),
            "autonomous": True
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Environment setup timed out. Please run manually: bash aegis-vision/scripts/setup_openvino_env.sh"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Failed to setup environment: {e}",
            "traceback": traceback.format_exc()
        }


def run_openvino_conversion(
    input_path: str,
    output_path: Optional[str] = None,
    precision: str = "fp16",
    image_size: int = 640,
    simplify: bool = True,
    auto_setup: bool = True,
) -> Dict[str, Any]:
    """
    Run OpenVINO conversion in isolated Python environment
    
    Args:
        input_path: Path to input .pt model file
        output_path: Optional output directory for OpenVINO IR (.xml and .bin files)
        precision: "fp16" or "fp32"
        image_size: Input image size
        simplify: Simplify the model graph for better performance
        auto_setup: Automatically create environment if missing (default: True)
        
    Returns:
        Dictionary with conversion results
    """
    
    # Path to the OpenVINO virtual environment
    venv_path = get_openvino_venv_path()
    python_path = venv_path / "bin" / "python"
    
    # Check if environment exists, create if needed
    if not python_path.exists():
        logger.warning(f"OpenVINO virtual environment not found at: {venv_path}")
        
        if auto_setup:
            logger.info(f"🔧 Attempting automatic setup...")
            setup_result = setup_openvino_environment(venv_path, auto_install=True)
            
            if not setup_result["success"]:
                logger.error(f"❌ Automatic setup failed: {setup_result.get('error')}")
                return {
                    "success": False,
                    "error": "OpenVINO environment setup failed",
                    "details": setup_result,
                    "venv_path": str(venv_path),
                    "help": "Try manual setup: bash aegis-vision/scripts/setup_openvino_env.sh"
                }
            
            logger.info(f"✅ Automatic setup completed successfully!")
        else:
            logger.error("Please run: aegis-vision/scripts/setup_openvino_env.sh")
            return {
                "success": False,
                "error": "OpenVINO virtual environment not found and auto_setup=False",
                "venv_path": str(venv_path),
                "help": "Run scripts/setup_openvino_env.sh to create the environment"
            }
    
    # Validate input path
    input_path_obj = Path(input_path).resolve()
    if not input_path_obj.exists():
        return {
            "success": False,
            "error": f"Input model not found: {input_path_obj}"
        }
    
    # Determine output path
    if output_path is None:
        output_path = str(input_path_obj.parent / (input_path_obj.stem + "_openvino_model"))
    
    # Create conversion script (runs in isolated environment)
    conversion_script = f'''
import os
os.environ['YOLO_AUTOINSTALL'] = 'false'

# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'

# Import PyTorch FIRST before any other ML libraries
import torch
from ultralytics import YOLO
import sys
import json
import shutil
import traceback

def main():
    try:
        print(f"PyTorch version: {{torch.__version__}}", file=sys.stderr)
        print("Loading YOLO model...", file=sys.stderr)
        model = YOLO("{input_path_obj}")
        
        print(f"Starting OpenVINO conversion...", file=sys.stderr)
        print(f"Precision: {precision}", file=sys.stderr)
        print(f"Image size: {image_size}", file=sys.stderr)
        print(f"Simplify: {simplify}", file=sys.stderr)
        
        # Configure export parameters
        export_args = {{
            "format": "openvino",
            "imgsz": {image_size},
            "verbose": True,
            "half": {"True" if precision == "fp16" else "False"},
            "simplify": {simplify},
        }}
        
        print(f"Export arguments: {{export_args}}", file=sys.stderr)
        
        result = model.export(**export_args)
        
        # Move result to desired output path if different
        result_path = str(result)
        target_path = "{output_path}"
        
        if result_path != target_path:
            print(f"Moving {{result_path}} to {{target_path}}", file=sys.stderr)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.move(result_path, target_path)
            result_path = target_path
        
        # Verify output files exist
        xml_file = None
        bin_file = None
        
        if os.path.isdir(result_path):
            for file in os.listdir(result_path):
                if file.endswith('.xml'):
                    xml_file = os.path.join(result_path, file)
                elif file.endswith('.bin'):
                    bin_file = os.path.join(result_path, file)
        
        return {{
            "success": True,
            "output_path": result_path,
            "xml_file": xml_file,
            "bin_file": bin_file,
            "message": "OpenVINO conversion completed successfully"
        }}
            
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": f"OpenVINO conversion failed: {{e}}"
        }}

if __name__ == "__main__":
    result = main()
    print(json.dumps(result))
'''
    
    try:
        logger.info(f"Running OpenVINO conversion in isolated environment: {venv_path}")
        logger.info(f"Input: {input_path_obj}")
        logger.info(f"Output: {output_path}")
        
        # Run the conversion script in the OpenVINO environment
        result = subprocess.run(
            [str(python_path), "-c", conversion_script],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for larger models
        )
        
        if result.returncode == 0:
            # Parse the JSON output from the last line
            lines = result.stdout.strip().split('\n')
            json_output = None
            
            # Find the JSON output (last valid JSON line)
            for line in reversed(lines):
                try:
                    json_output = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            
            if json_output:
                # Log stderr for debugging
                if result.stderr:
                    logger.debug(f"OpenVINO conversion stderr: {result.stderr}")
                return json_output
            else:
                return {
                    "success": False,
                    "error": "Could not parse conversion result",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        else:
            return {
                "success": False,
                "error": f"Conversion process failed with exit code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "OpenVINO conversion timed out after 10 minutes"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Failed to run OpenVINO conversion: {e}",
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    # CLI interface for standalone usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert YOLO model to OpenVINO format")
    parser.add_argument("input_path", help="Path to input .pt model file")
    parser.add_argument("-o", "--output", help="Output directory for OpenVINO IR files")
    parser.add_argument("--precision", default="fp16", choices=["fp16", "fp32"],
                       help="Model precision")
    parser.add_argument("--image-size", type=int, default=640,
                       help="Input image size")
    parser.add_argument("--no-simplify", action="store_true",
                       help="Disable graph simplification")
    
    args = parser.parse_args()
    
    result = run_openvino_conversion(
        input_path=args.input_path,
        output_path=args.output,
        precision=args.precision,
        image_size=args.image_size,
        simplify=not args.no_simplify
    )
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)
