"""
Environment validation and auto-fix for Aegis Vision agents.

Checks for common compatibility issues and provides automated fixes.
"""

import sys
import os
import subprocess
import importlib.metadata
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class EnvironmentIssue:
    """Represents an environment compatibility issue"""
    
    def __init__(
        self,
        severity: str,  # 'error', 'warning', 'info'
        title: str,
        description: str,
        packages_affected: List[str],
        fix_command: Optional[str] = None,
        fix_description: Optional[str] = None,
        alternative_solution: Optional[str] = None
    ):
        self.severity = severity
        self.title = title
        self.description = description
        self.packages_affected = packages_affected
        self.fix_command = fix_command
        self.fix_description = fix_description
        self.alternative_solution = alternative_solution


class EnvironmentChecker:
    """Check and validate the Python environment for compatibility issues"""
    
    @staticmethod
    def _get_system_cuda_version() -> Optional[str]:
        """
        Get system CUDA version from nvcc or nvidia-smi.
        
        Returns:
            CUDA version string (e.g., "12.1") or None
        """
        # Try nvcc first (most reliable)
        try:
            result = subprocess.run(
                ['nvcc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                match = re.search(r'release\s+([\d.]+)', result.stdout)
                if match:
                    return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try nvidia-smi (shows driver CUDA version)
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # nvidia-smi shows driver version, not CUDA version directly
                # But we can infer from driver version or check CUDA_HOME
                pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try CUDA_HOME environment variable
        cuda_home = os.environ.get('CUDA_HOME') or os.environ.get('CUDA_PATH')
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
    def _map_cuda_to_pytorch_wheel(cuda_version: str) -> str:
        """
        Map system CUDA version to PyTorch wheel CUDA version.
        
        PyTorch wheels are available for: cu118, cu121, cu124, cu126, cu128
        Maps system CUDA to closest available PyTorch wheel.
        
        Args:
            cuda_version: System CUDA version (e.g., "12.1", "12.8", "11.8")
            
        Returns:
            PyTorch wheel CUDA version (e.g., "cu121", "cu128", "cu118")
        """
        try:
            major, minor = map(int, cuda_version.split('.')[:2])
            
            # Map to PyTorch wheel versions
            if major == 11:
                if minor >= 8:
                    return "cu118"  # CUDA 11.8
                else:
                    return "cu118"  # Fallback to 11.8
            elif major == 12:
                if minor >= 8:
                    return "cu128"  # CUDA 12.8+ -> try cu128
                elif minor >= 6:
                    return "cu126"  # CUDA 12.6-12.7 -> cu126
                elif minor >= 4:
                    return "cu124"  # CUDA 12.4-12.5 -> cu124
                elif minor >= 1:
                    return "cu121"  # CUDA 12.1-12.3 -> cu121
                else:
                    return "cu121"  # CUDA 12.0 -> 12.1
            elif major >= 13:
                return "cu126"  # CUDA 13+ -> use nightly with cu126 (or cu128 if available)
            else:
                return "cu118"  # Default fallback
        except (ValueError, AttributeError):
            return "cu118"  # Default fallback
    
    @staticmethod
    def check_numpy_compatibility() -> Optional[EnvironmentIssue]:
        """
        Check if NumPy version is compatible with compiled modules.
        
        Many packages (onnxruntime, opencv-python, scipy, etc.) are compiled
        against NumPy 1.x and will fail or show warnings with NumPy 2.x.
        
        Additionally, opencv-python 4.12.0+ REQUIRES NumPy 2.x for Python >= 3.9,
        so we must pin opencv-python < 4.12.0 to allow NumPy 1.x usage.
        """
        try:
            import numpy as np
            numpy_version = np.__version__
            
            # Check if NumPy 2.x
            major_version = int(numpy_version.split('.')[0])
            
            if major_version >= 2:
                # Find which packages are compiled against NumPy 1.x
                problematic_packages = []
                
                # Check packages known to have NumPy 1.x compiled extensions
                packages_to_check = [
                    ('onnxruntime', 'ONNX Runtime (ML inference)'),
                    ('cv2', 'OpenCV (computer vision)'),
                    ('scipy', 'SciPy (scientific computing)'),
                    ('torch', 'PyTorch (deep learning)'),
                    ('ultralytics', 'Ultralytics (YOLO training)'),
                ]
                
                for pkg_name, description in packages_to_check:
                    try:
                        importlib.import_module(pkg_name)
                        problematic_packages.append(description)
                    except ImportError:
                        pass  # Package not installed
                
                # Also check opencv-python version
                opencv_issue = ""
                try:
                    import cv2
                    cv2_version = cv2.__version__
                    # Extract opencv-python version (format: 4.x.y.z)
                    if cv2_version.startswith('4.12.') or cv2_version.startswith('4.13.'):
                        opencv_issue = (
                            "\n\nAdditionally, opencv-python 4.12.0+ REQUIRES NumPy 2.x for Python >= 3.9. "
                            "You must downgrade opencv-python to < 4.12.0 AND NumPy to < 2.0."
                        )
                except ImportError:
                    pass
                
                if problematic_packages:
                    return EnvironmentIssue(
                        severity='error',
                        title='NumPy 2.x Incompatibility',
                        description=(
                            f'NumPy {numpy_version} is installed, but the following packages '
                            'were compiled with NumPy 1.x and may crash or malfunction:\n'
                            + '\n'.join(f'  • {pkg}' for pkg in problematic_packages) +
                            opencv_issue +
                            '\n\nThis is a known compatibility issue. See: '
                            'https://numpy.org/doc/stable/numpy_2_0_migration_guide.html'
                        ),
                        packages_affected=problematic_packages,
                        fix_command='pip install "numpy<2.0" "opencv-python<4.12.0"',
                        fix_description='Downgrade NumPy to 1.x and opencv-python to <4.12.0',
                        alternative_solution=(
                            'Use a Docker image with NumPy 1.x pre-installed, such as:\n'
                            '  • nvcr.io/nvidia/pytorch:24.08-py3 (NumPy 1.26.4)\n'
                            '  • nvcr.io/nvidia/pytorch:24.12-py3 (NumPy 1.26.4)\n'
                            '  • python:3.10-slim with manual NumPy 1.x installation'
                        )
                    )
        except ImportError:
            # NumPy not installed - will be caught by other checks
            pass
        
        return None
    
    @staticmethod
    def _get_pytorch_reinstall_command(
        system_cuda_version: Optional[str] = None, 
        pytorch_cuda_version: Optional[str] = None,
        is_rocm: bool = False
    ) -> str:
        """
        Generate PyTorch reinstall command based on system environment.
        """
        # ROCm case (AMD MI300)
        if is_rocm:
            # Detect actual ROCm version and map to available PyTorch wheel
            try:
                from .gpu_detection_rocm import ROCmGPUDetector, map_rocm_to_pytorch_wheel
                rocm_info = ROCmGPUDetector.detect_via_rocm_smi()
                rocm_wheel = map_rocm_to_pytorch_wheel(rocm_info.get("rocm_version"))
            except Exception:
                rocm_wheel = "rocm6.4"  # Fallback to latest stable
            return (
                'pip uninstall -y torch torchvision torchaudio && '
                'pip install torch torchvision torchaudio --index-url '
                f'https://download.pytorch.org/whl/{rocm_wheel}'
            )

        # Prefer system CUDA version if available
        if system_cuda_version:
            pytorch_wheel_cuda = EnvironmentChecker._map_cuda_to_pytorch_wheel(system_cuda_version)
            return (
                f'pip uninstall -y torch torchvision torchaudio && '
                f'pip install torch torchvision torchaudio --index-url '
                f'https://download.pytorch.org/whl/{pytorch_wheel_cuda}'
            )
        elif pytorch_cuda_version:
            # Fallback to PyTorch's CUDA version
            cuda_major_minor = pytorch_cuda_version.replace('.', '')[:2]
            return (
                f'pip uninstall -y torch torchvision torchaudio && '
                f'pip install torch torchvision torchaudio --index-url '
                f'https://download.pytorch.org/whl/cu{cuda_major_minor}'
            )
        else:
            # Default to CUDA 11.8
            return (
                'pip uninstall -y torch torchvision torchaudio && '
                'pip install torch torchvision torchaudio --index-url '
                'https://download.pytorch.org/whl/cu118'
            )

    @staticmethod
    def check_rocm_compatibility() -> Optional[EnvironmentIssue]:
        """
        Check if ROCm is correctly configured for AMD GPUs.
        """
        try:
            from .gpu_detection_rocm import ROCmGPUDetector
            rocm_info = ROCmGPUDetector.detect()
            
            if not rocm_info["detected"]:
                return None
            
            # AMD GPU detected, now check PyTorch
            import torch
            
            # Check if PyTorch has ROCm support
            has_rocm_support = hasattr(torch.version, 'rocm') or hasattr(torch.version, 'hip')
            
            if not has_rocm_support:
                gpu_name = rocm_info["gpus"][0]["name"] if rocm_info["gpus"] else "AMD GPU"
                # Get the PyTorch wheel version that will be installed
                try:
                    from .gpu_detection_rocm import map_rocm_to_pytorch_wheel
                    rocm_wheel = map_rocm_to_pytorch_wheel(rocm_info.get("rocm_version"))
                except Exception:
                    rocm_wheel = "rocm6.4"
                return EnvironmentIssue(
                    severity='error',
                    title='AMD ROCm Incompatibility',
                    description=(
                        f'❌ Detected {gpu_name}, but your PyTorch installation does NOT support ROCm.\n\n'
                        'By default, "pip install aegis-vision" may install the generic CUDA variant of PyTorch '
                        'if not already present. To use the MI300 GPU, you need the ROCm-enabled PyTorch build.'
                    ),
                    packages_affected=['PyTorch', 'torch'],
                    fix_command=EnvironmentChecker._get_pytorch_reinstall_command(is_rocm=True),
                    fix_description=f'Install hardware-optimized PyTorch for {rocm_wheel.upper()} (AMD Instinct)',
                    alternative_solution=(
                        'Use the official AMD ROCm Docker image:\n'
                        f'  docker run -it --device=/dev/kfd --device=/dev/dri rocm/pytorch:rocm6.4-pytorch2.5-py3.11'
                    )
                )
            
            # If ROCm support is present, test if kernels work
            try:
                if torch.cuda.is_available():
                    test_tensor = torch.zeros(1, device='cuda:0')
                    _ = test_tensor + 1
                    del test_tensor
                    torch.cuda.empty_cache()
                else:
                    raise RuntimeError("torch.cuda.is_available() is False on ROCm build")
            except Exception as e:
                return EnvironmentIssue(
                    severity='error',
                    title='ROCm Kernel Execution Failed',
                    description=(
                        f'❌ ROCm Error: {str(e)}\n\n'
                        'PyTorch is ROCm-enabled but cannot communicate with the AMD GPU interface (/dev/kfd).\n'
                        'This often happens due to missing permissions or drivers.'
                    ),
                    packages_affected=['PyTorch'],
                    alternative_solution=(
                        'Check permissions and drivers:\n'
                        '  1. sudo usermod -aG video,render $USER\n'
                        '  2. Check rocm-smi status'
                    )
                )
        except Exception as e:
            pass
            
        return None
    
    @staticmethod
    def check_pytorch_cuda_compatibility() -> Optional[EnvironmentIssue]:
        """
        Check if PyTorch supports the available GPU architecture.
        
        Newer GPUs (Blackwell/GB10 - sm_121) require PyTorch nightly builds or NVIDIA NGC containers.
        """
        try:
            import torch
            
            if not torch.cuda.is_available():
                return None  # No GPU, no issue
            
            # Get GPU compute capability
            try:
                props = torch.cuda.get_device_properties(0)
                gpu_name = torch.cuda.get_device_name(0)
                compute_capability = f"sm_{props.major}{props.minor}"
                pytorch_version = torch.__version__
                pytorch_cuda_version = torch.version.cuda  # CUDA version PyTorch was compiled with
                
                # Get system CUDA version (what we should match PyTorch to)
                system_cuda_version = EnvironmentChecker._get_system_cuda_version()
                
                # CRITICAL: Test if PyTorch can actually run kernels on this GPU
                # This catches "no kernel image is available for execution on the device" errors
                kernel_test_passed = False
                try:
                    # Try to create a simple tensor and perform an operation
                    test_tensor = torch.zeros(1, device='cuda:0')
                    _ = test_tensor + 1  # Simple operation to trigger kernel execution
                    del test_tensor
                    torch.cuda.empty_cache()
                    kernel_test_passed = True  # Kernel test succeeded - environment is working!
                except RuntimeError as e:
                    error_msg = str(e)
                    if 'no kernel image' in error_msg.lower() or 'cudaErrorNoKernelImageForDevice' in error_msg:
                        # This is the specific error we're trying to catch
                        return EnvironmentIssue(
                            severity='error',
                            title='CUDA Kernel Compatibility Error',
                            description=(
                                f'❌ CUDA Error: no kernel image is available for execution on the device\n\n'
                                f'GPU: {gpu_name}\n'
                                f'Compute Capability: {compute_capability} (sm_{props.major}{props.minor})\n'
                                f'PyTorch Version: {pytorch_version}\n'
                                f'PyTorch CUDA Version (compiled): {pytorch_cuda_version}\n'
                                + (f'System CUDA Version: {system_cuda_version}\n' if system_cuda_version else 'System CUDA Version: Not detected\n') +
                                '\nThis error occurs when PyTorch was compiled for a different GPU architecture '
                                'than your current GPU. The pre-compiled PyTorch kernels do not match your GPU.\n\n'
                                'Common causes:\n'
                                '  • PyTorch installed from pip with wrong CUDA version\n'
                                '  • GPU compute capability not supported by PyTorch build\n'
                                '  • Mismatch between PyTorch CUDA version and system CUDA\n\n'
                                'Solutions:\n'
                                '  1. Reinstall PyTorch with correct CUDA version for your system\n'
                                '  2. Use NVIDIA NGC Docker container (recommended)\n'
                                '  3. Build PyTorch from source with your GPU architecture'
                            ),
                            packages_affected=['PyTorch'],
                            fix_command=(
                                EnvironmentChecker._get_pytorch_reinstall_command(system_cuda_version, pytorch_cuda_version)
                            ),
                            fix_description=(
                                f'Reinstall PyTorch matching system CUDA version. '
                                + (f'System CUDA: {system_cuda_version}, ' if system_cuda_version else '')
                                + f'PyTorch was compiled with CUDA {pytorch_cuda_version}. '
                                'Note: This may not work if your GPU architecture is too new. '
                                'In that case, use an NVIDIA NGC container.'
                            ),
                            alternative_solution=(
                                'Use NVIDIA NGC PyTorch container (RECOMMENDED):\n'
                                '  docker pull nvcr.io/nvidia/pytorch:24.12-py3\n'
                                '  # Or latest:\n'
                                '  docker pull nvcr.io/nvidia/pytorch:25.01-py3\n\n'
                                'NGC containers include PyTorch pre-compiled for all modern GPU architectures.\n\n'
                                'For newer GPUs (H100, H200, Blackwell), you may need:\n'
                                '  pip install --pre torch torchvision torchaudio --index-url '
                                'https://download.pytorch.org/whl/nightly/cu126'
                            )
                        )
                    else:
                        # Other CUDA errors - still report but with different message
                        return EnvironmentIssue(
                            severity='error',
                            title='CUDA Runtime Error',
                            description=(
                                f'CUDA error detected: {error_msg}\n\n'
                                f'GPU: {gpu_name}\n'
                                f'Compute Capability: {compute_capability}\n'
                                f'PyTorch Version: {pytorch_version}'
                            ),
                            packages_affected=['PyTorch'],
                            fix_command=None,
                            fix_description=None,
                            alternative_solution=(
                                'Check CUDA installation and GPU drivers:\n'
                                '  nvidia-smi  # Verify GPU is detected\n'
                                '  python -c "import torch; print(torch.cuda.is_available())"  # Test PyTorch CUDA'
                            )
                        )
                
                # If kernel test passed, the environment is working correctly
                # Don't suggest any changes - return None (no issues)
                # This is the key fix: if PyTorch can run kernels on the GPU, the environment is fine
                if kernel_test_passed:
                    return None
            except Exception as e:
                # If we can't get device properties, try a simpler check
                try:
                    import torch
                    if torch.cuda.is_available():
                        # Try the kernel test anyway
                        test_tensor = torch.zeros(1, device='cuda:0')
                        _ = test_tensor + 1
                        del test_tensor
                        torch.cuda.empty_cache()
                except RuntimeError as runtime_error:
                    error_msg = str(runtime_error)
                    if 'no kernel image' in error_msg.lower():
                        return EnvironmentIssue(
                            severity='error',
                            title='CUDA Kernel Compatibility Error',
                            description=(
                                f'CUDA Error: {error_msg}\n\n'
                                'PyTorch cannot execute kernels on your GPU. '
                                'This usually means PyTorch was compiled for a different GPU architecture.'
                            ),
                            packages_affected=['PyTorch'],
                            fix_command=None,
                            fix_description=None,
                            alternative_solution=(
                                'Reinstall PyTorch or use NVIDIA NGC container:\n'
                                '  docker pull nvcr.io/nvidia/pytorch:24.12-py3'
                            )
                        )
        except ImportError:
            # PyTorch not installed
            pass
        
        return None
    
    @staticmethod
    def check_all() -> List[EnvironmentIssue]:
        """Run all environment checks and return list of issues"""
        issues = []
        
        # Run all checks
        checks = [
            EnvironmentChecker.check_numpy_compatibility,
            EnvironmentChecker.check_pytorch_cuda_compatibility,
            EnvironmentChecker.check_rocm_compatibility,
        ]
        
        for check in checks:
            issue = check()
            if issue:
                issues.append(issue)
        
        return issues
    
    @staticmethod
    def apply_fix(issue: EnvironmentIssue) -> Tuple[bool, str]:
        """
        Apply the automatic fix for an issue.
        
        Returns:
            (success: bool, message: str)
        """
        if not issue.fix_command:
            return False, "No automatic fix available"
        
        try:
            # Execute fix command
            result = subprocess.run(
                issue.fix_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode == 0:
                return True, "Fix applied successfully"
            else:
                return False, f"Fix failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Fix timed out (5 minutes)"
        except Exception as e:
            return False, f"Fix error: {e}"


def print_issue(issue: EnvironmentIssue, index: Optional[int] = None) -> None:
    """Pretty print an environment issue"""
    
    # Severity emoji
    severity_emoji = {
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    emoji = severity_emoji.get(issue.severity, '•')
    
    # Header
    if index is not None:
        print(f"\n{emoji} Issue #{index}: {issue.title}")
    else:
        print(f"\n{emoji} {issue.title}")
    
    print("─" * 70)
    
    # Description
    print(f"\n{issue.description}")
    
    # Packages affected
    if issue.packages_affected:
        print(f"\n📦 Affected packages:")
        for pkg in issue.packages_affected:
            print(f"   • {pkg}")
    
    # Fix option
    if issue.fix_command:
        print(f"\n✅ Automatic fix available:")
        print(f"   {issue.fix_description}")
        print(f"\n   Command:")
        print(f"   {issue.fix_command}")
    
    # Alternative
    if issue.alternative_solution:
        print(f"\n🐳 Alternative (Docker-based):")
        for line in issue.alternative_solution.split('\n'):
            print(f"   {line}")


def check_environment_interactive() -> bool:
    """
    Check environment and prompt user for fixes.
    
    Returns:
        True if environment is OK or fixes were applied
        False if user declined fixes or environment has errors
    """
    print("🔍 Checking environment compatibility...")
    print()
    
    issues = EnvironmentChecker.check_all()
    
    if not issues:
        print("✅ Environment check passed! All systems ready.")
        return True
    
    # Show all issues
    print(f"⚠️  Found {len(issues)} environment issue(s):\n")
    
    for i, issue in enumerate(issues, 1):
        print_issue(issue, i)
    
    print("\n" + "=" * 70)
    
    # Count errors vs warnings
    errors = [iss for iss in issues if iss.severity == 'error']
    warnings = [iss for iss in issues if iss.severity == 'warning']
    
    if errors:
        print(f"\n❌ Found {len(errors)} critical error(s) that must be fixed.")
    if warnings:
        print(f"⚠️  Found {len(warnings)} warning(s) that should be addressed.")
    
    print()
    
    # Prompt for fixes
    fixable_issues = [iss for iss in issues if iss.fix_command]
    
    if not fixable_issues:
        print("💡 Please apply the suggested solutions manually.")
        return len(errors) == 0  # OK if only warnings
    
    # Ask user if they want automatic fixes
    print("🔧 Automatic fixes are available.")
    print()
    
    try:
        response = input("Apply automatic fixes now? [y/N]: ").strip().lower()
        
        if response not in ['y', 'yes']:
            print()
            print("❌ Fixes declined. Please fix manually or use a compatible Docker image.")
            print()
            for issue in fixable_issues:
                if issue.alternative_solution:
                    print(f"💡 {issue.title}:")
                    print(issue.alternative_solution)
                    print()
            return False
        
        # Apply fixes
        print()
        print("🔧 Applying fixes...")
        print()
        
        all_success = True
        for i, issue in enumerate(fixable_issues, 1):
            print(f"[{i}/{len(fixable_issues)}] Fixing: {issue.title}")
            print(f"      Command: {issue.fix_command}")
            
            success, message = EnvironmentChecker.apply_fix(issue)
            
            if success:
                print(f"      ✅ {message}")
            else:
                print(f"      ❌ {message}")
                all_success = False
            print()
        
        if all_success:
            print("=" * 70)
            print("✅ All fixes applied successfully!")
            print("🔄 Please restart the agent for changes to take effect.")
            return True
        else:
            print("=" * 70)
            print("⚠️  Some fixes failed. Please review the errors above.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n❌ Fixes cancelled by user.")
        return False
