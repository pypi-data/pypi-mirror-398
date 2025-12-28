"""
PyHelios runtime capability detection.

This module provides runtime detection of hardware and software capabilities
for PyHelios functionality, used primarily for test skipping and graceful
degradation when hardware is not available.
"""

from .gpu_detector import is_gpu_runtime_available, get_gpu_runtime_info

__all__ = [
    'is_gpu_runtime_available',
    'get_gpu_runtime_info'
]