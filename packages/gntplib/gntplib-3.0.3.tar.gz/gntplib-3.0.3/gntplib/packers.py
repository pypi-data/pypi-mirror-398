#!/usr/bin/env python3

# File: gntplib/packers.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Message packing and serialization for GNTP protocol.
# License: MIT

"""Message packing and serialization for GNTP protocol.

This module handles the serialization of GNTP requests into the wire format,
including encryption and authentication.
"""

import io
from typing import Optional, Any, List, Tuple

from .models import Resource
from .constants import (
    LINE_DELIMITER,
    SECTION_DELIMITER,
    SECTION_BODY_START,
    SECTION_BODY_END,
    CUSTOM_HEADER_PREFIX,
    APP_SPECIFIC_HEADER_PREFIX
)
from .keys import Key
from .ciphers import Cipher, NullCipher
from .exceptions import GNTPError

__all__ = [
    'MessagePackerFactory',
    'MessagePacker',
    'InformationLinePacker',
    'HeaderPacker',
    'SectionPacker'
]


class MessagePackerFactory:
    """Factory for creating message packers with encryption and authentication.
    
    This factory creates MessagePacker instances configured with the
    appropriate key and cipher settings.
    
    Attributes:
        password: Optional password for authentication
        hashing: Key hashing algorithm
        encryption: Cipher algorithm or None
    """
    
    def __init__(
        self,
        password: Optional[str] = None,
        hashing: Optional[Any] = None,
        encryption: Optional[Any] = None
    ):
        """Initialize message packer factory.
        
        Args:
            password: Password for authentication (None = no auth)
            hashing: Hashing algorithm from keys module
            encryption: Encryption algorithm from ciphers module or None
            
        Example:
            >>> from gntplib import keys, ciphers
            >>> factory = MessagePackerFactory(
            ...     password='secret',
            ...     hashing=keys.SHA256,
            ...     encryption=ciphers.AES
            ... )
        """
        self.password = password
        self.hashing = hashing if password else None
        self.encryption = encryption if password else None
    
    def create(self) -> 'MessagePacker':
        """Create a new MessagePacker instance.
        
        Returns:
            Configured MessagePacker
            
        Example:
            >>> packer = factory.create()
            >>> message = packer.pack(request)
        """
        key = None
        cipher = NullCipher
        
        if self.password and self.hashing:
            key = self.hashing.key(self.password)
            
            if self.encryption:
                cipher = self.encryption.cipher(key)
        
        return MessagePacker(key, cipher)


class MessagePacker:
    """Serializes GNTP requests into wire format.
    
    Handles the complete serialization process including information line,
    headers, and binary sections with optional encryption.
    
    Attributes:
        key: Optional authentication key
        cipher: Cipher for encryption (or NullCipher)
    """
    
    def __init__(
        self,
        key: Optional[Key] = None,
        cipher: Optional[Cipher] = None
    ):
        """Initialize message packer.
        
        Args:
            key: Authentication key (None = no auth)
            cipher: Encryption cipher (None = no encryption)
        """
        self.key = key
        self.cipher = cipher or NullCipher
    
    def pack(self, request: Any) -> bytes:
        """Pack request into GNTP wire format.
        
        Args:
            request: Request object to serialize
            
        Returns:
            Complete GNTP message as bytes
            
        Example:
            >>> message = packer.pack(register_request)
            >>> print(message[:50])
            b'GNTP/1.0 REGISTER NONE SHA256:...'
        """
        parts = [
            InformationLinePacker(self.key, self.cipher).pack(request),
            LINE_DELIMITER,
            HeaderPacker(self.cipher).pack(request),
            SectionPacker(self.cipher).pack(request),
            LINE_DELIMITER
        ]
        
        return b''.join(parts)


