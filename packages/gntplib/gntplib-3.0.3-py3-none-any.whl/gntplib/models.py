#!/usr/bin/env python3

# File: gntplib/models.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Core model classes for GNTP protocol.
# License: MIT

"""Core model classes for GNTP protocol.

This module defines the core data models used in GNTP communication:
- Resources: Binary data like icons and images
- Events: Notification type definitions
- Notifications: Individual notification instances
- Callbacks: Response handling
"""

import hashlib
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from .constants import RESOURCE_URL_SCHEME
from .exceptions import GNTPValidationError

__all__ = [
    'Resource',
    'Event', 
    'Notification',
    'SocketCallback',
    'URLCallback'
]


class Resource:
    """Binary resource for GNTP messages (icons, images, etc).
    
    Resources are binary data that can be embedded in GNTP messages
    or referenced by URL. Each resource has a unique identifier based
    on its content hash.
    
    Attributes:
        data: Binary content of the resource
        url: Optional URL if resource is remote
    """
    
    def __init__(self, data: Optional[bytes] = None, url: Optional[str] = None):
        """Initialize resource with binary data or URL.
        
        Args:
            data: Binary content (for embedded resources)
            url: URL string (for remote resources)
            
        Example:
            >>> # Embedded resource
            >>> with open('icon.png', 'rb') as f:
            ...     icon = Resource(data=f.read())
            >>> 
            >>> # URL resource
            >>> icon = Resource(url='https://example.com/icon.png')
        """
        self.data = None
        self.url = None

        try:
            if data and Path(data).is_file():  # type: ignore
                self.data = Resource.from_file(data)()  # type: ignore
        except Exception:
            pass

        try:
            if not self.data and data and data.startswith(b'http'):  # type: ignore
                data = Resource.from_url(data)()  # type: ignore
                self.data = data
            else:
                self.url = url
        except TypeError:
            if not self.data and data and data.startswith('http'):  # type: ignore
                data = Resource.from_url(data)()  # type: ignore
                self.data = data
            else:
                self.url = url

        try:
            if not self.data and data and not Path(data).is_file():  # type: ignore
                # check if data is base64encode
                import base64
                self.data = base64.b64decode(data)
        except Exception:
            pass

        self.data = self.data or data
        
        self._unique_value: Optional[bytes] = None

    def __call__(self) -> Optional[bytes]:
        """Get resource data.
        
        Returns:
            Binary data of the resource or None if URL-based
            
        Example:
            >>> resource = Resource(b'binary data')
            >>> data = resource()
        """
        return self.data  # type: ignore
    
    @classmethod
    def from_file(cls, filepath: str) -> 'Resource':
        """Create resource from file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Resource instance with file contents
            
        Raises:
            IOError: If file cannot be read
            
        Example:
            >>> icon = Resource.from_file('icon.png')
        """
        with open(filepath, 'rb') as f:
            return cls(data=f.read())
    
    @classmethod
    def from_url(cls, url: str) -> 'Resource':
        """Create resource from URL.
        
        Args:
            url: URL to resource
            
        Returns:
            Resource instance referencing URL
            
        Example:
            >>> icon = Resource.from_url('https://example.com/icon.png')
        """
        return cls(url=url)
    
    def unique_value(self) -> Optional[bytes]:
        """Get unique hash identifier for resource content.
        
        Returns MD5 hash of resource data as hex bytes.
        
        Returns:
            Hex-encoded MD5 hash or None if no data
            
        Example:
            >>> resource = Resource(b'test data')
            >>> resource.unique_value()
            b'eb733a00c0c9d336e65691a37ab54293'
        """
        if self.data is not None and self._unique_value is None:
            self._unique_value = hashlib.md5(self.data).hexdigest().encode('utf-8')  # type: ignore
        return self._unique_value
    
    def unique_id(self) -> Optional[bytes]:
        """Get unique resource identifier with protocol scheme.
        
        Returns:
            Full resource identifier or None if no data
            
        Example:
            >>> resource = Resource(b'test')
            >>> resource.unique_id()
            b'x-growl-resource://098f6bcd4621d373cade4e832627b4f6'
        """
        unique_val = self.unique_value()
        if unique_val is not None:
            return RESOURCE_URL_SCHEME + unique_val
        return None
    
    def __repr__(self) -> str:
        """Return string representation."""
        if self.url:
            return f"Resource(url={self.url!r})"
        elif self.data:
            return f"Resource(size={len(self.data)} bytes)"
        else:
            return "Resource(empty)"
    
    def __bool__(self) -> bool:
        """Check if resource has content."""
        return self.data is not None or self.url is not None


