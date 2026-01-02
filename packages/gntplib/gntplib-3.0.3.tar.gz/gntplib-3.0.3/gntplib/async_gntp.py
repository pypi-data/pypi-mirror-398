#!/usr/bin/env python3

# File: gntplib/async_gntp.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Asynchronous GNTP implementation using Tornado
# License: MIT

"""Asynchronous GNTP implementation using Tornado.

This module provides async/await based GNTP communication using the
Tornado framework. Requires Python 3.7+ and Tornado 5.0+.

Example:
    >>> import asyncio
    >>> from gntplib.async_gntp import AsyncPublisher, AsyncResource
    >>> from gntplib import Event
    >>> 
    >>> async def main():
    ...     icon = AsyncResource('https://example.com/icon.png')
    ...     pub = AsyncPublisher('MyApp', [Event('test')], icon=icon)
    ...     pub.register()
    ...     pub.publish('test', 'Hello', 'World')
    >>> 
    >>> asyncio.run(main())
"""

import logging
import socket
import asyncio
from typing import List, Optional, Tuple, Any, Union

try:
    from tornado import httpclient, ioloop, iostream
    TORNADO_AVAILABLE = True
except ImportError:
    TORNADO_AVAILABLE = False
    httpclient = ioloop = iostream = None

from .lib import Publisher as SyncPublisher, Subscriber as SyncSubscriber
from .models import Resource, Event
from .connections import BaseGNTPConnection, GNTPClient
from .requests import RegisterRequest, NotifyRequest
from .constants import MESSAGE_DELIMITER, DEFAULT_PORT
from .exceptions import GNTPError

__all__ = [
    'AsyncPublisher',
    'AsyncSubscriber',
    'AsyncGNTPConnection',
    'AsyncGNTPClient',
    'AsyncResource',
    'fetch_async_resources_in_parallel',
    'collect_async_resources'
]

logger = logging.getLogger(__name__)


def _check_tornado():
    """Check if Tornado is available."""
    if not TORNADO_AVAILABLE:
        raise ImportError(
            "Tornado is required for async functionality. "
            "Install with: pip install tornado"
        )


class AsyncPublisher(SyncPublisher):
    """Asynchronous GNTP notification publisher.
    
    Same as Publisher but uses AsyncGNTPClient for non-blocking operations.
    Requires Tornado.
    
    Example:
        >>> import asyncio
        >>> from gntplib.async_gntp import AsyncPublisher
        >>> from gntplib import Event
        >>> 
        >>> async def main():
        ...     pub = AsyncPublisher('MyApp', [Event('test')])
        ...     pub.register()
        ...     pub.publish('test', 'Title', 'Message')
        >>> 
        >>> asyncio.run(main())
    """
    
    def __init__(
        self,
        name: str,
        event_defs: List[Union[str, Tuple[str, bool], Event]],
        icon: Optional[Any] = None,
        io_loop: Optional['ioloop.IOLoop'] = None,
        **kwargs
    ):
        """Initialize async publisher.
        
        Args:
            name: Application name
            event_defs: Event definitions
            icon: Optional app icon (can be AsyncResource)
            io_loop: Tornado IOLoop (default: current loop)
            **kwargs: Additional client arguments
            
        Raises:
            ImportError: If Tornado is not installed
        """
        _check_tornado()
        
        io_loop = io_loop or ioloop.IOLoop.current()
        
        super().__init__(
            name,
            event_defs,
            icon,
            gntp_client_class=AsyncGNTPClient,
            io_loop=io_loop,
            **kwargs
        )


