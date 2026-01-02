#!/usr/bin/env python3

# File: gntplib/connections.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: GNTP connection and client implementations.
# License: MIT

"""GNTP connection and client implementations.

This module provides synchronous connection handling and client logic
for communicating with GNTP servers.
"""

import socket
from typing import Optional, Callable, Any, Tuple, Generator

from .constants import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    MESSAGE_DELIMITER,
    MESSAGE_DELIMITER_SIZE,
    MAX_MESSAGE_SIZE
)
from .exceptions import GNTPConnectionError, GNTPError
from .packers import MessagePackerFactory
from .requests import parse_response
from .keys import Key, Algorithm as KeyAlgorithm
from .ciphers import Cipher, Algorithm as CipherAlgorithm

__all__ = [
    'BaseGNTPConnection',
    'GNTPConnection',
    'GNTPClient'
]


class BaseGNTPConnection:
    """Abstract base class for GNTP connections.
    
    Defines the interface for GNTP server connections. Subclasses must
    implement write_message, read_message, and close methods.
    
    Attributes:
        final_callback: Callback when connection completes
        socket_callback: Optional callback for socket events
    """
    
    def __init__(
        self,
        final_callback: Optional[Callable] = None,
        socket_callback: Optional[Any] = None
    ):
        """Initialize base connection.
        
        Args:
            final_callback: Called when operation completes
            socket_callback: Optional socket event callback
        """
        self.final_callback = final_callback
        self.socket_callback = socket_callback
    
    def on_ok_message(self, message: bytes) -> None:
        """Handle -OK response from server.
        
        Args:
            message: Response message bytes
        """
        try:
            response = parse_response(message, '-OK')
            
            # If socket callback is registered, wait for callback message
            if self.socket_callback is not None:
                self.read_message(self.on_callback_message)
        finally:
            # Close if no callback expected
            if self.socket_callback is None:
                self.close()
        
        # Call final callback if no socket callback
        if self.socket_callback is None and self.final_callback is not None:
            self.final_callback(response)
    
    def on_callback_message(self, message: bytes) -> None:
        """Handle -CALLBACK response from server.
        
        Args:
            message: Callback message bytes
        """
        try:
            response = parse_response(message, '-CALLBACK')
            callback_result = self.socket_callback(response)
        finally:
            self.close()
        
        # Call final callback with result
        if self.final_callback is not None:
            self.final_callback(callback_result)
    
    def write_message(self, message: bytes) -> None:
        """Send message to server.
        
        Subclasses must implement this method.
        
        Args:
            message: Message bytes to send
        """
        raise NotImplementedError
    
    def read_message(self, callback: Callable[[bytes], None]) -> None:
        """Read message from server.
        
        Subclasses must implement this method.
        
        Args:
            callback: Function to call with received message
        """
        raise NotImplementedError
    
    def close(self) -> None:
        """Close the connection.
        
        Subclasses must implement this method.
        """
        raise NotImplementedError


