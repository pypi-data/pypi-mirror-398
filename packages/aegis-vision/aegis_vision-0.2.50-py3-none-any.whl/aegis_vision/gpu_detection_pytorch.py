"""
PyTorch GPU detection module.

Detects CUDA and MPS acceleration via PyTorch CUDA API.
This is the primary detection method when PyTorch is available.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PyTorchGPUDetector:
    """
    PyTorch-based GPU detection.
    
    Works with both CUDA (NVIDIA) and MPS (Apple Silicon) backends.
    """
    
    @staticmethod
    def detect_cuda() -> Dict[str, Any]:
        """
        Detect NVIDIA CUDA GPUs via PyTorch.
        
        Returns:
            Dict with CUDA GPU info
        """
        result = {
            "available": False,
            "version": None,
            "device_count": 0,
            "devices": [],
            "error": None
        }
        
        try:
            import torch
            
            if not torch.cuda.is_available():
                result["error"] = "torch.cuda.is_available() returned False"
                logger.debug(result["error"])
                return result
            
            result["available"] = True
            result["version"] = torch.version.cuda
            result["device_count"] = torch.cuda.device_count()
            
            for i in range(result["device_count"]):
                try:
                    props = torch.cuda.get_device_properties(i)
                    device_name = torch.cuda.get_device_name(i)
                    total_memory = torch.cuda.get_device_properties(i).total_memory
                    
                    device_info = {
                        "index": i,
                        "name": device_name,
                        "memory": round(total_memory / (1024**3), 2),  # Convert to GB
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multi_processor_count": props.multi_processor_count,
                        "total_memory_bytes": total_memory
                    }
                    
                    result["devices"].append(device_info)
                    
                except Exception as e:
                    logger.debug(f"Failed to get device {i} properties: {e}")
                    
        except ImportError:
            result["error"] = "PyTorch not installed"
            logger.debug(result["error"])
        except Exception as e:
            result["error"] = str(e)
            logger.debug(f"CUDA detection failed: {e}")
        
        return result
    
    @staticmethod
    def detect_rocm() -> Dict[str, Any]:
        """
        Detect AMD ROCm GPUs via PyTorch.
        
        Returns:
            Dict with ROCm info
        """
        result = {
            "available": False,
            "version": None,
            "device_count": 0,
            "devices": [],
            "error": None
        }
        
        try:
            import torch
            
            # Check if PyTorch was built with ROCm/HIP
            # torch.version.hip often exists on ROCm builds
            rocm_version = getattr(torch.version, 'rocm', None)
            if not rocm_version and hasattr(torch.version, 'hip'):
                rocm_version = torch.version.hip
                
            if not rocm_version and torch.version.cuda is None:
                # If neither CUDA nor ROCm is detected in version, it's likely CPU
                result["error"] = "Not a ROCm-enabled PyTorch build"
                return result

            # ROCm uses the same CUDA API
            if torch.cuda.is_available():
                result["available"] = True
                result["version"] = rocm_version
                result["device_count"] = torch.cuda.device_count()
                
                for i in range(result["device_count"]):
                    try:
                        device_name = torch.cuda.get_device_name(i)
                        props = torch.cuda.get_device_properties(i)
                        
                        device_info = {
                            "index": i,
                            "name": device_name,
                            "memory": round(props.total_memory / (1024**3), 2),
                        }
                        
                        if hasattr(props, 'gcnArchName'):
                            device_info["compute_capability"] = props.gcnArchName
                        
                        result["devices"].append(device_info)
                    except Exception as e:
                        logger.debug(f"Failed to get ROCm device {i} properties: {e}")
            else:
                result["error"] = "torch.cuda.is_available() returned False on ROCm build"
                
        except ImportError:
            result["error"] = "PyTorch not installed"
        except Exception as e:
            result["error"] = str(e)
            logger.debug(f"ROCm detection failed: {e}")
            
        return result

    @staticmethod
    def get_optimal_device() -> Dict[str, Any]:
        """
        Determine the optimal device for training.
        
        Priority: CUDA > ROCm > MPS > CPU
        
        Returns:
            Dict with optimal device info
        """
        result = {
            "device": "cpu",
            "device_name": "CPU",
            "reason": "Using CPU fallback",
            "priority": 0
        }
        
        try:
            # Try CUDA first
            cuda_info = PyTorchGPUDetector.detect_cuda()
            if cuda_info["available"] and cuda_info["devices"]:
                primary_gpu = cuda_info["devices"][0]
                # Filter out AMD devices that might show up in "detect_cuda" 
                # but should be handled by ROCm path for clarity
                if "AMD" not in primary_gpu["name"] and "MI" not in primary_gpu["name"]:
                    result["device"] = "cuda"
                    result["device_name"] = primary_gpu["name"]
                    result["reason"] = f"CUDA available: {primary_gpu['name']}"
                    result["priority"] = 100
                    result["cuda_info"] = cuda_info
                    return result
            
            # Try ROCm
            rocm_info = PyTorchGPUDetector.detect_rocm()
            if rocm_info["available"] and rocm_info["devices"]:
                primary_amd = rocm_info["devices"][0]
                result["device"] = "cuda" # PyTorch uses 'cuda' as device string for ROCm too
                result["device_name"] = primary_amd["name"]
                result["reason"] = f"ROCm available (AMD MI300/Instinct): {primary_amd['name']}"
                result["priority"] = 90
                result["rocm_info"] = rocm_info
                return result

            # Try MPS
            mps_info = PyTorchGPUDetector.detect_mps()
            if mps_info["available"]:
                result["device"] = "mps"
                result["device_name"] = "Apple Metal (MPS)"
                result["reason"] = "MPS available (Apple Silicon)"
                result["priority"] = 50
                result["mps_info"] = mps_info
                return result
            
        except Exception as e:
            logger.debug(f"Error determining optimal device: {e}")
        
        return result

    @staticmethod
    def detect() -> Dict[str, Any]:
        """
        Complete PyTorch GPU detection.
        
        Returns:
            Dict with all GPU/accelerator info
        """
        return {
            "cuda": PyTorchGPUDetector.detect_cuda(),
            "rocm": PyTorchGPUDetector.detect_rocm(),
            "mps": PyTorchGPUDetector.detect_mps(),
            "optimal_device": PyTorchGPUDetector.get_optimal_device()
        }
    
    @staticmethod
    def print_pytorch_info():
        """Print detailed PyTorch GPU information."""
        try:
            import torch
            print(f"PyTorch version: {torch.__version__}")
            print(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"CUDA version: {torch.version.cuda}")
                print(f"GPU count: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        except ImportError:
            print("PyTorch not installed")
        except Exception as e:
            print(f"Error printing PyTorch info: {e}")

