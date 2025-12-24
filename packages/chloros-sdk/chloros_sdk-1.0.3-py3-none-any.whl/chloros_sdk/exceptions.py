"""
Chloros SDK Exceptions
======================

Custom exception classes for the Chloros SDK.
"""


class ChlorosError(Exception):
    """Base exception for all Chloros SDK errors"""
    pass


class ChlorosBackendError(ChlorosError):
    """Raised when the Chloros backend fails to start or respond"""
    pass


class ChlorosLicenseError(ChlorosError):
    """Raised when there are license validation issues"""
    pass


class ChlorosConnectionError(ChlorosError):
    """Raised when connection to the Chloros backend fails"""
    pass


class ChlorosProcessingError(ChlorosError):
    """Raised when image processing fails"""
    pass


class ChlorosAuthenticationError(ChlorosError):
    """Raised when authentication fails"""
    pass


class ChlorosConfigurationError(ChlorosError):
    """Raised when there are configuration errors"""
    pass














