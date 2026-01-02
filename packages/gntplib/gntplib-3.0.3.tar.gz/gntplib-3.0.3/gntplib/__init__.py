try:
    from . __version__ import version
except:
    from __version__ import version

f"""GNTP Library - Growl Notification Transport Protocol Client Library.

This module provides a Python 3 implementation of the Growl Notification
Transport Protocol (GNTP) client library for sending notifications to
Growl-compatible notification systems.

Main Components:
    - Publisher: Send notifications to GNTP servers
    - Subscriber: Subscribe to GNTP notification feeds
    - Event: Define notification types
    - Resource: Handle binary resources (icons, images)
    - AsyncPublisher/AsyncSubscriber: Async variants using Tornado

Basic Usage:
    >>> from gntplib import publish
    >>> publish('MyApp', 'MyEvent', 'Hello', 'World')

For more control:
    >>> from gntplib import Publisher, Event
    >>> events = [Event('update', 'Software Update')]
    >>> pub = Publisher('MyApp', events)
    >>> pub.register()
    >>> pub.publish('update', 'New Version', 'Version 2.0 available')

GNTP Specification: http://www.growlforwindows.com/gfw/help/gntp.aspx

Author: Hadi Cahyadi <cumulus13@gmail.com>
License: MIT
Version: {version}
"""

from typing import List, Optional, Union

from .lib import (
    notify,
    publish,
    subscribe,
    Event,
    Publisher,
    Subscriber,
    Resource,
    SocketCallback,
)

from .async_gntp import (
    AsyncPublisher,
    AsyncSubscriber,
    AsyncGNTPConnection,
    AsyncGNTPClient,
    AsyncResource,
    fetch_async_resources_in_parallel,
    collect_async_resources,
)

from .exceptions import GNTPError
import traceback
from pathlib import Path
import os

def get_version():
    """
    Get the version of the ddf module.
    Version is taken from the __version__.py file if it exists.
    The content of __version__.py should be:
    version = "0.33"
    """
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
    except Exception as e:
        if os.getenv('TRACEBACK') and os.getenv('TRACEBACK') in ['1', 'true', 'True']:
            print(traceback.format_exc())
        else:
            print(f"ERROR: {e}")

    return "3.0.0"

__version__ = version or get_version()
__author__ = 'GNTP Library Contributors'
__license__ = 'MIT'

__all__ = [
    # Core functions
    'notify',
    'publish',
    'subscribe',
    
    # Core classes
    'Event',
    'Publisher',
    'Subscriber',
    'Resource',
    'SocketCallback',
    
    # Async classes
    'AsyncPublisher',
    'AsyncSubscriber',
    'AsyncGNTPConnection',
    'AsyncGNTPClient',
    'AsyncResource',
    
    # Async utilities
    'fetch_async_resources_in_parallel',
    'collect_async_resources',
    
    # Exceptions
    'GNTPError',
]


# Convenience functions for quick access
def quick_notify(
    app_name: str,
    event_name: str,
    title: str,
    text: str = '',
    icon: Optional[Union[str, Resource]] = None,
    priority: int = 0,
    sticky: bool = False
) -> None:
    """Send a quick notification with common parameters.
    
    This is a convenience wrapper around publish() with additional parameters.
    
    Args:
        app_name: Name of the application sending the notification
        event_name: Name of the event/notification type
        title: Notification title
        text: Notification message body (default: '')
        icon: Optional icon URL or Resource object
        priority: Priority level from -2 to 2 (default: 0)
        sticky: Whether notification stays until dismissed (default: False)
        
    Example:
        >>> quick_notify('MyApp', 'Alert', 'Warning', 'System overheating',
        ...              priority=1, sticky=True)
    """
    publisher = Publisher(app_name, [Event(event_name)], icon=icon)
    publisher.register()
    publisher.publish(
        event_name,
        title,
        text,
        priority=priority,
        sticky=sticky,
        icon=icon
    )