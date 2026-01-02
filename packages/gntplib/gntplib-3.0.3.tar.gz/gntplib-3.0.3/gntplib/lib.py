#!/usr/bin/env python3

# File: gntplib/lib.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Main library implementation for GNTP protocol.
# License: MIT

"""Main library implementation for GNTP protocol.

This module provides the high-level Publisher and Subscriber classes
for sending and receiving GNTP notifications.
"""

from typing import List, Optional, Union, Callable, Any, Tuple

from .models import Event, Notification, Resource, SocketCallback, URLCallback
from .requests import RegisterRequest, NotifyRequest, SubscribeRequest, Response
from .connections import GNTPClient
from .constants import DEFAULT_PORT, DEFAULT_TTL
from .exceptions import GNTPError, GNTPValidationError

__all__ = [
    'publish',
    'subscribe',
    'Publisher',
    'Subscriber',
    # Deprecated aliases
    'notify',
    'Notifier'
]


def publish(
    app_name: str,
    event_name: str,
    title: str,
    text: str = ''
) -> None:
    """Quick publish: Register and send notification in one call.
    
    This is a convenience function that registers an application with a
    single event type and immediately sends a notification.
    
    Args:
        app_name: Name of the application
        event_name: Name of the notification event
        title: Notification title
        text: Notification message (default: '')
        
    Example:
        >>> from gntplib import publish
        >>> publish('MyApp', 'Alert', 'Warning', 'System overheating')
    """
    publisher = Publisher(app_name, [Event(event_name)])
    publisher.register()
    publisher.publish(event_name, title, text)


def notify(app_name: str, event_name: str, title: str, text: str = '') -> None:
    """Deprecated: Use publish() instead."""
    import warnings
    warnings.warn(
        'notify() is deprecated, use publish() instead',
        DeprecationWarning,
        stacklevel=2
    )
    publish(app_name, event_name, title, text)


def subscribe(
    id_: str,
    name: str,
    hub: Union[str, Tuple[str, int]],
    password: str,
    port: int = DEFAULT_PORT
) -> int:
    """Quick subscribe: Send subscription request and return TTL.
    
    Args:
        id_: Unique subscriber ID
        name: Subscriber name
        hub: Hub address (hostname or (host, port) tuple)
        password: Hub password
        port: Subscriber port (default: 23053)
        
    Returns:
        Subscription TTL in seconds
        
    Example:
        >>> from gntplib import subscribe
        >>> ttl = subscribe('sub-123', 'MySubscriber', 'hub.example.com', 'secret')
    """
    subscriber = Subscriber(id_, name, hub, password, port=port)
    subscriber.subscribe()
    return subscriber.ttl


def coerce_to_events(items: List[Union[str, Tuple[str, bool], Event]]) -> List[Event]:
    """Convert various event definitions to Event instances.
    
    Args:
        items: List of event definitions
            - str: Event name (enabled by default)
            - (str, bool): (Event name, enabled flag)
            - Event: Event instance (used as-is)
            
    Returns:
        List of Event instances
        
    Example:
        >>> events = coerce_to_events(['event1', ('event2', False)])
    """
    results = []
    
    for item in items:
        if isinstance(item, str):
            results.append(Event(item, enabled=True))
        elif isinstance(item, tuple):
            name, enabled = item
            results.append(Event(name, enabled=enabled))
        elif isinstance(item, Event):
            results.append(item)
        else:
            raise GNTPValidationError(
                f"Invalid event definition: {item}. "
                f"Expected str, (str, bool), or Event"
            )
    
    return results


def coerce_to_callback(
    gntp_callback: Optional[Union[str, SocketCallback]] = None,
    **socket_callback_options
) -> Optional[Union[URLCallback, SocketCallback]]:
    """Convert callback specification to callback instance.
    
    Args:
        gntp_callback: URL string or SocketCallback instance
        **socket_callback_options: Options for creating SocketCallback
        
    Returns:
        URLCallback, SocketCallback, or None
        
    Raises:
        GNTPError: If both gntp_callback and options are provided
    """
    if gntp_callback is not None:
        if socket_callback_options:
            raise GNTPError(
                "Cannot specify both gntp_callback and socket_callback_options"
            )
        
        if isinstance(gntp_callback, str):
            return URLCallback(gntp_callback)
        else:
            return gntp_callback
    
    if socket_callback_options:
        return SocketCallback(**socket_callback_options)
    
    return None


