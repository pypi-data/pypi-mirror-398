"""
Runtime GPU capability detection for PyHelios.

This module provides runtime detection of GPU hardware and driver availability,
which is essential for determining whether GPU-accelerated tests should run.
"""

import platform
import subprocess
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def is_gpu_runtime_available() -> bool:
    """
    Check if GPU hardware and drivers are actually available at runtime.

    This is different from build-time CUDA availability - this checks if
    the GPU can actually be used for computation at runtime.

    Returns:
        bool: True if GPU is available for runtime use, False otherwise
    """
    try:
        info = get_gpu_runtime_info()
        return info.get('cuda_runtime_available', False) or info.get('opencl_available', False)
    except Exception as e:
        logger.debug(f"GPU runtime check failed: {e}")
        return False


def get_gpu_runtime_info() -> Dict[str, any]:
    """
    Get detailed information about GPU runtime capabilities.

    Returns:
        Dict containing GPU runtime information:
        - cuda_runtime_available: bool
        - cuda_device_count: int
        - cuda_version: str
        - opencl_available: bool
        - platform: str
        - error_message: str (if any errors)
    """
    info = {
        'cuda_runtime_available': False,
        'cuda_device_count': 0,
        'cuda_version': None,
        'opencl_available': False,
        'platform': platform.system(),
        'error_message': None
    }

    # Check CUDA runtime capability
    try:
        info.update(_check_cuda_runtime())
    except Exception as e:
        info['error_message'] = f"CUDA check failed: {e}"
        logger.debug(f"CUDA runtime check failed: {e}")

    # Check OpenCL capability (fallback for some systems)
    try:
        info['opencl_available'] = _check_opencl_runtime()
    except Exception as e:
        logger.debug(f"OpenCL runtime check failed: {e}")

    return info


def _check_cuda_runtime() -> Dict[str, any]:
    """
    Check CUDA runtime availability by trying to initialize CUDA.

    Returns:
        Dict with CUDA runtime information
    """
    cuda_info = {
        'cuda_runtime_available': False,
        'cuda_device_count': 0,
        'cuda_version': None
    }

    # Method 1: Try nvidia-smi (most reliable for checking GPU hardware)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            device_count = len(result.stdout.strip().split('\n'))
            if device_count > 0:
                cuda_info['cuda_device_count'] = device_count
                cuda_info['cuda_runtime_available'] = True
                logger.debug(f"nvidia-smi detected {device_count} GPU(s)")

                # Try to get CUDA version
                try:
                    version_result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=5
                    )
                    if version_result.returncode == 0:
                        cuda_info['cuda_version'] = version_result.stdout.strip().split('\n')[0]
                except Exception:
                    pass

                return cuda_info
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.debug("nvidia-smi not available")

    # Method 2: Try CUDA runtime library direct check
    try:
        # Try to import pycuda if available (optional dependency)
        import pycuda.driver as cuda
        import pycuda.autoinit

        cuda.init()
        device_count = cuda.Device.count()

        if device_count > 0:
            cuda_info['cuda_device_count'] = device_count
            cuda_info['cuda_runtime_available'] = True

            # Get CUDA version
            try:
                cuda_info['cuda_version'] = ".".join(map(str, cuda.get_version()))
            except Exception:
                pass

            logger.debug(f"PyCUDA detected {device_count} GPU(s)")
            return cuda_info

    except ImportError:
        logger.debug("PyCUDA not available")
    except Exception as e:
        logger.debug(f"PyCUDA initialization failed: {e}")

    # Method 3: Try nvidia-ml-py if available (alternative NVIDIA library)
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        if device_count > 0:
            cuda_info['cuda_device_count'] = device_count
            cuda_info['cuda_runtime_available'] = True

            try:
                # Get driver version from first device
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                cuda_info['cuda_version'] = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
            except Exception:
                pass

            logger.debug(f"pynvml detected {device_count} GPU(s)")
            return cuda_info

    except ImportError:
        logger.debug("pynvml not available")
    except Exception as e:
        logger.debug(f"pynvml initialization failed: {e}")

    # Method 4: Try checking for CUDA device files on Linux
    if platform.system() == "Linux":
        try:
            import os
            nvidia_devices = [f for f in os.listdir("/dev") if f.startswith("nvidia") and f != "nvidiactl"]
            if nvidia_devices:
                cuda_info['cuda_device_count'] = len(nvidia_devices)
                cuda_info['cuda_runtime_available'] = True
                logger.debug(f"Found {len(nvidia_devices)} NVIDIA device files in /dev")
                return cuda_info
        except Exception:
            pass

    logger.debug("No CUDA runtime capability detected")
    return cuda_info


def _check_opencl_runtime() -> bool:
    """
    Check OpenCL runtime availability.

    Returns:
        bool: True if OpenCL is available, False otherwise
    """
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()

        for platform in platforms:
            devices = platform.get_devices()
            if devices:
                logger.debug(f"OpenCL available with {len(devices)} devices on platform {platform.name}")
                return True

    except ImportError:
        logger.debug("PyOpenCL not available")
    except Exception as e:
        logger.debug(f"OpenCL check failed: {e}")

    return False