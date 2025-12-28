"""
OpenCV headless environment fix.

This module automatically detects and fixes OpenCV conflicts in headless Docker environments.
Inspired by Kaggle/Colab's approach - check at runtime and provide helpful guidance.
"""
import sys
import warnings


def check_opencv_headless():
    """
    Check if we're in a headless environment with opencv-python (GUI version) installed.
    
    This runs automatically when aegis_vision is imported.
    Similar to how Kaggle/Colab handle environment setup.
    """
    try:
        import cv2
        
        # Try to detect if we have the GUI version in a headless environment
        # The GUI version will fail when trying to use display functions
        cv2_file = cv2.__file__
        
        # Check if both opencv-python and opencv-python-headless are installed
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            has_opencv_python = "opencv-python " in result.stdout
            has_opencv_headless = "opencv-python-headless" in result.stdout
            
            if has_opencv_python and has_opencv_headless:
                # Both are installed - this is the conflict situation
                warnings.warn(
                    "\n⚠️  OpenCV Conflict Detected!\n"
                    "   Both opencv-python and opencv-python-headless are installed.\n"
                    "   In headless Docker environments, use only opencv-python-headless.\n"
                    "\n"
                    "   Fix: Run this command once:\n"
                    "   pip uninstall -y opencv-python\n"
                    "\n"
                    "   Or use the automated script:\n"
                    "   ./scripts/fix_opencv.sh\n",
                    RuntimeWarning,
                    stacklevel=2
                )
            elif has_opencv_python and not has_opencv_headless:
                # Only GUI version - might fail in headless environment
                # But don't warn if we're in Kaggle/Colab (they have libGL)
                try:
                    # Try to detect if libGL is available
                    import ctypes.util
                    libgl = ctypes.util.find_library('GL')
                    if not libgl:
                        # No libGL - we're in a truly headless environment
                        warnings.warn(
                            "\n⚠️  Headless Environment Detected!\n"
                            "   opencv-python (GUI version) is installed but libGL is not available.\n"
                            "   This may cause errors in Docker environments.\n"
                            "\n"
                            "   Recommended: Use opencv-python-headless instead:\n"
                            "   pip uninstall -y opencv-python\n"
                            "   pip install opencv-python-headless\n",
                            RuntimeWarning,
                            stacklevel=2
                        )
                except:
                    pass  # Can't detect libGL, skip warning
                    
        except Exception:
            pass  # Can't check pip list, skip the check
            
    except ImportError:
        # OpenCV not installed at all
        warnings.warn(
            "OpenCV (cv2) is not installed. Install opencv-python-headless for Docker environments.",
            RuntimeWarning,
            stacklevel=2
        )
    except Exception as e:
        # Some other error - don't block import
        pass


# Run the check when this module is imported
# But make it non-blocking - don't fail if the check fails
try:
    check_opencv_headless()
except Exception:
    pass  # Don't block import if check fails


