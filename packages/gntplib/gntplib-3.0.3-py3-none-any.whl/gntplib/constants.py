#!/usr/bin/env python3

# File: gntplib/constants.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Constants and utility functions for GNTP library.
# License: MIT

"""Constants and utility functions for GNTP library.

This module defines all constants used in the GNTP protocol and provides
utility functions for common operations.
"""

import re
import secrets
import struct
from typing import List, Pattern

# ============================================================================
# CONSTANTS
# ============================================================================

# Protocol versions
SUPPORTED_VERSIONS: List[str] = ['1.0']
PROTOCOL_VERSION: str = '1.0'

# Network defaults
DEFAULT_PORT: int = 23053
DEFAULT_TIMEOUT: float = 10.0
DEFAULT_TTL: int = 60

# Message size limits
MAX_MESSAGE_SIZE: int = 4096
MAX_LINE_SIZE: int = 1024

# Message delimiters
LINE_DELIMITER: bytes = b'\r\n'
SECTION_DELIMITER: bytes = b'\r\n'
SECTION_BODY_START: bytes = b'\r\n'
SECTION_BODY_END: bytes = b'\r\n'
MESSAGE_DELIMITER: bytes = b'\r\n\r\n'
MESSAGE_DELIMITER_SIZE: int = len(MESSAGE_DELIMITER)

# Header prefixes
CUSTOM_HEADER_PREFIX: str = 'X-'
APP_SPECIFIC_HEADER_PREFIX: str = 'Data-'

# Response types
RESPONSE_OK: str = '-OK'
RESPONSE_ERROR: str = '-ERROR'
RESPONSE_CALLBACK: str = '-CALLBACK'

# Notification priorities
PRIORITY_VERY_LOW: int = -2
PRIORITY_LOW: int = -1
PRIORITY_NORMAL: int = 0
PRIORITY_HIGH: int = 1
PRIORITY_EMERGENCY: int = 2

# Callback results
CALLBACK_CLICKED: str = 'CLICKED'
CALLBACK_CLOSED: str = 'CLOSED'
CALLBACK_TIMEDOUT: str = 'TIMEDOUT'
CALLBACK_CLICK: str = 'CLICK'  # Alternative form
CALLBACK_CLOSE: str = 'CLOSE'  # Alternative form
CALLBACK_TIMEOUT: str = 'TIMEOUT'  # Alternative form

# Regular expressions
RESPONSE_INFORMATION_LINE_RE: Pattern[bytes] = re.compile(
    rb'GNTP/([^ ]+) (-OK|-ERROR|-CALLBACK) NONE'
)

# Resource URL scheme
RESOURCE_URL_SCHEME: bytes = b'x-growl-resource://'


def random_bytes(num_bytes: int) -> bytes:
    """Generate cryptographically secure random bytes.
    
    This function uses secrets module for secure random generation,
    suitable for cryptographic operations.
    
    Args:
        num_bytes: Number of random bytes to generate
        
    Returns:
        Bytes object containing random data
        
    Raises:
        ValueError: If num_bytes is negative
        
    Example:
        >>> data = random_bytes(16)
        >>> len(data)
        16
    """
    if num_bytes < 0:
        raise ValueError("num_bytes must be non-negative")
    
    return secrets.token_bytes(num_bytes)


def random_hex_string(num_bytes: int) -> str:
    """Generate a random hex string.
    
    Args:
        num_bytes: Number of bytes to generate (hex string will be 2x this length)
        
    Returns:
        Hex string representation of random bytes
        
    Example:
        >>> hex_str = random_hex_string(8)
        >>> len(hex_str)
        16
    """
    return secrets.token_hex(num_bytes)


def encode_utf8(text: str) -> bytes:
    """Safely encode text to UTF-8 bytes.
    
    Args:
        text: String to encode
        
    Returns:
        UTF-8 encoded bytes
        
    Example:
        >>> encode_utf8('Hello')
        b'Hello'
    """
    if isinstance(text, bytes):
        return text
    return text.encode('utf-8')


def decode_utf8(data: bytes) -> str:
    """Safely decode UTF-8 bytes to string.
    
    Args:
        data: Bytes to decode
        
    Returns:
        Decoded string
        
    Raises:
        UnicodeDecodeError: If data is not valid UTF-8
        
    Example:
        >>> decode_utf8(b'Hello')
        'Hello'
    """
    if isinstance(data, str):
        return data
    return data.decode('utf-8')


def safe_int_conversion(value: any, default: int = 0) -> int:  # type: ignore
    """Safely convert a value to integer with fallback.
    
    Args:
        value: Value to convert to int
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
        
    Example:
        >>> safe_int_conversion('42')
        42
        >>> safe_int_conversion('invalid', default=-1)
        -1
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def validate_priority(priority: int) -> int:
    """Validate and clamp priority value to valid range.
    
    Priority must be between -2 and 2 (inclusive).
    
    Args:
        priority: Priority value to validate
        
    Returns:
        Clamped priority value
        
    Example:
        >>> validate_priority(5)
        2
        >>> validate_priority(-5)
        -2
    """
    return max(PRIORITY_VERY_LOW, min(PRIORITY_EMERGENCY, priority))