class InformationLinePacker:
    """Packs the GNTP information line.
    
    Format: GNTP/1.0 <messagetype> <encryptionAlgorithmID>[:<ivValue>] 
            [<keyHashAlgorithmID>:<keyHash>.<salt>]
    """
    
    def __init__(self, key: Optional[Key], cipher: Cipher):
        """Initialize information line packer.
        
        Args:
            key: Authentication key
            cipher: Encryption cipher
        """
        self.key = key
        self.cipher = cipher
    
    def pack(self, request: Any) -> bytes:
        """Pack information line for request.
        
        Args:
            request: Request with message_type attribute
            
        Returns:
            Information line bytes
        """
        parts = [
            b'GNTP/1.0 ',
            request.message_type.encode('utf-8'),
            b' ',
            self.cipher.algorithm_id.encode('utf-8')
        ]
        
        # Add IV if encryption is used
        if self.cipher.algorithm is not None:
            parts.extend([b':', self.cipher.iv_hex])
        
        # Add key hash if authentication is used
        if self.key is not None:
            parts.extend([
                b' ',
                self.key.algorithm_id.encode('utf-8'),
                b':',
                self.key.key_hash_hex,
                b'.',
                self.key.salt_hex
            ])
        
        return b''.join(parts)


class HeaderPacker:
    """Packs GNTP headers.
    
    Handles serialization of request headers with optional encryption.
    """
    
    def __init__(self, cipher: Cipher):
        """Initialize header packer.
        
        Args:
            cipher: Cipher for encrypting headers
        """
        self.writer = io.BytesIO()
        self.cipher = cipher
    
    def pack(self, request: Any) -> bytes:
        """Pack headers for request.
        
        Args:
            request: Request object
            
        Returns:
            Packed headers bytes (possibly encrypted)
        """
        # Let request write its headers
        request.write_into(self)
        
        # Get headers and encrypt if needed
        headers = self.writer.getvalue()
        result = self.cipher.encrypt(headers)
        
        # Add delimiter if encrypted
        if self.cipher.algorithm is not None:
            result += LINE_DELIMITER
        
        return result
    
    def write_base_request(self, request: Any) -> None:
        """Write base request headers (custom and app-specific).
        
        Args:
            request: Request with header lists
        """
        self._write_additional_headers(
            request.custom_headers,
            CUSTOM_HEADER_PREFIX
        )
        self._write_additional_headers(
            request.app_specific_headers,
            APP_SPECIFIC_HEADER_PREFIX
        )
    
    def _write_additional_headers(
        self,
        headers: List[Tuple[str, Any]],
        prefix: str
    ) -> None:
        """Write custom headers with prefix.
        
        Args:
            headers: List of (key, value) tuples
            prefix: Prefix to add to header names
        """
        for key, value in headers:
            if not key.startswith(prefix):
                key = prefix + key
            self.write(key.encode('utf-8'), value)
    
    def write_register_request(self, request: Any) -> None:
        """Write REGISTER request headers.
        
        Args:
            request: RegisterRequest instance
        """
        self.write(b'Application-Name', request.app_name)
        self.write(b'Application-Icon', request.app_icon)
        self.write(b'Notifications-Count', len(request.events))
        
        # Write each event definition
        for event in request.events:
            self.writer.write(LINE_DELIMITER)
            self.write(b'Notification-Name', event.name)
            self.write(b'Notification-Display-Name', event.display_name)
            self.write(b'Notification-Enabled', event.enabled)
            self.write(b'Notification-Icon', event.icon)
    
    def write_notify_request(self, request: Any) -> None:
        """Write NOTIFY request headers.
        
        Args:
            request: NotifyRequest instance
        """
        self.write(b'Application-Name', request.app_name)
        self._write_notification(request.notification)
    
    def write_subscribe_request(self, request: Any) -> None:
        """Write SUBSCRIBE request headers.
        
        Args:
            request: SubscribeRequest instance
        """
        self.write(b'Subscriber-ID', request.id_)
        self.write(b'Subscriber-Name', request.name)
        self.write(b'Subscriber-Port', request.port)
    
    def _write_notification(self, notification: Any) -> None:
        """Write notification headers.
        
        Args:
            notification: Notification instance
        """
        self.write(b'Notification-Name', notification.name)
        self.write(b'Notification-ID', notification.id_)
        self.write(b'Notification-Title', notification.title)
        self.write(b'Notification-Text', notification.text)
        self.write(b'Notification-Sticky', notification.sticky)
        self.write(b'Notification-Priority', notification.priority)
        self.write(b'Notification-Icon', notification.icon)
        self.write(b'Notification-Coalescing-ID', notification.coalescing_id)
        
        # Write callback if present
        if notification.callback is not None:
            notification.callback.write_into(self)
    
    def write_socket_callback(self, callback: Any) -> None:
        """Write socket callback headers.
        
        Args:
            callback: SocketCallback instance
        """
        self.write(b'Notification-Callback-Context', callback.context)
        self.write(b'Notification-Callback-Context-Type', callback.context_type)
    
    def write_url_callback(self, callback: Any) -> None:
        """Write URL callback headers.
        
        Args:
            callback: URLCallback instance
        """
        self.write(b'Notification-Callback-Target', callback.url)
    
    def write(self, name: bytes, value: Any) -> None:
        """Write a header line.
        
        Args:
            name: Header name as bytes
            value: Header value (converted to bytes)
        """
        if value is None:
            return
        
        # Handle Resource objects
        if isinstance(value, Resource):
            value = value.unique_id()
            if value is None:
                return
        
        # Convert value to bytes
        if not isinstance(value, bytes):
            value = str(value).encode('utf-8')
        
        # Write header line
        self.writer.write(name)
        self.writer.write(b': ')
        self.writer.write(value)
        self.writer.write(LINE_DELIMITER)


