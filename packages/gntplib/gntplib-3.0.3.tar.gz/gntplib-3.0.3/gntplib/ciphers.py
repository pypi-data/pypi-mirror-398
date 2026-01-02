#!/usr/bin/env python3

# File: gntplib/ciphers.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Encryption support for GNTP messages using PyCryptodome.
# License: MIT

"""Encryption support for GNTP messages using PyCryptodome.

This module provides encryption capabilities for GNTP messages using
AES, DES, and 3DES algorithms. Requires PyCryptodome package.

Note: This module requires PyCryptodome to be installed:
    pip install pycryptodomex
"""

import binascii
import struct
from typing import Optional

try:
    from Cryptodome.Cipher import AES as CryptoAES
    from Cryptodome.Cipher import DES as CryptoDES
    from Cryptodome.Cipher import DES3 as CryptoDES3
    CRYPTO_AVAILABLE = True
except ImportError:
    try:
        from Crypto.Cipher import AES as CryptoAES
        from Crypto.Cipher import DES as CryptoDES
        from Crypto.Cipher import DES3 as CryptoDES3
        CRYPTO_AVAILABLE = True
    except ImportError:
        CRYPTO_AVAILABLE = False
        CryptoAES = CryptoDES = CryptoDES3 = None

from .constants import random_bytes
from .exceptions import GNTPEncryptionError

__all__ = ['AES', 'DES', 'DES3', 'Cipher', 'NullCipher', 'Algorithm']


class Algorithm:
    """Factory class for creating cipher instances.
    
    Attributes:
        algorithm_id: String identifier for the algorithm
        key_size: Required key size in bytes
    """
    
    def __init__(self, algorithm_id: str, key_size: int):
        """Initialize cipher algorithm configuration.
        
        Args:
            algorithm_id: Algorithm identifier (AES, DES, 3DES)
            key_size: Required key size in bytes
        """
        if not CRYPTO_AVAILABLE:
            raise GNTPEncryptionError(
                "PyCryptodome is required for encryption. "
                "Install with: pip install pycryptodomex"
            )
        
        self.algorithm_id = algorithm_id
        self.key_size = key_size
    
    def cipher(self, key: 'Key') -> 'Cipher':
        """Create a Cipher instance using this algorithm.
        
        Args:
            key: Key instance for encryption
            
        Returns:
            Cipher instance configured with this algorithm
            
        Example:
            >>> from gntplib import keys, ciphers
            >>> key = keys.SHA256.key('mypassword')
            >>> cipher = ciphers.AES.cipher(key)
        """
        return Cipher(key, self.algorithm_id)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"Algorithm(id={self.algorithm_id}, key_size={self.key_size})"


# Pre-configured cipher algorithms
# AES: 192-bit key, 128-bit block, 128-bit IV
AES = Algorithm('AES', 24) if CRYPTO_AVAILABLE else None

# DES: 64-bit key, 64-bit block, 64-bit IV
DES = Algorithm('DES', 8) if CRYPTO_AVAILABLE else None

# 3DES: 192-bit key, 64-bit block, 64-bit IV
DES3 = Algorithm('3DES', 24) if CRYPTO_AVAILABLE else None


# Algorithm mapping
ALGORITHM_MAP = {
    'AES': CryptoAES,
    'DES': CryptoDES,
    '3DES': CryptoDES3,
} if CRYPTO_AVAILABLE else {}

KEY_SIZE_MAP = {
    'AES': 24,
    'DES': 8,
    '3DES': 24,
}


