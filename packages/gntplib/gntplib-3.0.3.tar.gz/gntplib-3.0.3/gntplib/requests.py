#!/usr/bin/env python3

# File: gntplib/requests.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: GNTP request and response classes.
# License: MIT

"""GNTP request and response classes.

This module defines the request and response structures for GNTP protocol
communication.
"""

from typing import List, Tuple, Optional, Dict, Any
from .models import Event, Notification, Resource
from .exceptions import GNTPResponseError, GNTPProtocolError

__all__ = [
    'BaseRequest',
    'RegisterRequest',
    'NotifyRequest',
    'SubscribeRequest',
    'Response'
]


class BaseRequest:
    """Base class for GNTP requests.
    
    All GNTP requests inherit from this class and must define a message_type.
    
    Attributes:
        message_type: GNTP message type (REGISTER, NOTIFY, SUBSCRIBE)
        custom_headers: List of (key, value) tuples for custom headers
        app_specific_headers: List of (key, value) tuples for app headers
    """
    
    message_type: Optional[str] = None
    
    def __init__(
        self,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None
    ):
        """Initialize base request.
        
        Args:
            custom_headers: Custom X- headers as (key, value) tuples
            app_specific_headers: App Data- headers as (key, value) tuples
        """
        self.custom_headers = custom_headers or []
        self.app_specific_headers = app_specific_headers or []
    
    def write_into(self, writer: Any) -> None:
        """Serialize request into writer.
        
        Subclasses must call this first, then add their specific fields.
        
        Args:
            writer: Message writer instance
        """
        writer.write_base_request(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(type={self.message_type})"


class RegisterRequest(BaseRequest):
    """REGISTER request for registering an application.
    
    This request must be sent before notifications can be published.
    It registers the application and defines available notification types.
    
    Attributes:
        app_name: Application name
        app_icon: Optional application icon
        events: List of Event definitions
    """
    
    message_type = 'REGISTER'
    
    def __init__(
        self,
        app_name: str,
        app_icon: Optional[Resource],
        events: List[Event],
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None
    ):
        """Initialize REGISTER request.
        
        Args:
            app_name: Name of the application
            app_icon: Optional icon resource for the application
            events: List of notification event definitions
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            
        Example:
            >>> from gntplib import Event, Resource
            >>> events = [Event('update', 'Update Available')]
            >>> icon = Resource.from_file('app_icon.png')
            >>> request = RegisterRequest('MyApp', icon, events)
        """
        super().__init__(custom_headers, app_specific_headers)
        self.app_name = app_name
        self.app_icon = app_icon
        self.events = events
    
    def write_into(self, writer: Any) -> None:
        """Serialize REGISTER request."""
        super().write_into(writer)
        writer.write_register_request(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RegisterRequest(app={self.app_name!r}, "
            f"events={len(self.events)})"
        )


class NotifyRequest(BaseRequest):
    """NOTIFY request for sending a notification.
    
    Sends an individual notification to the GNTP server.
    The application must be registered first.
    
    Attributes:
        app_name: Application name (must match registered name)
        notification: Notification instance to send
    """
    
    message_type = 'NOTIFY'
    
    def __init__(
        self,
        app_name: str,
        notification: Notification,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None
    ):
        """Initialize NOTIFY request.
        
        Args:
            app_name: Name of the registered application
            notification: Notification to send
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            
        Example:
            >>> from gntplib import Notification
            >>> notif = Notification('update', 'New Version', 'v2.0 released')
            >>> request = NotifyRequest('MyApp', notif)
        """
        super().__init__(custom_headers, app_specific_headers)
        self.app_name = app_name
        self.notification = notification
    
    def write_into(self, writer: Any) -> None:
        """Serialize NOTIFY request."""
        super().write_into(writer)
        writer.write_notify_request(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"NotifyRequest(app={self.app_name!r}, "
            f"notification={self.notification.name!r})"
        )


class SubscribeRequest(BaseRequest):
    """SUBSCRIBE request for subscribing to notifications.
    
    Allows a client to subscribe to receive notifications from a hub.
    
    Attributes:
        id_: Unique subscriber identifier
        name: Subscriber name
        port: Port number for receiving notifications
    """
    
    message_type = 'SUBSCRIBE'
    
    def __init__(
        self,
        id_: str,
        name: str,
        port: int,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None
    ):
        """Initialize SUBSCRIBE request.
        
        Args:
            id_: Unique subscriber ID
            name: Subscriber name
            port: Port for receiving notifications
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            
        Example:
            >>> request = SubscribeRequest('sub-123', 'MySubscriber', 23053)
        """
        super().__init__(custom_headers, app_specific_headers)
        self.id_ = id_
        self.name = name
        self.port = port
    
    def write_into(self, writer: Any) -> None:
        """Serialize SUBSCRIBE request."""
        super().write_into(writer)
        writer.write_subscribe_request(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SubscribeRequest(id={self.id_!r}, name={self.name!r}, "
            f"port={self.port})"
        )


class Response:
    """GNTP response from server.
    
    Represents the response received from a GNTP server after sending a request.
    
    Attributes:
        message_type: Response type (-OK, -ERROR, -CALLBACK)
        headers: Dictionary of response headers
    """
    
    def __init__(self, message_type: str, headers: Dict[str, str]):
        """Initialize response.
        
        Args:
            message_type: Response type (-OK, -ERROR, -CALLBACK)
            headers: Response headers as dictionary
            
        Raises:
            GNTPResponseError: If response indicates an error
            
        Example:
            >>> response = Response('-OK', {'Response-Action': 'REGISTER'})
        """
        self.message_type = message_type
        self.headers = headers
        
        # Check for error response
        if message_type == '-ERROR':
            error_code = headers.get('Error-Code', 'UNKNOWN')
            error_desc = headers.get('Error-Description', 'No description')
            raise GNTPResponseError(error_code, error_desc)
    
    def is_ok(self) -> bool:
        """Check if response is successful.
        
        Returns:
            True if response type is -OK
        """
        return self.message_type == '-OK'
    
    def is_error(self) -> bool:
        """Check if response is an error.
        
        Returns:
            True if response type is -ERROR
        """
        return self.message_type == '-ERROR'
    
    def is_callback(self) -> bool:
        """Check if response is a callback.
        
        Returns:
            True if response type is -CALLBACK
        """
        return self.message_type == '-CALLBACK'
    
    def get_header(self, name: str, default: Any = None) -> Any:
        """Get header value with optional default.
        
        Args:
            name: Header name
            default: Default value if header not found
            
        Returns:
            Header value or default
        """
        return self.headers.get(name, default)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"Response(type={self.message_type}, headers={len(self.headers)})"
    
    def __str__(self) -> str:
        """Return human-readable string."""
        lines = [f"GNTP Response: {self.message_type}"]
        for key, value in self.headers.items():
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)


def parse_response(message: bytes, expected_type: Optional[str] = None) -> Response:
    """Parse GNTP response message.
    
    Args:
        message: Raw response message bytes
        expected_type: Expected response type for validation
        
    Returns:
        Response instance
        
    Raises:
        GNTPProtocolError: If response format is invalid
        GNTPResponseError: If response indicates an error
        
    Example:
        >>> response = parse_response(b'GNTP/1.0 -OK NONE\\r\\n...')
    """
    from .constants import LINE_DELIMITER, RESPONSE_INFORMATION_LINE_RE
    
    try:
        # Split message into lines
        lines = [line for line in message.split(LINE_DELIMITER) if line]
        
        if not lines:
            raise GNTPProtocolError("Empty response message")
        
        # Parse information line
        info_line = lines[0]
        match = RESPONSE_INFORMATION_LINE_RE.match(info_line)
        
        if not match:
            raise GNTPProtocolError(f"Invalid information line: {info_line!r}")
        
        version = match.group(1).decode('utf-8')
        message_type = match.group(2).decode('utf-8')
        
        # Validate expected type
        if expected_type and message_type != expected_type:
            raise GNTPProtocolError(
                f"Expected {expected_type}, got {message_type}"
            )
        
        # Parse headers
        headers = {}
        for line in lines[1:]:
            if b':' not in line:
                continue
            
            key, _, value = line.partition(b':')
            key = key.strip().decode('utf-8')
            value = value.strip().decode('utf-8')
            headers[key] = value
        
        return Response(message_type, headers)
        
    except Exception as e:
        if isinstance(e, (GNTPProtocolError, GNTPResponseError)):
            raise
        raise GNTPProtocolError(
            f"Failed to parse response: {e}",
            details=f"Original message: {message!r}"
        )