class BaseApp:
    """Base class for GNTP applications.
    
    Provides common functionality for Publisher and Subscriber.
    
    Attributes:
        custom_headers: List of (key, value) for custom X- headers
        app_specific_headers: List of (key, value) for Data- headers
        gntp_client: GNTP client instance
    """
    
    def __init__(
        self,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None,
        gntp_client_class: Optional[type] = None,
        **kwargs
    ):
        """Initialize base app.
        
        Args:
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            gntp_client_class: Client class (default: GNTPClient)
            **kwargs: Additional client arguments
        """
        self.custom_headers = custom_headers or []
        self.app_specific_headers = app_specific_headers or []
        
        if gntp_client_class is None:
            gntp_client_class = GNTPClient
        
        self.gntp_client = gntp_client_class(**kwargs)


class Publisher(BaseApp):
    """GNTP notification publisher.
    
    Registers an application and sends notifications to GNTP servers.
    
    Attributes:
        name: Application name
        icon: Optional application icon
        events: List of notification event definitions
    """
    
    def __init__(
        self,
        name: str,
        event_defs: List[Union[str, Tuple[str, bool], Event]],
        icon: Optional[Union[str, Resource]] = None,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None,
        gntp_client_class: Optional[type] = None,
        **kwargs
    ):
        """Initialize publisher.
        
        Args:
            name: Application name
            event_defs: Event definitions (str, tuple, or Event instances)
            icon: Optional app icon (URL or Resource)
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            gntp_client_class: Client class (default: GNTPClient)
            **kwargs: Additional client arguments
            
        Raises:
            GNTPValidationError: If no events defined
            
        Example:
            >>> from gntplib import Publisher, Event, Resource
            >>> events = [Event('update', 'Update Available')]
            >>> icon = Resource.from_file('icon.png')
            >>> pub = Publisher('MyApp', events, icon=icon)
        """
        self.name = name
        self.icon = self._coerce_to_resource(icon)
        self.events = coerce_to_events(event_defs)
        
        if not self.events:
            raise GNTPValidationError(
                "At least one notification event type must be defined"
            )
        
        super().__init__(
            custom_headers,
            app_specific_headers,
            gntp_client_class,
            **kwargs
        )
    
    def register(self, callback: Optional[Callable[[Response], None]] = None) -> None:
        """Register this publisher with the GNTP server.
        
        Must be called before publishing notifications.
        
        Args:
            callback: Optional callback called with server response
            
        Example:
            >>> pub = Publisher('MyApp', [Event('test')])
            >>> pub.register()
        """
        request = RegisterRequest(
            self.name,
            self.icon,
            self.events,
            self.custom_headers,
            self.app_specific_headers
        )
        self.gntp_client.process_request(request, callback)
    
    def publish(
        self,
        name: str,
        title: str,
        text: str = '',
        id_: Optional[str] = None,
        sticky: bool = False,
        priority: int = 0,
        icon: Optional[Union[str, Resource]] = None,
        coalescing_id: Optional[str] = None,
        callback: Optional[Callable] = None,
        gntp_callback: Optional[Union[str, SocketCallback]] = None,
        **socket_callback_options
    ) -> None:
        """Send a notification.
        
        Args:
            name: Event name (must be registered)
            title: Notification title
            text: Notification message (default: '')
            id_: Unique notification ID
            sticky: Keep until dismissed (default: False)
            priority: Priority -2 to 2 (default: 0)
            icon: Optional icon (URL or Resource)
            coalescing_id: ID for grouping notifications
            callback: Completion callback
            gntp_callback: URL or SocketCallback for notification events
            **socket_callback_options: Options for SocketCallback
            
        Example:
            >>> pub.publish(
            ...     'update',
            ...     'New Version',
            ...     'Version 2.0 is available',
            ...     priority=1,
            ...     sticky=True
            ... )
        """
        notification = Notification(
            name,
            title,
            text,
            id_=id_,
            sticky=sticky,
            priority=priority,
            icon=self._coerce_to_resource(icon),
            coalescing_id=coalescing_id,
            callback=coerce_to_callback(gntp_callback, **socket_callback_options)
        )
        
        request = NotifyRequest(
            self.name,
            notification,
            self.custom_headers,
            self.app_specific_headers
        )
        
        self.gntp_client.process_request(
            request,
            callback,
            socket_callback=notification.socket_callback
        )
    
    def _coerce_to_resource(
        self,
        value: Optional[Union[str, Resource]]
    ) -> Optional[Resource]:
        """Convert value to Resource if needed."""
        if value is None or isinstance(value, Resource):
            return value
        if isinstance(value, str):
            return Resource(url=value)
        return value
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"Publisher(name={self.name!r}, events={len(self.events)})"


