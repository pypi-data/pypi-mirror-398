#!/usr/bin/env python3

# File: gntplib/keys.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Authentication and key management for GNTP messages.
# License: MIT

"""Authentication and key management for GNTP messages.

This module provides secure key generation and hashing for GNTP authentication.
Supports MD5, SHA1, SHA256, and SHA512 hashing algorithms.
"""

import binascii
import hashlib
import secrets
from typing import Optional

from .constants import random_bytes

__all__ = ['MD5', 'SHA1', 'SHA256', 'SHA512', 'Key', 'Algorithm']


# Hashing algorithm constraints
MIN_SALT_BYTES: int = 8  # Increased from 4 for better security
MAX_SALT_BYTES: int = 16
DEFAULT_SALT_BYTES: int = 16


class Algorithm:
    """Factory class for creating authentication keys with specific hash algorithms.
    
    This class represents a hashing algorithm configuration that can be used
    to create Key instances.
    
    Attributes:
        algorithm_id: String identifier for the algorithm (e.g., 'SHA256')
        key_size: Size of the hash output in bytes
    """
    
    def __init__(self, algorithm_id: str, key_size: int):
        """Initialize algorithm configuration.
        
        Args:
            algorithm_id: Algorithm identifier (MD5, SHA1, SHA256, SHA512)
            key_size: Expected hash output size in bytes
        """
        self.algorithm_id = algorithm_id
        self.key_size = key_size
    
    def key(self, password: str, salt: Optional[bytes] = None) -> 'Key':
        """Create a Key instance using this algorithm.
        
        Args:
            password: Password for authentication
            salt: Optional salt bytes. If None, random salt is generated
            
        Returns:
            Key instance configured with this algorithm
            
        Example:
            >>> algo = SHA256
            >>> key = algo.key('mypassword')
        """
        return Key(password, self.algorithm_id, salt)
    
    def __repr__(self) -> str:
        """Return string representation of algorithm."""
        return f"Algorithm(id={self.algorithm_id}, key_size={self.key_size})"


# Pre-configured algorithm instances
MD5 = Algorithm('MD5', 16)      # 128-bit, 16 bytes, 32 chars hex
SHA1 = Algorithm('SHA1', 20)    # 160-bit, 20 bytes, 40 chars hex
SHA256 = Algorithm('SHA256', 32)  # 256-bit, 32 bytes, 64 chars hex (recommended)
SHA512 = Algorithm('SHA512', 64)  # 512-bit, 64 bytes, 128 chars hex


def random_salt(num_bytes: int = DEFAULT_SALT_BYTES) -> bytes:
    """Generate cryptographically secure random salt.
    
    Args:
        num_bytes: Number of salt bytes to generate (default: 16)
        
    Returns:
        Random salt bytes
        
    Raises:
        ValueError: If num_bytes is outside valid range
        
    Example:
        >>> salt = random_salt(16)
        >>> len(salt)
        16
    """
    if not MIN_SALT_BYTES <= num_bytes <= MAX_SALT_BYTES:
        raise ValueError(
            f"Salt size must be between {MIN_SALT_BYTES} and {MAX_SALT_BYTES} bytes"
        )
    
    return random_bytes(num_bytes)


class Key:
    """Authentication key for GNTP messages.
    
    This class handles password-based authentication by generating secure
    hashes using a salt. The key is used for both authentication and
    optional encryption of GNTP messages.
    
    Attributes:
        password: Original password (stored as UTF-8 bytes)
        algorithm_id: Hash algorithm identifier
        salt: Random salt used in key derivation
        key: Derived key from password and salt
        key_hash: Hash of the derived key
    """
    
    def __init__(
        self,
        password: str,
        algorithm_id: str = 'SHA256',
        salt: Optional[bytes] = None
    ):
        """Initialize authentication key.
        
        Args:
            password: Password for authentication
            algorithm_id: Hash algorithm (MD5, SHA1, SHA256, SHA512)
            salt: Optional salt. If None, random salt is generated
            
        Raises:
            ValueError: If algorithm_id is not supported
            
        Example:
            >>> key = Key('mypassword', 'SHA256')
            >>> key.key_hash_hex
            b'...'
        """
        if algorithm_id not in ['MD5', 'SHA1', 'SHA256', 'SHA512']:
            raise ValueError(
                f"Unsupported algorithm: {algorithm_id}. "
                f"Use MD5, SHA1, SHA256, or SHA512"
            )
        
        self.password = password.encode('utf-8')
        self.algorithm_id = algorithm_id
        self.salt = salt if salt is not None else random_salt()
        
        # Get hash function
        hash_func = getattr(hashlib, algorithm_id.lower())
        
        # Derive key from password and salt
        key_basis = self.password + self.salt
        self.key = hash_func(key_basis).digest()
        
        # Create hash of the key for verification
        self.key_hash = hash_func(self.key).digest()
    
    @property
    def salt_hex(self) -> bytes:
        """Get hex-encoded salt.
        
        Returns:
            Hex-encoded salt as bytes
        """
        return binascii.hexlify(self.salt)
    
    @property
    def key_hex(self) -> bytes:
        """Get hex-encoded key.
        
        Returns:
            Hex-encoded key as bytes
        """
        return binascii.hexlify(self.key)
    
    @property
    def key_hash_hex(self) -> bytes:
        """Get hex-encoded key hash.
        
        Returns:
            Hex-encoded key hash as bytes
        """
        return binascii.hexlify(self.key_hash)
    
    def verify_password(self, password: str) -> bool:
        """Verify if a password matches this key.
        
        Args:
            password: Password to verify
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            >>> key = Key('secret', 'SHA256')
            >>> key.verify_password('secret')
            True
            >>> key.verify_password('wrong')
            False
        """
        # Create temporary key with same salt
        temp_key = Key(password, self.algorithm_id, self.salt)
        return temp_key.key == self.key
    
    def __repr__(self) -> str:
        """Return string representation of key."""
        return (
            f"Key(algorithm={self.algorithm_id}, "
            f"salt_length={len(self.salt)})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality with another Key instance."""
        if not isinstance(other, Key):
            return False
        return (
            self.algorithm_id == other.algorithm_id and
            self.salt == other.salt and
            self.key == other.key
        )