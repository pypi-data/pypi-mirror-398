"""
Chloros Python SDK
==================

Official Python SDK for MAPIR Chloros image processing software.
Provides programmatic access to the Chloros API for automation and integration.

Requirements:
    - Chloros Desktop installed locally
    - Active Chloros+ license (paid plan)
    - Windows 10/11 64-bit

License:
    Proprietary - Requires active Chloros+ subscription
    Copyright (c) 2025 MAPIR Inc. All rights reserved.

Documentation:
    https://docs.chloros.com/api-python-sdk
"""

from .local import ChlorosLocal, process_folder
from .exceptions import (
    ChlorosError,
    ChlorosBackendError,
    ChlorosLicenseError,
    ChlorosConnectionError,
    ChlorosProcessingError
)
from .__version__ import __version__, __title__, __description__, __author__

__all__ = [
    'ChlorosLocal',
    'process_folder',
    'ChlorosError',
    'ChlorosBackendError',
    'ChlorosLicenseError',
    'ChlorosConnectionError',
    'ChlorosProcessingError',
    '__version__',
]