class AsyncSubscriber(SyncSubscriber):
    """Asynchronous GNTP notification subscriber.
    
    Same as Subscriber but uses AsyncGNTPClient for non-blocking operations.
    Requires Tornado.
    
    Example:
        >>> import asyncio
        >>> from gntplib.async_gntp import AsyncSubscriber
        >>> 
        >>> async def main():
        ...     sub = AsyncSubscriber('id', 'name', 'hub.example.com', 'pass')
        ...     sub.subscribe()
        >>> 
        >>> asyncio.run(main())
    """
    
    def __init__(
        self,
        id_: str,
        name: str,
        hub: Union[str, Tuple[str, int]],
        password: str,
        port: int = DEFAULT_PORT,
        io_loop: Optional['ioloop.IOLoop'] = None,
        **kwargs
    ):
        """Initialize async subscriber.
        
        Args:
            id_: Unique subscriber ID
            name: Subscriber name
            hub: Hub address
            password: Hub password
            port: Subscriber port (default: 23053)
            io_loop: Tornado IOLoop (default: current loop)
            **kwargs: Additional client arguments
            
        Raises:
            ImportError: If Tornado is not installed
        """
        _check_tornado()
        
        io_loop = io_loop or ioloop.IOLoop.current()
        
        super().__init__(
            id_,
            name,
            hub,
            password,
            port=port,
            gntp_client_class=AsyncGNTPClient,
            io_loop=io_loop,
            **kwargs
        )


class AsyncGNTPConnection(BaseGNTPConnection):
    """Asynchronous GNTP connection using Tornado IOStream.
    
    Provides non-blocking socket communication with GNTP server.
    
    Attributes:
        stream: Tornado IOStream for async socket operations
    """
    
    def __init__(
        self,
        address: Tuple[str, int],
        timeout: float,
        final_callback: Any,
        socket_callback: Optional[Any] = None,
        io_loop: Optional['ioloop.IOLoop'] = None
    ):
        """Initialize async connection.
        
        Args:
            address: (host, port) tuple
            timeout: Connection timeout in seconds
            final_callback: Callback when operation completes
            socket_callback: Optional socket event callback
            io_loop: Tornado IOLoop (default: current loop)
            
        Raises:
            ImportError: If Tornado is not installed
        """
        _check_tornado()
        
        super().__init__(final_callback, socket_callback)
        
        sock = socket.create_connection(address, timeout=timeout)
        self.stream = iostream.IOStream(sock, io_loop=io_loop)
    
    def write_message(self, message: bytes) -> None:
        """Send message to server asynchronously.
        
        Args:
            message: Message bytes to send
        """
        self.stream.write(message)
    
    def read_message(self, callback: Any) -> None:
        """Read message from server asynchronously.
        
        Args:
            callback: Function to call with received message
        """
        self.stream.read_until(MESSAGE_DELIMITER, callback)
    
    def close(self) -> None:
        """Close the stream."""
        if self.stream is not None:
            self.stream.close()
            self.stream = None


class AsyncGNTPClient(GNTPClient):
    """Asynchronous GNTP client using Tornado.
    
    Extends GNTPClient with async resource fetching capabilities.
    
    Attributes:
        io_loop: Tornado IOLoop instance
    """
    
    def __init__(
        self,
        io_loop: Optional['ioloop.IOLoop'] = None,
        **kwargs
    ):
        """Initialize async client.
        
        Args:
            io_loop: Tornado IOLoop (default: current loop)
            **kwargs: Additional arguments for GNTPClient
            
        Raises:
            ImportError: If Tornado is not installed
        """
        _check_tornado()
        
        super().__init__(connection_class=AsyncGNTPConnection, **kwargs)
        self.io_loop = io_loop or ioloop.IOLoop.current()
    
    async def process_request(
        self,
        request: Any,
        callback: Any,
        **kwargs
    ) -> None:
        """Process request asynchronously.
        
        If request contains AsyncResource instances, fetches them
        before sending the request.
        
        Args:
            request: GNTP request to process
            callback: Callback when operation completes
            **kwargs: Additional connection arguments
        """
        # Fetch async resources first
        async_resources = collect_async_resources(request)
        if async_resources:
            await fetch_async_resources_in_parallel(async_resources)
        
        # Process request normally
        super().process_request(
            request,
            callback,
            io_loop=self.io_loop,
            **kwargs
        )


