#!/usr/bin/env python3
"""
NUITKA + RAY COMPATIBILITY FIX

This module provides Ray configuration specifically designed for Nuitka frozen executables.
The key insight: Ray's worker processes don't work in Nuitka's frozen environment.

SOLUTION: Force Ray into local mode for Nuitka, but allow full performance in development.
"""

import os
import sys
import tempfile
import warnings

# Suppress Ray's SIGTERM warning (harmless, happens when not on main thread)
warnings.filterwarnings('ignore', message='.*SIGTERM.*')

def configure_ray_for_nuitka():
    """
    Configure Ray environment variables for maximum Nuitka compatibility.
    
    This function MUST be called before ANY Ray imports.
    """
    
    # Detect if we're running as a Nuitka frozen executable
    # Check multiple indicators for maximum reliability
    is_frozen_attr = getattr(sys, 'frozen', False)
    is_compiled_attr = '__compiled__' in globals()
    
    # Also check if executable name suggests frozen state
    exe_name = os.path.basename(sys.executable).lower()
    is_exe_name = exe_name.endswith(('.exe', '.bin')) and not exe_name.startswith('python')
    
    is_nuitka_frozen = is_frozen_attr or is_compiled_attr or is_exe_name
    
    if is_nuitka_frozen:
        # STANDALONE MODE: Ray works normally, just needs proper environment setup
        # Set temp directory for Ray's runtime files
        import tempfile
        ray_temp_dir = os.path.join(tempfile.gettempdir(), 'ray')
        os.makedirs(ray_temp_dir, exist_ok=True)
        
        # Basic Ray environment configuration for standalone mode
        os.environ.update({
            'RAY_DISABLE_IMPORT_WARNING': '1',
            'RAY_DISABLE_RUNTIME_METRICS': '1',
            'RAY_LOG_TO_STDERR': '0',
            'RAY_OBJECT_STORE_ALLOW_SLOW_STORAGE': '1',
            'RAY_DISABLE_TELEMETRY': '1',
            'RAY_IGNORE_UNHANDLED_ERRORS': '1',
            'PYTHONOPTIMIZE': '1',
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONUNBUFFERED': '1',
            'PYTHONWARNINGS': 'ignore',
        })
        
        return {
            'local_mode': False,          # Full parallel mode for standalone
            'num_cpus': 6,                # Multiple CPU cores
            'num_gpus': 1,                # GPU support
            'include_dashboard': False,   # No dashboard
            'configure_logging': False,   # No logging setup
            'ignore_reinit_error': True,  # Ignore reinit errors
            'log_to_driver': False,       # No driver logging
            'logging_level': 'error',     # Minimal logging
            '_temp_dir': ray_temp_dir,    # Explicit temp directory
            'object_store_memory': 2000000000,  # 2GB
        }
    
    else:
        # Standard development mode: full performance with warnings suppressed
        os.environ.update({
            'RAY_DISABLE_IMPORT_WARNING': '1',
            'RAY_DISABLE_RUNTIME_METRICS': '1',
            'RAY_LOG_TO_STDERR': '0',
            'RAY_DISABLE_TELEMETRY': '1',
            'RAY_IGNORE_UNHANDLED_ERRORS': '1',
            'PYTHONWARNINGS': 'ignore',
        })
        
        return {
            'local_mode': False,
            'num_cpus': 8,
            'num_gpus': 1,
            'include_dashboard': False,
            'configure_logging': False,
            'ignore_reinit_error': True,
            'log_to_driver': False,
            'logging_level': 'error',
            'object_store_memory': 2000000000,  # 2GB
        }

def get_nuitka_ray_config():
    """
    Get Ray configuration for Nuitka compatibility.
    This is called by ray_session_manager.py for advanced initialization.
    """
    return configure_ray_for_nuitka()

def initialize_ray_for_nuitka():
    """
    Initialize Ray with Nuitka-compatible configuration.
    
    Returns:
        bool: True if Ray initialized successfully, False otherwise
    """
    try:
        import ray
        
        if ray.is_initialized():
            return True
        
        config = get_nuitka_ray_config()
        
        ray.init(**config)
        
        return True
        
    except Exception as e:
        return False

# Configuration will be called explicitly by backend_server.py
# This ensures proper timing and avoids double-configuration
