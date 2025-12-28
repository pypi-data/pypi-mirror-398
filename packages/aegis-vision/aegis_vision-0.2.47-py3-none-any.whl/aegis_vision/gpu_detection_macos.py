"""
macOS-specific GPU detection for Metal/MPS acceleration.

macOS does NOT support CUDA - use Metal/MPS instead.
This detector identifies Apple Silicon (Metal) capabilities.

Reference:
- PyTorch MPS support: https://pytorch.org/docs/stable/notes/mps.html
- Metal Performance Shaders: https://developer.apple.com/metal/
"""

import platform
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class macOSGPUDetector:
    """
    macOS GPU detection for Metal/MPS acceleration.
    
    Note: macOS does NOT support CUDA. Use Metal (Apple Silicon) or
    CPU-based training instead.
    """
    
    @staticmethod
    def detect_apple_silicon() -> Dict[str, Any]:
        """
        Detect Apple Silicon (ARM-based) Macs.
        
        Returns:
            Dict with Apple Silicon info
        """
        result = {
            "detected": False,
            "is_apple_silicon": False,
            "mps_available": False,
            "chip_type": None,
            "memory": None
        }
        
        try:
            machine = platform.machine().lower()
            
            if 'arm' in machine or 'aarch64' in machine:
                result["is_apple_silicon"] = True
                result["detected"] = True
                
                # Try to get chip information
                try:
                    proc = subprocess.run(
                        ['sysctl', '-n', 'machdep.cpu.brand_string'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if proc.returncode == 0:
                        result["chip_type"] = proc.stdout.strip()
                except Exception:
                    result["chip_type"] = "Apple Silicon (ARM64)"
                
                # Get memory information
                try:
                    proc = subprocess.run(
                        ['sysctl', '-n', 'hw.memsize'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if proc.returncode == 0:
                        memory_bytes = int(proc.stdout.strip())
                        result["memory"] = round(memory_bytes / (1024**3), 2)
                except Exception:
                    pass
                    
            else:
                result["chip_type"] = "Intel Mac"
                
        except Exception as e:
            logger.debug(f"Apple Silicon detection failed: {e}")
        
        return result
    
    @staticmethod
    def detect_mps_support() -> Dict[str, Any]:
        """
        Detect PyTorch MPS (Metal Performance Shaders) support.
        
        MPS is the recommended way to accelerate ML on macOS.
        
        Returns:
            Dict with MPS info
        """
        result = {
            "mps_available": False,
            "reason": None,
            "pytorch_mps_supported": False
        }
        
        try:
            import torch
            
            # Check if MPS is available
            if hasattr(torch.backends, 'mps'):
                result["pytorch_mps_supported"] = True
                
                if torch.backends.mps.is_available():
                    result["mps_available"] = True
                    result["reason"] = "PyTorch MPS is available"
                    
                    # Try to get MPS version/info
                    try:
                        if hasattr(torch.backends.mps, 'version'):
                            version = torch.backends.mps.version()
                            result["mps_version"] = version
                    except Exception:
                        pass
                else:
                    result["reason"] = "PyTorch MPS not available (requires Apple Silicon + PyTorch 1.12+)"
            else:
                result["reason"] = "PyTorch installed without MPS support"
                
        except ImportError:
            result["reason"] = "PyTorch not installed"
        except Exception as e:
            result["reason"] = f"MPS detection error: {e}"
            logger.debug(f"MPS detection failed: {e}")
        
        return result
    
    @staticmethod
    def detect_intel_gpu() -> Dict[str, Any]:
        """
        Detect Intel integrated graphics on older Intel Macs.
        
        Note: Intel Macs do NOT support CUDA and have limited ML acceleration.
        Consider using CPU-based training or upgrading to Apple Silicon.
        
        Returns:
            Dict with Intel GPU info
        """
        result = {
            "detected": False,
            "has_intel_gpu": False,
            "warning": "Intel Macs have limited ML acceleration support. "
                      "Consider using Apple Silicon Macs for better performance."
        }
        
        try:
            # Check for Intel GPU using system_profiler
            proc = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.returncode == 0:
                output = proc.stdout.lower()
                if 'intel' in output or 'iris' in output or 'hd graphics' in output:
                    result["detected"] = True
                    result["has_intel_gpu"] = True
                    
        except Exception as e:
            logger.debug(f"Intel GPU detection failed: {e}")
        
        return result
    
    @staticmethod
    def detect() -> Dict[str, Any]:
        """
        Complete macOS GPU detection.
        
        Returns:
            Dict with macOS GPU/ML acceleration info
        """
        result = {
            "platform": "macOS",
            "cuda_supported": False,  # macOS does NOT support CUDA
            "apple_silicon": macOSGPUDetector.detect_apple_silicon(),
            "mps": macOSGPUDetector.detect_mps_support(),
            "intel_gpu": macOSGPUDetector.detect_intel_gpu(),
        }
        
        # Determine best acceleration method
        if result["apple_silicon"]["detected"]:
            if result["mps"]["mps_available"]:
                result["recommended_device"] = "mps"
                result["recommendation"] = "Use PyTorch with MPS for Apple Silicon acceleration"
            else:
                result["recommended_device"] = "cpu"
                result["recommendation"] = "Install PyTorch 1.12+ with MPS support for Apple Silicon acceleration"
        elif result["intel_gpu"]["detected"]:
            result["recommended_device"] = "cpu"
            result["recommendation"] = "Intel Macs have limited ML acceleration. Use CPU-based training."
        else:
            result["recommended_device"] = "cpu"
            result["recommendation"] = "Use CPU-based training"
        
        return result
    
    @staticmethod
    def print_macos_advice():
        """Print helpful advice for macOS users."""
        advice = """
═══════════════════════════════════════════════════════════════════
                    macOS ML Acceleration Guide
═══════════════════════════════════════════════════════════════════

IMPORTANT: macOS does NOT support CUDA. Use these options instead:

1. APPLE SILICON (Recommended) - M1/M2/M3/M4 Macs
   - Use PyTorch with Metal Performance Shaders (MPS)
   - Install: pip install torch torchvision torchaudio
   - Device: torch.device('mps') or 'cpu' as fallback
   - Performance: 3-5x faster than CPU on M1/M2

2. INTEL MACS (Legacy)
   - Limited acceleration available
   - Use CPU-based training (slower)
   - Consider upgrading to Apple Silicon

3. EXTERNAL GPU (Rare)
   - eGPU support on Intel Macs only
   - Requires dedicated thunderbolt GPU
   - Often not recommended due to bandwidth limitations

═══════════════════════════════════════════════════════════════════
        Reference: https://pytorch.org/docs/stable/notes/mps.html
═══════════════════════════════════════════════════════════════════
        """
        print(advice)