class SectionPacker:
    """Packs GNTP binary sections (resources).
    
    Handles serialization of binary resources like icons and images.
    """
    
    def __init__(self, cipher: Cipher):
        """Initialize section packer.
        
        Args:
            cipher: Cipher for encrypting sections
        """
        self.writer = io.BytesIO()
        self.cipher = cipher
    
    def pack(self, request: Any) -> bytes:
        """Pack binary sections for request.
        
        Args:
            request: Request object
            
        Returns:
            Packed sections bytes
        """
        request.write_into(self)
        return self.writer.getvalue()
    
    def write_base_request(self, request: Any) -> None:
        """Write base request sections.
        
        Args:
            request: Request with header lists
        """
        # Write custom header resources
        for _, value in request.custom_headers:
            if isinstance(value, Resource):
                self.write(value)
        
        # Write app-specific header resources
        for _, value in request.app_specific_headers:
            if isinstance(value, Resource):
                self.write(value)
    
    def write_register_request(self, request: Any) -> None:
        """Write REGISTER request sections.
        
        Args:
            request: RegisterRequest instance
        """
        self.write(request.app_icon)
        for event in request.events:
            self.write(event.icon)
    
    def write_notify_request(self, request: Any) -> None:
        """Write NOTIFY request sections.
        
        Args:
            request: NotifyRequest instance
        """
        self.write(request.notification.icon)
    
    def write_subscribe_request(self, request: Any) -> None:
        """Write SUBSCRIBE request sections (none).
        
        Args:
            request: SubscribeRequest instance
        """
        pass
    
    def write(self, resource: Optional[Resource]) -> None:
        """Write a binary resource section.
        
        Args:
            resource: Resource to write
        """
        if not isinstance(resource, Resource) or resource.data is None:
            return
        
        # Encrypt data
        data = self.cipher.encrypt(resource.data)
        
        # Write section header
        self.writer.write(SECTION_DELIMITER)
        self.writer.write(b'Identifier: ')
        self.writer.write(resource.unique_value())
        self.writer.write(LINE_DELIMITER)
        self.writer.write(b'Length: ')
        self.writer.write(str(len(data)).encode('utf-8'))
        self.writer.write(LINE_DELIMITER)
        
        # Write section body
        self.writer.write(SECTION_BODY_START)
        self.writer.write(data)
        self.writer.write(SECTION_BODY_END)