"""
Linux-specific GPU detection for NVIDIA GPUs.

Implements multi-method detection strategy:
1. PyTorch CUDA API (if available)
2. nvidia-smi command (most reliable)
3. /proc filesystem (headless environments, no nvidia-smi binary)
4. CUDA toolkit detection (nvcc, CUDA_HOME)
"""

import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LinuxGPUDetector:
    """
    Linux GPU detection using multiple fallback strategies.
    Handles edge cases like CPU-only PyTorch builds.
    """
    
    @staticmethod
    def detect_nvidia_via_smi() -> Dict[str, Any]:
        """
        Detect NVIDIA GPUs using nvidia-smi command.
        
        Returns:
            Dict with detected GPU info:
            {
                "detected": bool,
                "gpus": [...],
                "driver_version": str | None,
                "cuda_version": str | None
            }
        """
        result = {
            "detected": False,
            "gpus": [],
            "driver_version": None,
            "cuda_version": None
        }
        
        try:
            # Query GPU information
            # Note: compute_capability is not a valid query field in all nvidia-smi versions
            cmd = [
                'nvidia-smi',
                '--query-gpu=index,name,memory.total,driver_version',
                '--format=csv,noheader,nounits'
            ]
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.returncode != 0:
                logger.debug(f"nvidia-smi failed: {proc.stderr}")
                return result
            
            result["detected"] = True
            lines = proc.stdout.strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        # Handle memory value that might be [N/A]
                        memory_val = 0
                        if len(parts) > 2 and parts[2] != '[N/A]':
                            try:
                                memory_val = round(int(parts[2]) / 1024, 2)  # MB to GB
                            except ValueError:
                                memory_val = 0
                        
                        gpu_info = {
                            "index": int(parts[0]),
                            "name": parts[1],
                            "memory": memory_val,
                            "compute_capability": "Unknown"  # Not available via nvidia-smi query
                        }
                        result["gpus"].append(gpu_info)
                        
                        # Extract driver version from first line
                        if len(parts) > 3 and not result["driver_version"]:
                            result["driver_version"] = parts[3]
                            
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse GPU info: {e}")
            
            # Get CUDA version from nvcc
            result["cuda_version"] = LinuxGPUDetector._get_cuda_version()
            
            return result
            
        except FileNotFoundError:
            logger.debug("nvidia-smi not found in PATH")
            return result
        except subprocess.TimeoutExpired:
            logger.debug("nvidia-smi command timed out")
            return result
        except Exception as e:
            logger.debug(f"nvidia-smi detection failed: {e}")
            return result
    
    @staticmethod
    def detect_nvidia_via_proc() -> Dict[str, Any]:
        """
        Detect NVIDIA GPUs using /proc filesystem (Linux only).
        
        Used when nvidia-smi is not available (e.g., containers, minimal environments).
        
        Returns:
            Dict with GPU detection info
        """
        result = {
            "detected": False,
            "gpus": [],
            "driver_version": None,
            "cuda_version": None
        }
        
        try:
            # Check if NVIDIA driver is loaded
            proc_path = Path("/proc/driver/nvidia/version")
            if not proc_path.exists():
                logger.debug("NVIDIA driver not detected in /proc")
                return result
            
            # Read driver version
            with open(proc_path, 'r') as f:
                version_str = f.read()
                match = re.search(r'NVRM version: (\S+)', version_str)
                if match:
                    result["driver_version"] = match.group(1)
            
            # Check for GPU devices in /proc/driver/nvidia/gpus/
            gpus_path = Path("/proc/driver/nvidia/gpus")
            if gpus_path.exists():
                result["detected"] = True
                
                for gpu_dir in sorted(gpus_path.iterdir()):
                    if gpu_dir.is_dir():
                        try:
                            gpu_index = int(gpu_dir.name)
                            info_path = gpu_dir / "information"
                            
                            gpu_info = {
                                "index": gpu_index,
                                "name": "NVIDIA GPU",  # Name not available in /proc
                                "memory": 0,  # Memory not easily available
                                "compute_capability": "Unknown"
                            }
                            
                            if info_path.exists():
                                with open(info_path, 'r') as f:
                                    info = f.read()
                                    # Try to extract GPU name
                                    name_match = re.search(r'Model:\s+(.+)', info)
                                    if name_match:
                                        gpu_info["name"] = name_match.group(1)
                            
                            result["gpus"].append(gpu_info)
                        except (ValueError, IOError):
                            pass
            
            # Get CUDA version
            result["cuda_version"] = LinuxGPUDetector._get_cuda_version()
            
            return result
            
        except Exception as e:
            logger.debug(f"/proc GPU detection failed: {e}")
            return result
    
    @staticmethod
    def _get_cuda_version() -> Optional[str]:
        """
        Detect CUDA version from nvcc or CUDA_HOME environment variable.
        
        Returns:
            CUDA version string (e.g., "12.1") or None
        """
        try:
            # Try nvcc first
            proc = subprocess.run(
                ['nvcc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if proc.returncode == 0:
                match = re.search(r'release\s+([\d.]+)', proc.stdout)
                if match:
                    return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try CUDA_HOME environment variable
        import os
        cuda_home = os.environ.get('CUDA_HOME')
        if cuda_home:
            version_file = Path(cuda_home) / "version.txt"
            if version_file.exists():
                try:
                    with open(version_file, 'r') as f:
                        match = re.search(r'CUDA Release ([\d.]+)', f.read())
                        if match:
                            return match.group(1)
                except IOError:
                    pass
        
        return None
    
    @staticmethod
    def detect() -> Dict[str, Any]:
        """
        Detect NVIDIA GPUs on Linux using multiple strategies.
        
        Returns:
            Standardized GPU detection result
        """
        # Try nvidia-smi first (most reliable)
        result = LinuxGPUDetector.detect_nvidia_via_smi()
        
        if result["detected"] and result["gpus"]:
            logger.debug(f"Detected {len(result['gpus'])} GPU(s) via nvidia-smi")
            return result
        
        # Fallback to /proc filesystem
        logger.debug("nvidia-smi failed, trying /proc filesystem")
        result = LinuxGPUDetector.detect_nvidia_via_proc()
        
        if result["detected"] and result["gpus"]:
            logger.debug(f"Detected {len(result['gpus'])} GPU(s) via /proc")
        
        return result
