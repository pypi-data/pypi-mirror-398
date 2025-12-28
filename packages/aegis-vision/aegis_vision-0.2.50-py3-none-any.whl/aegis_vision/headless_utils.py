"""
Headless Environment Utilities

Utilities for handling headless environments where GUI libraries are not available.
This is particularly important for Docker containers and server environments.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _check_opencv_conflict() -> None:
    """
    Check for OpenCV import issues and provide fix suggestions.
    
    Detects missing libGL libraries and suggests installation.
    This runs once when aegis_vision is first imported.
    """
    try:
        # Try to import cv2
        import cv2
        # If successful, no issues
        return
    except ImportError as e:
        error_str = str(e)
        
        # Check if it's a libGL missing error
        if 'libGL.so.1' in error_str or 'libGL' in error_str:
            # Don't show warning on import - only show on agent commands
            # Store the error for later display
            import os
            os.environ['_AEGIS_LIBGL_MISSING'] = '1'
        
    except Exception:
        # Some other error, ignore
        pass


def _detect_libgl_package_name() -> tuple[str, str]:
    """
    Detect the correct libGL package name for the current distribution.
    
    Returns:
        Tuple of (libgl_package, package_manager_name)
    """
    import subprocess
    import shutil
    
    try:
        # Try to detect distribution from /etc/os-release
        with open('/etc/os-release', 'r') as f:
            os_info = f.read().lower()
        
        # Extract ID and VERSION_ID
        distro_id = None
        version_id = None
        for line in os_info.split('\n'):
            if line.startswith('id='):
                distro_id = line.split('=')[1].strip('"').strip("'")
            elif line.startswith('version_id='):
                version_id = line.split('=')[1].strip('"').strip("'")
        
        # Ubuntu / Debian (apt-get)
        if distro_id in ['ubuntu', 'debian']:
            if distro_id == 'ubuntu' and version_id:
                major_version = float(version_id.split('.')[0])
                if major_version >= 22:
                    return ('libgl1', 'apt-get')
                else:
                    return ('libgl1-mesa-glx', 'apt-get')
            elif distro_id == 'debian' and version_id:
                major_version = int(version_id.split('.')[0])
                if major_version >= 12:
                    return ('libgl1', 'apt-get')
                else:
                    return ('libgl1-mesa-glx', 'apt-get')
            # Default for Ubuntu/Debian
            return ('libgl1', 'apt-get')
        
        # Fedora / CentOS / RHEL (dnf/yum)
        elif distro_id in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
            # Check if dnf is available (newer), otherwise use yum
            pkg_manager = 'dnf' if shutil.which('dnf') else 'yum'
            return ('mesa-libGL', pkg_manager)
        
        # Alpine Linux (apk)
        elif distro_id == 'alpine':
            return ('mesa-gl', 'apk')
        
        # Arch Linux (pacman)
        elif distro_id in ['arch', 'manjaro']:
            return ('mesa', 'pacman')
        
        # openSUSE (zypper)
        elif distro_id in ['opensuse', 'opensuse-leap', 'opensuse-tumbleweed', 'sles']:
            return ('Mesa-libGL1', 'zypper')
        
        # Default: assume Debian-based with newer package name
        return ('libgl1', 'apt-get')
        
    except Exception:
        # If detection fails, use Debian default
        return ('libgl1', 'apt-get')


def check_and_fix_libgl() -> bool:
    """
    Check if libGL is available and suggest fix if missing.
    
    This should be called by aegis-agent commands (init, login, etc.)
    
    Returns:
        True if libGL is available or can be fixed, False otherwise
    """
    import os
    
    # Check if we already detected missing libGL
    if os.environ.get('_AEGIS_LIBGL_MISSING') != '1':
        # Try to import cv2 to check
        try:
            import cv2
            return True  # OpenCV works fine
        except ImportError as e:
            if 'libGL.so.1' not in str(e) and 'libGL' not in str(e):
                return True  # Different error, not our concern
    
    # Detect the correct package name for this distribution
    libgl_package, pkg_manager = _detect_libgl_package_name()
    
    # libGL is missing - provide fix suggestion
    print("\n" + "=" * 70)
    print("⚠️  OpenGL Libraries Missing")
    print("=" * 70)
    print("OpenCV requires libGL.so.1 which is not installed in this container.")
    print("")
    print("Quick fix (run once as root):")
    print(f"  {pkg_manager} update && {pkg_manager} install -y {libgl_package} libglib2.0-0")
    print("")
    print("Or add to your Dockerfile:")
    print(f"  RUN {pkg_manager} update && {pkg_manager} install -y {libgl_package} libglib2.0-0")
    print("")
    print("This is a one-time setup (~10MB). After installation, aegis-agent will work normally.")
    print("=" * 70)
    print("")
    
    # Ask if user wants to install now (if running as root)
    if os.geteuid() == 0:
        try:
            response = input("Install libGL libraries now? [y/N]: ").strip().lower()
            if response == 'y':
                import subprocess
                print(f"\n📦 Installing libGL libraries ({libgl_package})...")
                
                # Different package managers have different commands
                if pkg_manager in ['apt-get', 'apt']:
                    # Debian/Ubuntu
                    result = subprocess.run(
                        [pkg_manager, "update", "-qq"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        result = subprocess.run(
                            [pkg_manager, "install", "-y", libgl_package, "libglib2.0-0"],
                            capture_output=False,
                            text=True
                        )
                elif pkg_manager in ['dnf', 'yum']:
                    # Fedora/CentOS/RHEL
                    result = subprocess.run(
                        [pkg_manager, "install", "-y", libgl_package, "glib2"],
                        capture_output=False,
                        text=True
                    )
                elif pkg_manager == 'apk':
                    # Alpine
                    subprocess.run(["apk", "update"], capture_output=True)
                    result = subprocess.run(
                        ["apk", "add", libgl_package, "glib"],
                        capture_output=False,
                        text=True
                    )
                elif pkg_manager == 'pacman':
                    # Arch
                    result = subprocess.run(
                        ["pacman", "-Sy", "--noconfirm", libgl_package, "glib2"],
                        capture_output=False,
                        text=True
                    )
                elif pkg_manager == 'zypper':
                    # openSUSE
                    result = subprocess.run(
                        ["zypper", "install", "-y", libgl_package, "glib2"],
                        capture_output=False,
                        text=True
                    )
                else:
                    print(f"❌ Unsupported package manager: {pkg_manager}")
                    return False
                
                if result.returncode == 0:
                    print("✅ libGL libraries installed successfully!")
                    print("   OpenCV should now work. Continuing...")
                    # Clear the flag
                    os.environ.pop('_AEGIS_LIBGL_MISSING', None)
                    return True
                else:
                    print(f"❌ Installation failed")
                    return False
        except KeyboardInterrupt:
            print("\n\nInstallation cancelled.")
            return False
        except Exception as e:
            print(f"❌ Error during installation: {e}")
            return False
    else:
        print("💡 Tip: Run as root (or use sudo) to install automatically.")
    
    return False


def setup_headless_environment() -> None:
    """
    Set up environment variables for headless operation.
    
    This function should be called before importing any packages that might
    try to load GUI libraries (like OpenCV, matplotlib, etc.).
    """
    # OpenCV headless settings
    os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Matplotlib headless backend
    os.environ['MPLBACKEND'] = 'Agg'
    
    # Additional headless settings
    os.environ['DISPLAY'] = ':99'  # Virtual display for X11
    os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered
    
    # Suppress CoreMLTools warnings on ARM64 Linux
    # CoreMLTools native libraries are not available for ARM64 Linux
    # This is expected and doesn't affect YOLO training
    import platform
    if platform.machine() in ['aarch64', 'arm64'] and platform.system() == 'Linux':
        import warnings
        warnings.filterwarnings('ignore', message='.*coremltools.*')
        warnings.filterwarnings('ignore', message='.*libcoremlpython.*')
        warnings.filterwarnings('ignore', message='.*libmilstoragepython.*')
    
    logger.debug("Headless environment configured")
    
    # Check for OpenCV conflicts (inspired by Kaggle/Colab approach)
    _check_opencv_conflict()


def is_headless_environment() -> bool:
    """
    Check if we're running in a headless environment.
    
    Returns:
        True if running in a headless environment (no display)
    """
    # Check for common headless indicators
    if os.environ.get('DISPLAY') is None:
        return True
    
    # Check if we're in a Docker container
    if os.path.exists('/.dockerenv'):
        return True
    
    # Check for common CI/CD environments
    ci_indicators = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 'TRAVIS']
    if any(os.environ.get(indicator) for indicator in ci_indicators):
        return True
    
    return False


def handle_opencv_import_error(error: Exception) -> Optional[Exception]:
    """
    Handle OpenCV import errors in headless environments.
    
    Args:
        error: The import error that occurred
        
    Returns:
        A more user-friendly error message, or None if the error should be re-raised
    """
    error_str = str(error)
    
    if 'libGL.so.1' in error_str or 'cv2' in error_str:
        logger.warning("OpenCV import failed in headless environment")
        logger.warning("This is expected in Docker containers without GUI libraries.")
        logger.warning("Consider using opencv-python-headless instead of opencv-python.")
        
        return RuntimeError(
            "OpenCV cannot be imported in this headless environment. "
            "Please install GUI libraries or use opencv-python-headless instead of opencv-python. "
            f"Original error: {error_str}"
        )
    
    return None


def get_opencv_import_advice() -> str:
    """
    Get advice for fixing OpenCV import issues.
    
    Returns:
        A string with advice for fixing OpenCV import issues
    """
    return """
OpenCV Import Error - Headless Environment

The error you're seeing is because OpenCV is trying to load GUI libraries that aren't available
in your headless environment (like a Docker container).

Solutions:
1. Install opencv-python-headless instead of opencv-python:
   pip uninstall opencv-python
   pip install opencv-python-headless

2. Install GUI libraries in your Docker container:
   apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

3. Use a different environment that has GUI libraries available

The aegis-vision package will work fine for training tasks in headless environments
once OpenCV is properly configured.
"""
