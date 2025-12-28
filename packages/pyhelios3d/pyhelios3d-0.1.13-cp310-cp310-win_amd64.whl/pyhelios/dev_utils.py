"""
Development utilities for PyHelios.

This module provides tools for development and testing without requiring
native Helios libraries to be built.
"""

import os
from typing import Optional

def enable_dev_mode(enable: bool = True) -> None:
    """
    Enable or disable PyHelios development mode.
    
    When development mode is enabled, PyHelios will use mock implementations
    instead of native libraries. This allows development and testing on any
    platform without requiring native library compilation.
    
    Args:
        enable: True to enable dev mode, False to disable
        
    Note:
        This must be called before importing any PyHelios modules.
        Setting this after modules are loaded will have no effect.
    """
    if enable:
        os.environ['PYHELIOS_DEV_MODE'] = '1'
    else:
        os.environ.pop('PYHELIOS_DEV_MODE', None)

def is_dev_mode_enabled() -> bool:
    """Check if development mode is currently enabled."""
    return os.getenv('PYHELIOS_DEV_MODE', '').lower() in ('1', 'true', 'yes', 'on')

def enable_mock_mode(enable: bool = True) -> None:
    """
    Enable or disable PyHelios mock mode (alias for enable_dev_mode).
    
    Args:
        enable: True to enable mock mode, False to disable
    """
    if enable:
        os.environ['PYHELIOS_MOCK_MODE'] = '1'
    else:
        os.environ.pop('PYHELIOS_MOCK_MODE', None)

def is_mock_mode_enabled() -> bool:
    """Check if mock mode is currently enabled."""
    return os.getenv('PYHELIOS_MOCK_MODE', '').lower() in ('1', 'true', 'yes', 'on')

def check_native_support() -> dict:
    """
    Check native library support status.
    
    Returns:
        Dictionary with platform support information
    """
    try:
        from .plugins import get_plugin_info
        return get_plugin_info()
    except ImportError as e:
        return {
            'error': f'Could not import PyHelios modules: {e}',
            'native_available': False,
            'is_mock': True
        }

def print_development_help():
    """Print help for development workflows."""
    print("""
PyHelios Development Mode Help
==============================

Development mode allows you to use PyHelios without building native libraries.

To enable development mode:

1. Set environment variable:
   export PYHELIOS_DEV_MODE=1

2. Or use Python:
   import pyhelios.dev_utils
   pyhelios.dev_utils.enable_dev_mode()
   # Now import other PyHelios modules
   from pyhelios import Context

3. For testing:
   PYHELIOS_DEV_MODE=1 pytest

To build native libraries:
   build_scripts/build_helios

Current Status:
""")
    info = check_native_support()
    for key, value in info.items():
        print(f"  {key}: {value}")