#!/usr/bin/env python3

# File: gntplib/exceptions.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Exception classes for GNTP library.
# License: MIT

"""Exception classes for GNTP library.

This module defines all custom exceptions used throughout the GNTP library.
All exceptions inherit from GNTPError for easy catching of library-specific errors.
"""

from typing import Optional, Any


class GNTPError(Exception):
    """Base exception class for all GNTP-related errors.
    
    This exception is raised for general GNTP protocol errors, connection issues,
    and any other errors specific to GNTP operations.
    
    Attributes:
        message: Primary error message
        details: Optional additional details about the error
        original_message: Original GNTP message that caused the error (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        original_message: Optional[bytes] = None
    ):
        """Initialize GNTP error with message and optional details.
        
        Args:
            message: Primary error description
            details: Additional context or information
            original_message: The original GNTP message that caused the error
        """
        self.message = message
        self.details = details
        self.original_message = original_message
        
        # Build full error message
        full_message = message
        if details:
            full_message = f"{message}: {details}"
        if original_message:
            full_message = f"{full_message} (original message: {original_message!r})"
            
        super().__init__(full_message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.args[0] if self.args else self.message


class GNTPConnectionError(GNTPError):
    """Raised when connection to GNTP server fails.
    
    This includes timeout errors, refused connections, and network issues.
    """
    pass


class GNTPAuthenticationError(GNTPError):
    """Raised when authentication with GNTP server fails.
    
    This occurs when password/key authentication is rejected.
    """
    pass


class GNTPEncryptionError(GNTPError):
    """Raised when encryption/decryption operations fail.
    
    This includes cipher initialization errors and key size mismatches.
    """
    pass


class GNTPProtocolError(GNTPError):
    """Raised when GNTP protocol violations are detected.
    
    This includes malformed messages, unsupported versions, and invalid headers.
    """
    pass


class GNTPResponseError(GNTPError):
    """Raised when GNTP server returns an error response.
    
    Attributes:
        error_code: The error code from the server
        error_description: Human-readable error description from server
    """
    
    def __init__(
        self,
        error_code: str,
        error_description: str,
        original_message: Optional[bytes] = None
    ):
        """Initialize response error with server error details.
        
        Args:
            error_code: Error code from GNTP server
            error_description: Error description from GNTP server
            original_message: Original response message
        """
        self.error_code = error_code
        self.error_description = error_description
        message = f"{error_code}: {error_description}"
        super().__init__(message, original_message=original_message)


class GNTPResourceError(GNTPError):
    """Raised when resource operations fail.
    
    This includes failures in fetching remote resources or processing binary data.
    """
    pass


class GNTPValidationError(GNTPError):
    """Raised when input validation fails.
    
    This includes invalid parameter values, missing required fields, etc.
    """
    pass


# Deprecated exception kept for backwards compatibility
class GrowlError(GNTPError):
    """Deprecated: Use GNTPError instead.
    
    This exception is kept for backwards compatibility with older code.
    """
    
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            'GrowlError is deprecated, use GNTPError instead',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)