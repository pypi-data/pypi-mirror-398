"""
PyHelios Plugins Module

Cross-platform interface to Helios native libraries.
Automatically detects platform and loads appropriate library files.
"""

import os
import logging
from .loader import load_helios_library, get_library_info, is_native_library_available, detect_available_plugins

# Configure logging for plugin loading
logger = logging.getLogger(__name__)


# Note: WeberPennTree asset syncing is now handled by the build system
# Assets are copied to pyhelios_build/build/plugins/weberpenntree/ during build
# and accessed via the working directory context manager in WeberPennTree.py

# Load the appropriate library for this platform
helios_lib = load_helios_library()
library_info = get_library_info()

# Log library loading information
if library_info['is_mock']:
    logger.info("PyHelios loaded in development mock mode")
    logger.info(f"Platform: {library_info['platform']}")
    if library_info['available_files']:
        logger.info(f"Available library files: {library_info['available_files']}")
    else:
        logger.info("No native library files found in plugins directory")
else:
    logger.info(f"PyHelios native library loaded successfully")
    logger.info(f"Platform: {library_info['platform']}")
    if 'library_path' in library_info:
        logger.info(f"Library path: {library_info['library_path']}")
    
    # Show available files for debugging
    if library_info['available_files']:
        logger.debug(f"Available library files: {library_info['available_files']}")

# Expose library information for debugging
def get_plugin_info():
    """Get information about loaded plugins and libraries."""
    info = get_library_info()
    info['native_available'] = is_native_library_available()
    info['available_plugins'] = detect_available_plugins()
    return info

def print_plugin_status():
    """Print current plugin status for debugging."""
    info = get_plugin_info()
    print(f"PyHelios Plugin Status:")
    print(f"  Platform: {info['platform']}")
    print(f"  Native library available: {info['native_available']}")
    print(f"  Mock mode: {info['is_mock']}")
    if info['available_files']:
        print(f"  Available library files: {', '.join(info['available_files'])}")
    if 'library_path' in info:
        print(f"  Loaded library: {info['library_path']}")

# For backward compatibility - ensure helios_lib is always available
__all__ = ['helios_lib', 'get_plugin_info', 'print_plugin_status']

