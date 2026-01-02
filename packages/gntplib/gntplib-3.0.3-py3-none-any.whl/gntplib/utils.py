#!/usr/bin/env python3

# File: gntplib/utils.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Utility functions for GNTP library.
# License: MIT

"""Utility functions for GNTP library.
This module provides various utility functions for random data generation,
string encoding/decoding, type conversions, priority validation, header formatting,
and data chunking.
"""

import secrets

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


def is_valid_header_name(name: str) -> bool:
    """Check if a header name is valid.
    
    Header names should not contain colons, newlines, or other control characters.
    
    Args:
        name: Header name to validate
        
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> is_valid_header_name('X-Custom-Header')
        True
        >>> is_valid_header_name('Invalid:Header')
        False
    """
    if not name:
        return False
    
    # Check for invalid characters
    invalid_chars = ['\r', '\n', '\0', ':']
    return not any(char in name for char in invalid_chars)


def format_header_name(name: str, prefix: str = '') -> str:
    """Format a header name with optional prefix.
    
    Args:
        name: Header name
        prefix: Optional prefix to add if not already present
        
    Returns:
        Formatted header name
        
    Example:
        >>> format_header_name('MyHeader', 'X-')
        'X-MyHeader'
        >>> format_header_name('X-MyHeader', 'X-')
        'X-MyHeader'
    """
    if prefix and not name.startswith(prefix):
        return prefix + name
    return name


def chunks(data: bytes, chunk_size: int):
    """Yield successive chunks from data.
    
    Args:
        data: Data to chunk
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of data
        
    Example:
        >>> list(chunks(b'123456789', 3))
        [b'123', b'456', b'789']
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]