class AsyncResource(Resource):
    """Resource that will be fetched asynchronously from URL.
    
    Use this class when you want to fetch icons or images from
    remote URLs asynchronously before sending the notification.
    
    Attributes:
        url: URL to fetch resource from
        data: Resource data (populated after fetch)
    """
    
    def __init__(self, url: str):
        """Initialize async resource.
        
        Args:
            url: URL to fetch resource from
            
        Example:
            >>> icon = AsyncResource('https://example.com/icon.png')
        """
        super().__init__(data=None)
        self.url = url
    
    def __repr__(self) -> str:
        """Return string representation."""
        status = f"{len(self.data)} bytes" if self.data else "not fetched"
        return f"AsyncResource(url={self.url!r}, {status})"


async def fetch_async_resources_in_parallel(
    async_resources: List[AsyncResource]
) -> List[AsyncResource]:
    """Fetch multiple AsyncResource URLs in parallel.
    
    Uses asyncio.gather to fetch all resources concurrently.
    Failed fetches are logged but don't stop the function.
    
    Args:
        async_resources: List of AsyncResource instances
        
    Returns:
        Same list with data populated
        
    Example:
        >>> resources = [
        ...     AsyncResource('https://example.com/icon1.png'),
        ...     AsyncResource('https://example.com/icon2.png')
        ... ]
        >>> await fetch_async_resources_in_parallel(resources)
    """
    _check_tornado()
    
    http_client = httpclient.AsyncHTTPClient()
    
    async def fetch_one(resource: AsyncResource) -> Tuple[AsyncResource, Any]:
        """Fetch a single resource with error handling."""
        try:
            response = await http_client.fetch(resource.url)
            return resource, response
        except Exception as e:
            logger.warning(f"Failed to fetch {resource.url!r}: {e}")
            return resource, None
    
    # Fetch all resources concurrently
    fetch_tasks = [fetch_one(resource) for resource in async_resources]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=False)
    
    # Process results
    for resource, response in results:
        if response is None:
            logger.warning(f"Failed to fetch {resource.url!r}")
            resource.data = None
        elif hasattr(response, 'error') and response.error:
            logger.warning(f"Failed to fetch {resource.url!r}: {response.error}")
            resource.data = None
        else:
            resource.data = response.body
    
    return async_resources


def collect_async_resources(request: Any) -> List[AsyncResource]:
    """Collect all AsyncResource instances from a request.
    
    Traverses the request object to find all AsyncResource instances
    that need to be fetched before the request can be sent.
    
    Args:
        request: GNTP request object
        
    Returns:
        List of unique AsyncResource instances
        
    Example:
        >>> from gntplib import Event
        >>> from gntplib.requests import RegisterRequest
        >>> icon = AsyncResource('https://example.com/icon.png')
        >>> request = RegisterRequest('MyApp', icon, [Event('test')])
        >>> resources = collect_async_resources(request)
    """
    resources = []
    
    # Collect from different request types
    if isinstance(request, RegisterRequest):
        resources = [request.app_icon] + [e.icon for e in request.events]
    elif isinstance(request, NotifyRequest):
        resources = [request.notification.icon]
    
    # Collect from custom headers
    resources.extend([
        value for _, value in request.custom_headers
        if isinstance(value, AsyncResource)
    ])
    
    # Collect from app-specific headers
    resources.extend([
        value for _, value in request.app_specific_headers
        if isinstance(value, AsyncResource)
    ])
    
    # Return unique AsyncResource instances only
    unique_resources = list(set(
        r for r in resources
        if isinstance(r, AsyncResource)
    ))
    
    return unique_resources


# Deprecated alias
class AsyncNotifier(AsyncPublisher):
    """Deprecated: Use AsyncPublisher instead."""
    
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            'AsyncNotifier is deprecated, use AsyncPublisher instead',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


# Deprecated alias
class AsyncIcon(AsyncResource):
    """Deprecated: Use AsyncResource instead."""
    
    def __init__(self, url: str):
        import warnings
        warnings.warn(
            'AsyncIcon is deprecated, use AsyncResource instead',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(url)