class Cipher:
    """Message encryption and decryption using symmetric ciphers.
    
    This class handles encryption of GNTP messages using AES, DES, or 3DES
    in CBC mode with PKCS7 padding.
    
    Attributes:
        key: Encryption key
        algorithm_id: Algorithm identifier
        algorithm: Cipher algorithm module
        key_size: Required key size
        iv: Initialization vector
    """
    
    def __init__(
        self,
        key: 'Key',
        algorithm_id: str = 'AES',
        iv: Optional[bytes] = None
    ):
        """Initialize cipher with key and algorithm.
        
        Args:
            key: Key instance for encryption
            algorithm_id: Algorithm (AES, DES, 3DES)
            iv: Optional initialization vector. If None, random IV is generated
            
        Raises:
            GNTPEncryptionError: If algorithm is not supported or crypto unavailable
            
        Example:
            >>> from gntplib import keys
            >>> key = keys.SHA256.key('password')
            >>> cipher = Cipher(key, 'AES')
        """
        if not CRYPTO_AVAILABLE:
            raise GNTPEncryptionError(
                "PyCryptodome is required for encryption. "
                "Install with: pip install pycryptodomex"
            )
        
        if algorithm_id not in ALGORITHM_MAP:
            raise GNTPEncryptionError(
                f"Unsupported algorithm: {algorithm_id}. "
                f"Use AES, DES, or 3DES"
            )
        
        self.key = key
        self.algorithm_id = algorithm_id
        self.algorithm = ALGORITHM_MAP[algorithm_id]
        self.key_size = KEY_SIZE_MAP[algorithm_id]
        self.iv = iv if iv is not None else self._random_iv()
        
        # Validate key size
        if len(key.key) < self.key_size:
            raise GNTPEncryptionError(
                f"Key too short for {algorithm_id}. "
                f"Need at least {self.key_size} bytes, got {len(key.key)}"
            )
    
    @property
    def iv_hex(self) -> bytes:
        """Get hex-encoded initialization vector.
        
        Returns:
            Hex-encoded IV as bytes
        """
        return binascii.hexlify(self.iv)
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext data.
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Encrypted data
            
        Raises:
            GNTPEncryptionError: If encryption fails
            
        Example:
            >>> cipher = Cipher(key, 'AES')
            >>> ciphertext = cipher.encrypt(b'secret message')
        """
        try:
            padded = self._pkcs7_pad(plaintext)
            cipher_obj = self._create_cipher()
            return cipher_obj.encrypt(padded)
        except Exception as e:
            raise GNTPEncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext data.
        
        Args:
            ciphertext: Data to decrypt
            
        Returns:
            Decrypted plaintext
            
        Raises:
            GNTPEncryptionError: If decryption fails
            
        Example:
            >>> plaintext = cipher.decrypt(ciphertext)
        """
        try:
            cipher_obj = self._create_cipher()
            padded = cipher_obj.decrypt(ciphertext)
            return self._pkcs7_unpad(padded)
        except Exception as e:
            raise GNTPEncryptionError(f"Decryption failed: {e}")
    
    def _create_cipher(self):
        """Create cipher object for encryption/decryption."""
        return self.algorithm.new(
            self.key.key[:self.key_size],
            self.algorithm.MODE_CBC,
            self.iv
        )
    
    def _pkcs7_pad(self, data: bytes) -> bytes:
        """Apply PKCS7 padding to data.
        
        Args:
            data: Data to pad
            
        Returns:
            Padded data
        """
        block_size = self.algorithm.block_size
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _pkcs7_unpad(self, data: bytes) -> bytes:
        """Remove PKCS7 padding from data.
        
        Args:
            data: Padded data
            
        Returns:
            Unpadded data
            
        Raises:
            GNTPEncryptionError: If padding is invalid
        """
        if not data:
            raise GNTPEncryptionError("Cannot unpad empty data")
        
        padding_length = data[-1]
        
        # Validate padding
        if padding_length > len(data) or padding_length == 0:
            raise GNTPEncryptionError("Invalid padding")
        
        # Check all padding bytes are correct
        padding = data[-padding_length:]
        if not all(byte == padding_length for byte in padding):
            raise GNTPEncryptionError("Invalid PKCS7 padding")
        
        return data[:-padding_length]
    
    def _random_iv(self) -> bytes:
        """Generate random initialization vector.
        
        Returns:
            Random IV bytes
        """
        return random_bytes(self.algorithm.block_size)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"Cipher(algorithm={self.algorithm_id}, iv_length={len(self.iv)})"
    
    def __bool__(self) -> bool:
        """Check if cipher is active."""
        return True


class _NullCipher:
    """Null cipher for no encryption.
    
    This is a null object pattern implementation that provides the same
    interface as Cipher but performs no encryption.
    """
    
    algorithm = None
    algorithm_id = 'NONE'
    
    def encrypt(self, data: bytes) -> bytes:
        """Return data unchanged."""
        return data
    
    def decrypt(self, data: bytes) -> bytes:
        """Return data unchanged."""
        return data
    
    def __bool__(self) -> bool:
        """Null cipher evaluates to False."""
        return False
    
    def __repr__(self) -> str:
        """Return string representation."""
        return "NullCipher()"


# Singleton instance of null cipher
NullCipher = _NullCipher()