class GNTPConnection(BaseGNTPConnection):
    """Synchronous GNTP connection implementation.
    
    Provides blocking socket communication with GNTP server.
    
    Attributes:
        sock: TCP socket connection
    """
    
    def __init__(
        self,
        address: Tuple[str, int],
        timeout: float,
        final_callback: Optional[Callable] = None,
        socket_callback: Optional[Any] = None
    ):
        """Initialize GNTP connection.
        
        Args:
            address: (host, port) tuple
            timeout: Connection timeout in seconds
            final_callback: Called when operation completes
            socket_callback: Optional socket event callback
            
        Raises:
            GNTPConnectionError: If connection fails
        """
        super().__init__(final_callback, socket_callback)
        
        try:
            self.sock = socket.create_connection(address, timeout=timeout)
        except socket.error as e:
            raise GNTPConnectionError(
                f"Failed to connect to {address[0]}:{address[1]}: {e}"
            )
    
    def write_message(self, message: bytes) -> None:
        """Send message to GNTP server.
        
        Args:
            message: Message bytes to send
            
        Raises:
            GNTPConnectionError: If send fails
        """
        try:
            self.sock.sendall(message)
        except socket.error as e:
            raise GNTPConnectionError(f"Failed to send message: {e}")
    
    def read_message(self, callback: Callable[[bytes], None]) -> None:
        """Read message from server and call callback.
        
        Args:
            callback: Function to call with received message
            
        Raises:
            GNTPConnectionError: If read fails
        """
        try:
            message = next(generate_messages(self.sock))
            callback(message)
        except StopIteration:
            raise GNTPConnectionError("Connection closed by server")
        except socket.error as e:
            raise GNTPConnectionError(f"Failed to read message: {e}")
    
    def close(self) -> None:
        """Close the socket connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            finally:
                self.sock = None


def generate_messages(
    sock: socket.socket,
    buffer_size: int = 1024
) -> Generator[bytes, None, None]:
    """Generate complete GNTP messages from socket.
    
    Reads from socket and yields complete messages terminated by
    double CRLF (\\r\\n\\r\\n).
    
    Args:
        sock: Socket to read from
        buffer_size: Read buffer size in bytes
        
    Yields:
        Complete GNTP message bytes
        
    Raises:
        GNTPError: If message exceeds maximum size
    """
    buffer = b''
    
    while True:
        chunk = sock.recv(buffer_size)
        
        if not chunk:
            break
        
        buffer += chunk
        
        # Look for message delimiter
        delimiter_pos = buffer.find(MESSAGE_DELIMITER)
        
        # Check message size limits
        if delimiter_pos < 0 and len(buffer) >= MAX_MESSAGE_SIZE:
            raise GNTPError(f"Message too large: {len(buffer)} bytes")
        
        if delimiter_pos > MAX_MESSAGE_SIZE - MESSAGE_DELIMITER_SIZE:
            raise GNTPError(f"Message too large: {delimiter_pos} bytes")
        
        # Yield complete message
        if delimiter_pos >= 0:
            end_pos = delimiter_pos + MESSAGE_DELIMITER_SIZE
            yield buffer[:end_pos]
            buffer = buffer[end_pos:]


class GNTPClient:
    """Synchronous GNTP client.
    
    Handles request processing with optional authentication and encryption.
    
    Attributes:
        address: (host, port) of GNTP server
        timeout: Connection timeout in seconds
        connection_class: Connection class to use
        packer_factory: Factory for creating message packers
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        password: Optional[str] = None,
        key_hashing: Optional[KeyAlgorithm] = None,
        encryption: Optional[CipherAlgorithm] = None,
        connection_class: Optional[type] = None
    ):
        """Initialize GNTP client.
        
        Args:
            host: GNTP server hostname
            port: GNTP server port
            timeout: Connection timeout in seconds
            password: Optional password for authentication
            key_hashing: Key hashing algorithm (default: SHA256)
            encryption: Optional encryption algorithm
            connection_class: Connection class (default: GNTPConnection)
            
        Raises:
            GNTPError: If encryption key size is too large for hashing
            
        Example:
            >>> from gntplib import keys, ciphers
            >>> client = GNTPClient(
            ...     host='localhost',
            ...     password='secret',
            ...     key_hashing=keys.SHA256,
            ...     encryption=ciphers.AES
            ... )
        """
        self.address = (host, port)
        self.timeout = timeout
        self.connection_class = connection_class or GNTPConnection
        
        # Set default key hashing
        if password and key_hashing is None:
            from .keys import SHA256
            key_hashing = SHA256
        
        # Validate encryption vs hashing key size
        if encryption and key_hashing:
            if encryption.key_size > key_hashing.key_size:
                raise GNTPError(
                    f"Key hashing size ({key_hashing.algorithm_id}:"
                    f"{key_hashing.key_size}) must be at least encryption "
                    f"key size ({encryption.algorithm_id}:"
                    f"{encryption.key_size})"
                )
        
        # Create packer factory
        self.packer_factory = MessagePackerFactory(
            password,
            key_hashing,
            encryption
        )
    
    def process_request(
        self,
        request: Any,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> None:
        """Process a GNTP request.
        
        Serializes the request, sends it to the server, and handles the response.
        
        Args:
            request: Request object to send
            callback: Optional callback when operation completes
            **kwargs: Additional arguments passed to connection
            
        Example:
            >>> from gntplib import RegisterRequest, Event
            >>> request = RegisterRequest('MyApp', None, [Event('test')])
            >>> client.process_request(request)
        """
        # Pack the message
        packer = self.packer_factory.create()
        message = packer.pack(request)
        
        # Create connection
        conn = self._connect(callback, **kwargs)
        
        # Send request
        conn.write_message(message)
        
        # Read response
        conn.read_message(conn.on_ok_message)
    
    def _connect(
        self,
        final_callback: Optional[Callable] = None,
        **kwargs
    ) -> BaseGNTPConnection:
        """Create connection to GNTP server.
        
        Args:
            final_callback: Callback when operation completes
            **kwargs: Additional connection arguments
            
        Returns:
            Connection instance
        """
        return self.connection_class(
            self.address,
            self.timeout,
            final_callback,
            **kwargs
        )
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"GNTPClient(host={self.address[0]!r}, "
            f"port={self.address[1]}, "
            f"timeout={self.timeout})"
        )