class Event:
    """Notification type definition.
    
    Events define the types of notifications an application can send.
    Each event must be registered before notifications of that type can be sent.
    
    Attributes:
        name: Unique identifier for the notification type
        display_name: Human-readable name shown in preferences
        enabled: Whether notifications of this type are enabled by default
        icon: Optional icon for this notification type
    """
    
    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        enabled: bool = True,
        icon: Optional[Resource] = None
    ):
        """Initialize notification event definition.
        
        Args:
            name: Event identifier (required)
            display_name: Display name (defaults to name)
            enabled: Enable by default (default: True)
            icon: Optional icon resource
            
        Raises:
            GNTPValidationError: If name is empty
            
        Example:
            >>> event = Event('Update', 'Software Update', enabled=True)
        """
        if not name:
            raise GNTPValidationError("Event name cannot be empty")
        
        self.name = name
        self.display_name = display_name or name
        self.enabled = enabled
        self.icon = icon
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Event(name={self.name!r}, "
            f"display_name={self.display_name!r}, "
            f"enabled={self.enabled})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on name."""
        if isinstance(other, Event):
            return self.name == other.name
        return False
    
    def __hash__(self) -> int:
        """Make Event hashable based on name."""
        return hash(self.name)


class Notification:
    """Individual notification instance.
    
    Represents a single notification to be sent to the GNTP server.
    
    Attributes:
        name: Event name this notification belongs to
        title: Notification title
        text: Notification message body
        id_: Optional unique identifier
        sticky: Whether notification stays until dismissed
        priority: Priority level (-2 to 2)
        icon: Optional icon resource
        coalescing_id: ID for grouping/replacing notifications
        callback: Optional callback handler
    """
    
    def __init__(
        self,
        name: str,
        title: str,
        text: str = '',
        id_: Optional[str] = None,
        sticky: bool = False,
        priority: int = 0,
        icon: Optional[Resource] = None,
        coalescing_id: Optional[str] = None,
        callback: Optional['BaseCallback'] = None
    ):
        """Initialize notification.
        
        Args:
            name: Event name
            title: Notification title
            text: Message text (default: '')
            id_: Unique notification ID
            sticky: Keep visible until dismissed (default: False)
            priority: Priority from -2 to 2 (default: 0)
            icon: Optional icon
            coalescing_id: Group/replace ID
            callback: Optional callback handler
            
        Raises:
            GNTPValidationError: If name or title is empty
            
        Example:
            >>> notif = Notification(
            ...     'Update',
            ...     'New Version',
            ...     'Version 2.0 is available',
            ...     priority=1,
            ...     sticky=True
            ... )
        """
        if not name:
            raise GNTPValidationError("Notification name cannot be empty")
        if not title:
            raise GNTPValidationError("Notification title cannot be empty")
        
        self.name = name
        self.title = title
        self.text = text
        self.id_ = id_
        self.sticky = sticky
        self.priority = max(-2, min(2, priority or 0))  # Clamp to valid range
        self.icon = icon
        self.coalescing_id = coalescing_id
        self.callback = callback
    
    @property
    def socket_callback(self) -> Optional['SocketCallback']:
        """Get socket callback if callback is SocketCallback type."""
        if isinstance(self.callback, SocketCallback):
            return self.callback
        return None
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Notification(name={self.name!r}, title={self.title!r}, "
            f"priority={self.priority}, sticky={self.sticky})"
        )


class BaseCallback:
    """Base class for notification callbacks."""
    
    def write_into(self, writer: Any) -> None:
        """Write callback to message writer.
        
        Subclasses must implement this method.
        
        Args:
            writer: Message writer instance
        """
        raise NotImplementedError


class SocketCallback(BaseCallback):
    """Socket-based callback for notification responses.
    
    Handles different callback events (clicked, closed, timeout) via
    registered callback functions.
    
    Attributes:
        context: Callback context value
        context_type: Type of context
        on_click_callback: Called when notification is clicked
        on_close_callback: Called when notification is closed
        on_timeout_callback: Called when notification times out
    """
    
    def __init__(
        self,
        context: str = 'None',
        context_type: str = 'None',
        on_click: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_timeout: Optional[Callable] = None
    ):
        """Initialize socket callback.
        
        Args:
            context: Context value (default: 'None')
            context_type: Context type (default: 'None')
            on_click: Callback for click events
            on_close: Callback for close events
            on_timeout: Callback for timeout events
            
        Example:
            >>> def on_clicked(response):
            ...     print("Notification clicked!")
            >>> 
            >>> callback = SocketCallback(
            ...     context='notification_1',
            ...     on_click=on_clicked
            ... )
        """
        self.context = context
        self.context_type = context_type
        self.on_click_callback = on_click
        self.on_close_callback = on_close
        self.on_timeout_callback = on_timeout
    
    def on_click(self, response: Any) -> Any:
        """Handle click event."""
        if self.on_click_callback:
            return self.on_click_callback(response)
    
    def on_close(self, response: Any) -> Any:
        """Handle close event."""
        if self.on_close_callback:
            return self.on_close_callback(response)
    
    def on_timeout(self, response: Any) -> Any:
        """Handle timeout event."""
        if self.on_timeout_callback:
            return self.on_timeout_callback(response)
    
    def __call__(self, response: Any) -> Any:
        """Dispatch to appropriate handler based on callback result.
        
        Args:
            response: Response object with callback result
            
        Returns:
            Result from handler callback
        """
        result = response.headers.get('Notification-Callback-Result', '')
        
        # Map callback results to handlers
        handlers: Dict[str, Callable] = {
            'CLICKED': self.on_click,
            'CLICK': self.on_click,
            'CLOSED': self.on_close,
            'CLOSE': self.on_close,
            'TIMEDOUT': self.on_timeout,
            'TIMEOUT': self.on_timeout,
        }
        
        handler = handlers.get(result)
        if handler:
            return handler(response)
    
    def write_into(self, writer: Any) -> None:
        """Write socket callback headers."""
        writer.write_socket_callback(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"SocketCallback(context={self.context!r})"


class URLCallback(BaseCallback):
    """URL-based callback for notification responses.
    
    When notification is interacted with, GNTP server will request the URL.
    
    Attributes:
        url: Callback URL
    """
    
    def __init__(self, url: str):
        """Initialize URL callback.
        
        Args:
            url: URL to be called on notification interaction
            
        Example:
            >>> callback = URLCallback('https://example.com/callback')
        """
        if not url:
            raise GNTPValidationError("Callback URL cannot be empty")
        
        self.url = url
    
    def write_into(self, writer: Any) -> None:
        """Write URL callback headers."""
        writer.write_url_callback(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"URLCallback(url={self.url!r})"