class Notifier(Publisher):
    """Deprecated: Use Publisher instead."""
    
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            'Notifier is deprecated, use Publisher instead',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
    
    def notify(self, *args, **kwargs):
        """Deprecated: Use publish() instead."""
        import warnings
        warnings.warn(
            'notify() method is deprecated, use publish() instead',
            DeprecationWarning,
            stacklevel=2
        )
        self.publish(*args, **kwargs)


class Subscriber(BaseApp):
    """GNTP notification subscriber.
    
    Subscribes to receive notifications from a GNTP hub.
    
    Attributes:
        id_: Unique subscriber ID
        name: Subscriber name
        hub: Hub (host, port) tuple
        password: Hub password
        port: Subscriber port
        ttl: Subscription time-to-live
    """
    
    def __init__(
        self,
        id_: str,
        name: str,
        hub: Union[str, Tuple[str, int]],
        password: str,
        port: int = DEFAULT_PORT,
        custom_headers: Optional[List[Tuple[str, Any]]] = None,
        app_specific_headers: Optional[List[Tuple[str, Any]]] = None,
        gntp_client_class: Optional[type] = None,
        **kwargs
    ):
        """Initialize subscriber.
        
        Args:
            id_: Unique subscriber ID
            name: Subscriber name
            hub: Hub address (hostname or (host, port) tuple)
            password: Hub password
            port: Subscriber port (default: 23053)
            custom_headers: Custom X- headers
            app_specific_headers: App Data- headers
            gntp_client_class: Client class (default: GNTPClient)
            **kwargs: Additional client arguments
            
        Example:
            >>> sub = Subscriber(
            ...     'sub-123',
            ...     'MySubscriber',
            ...     'hub.example.com',
            ...     'secret'
            ... )
        """
        self.id_ = id_
        self.name = name
        
        # Parse hub address
        if isinstance(hub, str):
            self.hub = (hub, DEFAULT_PORT)
        else:
            self.hub = hub
        
        self.password = password
        self.port = port
        self.ttl = DEFAULT_TTL
        
        # Initialize with hub connection settings
        super().__init__(
            custom_headers,
            app_specific_headers,
            gntp_client_class,
            host=self.hub[0],
            port=self.hub[1],
            password=self.password,
            **kwargs
        )
    
    def subscribe(
        self,
        callback: Optional[Callable[[Response], None]] = None
    ) -> None:
        """Send subscription request to hub.
        
        Updates ttl attribute with value from server response.
        
        Args:
            callback: Optional callback (default: updates ttl)
            
        Example:
            >>> sub.subscribe()
            >>> print(f"Subscription TTL: {sub.ttl} seconds")
        """
        request = SubscribeRequest(
            self.id_,
            self.name,
            self.port,
            self.custom_headers,
            self.app_specific_headers
        )
        
        self.gntp_client.process_request(
            request,
            callback or self.store_ttl
        )
    
    def store_ttl(self, response: Response) -> None:
        """Store TTL from subscription response.
        
        Args:
            response: Response from SUBSCRIBE request
        """
        ttl_str = response.headers.get('Subscription-TTL', str(DEFAULT_TTL))
        try:
            self.ttl = int(ttl_str)
        except ValueError:
            self.ttl = DEFAULT_TTL
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Subscriber(id={self.id_!r}, name={self.name!r}, "
            f"hub={self.hub[0]}:{self.hub[1]})"
        )